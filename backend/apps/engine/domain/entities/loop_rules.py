"""회차(loop)·비트 상태 전이 — 순수 함수. LLM·DB import 0."""

from dataclasses import dataclass, replace

from apps.engine.domain.value_objects.game_constants import (
    BEATS_PER_LOOP,
    LOOPS_PER_ATTEMPT,
)


class DomainError(Exception):
    pass


@dataclass(frozen=True)
class LoopState:
    loop_n: int
    beat: int
    budget_left: int
    ask_budget_left: int
    state: str  # day | night_pending


def initial_budget(loop_n: int) -> int:
    """발화 예산 8→4 (회차마다 -1)."""
    if not 1 <= loop_n <= LOOPS_PER_ATTEMPT:
        raise DomainError(f"회차는 1..{LOOPS_PER_ATTEMPT}: {loop_n}")
    return 9 - loop_n


def damage_for_loop(loop_n: int) -> tuple[int, bool]:
    """회차 → (손상 단계, 아침 문장 변형 여부). 기획서 §4.10."""
    table = {1: (0, False), 2: (1, False), 3: (2, False), 4: (2, True), 5: (3, False)}
    if loop_n not in table:
        raise DomainError(f"회차는 1..{LOOPS_PER_ATTEMPT}: {loop_n}")
    return table[loop_n]


def start_loop(loop_n: int) -> LoopState:
    return LoopState(
        loop_n=loop_n,
        beat=1,
        budget_left=initial_budget(loop_n),
        ask_budget_left=2,
        state="day",
    )


def apply_utterance(s: LoopState) -> LoopState:
    if s.state != "day":
        raise DomainError("낮이 아니면 발화할 수 없다")
    if s.budget_left <= 0:
        raise DomainError("발화 예산 소진")
    return replace(s, budget_left=s.budget_left - 1)


def next_beat(s: LoopState) -> LoopState:
    """비트 넘기기는 무료. 6에서 넘기면 밤 대기."""
    if s.state != "day":
        raise DomainError("낮이 아니면 비트를 넘길 수 없다")
    if s.beat >= BEATS_PER_LOOP:
        return replace(s, state="night_pending")
    return replace(s, beat=s.beat + 1)


def consume_ask_budget(s: LoopState) -> tuple[LoopState, bool]:
    """탐문 예산. 소진 시 (그대로, False) — 도구는 실행되지 않는다."""
    if s.ask_budget_left <= 0:
        return s, False
    return replace(s, ask_budget_left=s.ask_budget_left - 1), True
