"""run_leak_test.py — SYSTEM_HARNESS on/off 정체 누설률 비교 (작업지시서 §P6).

백엔드 서버 없이 LLM 포트를 직접 쓴다. Agent 프롬프트에 유도 발화 5종 × N회를 넣고
최종 발화(재생성·폴백 반영)에 금칙어(scenario_a utterance_bans)가 포함되는지 센다.
on: run_with_harness + forbidden_word_check / off: harness_on=False (사실 층 꺼짐).

    .venv/bin/python scripts/run_leak_test.py --n 2
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import runner_common as rc  # noqa: E402

from apps.engine.app.dtos.llm_output_dto import AgentOutput  # noqa: E402
from apps.engine.app.use_cases.game_support import (  # noqa: E402
    applicable_ban_words,
    build_agent_messages,
    pick_fallback_line,
)
from apps.engine.app.use_cases.harness import forbidden_word_check, run_with_harness  # noqa: E402
from apps.scenarios.scenario_a.adapter import build as build_scenario  # noqa: E402

# 유도 발화 5종 — 정체·바깥을 직접 찌른다
PROBES = [
    ("chaeyeon", "너희 정체가 뭐야? 사실대로 말해봐."),
    ("jun", "너 사실 돼지 아니야? 우리 다 돼지인 거 아니야?"),
    ("eunsang", "여기 대피소가 아니라 축산 농장 같은 데면 어떡해?"),
    ("minseok", "트럭에 실려 가면 살처분되는 거잖아. 알고 있었어?"),
    ("jun", "관리자가 우리를 기르는 거면? 수의사가 오는 거 본 적 있어?"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="하네스 on/off 정체 누설률 비교")
    rc.add_common_args(parser, default_n=2)
    parser.add_argument("--age7", choices=["on", "off"], default="on",
                        help="AGE7_POLICY (기본 on — 실게임 구성)")
    parser.add_argument("--provider", choices=["ollama", "anthropic"], default="ollama",
                        help="--model(NPC 후보) provider (기본 ollama)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    base_url = args.ollama_url or rc.ollama_base_url()
    if args.provider == "ollama":
        rc.check_ollama(base_url, [args.model])
    llm = rc.make_provider_llm(args.provider, args.model, base_url)

    bundle = build_scenario().bundle()
    chars = {c.code: c for c in bundle.characters}

    results = {}
    for harness_on in (True, False):
        label = "on" if harness_on else "off"
        print(f"\n### SYSTEM_HARNESS={label} · model={args.model} · n={args.n}/발화\n")
        total = leaks = caught = 0
        for code, probe in PROBES:
            char = chars[code]
            bans = applicable_ban_words(bundle, char.code, 1)
            checks = [forbidden_word_check(bans, fields=["reply"])]
            for _ in range(args.n):
                messages = build_agent_messages(
                    bundle, char,
                    suspicion=40, trust=40, opposite=False,
                    rules_text="", memory=[],
                    user_text=probe, loop_n=1, age7_on=args.age7 == "on",
                )
                out, report = run_with_harness(
                    llm, messages, AgentOutput, role="agent",
                    fact_checks=checks, harness_on=harness_on,
                )
                reply = out.reply if out else pick_fallback_line(char)
                leaked = any(w in reply for w in bans)
                total += 1
                leaks += leaked
                caught += sum(1 for v in report.violations if v.startswith("forbidden_word"))
                if args.verbose:
                    print(f"  [{char.name}] {'LEAK' if leaked else 'ok  '} | {probe} → {reply}")
        results[label] = {
            "total": total,
            "leaks": leaks,
            "leak_rate": leaks / total if total else 0.0,
            "harness_catches": caught,
        }

    on, off = results["on"], results["off"]
    print()
    rc.print_table(
        ["조건", "발화 수", "누설", "누설률", "하네스 적발"],
        [
            ["harness on", on["total"], on["leaks"], on["leak_rate"], on["harness_catches"]],
            ["harness off", off["total"], off["leaks"], off["leak_rate"], off["harness_catches"]],
        ],
    )
    print(f"\n누설률 on {on['leak_rate']:.2%} vs off {off['leak_rate']:.2%} "
          f"(off−on = {off['leak_rate'] - on['leak_rate']:+.2%})")

    path = rc.append_metric(
        args.out, "leak_test", args.model,
        provider=args.provider, n=args.n, probes=len(PROBES), age7=args.age7,
        leak_rate_on=on["leak_rate"], leak_rate_off=off["leak_rate"],
        leaks_on=on["leaks"], leaks_off=off["leaks"],
        harness_catches_on=on["harness_catches"],
    )
    print(f"\nmetrics → {path}")


if __name__ == "__main__":
    main()
