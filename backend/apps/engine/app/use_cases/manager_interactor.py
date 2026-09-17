"""Manager — 비트 경계 점검·원숭이손 생성 (모델정책 §5). 정답을 아는 유일한 LLM 역할."""

import json

from apps.engine.app.dtos.llm_output_dto import ManagerCheckOutput, ManagerPawOutput
from apps.engine.app.use_cases import prompts
from apps.engine.app.use_cases.game_support import system_msg
from apps.engine.app.use_cases.harness import run_with_harness


class ManagerInteractor:
    def __init__(self, *, core_llm, scenario, harness_on: bool) -> None:
        self._llm = core_llm
        self._scenario = scenario
        self._harness_on = harness_on

    def check(self, *, npc_states: list[dict], user_utterances: list[str], rules: list[str], budget_left: int, yesterday_score: float | None):
        """반환: (patches ≤ budget, flagged_abnormal, report)."""
        if budget_left <= 0:
            return [], [], None
        sys = prompts.MANAGER_SYSTEM.format(
            hidden_truth=self._scenario.hidden_truth(),
            budget_left=budget_left,
            npc_states=json.dumps(npc_states, ensure_ascii=False),
            user_utterances="\n".join(user_utterances) or "(없음)",
            rules="\n".join(rules) or "(없음)",
            yesterday_score=yesterday_score if yesterday_score is not None else "(첫날)",
        )
        out, report = run_with_harness(
            self._llm, [system_msg(sys)], ManagerCheckOutput,
            role="manager_check", harness_on=self._harness_on,
        )
        if out is None:
            return [], [], report  # 폴백: 패치 없음
        return out.patches[:budget_left], out.flagged_abnormal, report

    def make_paw_reason(self, wish):
        """원숭이손 제안 문구만 쓴다. 소원 선택은 코드다. 반환: (문구 또는 None, report)."""
        sys = prompts.MANAGER_SYSTEM.format(
            hidden_truth=self._scenario.hidden_truth(),
            budget_left=0,
            npc_states="(생략)",
            user_utterances="(생략)",
            rules="(생략)",
            yesterday_score="(생략)",
        ) + "\n\n" + prompts.MANAGER_PAW_ADDENDUM.format(wish=wish.label)
        out, report = run_with_harness(
            self._llm, [system_msg(sys)], ManagerPawOutput,
            role="manager_paw", harness_on=True,
        )
        return (out.shown_reason if out else None), report
