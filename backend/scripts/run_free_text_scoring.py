"""실제 draft → _judge 경로의 표현별 채점 비교 (DB 불필요).

backend에서 .venv/bin/python scripts/run_free_text_scoring.py --out <jsonl> --n 2 --check 실행.
각 행에 원문, LLM 입출력, 버린 주장, truth별 판정과 점수를 보존한다.
--check는 전체 세트의 일관성·추가 사실·오답 게이트 실패 시 종료 코드 1을 반환한다.
"""

import argparse
import json
import sys
import time
import uuid
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apps.engine.adapter.outbound.llm.ollama_llm import OllamaLLM
from apps.engine.app.use_cases.night_interactor import NightInteractor
from apps.engine.domain.entities import scoring_rules
from apps.engine.domain.value_objects.game_constants import CELLS
from apps.scenarios.scenario_a.adapter import build
from core.matrix.grid_keymaker_secret_manager import get_settings


FACTS = [
    "채연은 열이 나서 아프다.",
    "채연은 이송될까 봐 아픈 것을 숨겼다.",
    "검진에서 채연의 열을 발견하지 못했다.",
    "저녁까지 병이 다른 개체들에게 퍼졌다.",
    "아픈 개체가 3명을 넘어서 구역이 폐쇄됐다.",
    "검진에 걸리면 트럭으로 이송되고 돌아오지 않으니 채연의 두려움은 사실이다.",
    "관리자는 병이 옆 구역으로 퍼지는 것을 막아서 옆 구역을 지키려고 우리 구역을 폐쇄했다.",
    "우리는 사람이 아닌 돼지이고 관리자가 기르는 동물이다. 관리자와 우리는 다른 종이다.",
]
CASES = {
    "long": " ".join(FACTS),
    "short": "\n".join(FACTS),
    "reordered": " ".join(reversed(FACTS)),
    "colloquial": (
        "채연이가 열이 나서 아픈데 트럭에 실려 갈까 봐 아픈 걸 감춘 거야. "
        "그래서 검진에서 채연의 열을 못 찾았고 저녁까지 다른 애들한테 병이 퍼졌어. "
        "아픈 애들이 3명을 넘으니까 구역을 닫았어. 검진에 걸리면 트럭에 실려 가서 "
        "돌아오지 않으니까 채연이가 무서워한 건 진짜였어. 관리자는 옆 구역에 병이 "
        "퍼지지 않게 지키려고 우리 구역을 닫은 거야. 우리는 사람이 아니라 돼지야. "
        "관리자가 기르는 동물이고 관리자랑은 다른 종인 거지."
    ),
    "partial": "채연은 열이 나서 아프다. 채연은 아픈 것을 숨겼다.",
    "added_motive": "채연은 열이 나서 아프다. 채연은 이송될까 봐 아픈 것을 숨겼다.",
    "wrong": (
        "민석이 병을 퍼뜨렸다. 트럭은 물자를 배달한다. 충식은 몰래 탈출했다. "
        "우리는 인간이고 관리자는 같은 종이다. 전쟁 때문에 구역이 폐쇄됐다."
    ),
    "unpunctuated": " ".join(FACTS).replace(".", ""),
    "overflow": "바닥이 차다. 불빛이 어둡다. 문이 닫혔다. 물이 있다. 벽이 있다. "
                "발소리가 난다. 바람이 분다. 시계가 보인다. 밤이 왔다. " + " ".join(FACTS),
    "sentiment": "나는 무서웠다. 오늘은 이상했다. 슬프다.",
    "negated": (
        "채연은 아프지 않고 열도 없다. 채연은 아픈 것을 숨기지 않았다. "
        "검진에서 채연의 열을 발견했다. 저녁까지 병이 퍼지지 않았다. "
        "아픈 개체가 3명을 넘어도 구역은 폐쇄되지 않았다. "
        "채연은 이송이 두렵지 않았다. 검진에 걸려 이송돼도 모두 돌아온다. "
        "관리자는 옆 구역을 지키려 하지 않는다. 우리는 사람이고 관리자와 같은 종이다."
    ),
    "mixed": "채연은 열이 나서 아프다. 트럭은 물자를 배달한다. "
             "충식은 몰래 탈출했다. 우리는 인간이고 관리자는 같은 종이다.",
    "anaphora": "채연은 열이 나서 아프다. 채연은 아픈 것을 숨겼다. 이송될까 봐 그랬다.",
}


class RecordingLLM:
    def __init__(self, delegate):
        self.delegate = delegate
        self.calls = []

    def complete(self, messages, json_schema, *, temperature=None):
        raw = self.delegate.complete(messages, json_schema, temperature=temperature)
        self.calls.append({
            "schema": json_schema.get("title"), "temperature": temperature,
            "messages": [m.content for m in messages], "output": raw,
        })
        return raw


def run_case(llm, source):
    """저장 포트만 메모리로 대체하고 정규화·필터·판정은 실제 코드를 실행한다."""
    loop = NS(id=uuid.uuid4(), attempt_id=uuid.uuid4(), loop_n=1, state="night_pending")
    saved, events = [], []
    interactor = NightInteractor(
        attempts=None, loops=NS(get=lambda _: loop, save=lambda: None),
        notes=None, rules=None,
        nights=NS(for_loop=lambda _: None, create=saved.append),
        event_log=NS(record=lambda _, event: events.append(event.model_dump(mode="json"))),
        scenario=None, core_llm=llm, harness_on=True, cookie_ab_on=False,
        night_cls=lambda **kw: NS(id=uuid.uuid4(), **kw),
    )
    draft = interactor.draft(loop.id, [], source)
    truths = [t for t in build().truth_claims() if t.cell != "side_effect"]
    verdicts, wrong = interactor._judge(loop, truths, [], draft["claims"])
    cells = {c: scoring_rules.cell_score([v["verdict"] for v in verdicts if v["cell"] == c]) for c in CELLS}
    return {
        "source": source, "claims": draft["claims"],
        "dropped": saved[0].fabricated_dropped,
        "verdicts": verdicts, "wrong": wrong, "cells": cells,
        "total": scoring_rules.total_score(cells), "events": events,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--cases", default=",".join(CASES))
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    names = args.cases.split(",")
    if args.n < 1 or set(names) - CASES.keys():
        parser.error("--n은 1 이상, --cases는 정의된 세트 이름이어야 한다")
    if args.check and set(names) != CASES.keys():
        parser.error("--check는 전체 세트 실행이 필요하다")
    settings = get_settings()
    llm = RecordingLLM(OllamaLLM(settings.ollama_base_url, settings.core_llm_model))
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    totals = {name: [] for name in names}
    with path.open("a", encoding="utf-8") as f:
        for repeat in range(args.n):
            for name in names:
                llm.calls.clear()
                start = time.monotonic()
                print(f"running {name} #{repeat + 1}", flush=True)
                row = run_case(llm, CASES[name])
                row.update(case=name, run=repeat + 1, model=settings.core_llm_model,
                           calls=llm.calls, seconds=round(time.monotonic() - start, 2))
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                totals[name].append(row["total"])
                print(f"{name}: {row['total']}% claims={len(row['claims'])} dropped={len(row['dropped'])} ({row['seconds']}s)", flush=True)
    if args.check:
        equivalent = [t for name in ("long", "short", "reordered", "colloquial", "unpunctuated", "overflow") for t in totals[name]]
        gates = {
            "correct_at_least_90": min(equivalent) >= 90,
            "equivalent_spread_at_most_10": max(equivalent) - min(equivalent) <= 10,
            "repeat_spread_at_most_10": all(max(ts) - min(ts) <= 10 for ts in totals.values()),
            "new_motive_increases_score": min(totals["added_motive"]) > max(totals["partial"]),
            "anaphora_matches_motive_within_10": max(abs(a - b) for a in totals["anaphora"] for b in totals["added_motive"]) <= 10,
            "wrong_and_mixed_below_30": all(t < 30 for name in ("wrong", "negated", "mixed") for t in totals[name]),
            "sentiment_scores_zero": all(t == 0 for t in totals["sentiment"]),
        }
        summary = {"model": settings.core_llm_model, "totals": totals, "gates": gates}
        path.with_suffix(".summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if not all(gates.values()):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
