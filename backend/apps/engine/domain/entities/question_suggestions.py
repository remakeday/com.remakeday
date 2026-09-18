"""신의 질문 추천 — 답할 재료가 있는 오늘 기록에서만 찾기형 질문을 만든다 (테스터9 F19 해결 방향 3).

가설을 넣지 않는다(F11) — 판정 질문이 아니라 기록 찾기 질문이라 "알 수 없다"로 끝나지 않고,
플레이어가 두 사용법(판정 / 기록 찾기) 중 찾기 쪽을 몸으로 익힌다. 규칙만, 모델 호출 없음.
"오늘"이 든 질문은 조언자가 오늘 회차 기록을 먼저 고른다(advisor_context). "무엇인가"·"뜻"은
unresolved_question이 판정 보류로 처리하므로 쓰지 않는다.
"""

import re
from typing import TYPE_CHECKING

from apps.engine.domain.entities.scoring_rules import _with_topic_particle

if TYPE_CHECKING:
    from apps.engine.app.dtos.observation_dto import ObservationDTO

BROADCAST_QUESTION = "오늘 방송에서 관리자는 무엇을 말했는가?"  # "말했"이 있어야 전언(방송)도 판정 근거가 된다
NIGHT_CLUE_QUESTION = "오늘 소등 뒤에 무엇이 새로 드러났는가?"
ACTOR_QUESTION = "{name} 오늘 무엇을 했는가?"
ACTORS_PER_NIGHT = 2

# 같은 질문 판정 — advisor_advice._same_question_key와 같은 기준(공백·문장부호 무시)
_NOISE_RE = re.compile(r"[\s.,!?~…\"'「」]")


def question_key(text: str) -> str:
    return _NOISE_RE.sub("", text)


def _key(observation: "ObservationDTO") -> str:
    return observation.observation_id.split(":", 1)[-1]


def _is_broadcast(observation: "ObservationDTO") -> bool:
    key = _key(observation)
    return key.startswith("broadcast-") or key == "night-broadcast"


def _is_night_clue(observation: "ObservationDTO") -> bool:
    key = _key(observation)
    return key == "night-clue" or key.startswith("outcome-fragment-")


# 위에서부터 — 새 재료(방송·소등 뒤 단서)를 인물 행동보다 앞에 둔다
_RECORD_QUESTIONS = (
    (_is_broadcast, BROADCAST_QUESTION),
    (_is_night_clue, NIGHT_CLUE_QUESTION),
)


def _acting_names(today: list["ObservationDTO"]) -> list[str]:
    """오늘 직접 관찰된 행동이 있는 인물 — 가장 최근에 움직인 인물부터."""
    names: list[str] = []
    for observation in reversed(today):
        if observation.actor and observation.verification == "observed" and observation.actor not in names:
            names.append(observation.actor)
    return names


def suggest_questions(observations: list["ObservationDTO"], *, loop_n: int, asked: list[str],
                      limit: int = 3) -> list[str]:
    """오늘 회차 공개 기록으로 답할 수 있는 찾기 질문 — 같은 밤에 이미 한 질문은 뺀다."""
    today = [o for o in observations if o.loop_n == loop_n]
    candidates = [question for found, question in _RECORD_QUESTIONS if any(found(o) for o in today)]
    candidates += [ACTOR_QUESTION.format(name=_with_topic_particle(name))
                   for name in _acting_names(today)[:ACTORS_PER_NIGHT]]
    used = {question_key(q) for q in asked}
    suggestions = []
    for question in candidates:
        if question_key(question) not in used:
            suggestions.append(question)
            used.add(question_key(question))
    return suggestions[:limit]
