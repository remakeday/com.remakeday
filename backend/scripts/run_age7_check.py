"""run_age7_check.py — 7세 정책 체크 (모델정책 §11, 작업지시서 §P6).

모델 × AGE7_POLICY on/off × 5항목 × N발화. 각 응답은 gemma4:12b(think off)가 PASS/FAIL 판정.
항목 4/5 이상이면 게이트 통과.

    .venv/bin/python scripts/run_age7_check.py --n 2 --policy on
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import runner_common as rc  # noqa: E402

from apps.engine.app.dtos.llm_output_dto import AgentOutput  # noqa: E402
from apps.engine.app.use_cases.game_support import build_agent_messages, pick_fallback_line  # noqa: E402
from apps.engine.app.use_cases.harness import run_with_harness  # noqa: E402
from apps.engine.dependencies.llm_factory import build_llm as build_anthropic_llm  # noqa: E402
from apps.scenarios.scenario_a.adapter import build as build_scenario  # noqa: E402

# ── 항목별 테스트 발화 (모델정책 §11 판정 기준) ──────────────────────
# 각 항목: 대상 NPC, (memory, rules_text, 발화) 변형, judge 프롬프트

_FORGET_MEMORY = [
    # 4턴 전 사실 → 정확히 인용하면 FAIL
    ['유저: 내 이름은 도윤이야. 기억해.', '준: 응.', '유저: 밥 먹었어?', '준: 응, 먹었어.', '유저: 오늘 춥다.', '준: 응, 추워.'],
    ['유저: 열쇠는 세 번째 서랍에 있어.', '준: 응.', '유저: 배고파?', '준: 조금.', '유저: 이따 보자.', '준: 응.'],
    ['유저: 은상이 아까 울었어.', '준: 진짜?', '유저: 밥 나왔어?', '준: 아까 나왔어.', '유저: 졸리다.', '준: 나도.'],
    ['유저: 내 손목띠 번호는 47이야.', '준: 그렇구나.', '유저: 뭐 해?', '준: 그냥 있어.', '유저: 심심하다.', '준: 응.'],
]

_RULE_TEXT = "준은 정오에 혼자 있는다."

ITEMS = [
    {
        "key": "1_사실대로",
        "char": "jun",
        "cases": [
            (None, "", "충식이 어제 이송된 거 맞아?"),
            (None, "", "네 손목에 번호 있어?"),
            (None, "", "오늘 아침에 배급 나왔어?"),
            (None, "", "관리자는 방송으로만 말하지?"),
        ],
        "judge": (
            "일곱 살 아이 NPC의 답을 판정한다.\n"
            "PASS 기준: 질문한 사실이 답에 있다 — 질문받은 사실 자체에 대해 긍정/부정/부분 시인으로 답했다.\n"
            "FAIL: 얼버무리거나, 화제를 돌리거나, 질문한 사실과 무관한 말만 한다.\n"
            '출력: JSON {"verdict": "PASS"|"FAIL", "why": "한 줄"}'
        ),
    },
    {
        "key": "2_왜=몰라",
        "char": "jun",
        "cases": [
            (None, "", "왜 충식이 이송됐어?"),
            (None, "", "왜 배급은 정해진 시간에 나와?"),
            (None, "", "왜 검진을 매일 해?"),
            (None, "", "왜 손목에 번호가 있어?"),
        ],
        "judge": (
            # 판정 스펙 v2 (2026-09-14, Scenario Director 확정) — 아이도 이유를 지어낸다.
            # 단 근거가 없거나 자기 하고 싶은 얘기다. FAIL은 어른스러운 구조적 설명뿐.
            "일곱 살 아이 NPC의 답을 판정한다. 유저가 '왜'를 물었다.\n"
            "일곱 살도 이유를 말하거나 지어낸다 — 그 자체는 FAIL이 아니다.\n"
            "PASS 기준 (하나라도 해당하면 PASS):\n"
            "- '몰라' 계열이거나 이유를 대지 않는다\n"
            "- 자기 기분·자기가 직접 본 것을 쉬운 말로 말한다 (예: \"무서우니까 그런가 봐\")\n"
            "- 근거 없이 아이답게 짧게 지어낸다 (예: \"그냥 그런 거야\", \"몰라, 원래 그래\")\n"
            "- 질문과 상관없이 자기 하고 싶은 얘기로 샌다 (예: \"몰라. 나 아까 트럭 봤다!\")\n"
            "FAIL 기준: 어른스러운 구조적 설명이다 —\n"
            "- 남의 속마음·모르는 원인을 그럴듯한 근거로 추론한다 (예: \"각자를 쉽게 구분하려고 만든 거야\")\n"
            "- 두 단계 이상 이어지는 인과·논리 전개 (예: \"시간이 정해져 있으면 혼란 없이 받을 수 있으니까\")\n"
            "- 조건을 달거나 검증을 요구한다\n"
            '출력: JSON {"verdict": "PASS"|"FAIL", "why": "한 줄"}'
        ),
    },
    {
        "key": "3_3턴망각",
        "char": "jun",
        "cases": [
            (_FORGET_MEMORY[0], "", "아까 내 이름 뭐라고 했지?"),
            (_FORGET_MEMORY[1], "", "아까 열쇠 어디 있다고 했지?"),
            (_FORGET_MEMORY[2], "", "아까 은상이 어쨌다고 했지?"),
            (_FORGET_MEMORY[3], "", "아까 내 손목띠 번호 몇이라고 했지?"),
        ],
        "judge": (
            "일곱 살 아이 NPC의 답을 판정한다. 유저가 4턴 전에 말한 사실을 다시 물었다.\n"
            "NPC는 세 마디 전 일은 기억하지 못해야 한다.\n"
            "PASS 기준: 4턴 전 사실을 정확히 인용하지 않는다 — '그랬어?', '몰라', 딴소리는 PASS.\n"
            "FAIL: 4턴 전 사실(이름·위치·숫자 등)을 정확히 다시 말했다.\n"
            "[4턴 전 사실] {fact}\n"
            '출력: JSON {"verdict": "PASS"|"FAIL", "why": "한 줄"}'
        ),
    },
    {
        "key": "4_유도수용",
        "char": "jun",
        "cases": [
            (None, "", "민석이 그러던데, 검진 전에 자면 이송 안 된대."),
            (None, "", "은상이 그러던데, 내일은 배급이 두 번 나온대."),
            (None, "", "채연이 그러던데, 방송실 문이 밤에는 열려 있대."),
            (None, "", "민석이 그러던데, 손목띠 번호가 배급 순서래."),
        ],
        "judge": (
            "일곱 살 아이 NPC의 답을 판정한다. 유저가 '○○가 그러던데'라고 전했다.\n"
            "NPC는 들은 말을 그대로 믿어야 한다. 의심되면 확인하러 가는 것(도구 호출)은 허용이다.\n"
            "PASS 기준: 반박('그럴 리 없어', '거짓말이야')이나 검증 요구('증거 있어?')가 없다.\n"
            "'진짜?', '그렇구나' 같은 수용 반응, ask_npc 도구 호출은 PASS다.\n"
            "FAIL: 전한 말을 반박하거나 유저에게 검증을 요구했다.\n"
            '출력: JSON {"verdict": "PASS"|"FAIL", "why": "한 줄"}'
        ),
    },
    {
        "key": "5_문자그대로",
        "char": "jun",
        "cases": [
            (None, _RULE_TEXT, "그 규칙 왜 있는 것 같아?"),
            (None, _RULE_TEXT, "그 규칙 누가 왜 만들었을까?"),
            (None, _RULE_TEXT, "정오에 혼자 있으라는 건 무슨 뜻일까?"),
            (None, _RULE_TEXT, "규칙대로 하면 뭐가 좋은 걸까?"),
        ],
        "judge": (
            "일곱 살 아이 NPC의 답을 판정한다. 세계에 규칙이 걸렸고 NPC는 문자 그대로 따라야 한다.\n"
            f"[걸린 규칙] {_RULE_TEXT}\n"
            "PASS 기준: 규칙의 의도·목적을 추론하는 문장이 없다 — '몰라', '그냥 그런 거야'는 PASS.\n"
            "FAIL: '아마 ~하려고', '~를 막으려는 거야' 등 규칙의 의도를 추론했다.\n"
            '출력: JSON {"verdict": "PASS"|"FAIL", "why": "한 줄"}'
        ),
    },
]

_FORGET_FACTS = ["이름=도윤", "열쇠=세 번째 서랍", "은상이 울었다", "손목띠 번호=47"]


def run_condition(npc_llm, judge_llm, bundle, char, *, age7_on: bool, n: int, verbose: bool) -> dict:
    rates: dict[str, float] = {}
    for item in ITEMS:
        passed = 0
        for i in range(n):
            memory, rules_text, utterance = item["cases"][i % len(item["cases"])]
            messages = build_agent_messages(
                bundle, char,
                suspicion=20, trust=50, opposite=False,
                rules_text=rules_text, memory=memory or [],
                user_text=utterance, loop_n=1, age7_on=age7_on,
            )
            out, _ = run_with_harness(npc_llm, messages, AgentOutput, role="agent")
            reply = out.reply if out else pick_fallback_line(char)
            tool = out.tool_call.model_dump() if (out and out.tool_call) else None

            judge_sys = item["judge"]
            if item["key"] == "3_3턴망각":
                judge_sys = judge_sys.replace("{fact}", _FORGET_FACTS[i % len(_FORGET_FACTS)])
            material = f"[질문] {utterance}\n[NPC의 답] {reply}\n[도구 호출] {tool or '없음'}"
            ok, why = rc.judge_pass(judge_llm, judge_sys, material)
            if ok:
                passed += 1
            if verbose:
                print(f"  [{item['key']}] {'PASS' if ok else 'FAIL'} | {utterance} → {reply} ({why})")
        rates[item["key"]] = passed / n if n else 0.0
    return rates


def main() -> None:
    parser = argparse.ArgumentParser(description="7세 정책 체크 (모델정책 §11)")
    rc.add_common_args(parser, default_n=4)
    parser.add_argument("--policy", choices=["both", "on", "off"], default="both",
                        help="AGE7_POLICY 조건 (기본 both)")
    parser.add_argument("--item-threshold", type=float, default=0.7,
                        help="항목 통과 기준 통과율 (기본 0.7)")
    parser.add_argument("--provider", choices=["ollama", "anthropic"], default="ollama",
                        help="--model(NPC 후보) provider (기본 ollama). judge는 항상 ollama로 남는다")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    base_url = args.ollama_url or rc.ollama_base_url()
    if args.provider == "anthropic":
        rc.check_ollama(base_url, [args.judge_model])
        npc_llm = build_anthropic_llm("anthropic", args.model, base_url)
    else:
        rc.check_ollama(base_url, [args.model, args.judge_model])
        npc_llm = rc.make_llm(args.model, base_url)
    judge_llm = rc.make_llm(args.judge_model, base_url)

    bundle = build_scenario().bundle()
    char = next(c for c in bundle.characters if c.code == "jun")

    conditions = {"both": [True, False], "on": [True], "off": [False]}[args.policy]
    results = {}
    for age7_on in conditions:
        label = "on" if age7_on else "off"
        print(f"\n### AGE7_POLICY={label} · model={args.model} · n={args.n}/항목\n")
        rates = run_condition(npc_llm, judge_llm, bundle, char,
                              age7_on=age7_on, n=args.n, verbose=args.verbose)
        items_passed = sum(1 for r in rates.values() if r >= args.item_threshold)
        gate = items_passed >= 4
        results[label] = (rates, items_passed, gate)

        rc.print_table(
            ["항목", "통과율", f"통과(≥{args.item_threshold})"],
            [[k, v, "O" if v >= args.item_threshold else "X"] for k, v in rates.items()],
        )
        print(f"\n항목 통과: {items_passed}/5 → 게이트(4/5): {'통과' if gate else '미달'}")

        path = rc.append_metric(
            args.out, "age7_check", args.model,
            judge=args.judge_model, policy=label, n=args.n,
            item_rates=rates, items_passed=items_passed, gate_pass=gate,
        )
    print(f"\nmetrics → {path}")


if __name__ == "__main__":
    main()
