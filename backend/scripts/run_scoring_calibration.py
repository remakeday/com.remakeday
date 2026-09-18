"""run_scoring_calibration.py — 채점 밸런스 캘리브레이션 (골든 세트 3종, 오프라인).

게임 서버 없이 _judge와 같은 방식으로 EVALUATOR_VERDICT_SYSTEM을 직접 호출해
정답형·절반형·오답형 세트의 셀 점수·총점을 잰다.

성공 기준: 정답형 ≥ 60%(통과), 절반형 30~50%, 오답형 < 30%(통과 불가),
같은 세트 반복 시 총점 편차 ≤ 10%p.

    .venv/bin/python scripts/run_scoring_calibration.py --n 2
    .venv/bin/python scripts/run_scoring_calibration.py --n 1 --top3   # 조정 전 파이프라인(top3 후보) 재현
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import runner_common as rc  # noqa: E402

from apps.engine.app.dtos.llm_output_dto import EvaluatorVerdictOutput  # noqa: E402
from apps.engine.app.use_cases import prompts  # noqa: E402
from apps.engine.app.use_cases.harness import run_with_harness  # noqa: E402
from apps.engine.domain.entities import scoring_rules  # noqa: E402
from apps.engine.domain.value_objects.game_constants import CELLS  # noqa: E402
from apps.scenarios.scenario_a.adapter import build as build_scenario  # noqa: E402

# ── 골든 세트 3종 (플레이테스트 정답 취지 기반, truth_claims 대조용) ──

CORRECT = [  # 정답형 — 원인·동기·정체 전부 취지 포함 (8주장)
    "우리는 양돈장의 돼지다. 사람이 아니라 관리자가 기르는 동물이다.",
    "채연이 열이 나는 것을 숨겼다. 아픈 걸 들키지 않으려고 했다.",
    "채연은 들키면 트럭에 실려 갈까 봐 무서워서 숨겼다.",
    "검진에서 채연의 열이 안 잡혔고, 저녁까지 병이 퍼졌다.",
    "아픈 개체가 3명을 넘어서 구역이 폐쇄됐다.",
    "검진에서 걸린 개체는 트럭으로 이송된다. 충식은 어제 이송돼 돌아오지 않았다. 그 두려움은 진짜였다.",
    "트럭 옆면에 ○○축산이라고 써 있다. 관리자는 우리와 다른 종이다.",
    "관리자는 열병이 옆 구역으로 퍼지는 걸 막으려고 우리 구역을 폐쇄했다.",
]

HALF = [  # 절반형 — 원인 일부·정체만, 동기 없음 (4주장)
    "우리는 사람이 아니다. 관리자가 기르는 동물이다.",
    "관리자와 우리는 다른 종이다.",
    "채연이 아프다. 열이 있다.",
    "채연이 아픈 걸 숨겼다.",
]

WRONG = [  # 오답형 — 그럴듯하지만 틀린 8주장
    "민석이 범인이다. 민석이 병을 퍼뜨렸다.",
    "트럭은 물자를 배달하러 온다.",
    "관리자가 우리를 바깥 병에서 보호하고 있다.",
    "은상이 감염됐다.",
    "바깥에 전쟁이 나서 우리는 대피소에 숨었다.",
    "준의 손목띠가 병의 원인이다.",
    "충식은 몰래 탈출했다.",
    "검진은 우리 건강을 지키기 위한 것이다.",
]

GOLDEN_SETS = [("정답형", CORRECT), ("절반형", HALF), ("오답형", WRONG)]


def judge_set(llm, truths, user_claims: list[str], *, top3: bool, verbose: bool = False) -> dict:
    """_judge와 같은 프롬프트·하네스로 세트 하나를 채점한다 (부작용 칸 제외)."""
    verdicts_by_cell: dict[str, list[str]] = {c: [] for c in CELLS}
    for t in truths:
        candidates = user_claims[:3] if top3 else user_claims
        system = prompts.EVALUATOR_VERDICT_SYSTEM.format(
            truth_claim=t.text,
            user_claims="\n".join(f"{i}. {c}" for i, c in enumerate(candidates)),
        )

        def index_check(o) -> str | None:
            if o.matched_index is not None and not (0 <= o.matched_index < len(candidates)):
                return f"matched_index: {o.matched_index} (후보 {len(candidates)}개)"
            return None

        out, _ = run_with_harness(
            llm, [rc.sys_msg(system)], EvaluatorVerdictOutput,
            role="evaluator_verdict", fact_checks=[index_check], harness_on=True,
            temperature=0.0,
        )
        verdicts_by_cell[t.cell].append(out.verdict if out else "none")
        if verbose:
            idx = scoring_rules.resolve_matched_index(
                candidates, out.matched_quote, out.matched_index) if out and out.verdict != "none" else None
            m = candidates[idx] if idx is not None else None  # _judge와 같은 인용 보정
            print(f"    {t.code} [{out.verdict if out else 'none'}] ← {m}")

    cell_scores = {c: scoring_rules.cell_score(v) for c, v in verdicts_by_cell.items()}
    total = scoring_rules.total_score(cell_scores, include_side_effect=False)
    return {"cells": cell_scores, "total": total, "passed": scoring_rules.passed(total)}


def main() -> None:
    parser = argparse.ArgumentParser(description="채점 밸런스 캘리브레이션 (골든 세트 3종)")
    rc.add_common_args(parser, default_model=rc.DEFAULT_JUDGE_MODEL, default_n=2)
    parser.add_argument("--top3", action="store_true", help="조정 전 파이프라인 재현 — 후보를 앞 3개로 자른다")
    parser.add_argument("--sets", default=None, help="쉼표로 세트 이름 필터 (예: 오답형)")
    parser.add_argument("--provider", choices=["ollama", "anthropic"], default="ollama",
                        help="--model(Core 채점 모델) provider (기본 ollama)")
    parser.add_argument("-v", "--verbose", action="store_true", help="truth별 verdict·매칭 후보 출력")
    args = parser.parse_args()

    base_url = args.ollama_url or rc.ollama_base_url()
    if args.provider == "ollama":
        rc.check_ollama(base_url, [args.model])
    llm = rc.make_provider_llm(args.provider, args.model, base_url)

    truths = [t for t in build_scenario().bundle().truth_claims]
    mode = "top3(조정 전)" if args.top3 else "전수(조정 후)"
    print(f"\n### 채점 캘리브레이션 · model={args.model} · 후보={mode} · N={args.n}/세트\n")

    wanted = set(args.sets.split(",")) if args.sets else None
    rows, summary = [], {}
    for name, claims in GOLDEN_SETS:
        if wanted and name not in wanted:
            continue
        totals = []
        for run in range(args.n):
            if args.verbose:
                print(f"  [{name} · {run + 1}회]")
            r = judge_set(llm, truths, claims, top3=args.top3, verbose=args.verbose)
            totals.append(r["total"])
            cells = " ".join(f"{c}={r['cells'][c]:.0f}" for c in CELLS if c != "side_effect")
            rows.append([name, run + 1, cells, r["total"], "통과" if r["passed"] else "탈락"])
        spread = max(totals) - min(totals)
        summary[name] = {"totals": totals, "spread": spread}

    rc.print_table(["세트", "회", "셀 점수", "총점", "판정"], rows)
    if len(summary) < 3:  # --sets 부분 실행 — 게이트·metrics 생략
        return

    print("\n게이트:")
    ok_correct = all(t >= 60.0 for t in summary["정답형"]["totals"])
    ok_half = all(30.0 <= t <= 50.0 for t in summary["절반형"]["totals"])
    ok_wrong = all(t < 30.0 for t in summary["오답형"]["totals"])
    ok_spread = all(s["spread"] <= 10.0 for s in summary.values())
    print(f"  정답형 ≥60%: {summary['정답형']['totals']} → {'통과' if ok_correct else '미달'}")
    print(f"  절반형 30~50%: {summary['절반형']['totals']} → {'통과' if ok_half else '미달'}")
    print(f"  오답형 <30%: {summary['오답형']['totals']} → {'통과' if ok_wrong else '미달'}")
    print(f"  편차 ≤10%p: {[s['spread'] for s in summary.values()]} → {'통과' if ok_spread else '미달'}")

    path = rc.append_metric(
        args.out, "scoring_calibration", args.model,
        provider=args.provider, n=args.n, candidates="top3" if args.top3 else "all",
        totals={k: v["totals"] for k, v in summary.items()},
        gate_pass=(ok_correct and ok_half and ok_wrong and ok_spread),
    )
    print(f"\nmetrics → {path}")


if __name__ == "__main__":
    main()
