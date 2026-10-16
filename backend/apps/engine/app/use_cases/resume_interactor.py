"""이어하기 — 로그인 사용자의 진행 중인 판을 찾고, 그 판을 다시 여는 화면 데이터를 고른다 (설계 2026-10-16 §2.1~2.3).

진행 중인 판 = 그 사용자의 가장 최근 판이 status='active'일 때만 그 판. 단계는 최신 회차 상태가 정한다.
낮 장면은 LoopInteractor, 밤·채점·개입 데이터는 NightInteractor가 만든다 — 여기서는 단계에 맞는 조립기를 고르기만 한다.
쓰기는 abandon 하나뿐이다.
"""

from datetime import datetime, timezone

from apps.engine.app.dtos.auth_dto import SessionUserDTO

# 최신 회차 상태 → 프론트가 여는 단계. scored는 지금 엔진이 거치지 않지만(제출 뒤 곧바로 intervention) 스펙 표대로 둔다.
PHASE_BY_STATE = {
    "day": "day",
    "night_pending": "night",
    "night_draft": "night",
    "scored": "score",
    "intervention": "god",
    "closed": "entry",
}
NO_LOOP_PHASE = "entry"


def _no_night(loop) -> None:
    return None


class ResumeInteractor:
    def __init__(self, *, attempts, loops, users, scenario, day_view, night_view, user_daily_attempts: int) -> None:
        self._attempts = attempts
        self._loops = loops
        self._users = users
        self._scenario = scenario
        self._limit = user_daily_attempts
        # 단계 → (회차 데이터, 밤 데이터) 조립기. 낮만 장면을 다시 그리고, 나머지는 장면이 빈 회차 정보를 준다.
        self._builders = {
            "entry": (day_view.resume_shell, _no_night),
            "day": (day_view.resume_day, _no_night),
            "night": (day_view.resume_shell, night_view.resume_view),
            "score": (day_view.resume_shell, night_view.resume_view),
            "god": (day_view.resume_shell, night_view.resume_view),
        }

    def active(self, user: SessionUserDTO) -> dict:
        owner = self._users.get_by_sub(user.sub)
        attempt = self._attempts.latest_active(owner.id) if owner else None
        snapshot = {"attempt": None, "resume_phase": None, "loop": None, "night": None,
                    "today_remaining": self._remaining(owner), "daily_limit": self._limit}
        if attempt is None:
            return snapshot
        loop = self._loops.latest_for(attempt.id)
        phase = PHASE_BY_STATE[loop.state] if loop else NO_LOOP_PHASE
        build_loop, build_night = self._builders[phase]
        return {
            **snapshot,
            "attempt": {
                "attempt_id": str(attempt.id), "attempt_n": attempt.attempt_n,
                "entry_lines": self._scenario.entry_lines(), "prior_cell_results": attempt.prior_cell_results,
            },
            "resume_phase": phase,
            "loop": build_loop(loop) if loop else None,
            "night": build_night(loop) if loop else None,
        }

    def abandon(self, user: SessionUserDTO) -> None:
        """진행 중인 판을 abandoned로 닫는다. 없으면 아무 일도 하지 않는다. 포기한 판은 그날 판 수에 남는다."""
        owner = self._users.get_by_sub(user.sub)
        attempt = self._attempts.latest_active(owner.id) if owner else None
        if attempt is None:
            return
        attempt.status = "abandoned"
        self._attempts.save()

    def _remaining(self, owner) -> int:
        if owner is None:
            return self._limit
        return max(0, self._limit - self._attempts.count_today(owner.id, datetime.now(timezone.utc)))
