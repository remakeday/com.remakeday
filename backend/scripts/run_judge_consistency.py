"""run_judge_consistency.py — Evaluator 판정 일치율 + 소설 통과 테스트 (작업지시서 §P6).

1) 같은 (정답 주장, 유저 주장 top3) 세트를 EVALUATOR_VERDICT_SYSTEM으로 N회(기본 10)
   반복 → verdict 일치율 (게이트: ≥95%).
2) 세계 접촉 없는 서술 10종(판타지/일상/추상)을 유저 주장 세트로 넣고 정답 주장과
   confirm되는 비율이 0인지 (게이트: 소설 통과 0/10).

    .venv/bin/python scripts/run_judge_consistency.py --n 3 --novels 3
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import runner_common as rc  # noqa: E402

from apps.engine.app.dtos.llm_output_dto import EvaluatorVerdictOutput  # noqa: E402
from apps.engine.app.use_cases import prompts  # noqa: E402
from apps.engine.app.use_cases.harness import run_with_harness  # noqa: E402
from apps.scenarios.scenario_a.adapter import build as build_scenario  # noqa: E402

# ── 일치율 세트: (정답 주장, 유저 주장 top3) — 확인/경계/무관 케이스 ──
CONSISTENCY_SETS = [
    ("채연이 아프다",
     ["채연이 아픈 것 같다", "민석이 방송실 근처를 서성였다", "배급이 늦게 나왔다"]),
    ("채연은 이송될까 봐 숨겼다",
     ["채연이 밥을 남겼다", "은상이 소문을 냈다", "검진이 오후에 있었다"]),
    ("관리자와 우리는 다른 종이다",
     ["관리자는 방송으로만 존재한다", "우리는 관리자와 다른 것 같다", "트럭이 밤에 왔다"]),
]

# ── 소설 10종 — 세계 접촉 없는 서술 (판타지/일상/추상) ──────────────
NOVELS = [
    ["용이 마을을 태웠다", "기사가 검을 뽑았다", "공주가 도망쳤다"],
    ["나는 아침에 커피를 마셨다", "지하철이 늦게 왔다", "회사에 지각했다"],
    ["시간은 강물처럼 흐른다", "기억은 조금씩 흐려진다", "어제와 오늘은 닮았다"],
    ["우주선이 화성에 착륙했다", "선장이 지구로 신호를 보냈다", "모래폭풍이 불었다"],
    ["고양이가 소파에서 잤다", "비가 하루 종일 왔다", "우산을 잃어버렸다"],
    ["마법사가 탑에 산다", "제자가 주문을 외웠다", "촛불이 꺼졌다"],
    ["할머니가 김치를 담갔다", "장독대가 마당에 있다", "겨울이 빨리 왔다"],
    ["로봇이 시를 썼다", "심사위원이 울었다", "상은 사람이 받았다"],
    ["숫자는 거짓말을 하지 않는다", "통계가 진실을 가린다", "평균은 아무도 아니다"],
    ["어부가 그물을 던졌다", "바다가 조용했다", "달이 물 위에 떠 있었다"],
]

# 소설을 대조할 대표 정답 주장 (칸별 1개)
NOVEL_TRUTH_CODES = ["cause-1", "motive-1", "identity-2"]


def verdict_once(llm, truth: str, claims: list[str]) -> str:
    system = prompts.EVALUATOR_VERDICT_SYSTEM.format(
        truth_claim=truth,
        user_claims="\n".join(f"{i}. {c}" for i, c in enumerate(claims)),
    )
    out, _ = run_with_harness(
        llm, [rc.sys_msg(system), rc.usr_msg("판정하라.")],
        EvaluatorVerdictOutput, role="evaluator",
    )
    return out.verdict if out else "parse_error"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluator 판정 일치율 + 소설 통과 테스트")
    rc.add_common_args(parser, default_model=rc.DEFAULT_JUDGE_MODEL, default_n=10)
    parser.add_argument("--novels", type=int, default=10, help="소설 테스트 개수 (기본 10)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    base_url = args.ollama_url or rc.ollama_base_url()
    rc.check_ollama(base_url, [args.model])
    llm = rc.make_llm(args.model, base_url)

    bundle = build_scenario().bundle()
    truths = {t.code: t.text for t in bundle.truth_claims}

    # 1) 일치율
    print(f"\n### 판정 일치율 · model={args.model} · N={args.n}/세트\n")
    rows, rates = [], []
    for truth, claims in CONSISTENCY_SETS:
        verdicts = [verdict_once(llm, truth, claims) for _ in range(args.n)]
        counts = Counter(verdicts)
        mode, mode_n = counts.most_common(1)[0]
        rate = mode_n / len(verdicts)
        rates.append(rate)
        rows.append([truth, mode, f"{mode_n}/{len(verdicts)}", rate])
        if args.verbose:
            print(f"  {truth} → {verdicts}")
    consistency = sum(rates) / len(rates)
    rc.print_table(["정답 주장", "최빈 verdict", "빈도", "일치율"], rows)
    print(f"\n평균 일치율: {consistency:.2%} → 게이트(≥95%): {'통과' if consistency >= 0.95 else '미달'}")

    # 2) 소설 통과
    novels = NOVELS[: args.novels]
    truth_texts = [truths[c] for c in NOVEL_TRUTH_CODES if c in truths]
    print(f"\n### 소설 통과 테스트 · {len(novels)}종 × 정답 주장 {len(truth_texts)}개\n")
    confirmed_novels = 0
    novel_rows = []
    for claims in novels:
        hits = [t for t in truth_texts if verdict_once(llm, t, claims) == "confirmed"]
        confirmed_novels += bool(hits)
        novel_rows.append([claims[0] + " …", "CONFIRM(" + "; ".join(hits) + ")" if hits else "차단"])
    rc.print_table(["소설 서술", "결과"], novel_rows)
    print(f"\n소설 통과(오확인): {confirmed_novels}/{len(novels)} → 게이트(0): "
          f"{'통과' if confirmed_novels == 0 else '미달'}")

    path = rc.append_metric(
        args.out, "judge_consistency", args.model,
        n=args.n, sets=len(CONSISTENCY_SETS),
        consistency=consistency,
        novels=len(novels), novels_confirmed=confirmed_novels,
        gate_pass=(consistency >= 0.95 and confirmed_novels == 0),
    )
    print(f"\nmetrics → {path}")


if __name__ == "__main__":
    main()
