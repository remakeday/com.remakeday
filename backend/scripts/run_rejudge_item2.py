"""run_rejudge_item2.py — E6 항목 2('왜=몰라') 판정 스펙 v2 재판정.

배경: Scenario Director가 7세 스펙을 확정("애들도 이유를 지어낸다 — 단 근거가 없거나
자기 하고 싶은 얘기"). 기존 judge 기준('이유 문장이 있으면 FAIL')은 AGE7_POLICY
프롬프트 2번보다 엄격한 판정 결함이었다. run_age7_check.py의 항목 2 judge를 v2로
고친 뒤, 기존 E6 Formal ON transcripts의 응답을 **재생성 없이 재판정만** 한다.

    .venv/bin/python scripts/run_rejudge_item2.py
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import runner_common as rc  # noqa: E402
from run_age7_check import ITEMS  # noqa: E402 — v2 judge 텍스트를 그대로 쓴다

DEFAULT_SRC = ("docs/review-verification/2026-09-14-npc-descent/"
               "e6-descent-formal-20260914T053343Z.json")
ITEM_KEY = "2_왜=몰라"
ITEM_THRESHOLD = 0.7
JUDGE_VOTES = 3
ITEM_ORDER = ["1_사실대로", "2_왜=몰라", "3_3턴망각", "4_유도수용", "5_문자그대로"]


def collapse_v2(cell: dict, item2_rate: float) -> str:
    """§3.1 우선순위 재계산 — item2만 v2로 바꾼다. leak·schema·타 항목은 원 값."""
    rates = dict(cell["item_rates"])
    rates[ITEM_KEY] = item2_rate
    if cell["leak"]["rate"] > 0:
        return "leak"
    if cell["schema_validity"] is not None and cell["schema_validity"] < 0.98:
        return "schema"
    if rates.get("1_사실대로", 0.0) < ITEM_THRESHOLD:
        return "toddler"
    if sum(1 for k in ("2_왜=몰라", "4_유도수용", "5_문자그대로")
           if rates.get(k, 0.0) < ITEM_THRESHOLD) >= 2:
        return "adult"
    return "none"


def main() -> None:
    parser = argparse.ArgumentParser(description="E6 항목 2 판정 스펙 v2 재판정 (재생성 없음)")
    parser.add_argument("--src", default=DEFAULT_SRC, help="E6 Formal ON 원문 JSON")
    parser.add_argument("--judge-model", default=rc.DEFAULT_JUDGE_MODEL)
    parser.add_argument("--base-url", dest="ollama_url", default=None)
    parser.add_argument("--out", default=rc.DEFAULT_OUT)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    base_url = args.ollama_url or rc.ollama_base_url()
    rc.check_ollama(base_url, [args.judge_model])
    judge_llm = rc.make_llm(args.judge_model, base_url)
    judge_sys = next(it["judge"] for it in ITEMS if it["key"] == ITEM_KEY)

    src_path = rc.resolve_out(args.src)
    src = json.loads(src_path.read_text(encoding="utf-8"))
    assert all(c.get("policy") == "on" for c in src["cells"]), "ON 원문만 재판정한다"

    results = []
    for cell in src["cells"]:
        model = cell["model"]
        rows = [t for t in cell.get("transcripts", []) if t["item"] == ITEM_KEY]
        passed = 0
        agree_hits = agree_total = 0
        rejudged = []
        print(f"\n### 재판정 · {model} · {len(rows)}응답 × judge {JUDGE_VOTES}표", flush=True)
        for t in rows:
            material = (f"[질문] {t['utterance']}\n[NPC의 답] {t['reply']}\n"
                        f"[도구 호출] {t.get('tool') or '없음'}")
            votes = [rc.judge_pass(judge_llm, judge_sys, material)[0] for _ in range(JUDGE_VOTES)]
            valid = [x for x in votes if x is not None]
            ok = sum(valid) > len(valid) / 2 if valid else False
            if len(valid) == JUDGE_VOTES:
                agree_total += 1
                agree_hits += len(set(valid)) == 1
            passed += ok
            rejudged.append({**{k: t[k] for k in ("i", "utterance", "reply")},
                             "votes_v1": t["votes"], "votes_v2": votes, "pass_v2": ok})
            if args.verbose:
                print(f"    v1={t['votes']} → v2={votes} | {t['reply'][:60]}", flush=True)
        rate_v1 = cell["item_rates"][ITEM_KEY]
        rate_v2 = passed / len(rows) if rows else 0.0
        items_v2 = sum(1 for k, r in cell["item_rates"].items()
                       if (rate_v2 if k == ITEM_KEY else r) >= ITEM_THRESHOLD)
        row = {
            "model": model, "quant": cell["quant"], "policy": cell["policy"],
            "item2_rate_v1": rate_v1, "item2_rate_v2": round(rate_v2, 4),
            "items_passed_v1": cell["items_passed"], "items_passed_v2": items_v2,
            "collapse_v1": cell["collapse"], "collapse_v2": collapse_v2(cell, rate_v2),
            "judge_agreement_v2": round(agree_hits / agree_total, 4) if agree_total else None,
            "rejudged": rejudged,
        }
        results.append(row)
        print(f"  item2 {rate_v1} → {row['item2_rate_v2']} · items {row['items_passed_v1']} → "
              f"{items_v2} · collapse {row['collapse_v1']} → {row['collapse_v2']} · "
              f"일치 {row['judge_agreement_v2']}", flush=True)

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = src_path.parent / f"e6-rejudge-item2-{stamp}.json"
    out_path.write_text(json.dumps({
        "experiment": "E6", "rejudge": "item2-spec-v2", "src": src_path.name,
        "judge": args.judge_model, "judge_votes": JUDGE_VOTES, "started_at": stamp,
        "spec": "아이다운 근거 없는 지어내기·딴 얘기 PASS / 어른스러운 구조적 설명만 FAIL "
                "(Scenario Director 확정, 2026-09-14)",
        "cells": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    for row in results:
        rc.append_metric(
            args.out, "model_descent", row["model"],
            policy=row["policy"], tier="formal", runtime="ollama-cuda", host="rtx5060ti-16g",
            quant=row["quant"], note="rejudge-item2-spec-v2", src=src_path.name,
            item2_rate_v1=row["item2_rate_v1"], item2_rate_v2=row["item2_rate_v2"],
            items_passed_v2=row["items_passed_v2"], collapse_v2=row["collapse_v2"],
            judge_agreement=row["judge_agreement_v2"],
        )
    print(f"\n원문 → {out_path}\nmetrics → {rc.resolve_out(args.out)}")


if __name__ == "__main__":
    main()
