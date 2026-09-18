"""직접 쓰기 대안 순위 — 어간 겹침 vs 임베딩(ollama 두 모델·gemini) 5셀 비교 (부록 A.20).

Run from the project root::

    backend/.venv/bin/python backend/scripts/run_rule_alternatives_eval.py
    backend/.venv/bin/python backend/scripts/run_rule_alternatives_eval.py --cells stem,qwen1536

골든 `rule_alternatives_golden.yml`(에이전트 작성, 미검수)의 문장마다 실경로와 같은 후보 풀
(시나리오 a의 rule_templates, named_targets로 좁힘)에서 전체 순위를 뽑아 top-1·top-3 적중률과 건당 지연을 잰다.
차원이 같아도 공간이 다르다 — 모델 간 비교는 벡터 코사인이 아니라 순위 일치도(top-1 일치·top-3 Jaccard·Kendall τ)로만 한다.
metrics.yml 줄은 stdout에만 찍는다(파일에 쓰지 않는다). 원문 결과는 output/rule-alternatives-2026-09-18/에 저장.
Gemini는 429·일일 상한이 나오면 재시도하지 않고 그 시점까지의 n으로 집계한다.
"""

import argparse
from datetime import datetime, timezone
from itertools import combinations
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter

import yaml
from google.genai import types

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from apps.engine.adapter.outbound.embedding.gemini_embedding import GeminiEmbedding
from apps.engine.adapter.outbound.embedding.ollama_embedding import OllamaEmbedding
from apps.engine.app.ports.output.embedding_port import EmbeddingPort
from apps.engine.app.use_cases.alternative_rank import EmbeddingRank, StemOverlapRank
from apps.engine.app.use_cases.intervention_interactor import named_targets, suggest_alternatives
from apps.engine.dependencies.engine_dependency import rule_templates
from apps.engine.dependencies.scenario_factory import build_scenario
from core.matrix.grid_keymaker_secret_manager import get_settings

DATE = "2026-09-18"
GOLDEN = BACKEND / "scripts/rule_alternatives_golden.yml"
OUT_DIR = ROOT / f"output/rule-alternatives-{DATE}"
PAIRS = [("gemini", "qwen1536"), ("gemini", "qwen2560"), ("qwen2560", "qwen1536"), ("gemini", "bge"),
         ("stem", "qwen1536"), ("stem", "gemini"),
         ("gemini3072", "gemini2560"), ("gemini3072", "gemini"), ("gemini2560", "qwen2560"), ("gemini3072", "qwen2560"),
         ("gemini1024", "bge"), ("gemini1024", "gemini"), ("gemini1024", "qwen2560")]


class GeminiOnce(GeminiEmbedding):
    """재시도 없는 1회 호출 — 429는 그대로 올려 러너가 기록한다(프로덕션 어댑터의 백오프는 그대로 둔다)."""

    def embed(self, texts, task_type=None):
        res = self._client.models.embed_content(
            model=self._model, contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=self._dimensions, task_type=task_type))
        return [e.values for e in res.embeddings]


class Probe(EmbeddingPort):
    """임베딩 포트를 감싸 실패·차원을 기록한다 — EmbeddingRank가 조용히 폴백해도 러너는 안다."""

    def __init__(self, inner):
        self._inner, self.errors, self.dims = inner, [], None

    def _record(self, vectors):
        self.dims = self.dims or len(vectors[0])
        return vectors

    def embed(self, texts):
        return self._record(self._call(lambda: self._inner.embed(texts)))

    def embed_documents(self, texts):
        return self._record(self._call(lambda: self._inner.embed_documents(texts)))

    def embed_query(self, text):
        return self._record([self._call(lambda: self._inner.embed_query(text))])[0]

    def _call(self, fn):
        try:
            return fn()
        except Exception as exc:
            self.errors.append(f"{type(exc).__name__}: {exc}")
            raise


def cells(base_url: str, gemini_key: str) -> dict[str, dict]:
    return {
        "stem": dict(provider="stem", model="-", dims=None, embedding=None),
        "qwen2560": dict(provider="ollama", model="qwen3-embedding:4b", dims=2560,
                         embedding=OllamaEmbedding(base_url, "qwen3-embedding:4b", dimensions=None)),
        "qwen1536": dict(provider="ollama", model="qwen3-embedding:4b", dims=1536,
                         embedding=OllamaEmbedding(base_url, "qwen3-embedding:4b", dimensions=1536)),
        "bge": dict(provider="ollama", model="bge-m3", dims=1024,
                    embedding=OllamaEmbedding(base_url, "bge-m3", dimensions=None, query_instruct=None)),
        "gemini": dict(provider="gemini", model="gemini-embedding-001", dims=1536, embedding=GeminiOnce(api_key=gemini_key, dimensions=1536)),
        # 차원 상향 검토(2026-09-18 사용자 질문): 둘이 같이 올릴 수 있는 최대는 qwen 상한 2560, Gemini 단독은 3072
        "gemini2560": dict(provider="gemini", model="gemini-embedding-001", dims=2560,
                           embedding=GeminiOnce(api_key=gemini_key, dimensions=2560)),
        "gemini3072": dict(provider="gemini", model="gemini-embedding-001", dims=3072,
                           embedding=GeminiOnce(api_key=gemini_key, dimensions=3072)),
        # bge-m3(1024 고정)와 같은 차원으로 — 로컬 VRAM 예산(bge 0.66GB) 구성의 쌍 비교
        "gemini1024": dict(provider="gemini", model="gemini-embedding-001", dims=1024,
                           embedding=GeminiOnce(api_key=gemini_key, dimensions=1024)),
    }


def parse_pair(label: str) -> tuple[str, str]:
    target, action = label.split("은 ", 1)
    return target, action


def run_cell(name: str, cell: dict, items: list[dict], templates: list[dict], playable: list[str]) -> dict:
    probe = Probe(cell["embedding"]) if cell["embedding"] else None
    rank = EmbeddingRank(probe) if probe else StemOverlapRank()
    actions = list(dict.fromkeys(t["action"] for t in templates))
    if probe:
        rank.rank("warmup", actions)  # 행동 문구 캐시 채움 — 건당 지연에서 제외
    rows, latencies = [], []
    for item in items:
        if probe and probe.errors:
            rows.append({**item, "ok": False, "ranking": None})
            continue
        names = named_targets(item["text"], playable) or playable[:2]  # preview_rule과 같은 후보 풀
        t0 = perf_counter()
        ranked = suggest_alternatives(item["text"], names, templates, max_n=len(templates), rank=rank)
        ms = (perf_counter() - t0) * 1000
        if probe and probe.errors:
            rows.append({**item, "ok": False, "ranking": None})
            continue
        ranking = [parse_pair(label) for label in ranked]
        expected = (item["target"], item["action"])
        rows.append({**item, "ok": True, "ranking": ranking, "hit1": ranking[0] == expected,
                     "hit3": expected in ranking[:3], "latency_ms": round(ms, 1)})
        latencies.append(ms)
    ok = [r for r in rows if r["ok"]]
    note = f"{len(ok)}/{len(items)} 성공, 지연은 행동 문구 캐시 이후 질의 1건 기준"
    if probe and probe.errors:
        err = probe.errors[0]
        note += f"; 오류 후 중단: {err}"
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            note += " (lifetutorial 실측 해석: 키 쿼터가 아니라 gemini-embedding 베이스 모델 전역 공용 풀, 대개 1초 안에 풀림)"
    return {
        "cell": name, "rows": rows, "errors": probe.errors if probe else [],
        "metric": {"runner": "rule_alternatives_eval", "date": DATE, "provider": cell["provider"], "model": cell["model"],
                   "dims": (probe.dims if probe else None) or cell["dims"], "n": len(ok),
                   "top1": _rate(ok, "hit1"), "top3": _rate(ok, "hit3"),
                   "latency_p50_ms": _pct(latencies, 0.5), "latency_p95_ms": _pct(latencies, 0.95), "note": note},
    }


def _rate(rows, key):
    return round(sum(r[key] for r in rows) / len(rows), 4) if rows else None


def _pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, round(q * (len(xs) - 1)))], 1)


def kendall_tau(a: list, b: list) -> float:
    """두 순열(같은 원소 집합)의 Kendall τ — 순수 파이썬, n ≤ 17."""
    pos = {x: i for i, x in enumerate(b)}
    ranks = [pos[x] for x in a]
    concordant = sum(1 for i, j in combinations(range(len(ranks)), 2) if ranks[i] < ranks[j])
    total = len(ranks) * (len(ranks) - 1) / 2
    return (2 * concordant - total) / total if total else 1.0


def agreement(results: dict, a: str, b: str) -> dict | None:
    if a not in results or b not in results:
        return None
    both = [(ra, rb) for ra, rb in zip(results[a]["rows"], results[b]["rows"]) if ra["ok"] and rb["ok"]]
    if not both:
        return {"a": a, "b": b, "n": 0}
    top1 = sum(ra["ranking"][0] == rb["ranking"][0] for ra, rb in both) / len(both)
    jaccard = statistics.mean(len(set(ra["ranking"][:3]) & set(rb["ranking"][:3])) / len(set(ra["ranking"][:3]) | set(rb["ranking"][:3]))
                              for ra, rb in both)
    tau = statistics.mean(kendall_tau(ra["ranking"], rb["ranking"]) for ra, rb in both)
    return {"a": a, "b": b, "n": len(both), "top1_agree": round(top1, 4), "top3_jaccard": round(jaccard, 4), "kendall_tau": round(tau, 4)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cells", default="stem,qwen2560,qwen1536,bge,gemini")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    s = get_settings()
    bundle = build_scenario("a").bundle()
    templates = rule_templates(bundle)
    playable = [c.name for c in bundle.characters if c.playable]
    items = yaml.safe_load(GOLDEN.read_text(encoding="utf-8"))["items"]
    all_cells = cells(s.ollama_base_url, s.gemini_api_key)

    results = {}
    for name in args.cells.split(","):
        results[name] = run_cell(name, all_cells[name], items, templates, playable)
        print(f"[{name}] {results[name]['metric']['note']}", file=sys.stderr)
    agreements = [x for x in (agreement(results, a, b) for a, b in PAIRS) if x]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or OUT_DIR / f"rule-alternatives-{stamp}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"date": DATE, "golden": str(GOLDEN.relative_to(ROOT)), "n_items": len(items),
                                  "templates": len(templates), "cells": results, "agreements": agreements},
                                 ensure_ascii=False, indent=2, default=list), encoding="utf-8")

    print("\n# docs/metrics.yml 줄 (stdout만 — 파일에는 쓰지 않음)")
    for r in results.values():
        print("- " + json.dumps(r["metric"], ensure_ascii=False))
    print("\n# 셀 쌍별 순위 일치도 (벡터 코사인 아님 — 다른 모델은 다른 공간)")
    print(f"{'pair':22} {'n':>3} {'top1_agree':>10} {'top3_jaccard':>12} {'kendall_tau':>11}")
    for x in agreements:
        pair = f"{x['a']}↔{x['b']}"
        if x["n"] == 0:
            print(f"{pair:22} {0:>3}  (겹치는 성공 건 없음)")
        else:
            print(f"{pair:22} {x['n']:>3} {x['top1_agree']:>10.3f} {x['top3_jaccard']:>12.3f} {x['kendall_tau']:>11.3f}")
    print(f"\n원문: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
