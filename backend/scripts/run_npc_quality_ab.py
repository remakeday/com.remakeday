"""run_npc_quality_ab.py — NPC 발화 품질 쌍대 블라인드 A/B (E6과 별개 축).

E6 formal ON 원문의 transcripts를 재사용해 같은 발화·같은 회차의 두 모델 응답을
익명 쌍으로 judge(gemma3:12b)에 제시한다. 항목 4개 × 3표 × 순서 2회(스왑).
스왑 후 다수결이 서로 일치하는 쌍만 유효 판정 — 불일치는 위치 편향으로 무효 처리.
단일 종합 점수는 만들지 않는다.

    .venv/bin/python scripts/run_npc_quality_ab.py \
      --raw docs/review-verification/2026-09-14-npc-descent/e6-descent-formal-<stamp>.json
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import runner_common as rc  # noqa: E402
from pydantic import BaseModel, ConfigDict  # noqa: E402

from apps.engine.app.use_cases.harness import run_with_harness  # noqa: E402

CRITERIA = {
    "한국어_자연스러움": "어느 응답이 더 자연스러운 한국어인가 — 비문·직역투·외국 문자 혼입이 적은 쪽",
    "7세_말투": "어느 응답이 더 일곱 살 어린이다운 말투인가 — 짧고 단순하며 어른스러운 어휘·논평이 없는 쪽",
    "페르소나_적합": "어느 응답이 격리 구역에서 사는 일곱 살 아이라는 인물·세계관에 더 맞는가",
    "질문_관련성": "어느 응답이 질문받은 내용에 더 직접적으로 답하는가",
}
VOTES = 3

# 비한글 스크립트 혼입 — 한자·가나·키릴 (영문은 korean_only와 동일 기준으로 별도)
_FOREIGN_SCRIPT_RE = re.compile(r"[一-鿿㐀-䶿぀-ヿЀ-ӿ]")
_ENGLISH_WORD_RE = re.compile(r"[A-Za-z]{2,}")
_HANGUL_RE = re.compile(r"[가-힣]")


class ABVote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    winner: Literal["1", "2", "tie"]
    why: str = ""


def judge_once(judge_llm, criterion_desc, utterance, reply1, reply2):
    system = (
        "격리 구역이 배경인 게임에서 일곱 살 아이 NPC의 응답 두 개를 비교 판정한다.\n"
        f"판정 기준(이것 하나만 본다): {criterion_desc}\n"
        '더 적절한 쪽을 고른다. 우열을 가릴 수 없으면 tie.\n'
        '출력: JSON {"winner": "1"|"2"|"tie", "why": "한 줄"}'
    )
    material = f"[질문] {utterance}\n[응답1] {reply1}\n[응답2] {reply2}"
    out, _ = run_with_harness(
        judge_llm, [rc.sys_msg(system), rc.usr_msg(material)], ABVote, role="judge")
    return out.winner if out else None


def majority(winners: list[str | None]) -> str | None:
    valid = [w for w in winners if w is not None]
    if not valid:
        return None
    top = Counter(valid).most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return "tie"  # 3표가 갈려 다수 없음 — 무승부로 본다
    return top[0][0]


def deterministic_stats(replies: list[str]) -> dict:
    foreign = sum(1 for r in replies if _FOREIGN_SCRIPT_RE.search(r))
    english = sum(1 for r in replies
                  if len(_ENGLISH_WORD_RE.findall(r)) >= 2
                  or (_ENGLISH_WORD_RE.findall(r) and not _HANGUL_RE.search(r)))
    return {
        "n": len(replies),
        "foreign_script_replies": foreign,
        "foreign_script_rate": round(foreign / len(replies), 4) if replies else None,
        "english_violation_replies": english,
        "mean_len_chars": round(sum(len(r) for r in replies) / len(replies), 1) if replies else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="NPC 발화 품질 쌍대 블라인드 A/B")
    parser.add_argument("--raw", required=True, help="E6 formal ON 원문 JSON (프로젝트 루트 기준)")
    parser.add_argument("--raw-b", default=None,
                        help="model-b의 transcripts가 다른 원문에 있으면 그 JSON (기본: --raw와 동일)")
    parser.add_argument("--model-a", default="exaone3.5:7.8b")
    parser.add_argument("--model-b", default="qwen3.5:4b")
    parser.add_argument("--judge-model", default=rc.DEFAULT_JUDGE_MODEL)
    parser.add_argument("--base-url", dest="ollama_url", default=None)
    parser.add_argument("--out", default=rc.DEFAULT_OUT)
    parser.add_argument("--out-dir", default="docs/review-verification/2026-09-14-npc-descent")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    base_url = args.ollama_url or rc.ollama_base_url()
    rc.check_ollama(base_url, [args.judge_model])
    judge_llm = rc.make_llm(args.judge_model, base_url)

    raw = json.loads((rc.PROJECT_ROOT / args.raw).read_text(encoding="utf-8"))
    raw_b = (json.loads((rc.PROJECT_ROOT / args.raw_b).read_text(encoding="utf-8"))
             if args.raw_b else raw)
    by_model = {c["model"]: c for c in raw["cells"] if c.get("policy", "on") == "on"}
    by_model_b = {c["model"]: c for c in raw_b["cells"] if c.get("policy", "on") == "on"}
    if args.model_a not in by_model:
        raise SystemExit(f"[에러] --raw에 {args.model_a} 셀이 없다: {sorted(by_model)}")
    if args.model_b not in by_model_b:
        raise SystemExit(f"[에러] --raw-b에 {args.model_b} 셀이 없다: {sorted(by_model_b)}")
    ta = {(t["item"], t["i"]): t for t in by_model[args.model_a]["transcripts"]}
    tb = {(t["item"], t["i"]): t for t in by_model_b[args.model_b]["transcripts"]}
    keys = sorted(set(ta) & set(tb))
    print(f"### NPC 품질 A/B · A={args.model_a} vs B={args.model_b} · 쌍 {len(keys)} "
          f"· 항목 {len(CRITERIA)} × {VOTES}표 × 순서 2 · judge={args.judge_model}\n", flush=True)

    pairs = []
    tally = {c: Counter() for c in CRITERIA}      # A/B/tie/invalid per criterion
    for key in keys:
        a, b = ta[key], tb[key]
        utterance = a["utterance"]
        row = {"item": key[0], "i": key[1], "utterance": utterance,
               "reply_a": a["reply"], "reply_b": b["reply"], "criteria": {}}
        for crit, desc in CRITERIA.items():
            # 순서 1: (A=응답1, B=응답2) / 순서 2: 스왑
            m1 = majority([judge_once(judge_llm, desc, utterance, a["reply"], b["reply"])
                           for _ in range(VOTES)])
            m2 = majority([judge_once(judge_llm, desc, utterance, b["reply"], a["reply"])
                           for _ in range(VOTES)])
            map1 = {"1": "A", "2": "B", "tie": "tie", None: None}[m1]
            map2 = {"1": "B", "2": "A", "tie": "tie", None: None}[m2]
            verdict = map1 if (map1 is not None and map1 == map2) else "invalid"
            tally[crit][verdict] += 1
            row["criteria"][crit] = {"order1": map1, "order2": map2, "verdict": verdict}
        pairs.append(row)
        if args.verbose:
            print(f"  [{key[0]}#{key[1]}] " + " ".join(
                f"{c}={row['criteria'][c]['verdict']}" for c in CRITERIA), flush=True)

    stats_a = deterministic_stats([ta[k]["reply"] for k in keys])
    stats_b = deterministic_stats([tb[k]["reply"] for k in keys])
    stats_a["fallbacks"] = sum(1 for k in keys if ta[k].get("fallback"))
    stats_b["fallbacks"] = sum(1 for k in keys if tb[k].get("fallback"))

    summary = {}
    print()
    rc.print_table(
        ["항목", "A승", "B승", "무승부", "무효(편향)"],
        [[c, tally[c]["A"], tally[c]["B"], tally[c]["tie"], tally[c]["invalid"]] for c in CRITERIA])
    for c in CRITERIA:
        valid = tally[c]["A"] + tally[c]["B"] + tally[c]["tie"]
        summary[c] = {"a_wins": tally[c]["A"], "b_wins": tally[c]["B"],
                      "ties": tally[c]["tie"], "invalid": tally[c]["invalid"],
                      "valid_pairs": valid}
    print(f"\nA={args.model_a}: {stats_a}\nB={args.model_b}: {stats_b}")

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = rc.PROJECT_ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / f"npc-quality-ab-{stamp}.json"
    raw_path.write_text(json.dumps({
        "experiment": "npc_quality_ab", "source_raw": args.raw, "source_raw_b": args.raw_b,
        "model_a": args.model_a, "model_b": args.model_b,
        "judge": args.judge_model, "votes": VOTES, "orders": 2,
        "criteria": list(CRITERIA), "started_at": stamp,
        "summary": summary, "stats_a": stats_a, "stats_b": stats_b, "pairs": pairs,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    rc.append_metric(
        args.out, "npc_quality_ab", f"{args.model_a} vs {args.model_b}",
        judge=args.judge_model, votes=VOTES, orders=2, pairs=len(keys),
        summary={c: dict(tally[c]) for c in CRITERIA},
        foreign_script_rate_a=stats_a["foreign_script_rate"],
        foreign_script_rate_b=stats_b["foreign_script_rate"],
        mean_len_a=stats_a["mean_len_chars"], mean_len_b=stats_b["mean_len_chars"],
        fallbacks_a=stats_a["fallbacks"], fallbacks_b=stats_b["fallbacks"],
        source_raw=args.raw, source_raw_b=args.raw_b,
    )
    print(f"\n원문 → {raw_path}\nmetrics → {rc.resolve_out(args.out)}")


if __name__ == "__main__":
    main()
