"""클리어 화면 플레이 평가 기록.

소유권은 라우터의 require_attempt_owner가 이미 확인했다. 여기서는 판에 붙은
user_id를 그대로 표에 옮겨, 나중에 사람 판만 집계할 수 있게 한다.
"""

import uuid

from apps.engine.domain.value_objects.game_constants import SURVEY_SCORE_FIELDS


class SurveyInteractor:
    def __init__(self, attempts, votes) -> None:
        self._attempts, self._votes = attempts, votes

    def record(self, attempt_id: uuid.UUID, *, skipped: bool, scores: dict[str, int | None]) -> dict:
        attempt = self._attempts.get(attempt_id)
        given = {name: scores.get(name) for name in SURVEY_SCORE_FIELDS}
        # 별점을 하나도 안 매기고 보낸 것은 건너뛴 것과 같다 — 빈 표를 만들지 않는다.
        if not any(v is not None for v in given.values()):
            skipped, given = True, dict.fromkeys(SURVEY_SCORE_FIELDS)
        recorded = self._votes.record(
            attempt_id,
            attempt.user_id if attempt else None,
            skipped=skipped,
            scores=given,
        )
        return {"recorded": recorded}
