"""부록 C 로그 스키마 — 이벤트 DTO 17종.

- 필드는 부록 C를 그대로 따른다. 단 `session_end.pig_word_confirmed`는
  코어 시나리오 무지 원칙(§1-6)과 충돌하여 `identity_word_confirmed`로 중립화했다.
- 저장은 단일 events 테이블(JSONB payload). 필드 보장은 이 DTO들이 담당한다.
"""

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from apps.engine.domain.value_objects.event_type import EventType
from apps.engine.app.dtos.observation_dto import ObservationDTO


class EventBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ManagerPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    npc: str
    kind: Literal["memory_delete", "plan_patch"]
    detail: str
    reason: str


class TruthClaimVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    verdict: Literal["confirmed", "partial", "none"]
    matched_user_claim: str | None
    cited_chunks: list[str]


class CellScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cause: float
    motive: float
    side_effect: float
    identity: float


class SessionStartEvent(EventBase):
    type: Literal[EventType.SESSION_START] = EventType.SESSION_START
    session: str
    attempt_n: int
    prior_cell_results: CellScores | None


class LoopStartEvent(EventBase):
    type: Literal[EventType.LOOP_START] = EventType.LOOP_START
    session: str
    loop_n: int
    cumulative_loop_n: int
    budget: int
    rule_count: int
    damage: int
    measurement_version: str | None = None


class UtteranceEvent(EventBase):
    type: Literal[EventType.UTTERANCE] = EventType.UTTERANCE
    loop_n: int
    beat: int
    target: str
    text: str
    reply: str = ""  # NPC 응답 — 원인 체인·Advisor의 사실 원천 (부록 C 확장)
    budget_left: int
    suspicion_delta: int
    trust_delta: int
    disclosure_level: int


class ToolCallEvent(EventBase):
    type: Literal[EventType.TOOL_CALL] = EventType.TOOL_CALL
    loop_n: int
    beat: int
    caller: str
    tool: str
    args: dict
    result: str
    side_effect: str | None


class ManagerCheckEvent(EventBase):
    type: Literal[EventType.MANAGER_CHECK] = EventType.MANAGER_CHECK
    loop_n: int
    beat: int
    patches: list[ManagerPatch]
    budget_left: int


class MonkeyPawOfferEvent(EventBase):
    type: Literal[EventType.MONKEY_PAW_OFFER] = EventType.MONKEY_PAW_OFFER
    loop_n: int
    beat: int
    offer_index: Literal[1, 2]
    rule_id: str
    reason_shown: str | None
    accepted: bool


class AnswerDraftEvent(EventBase):
    type: Literal[EventType.ANSWER_DRAFT] = EventType.ANSWER_DRAFT
    loop_n: int
    tapped_note_ids: list[str]
    free_text: str


class AnswerNormalizedEvent(EventBase):
    type: Literal[EventType.ANSWER_NORMALIZED] = EventType.ANSWER_NORMALIZED
    loop_n: int
    claims: list[str] = Field(max_length=8)
    user_edited: bool
    edit_diff: str | None


class AnswerScoredEvent(EventBase):
    type: Literal[EventType.ANSWER_SCORED] = EventType.ANSWER_SCORED
    loop_n: int
    per_truth_claim: list[TruthClaimVerdict]
    cell_scores: CellScores
    total: float
    passed: bool


class AnswerWrongClaimsEvent(EventBase):
    type: Literal[EventType.ANSWER_WRONG_CLAIMS] = EventType.ANSWER_WRONG_CLAIMS
    loop_n: int
    claims: list[str]


class DeathEvent(EventBase):
    type: Literal[EventType.DEATH] = EventType.DEATH
    loop_n: int
    cause_chain: list[str]
    world_outcome: Literal["truck", "quiet", "closure"]
    ending_cell: str


class InterventionQuestionEvent(EventBase):
    type: Literal[EventType.INTERVENTION_QUESTION] = EventType.INTERVENTION_QUESTION
    loop_n: int
    q_index: int
    question: str
    answer: str
    hit_cause_chain: bool
    confirmed_note_id: str | None
    detail: str | None = None
    status: str = "unknown"
    evidence_ids: list[str] = Field(default_factory=list)
    next_observation: str | None = None


class InterventionOptionsEvent(EventBase):
    type: Literal[EventType.INTERVENTION_OPTIONS] = EventType.INTERVENTION_OPTIONS
    loop_n: int
    options: list[str] = Field(max_length=3)
    chosen: Literal["1", "2", "3", "custom"]
    custom_text: str | None


class RuleAppliedEvent(EventBase):
    type: Literal[EventType.RULE_APPLIED] = EventType.RULE_APPLIED
    loop_n: int
    rule_id: str
    source: Literal["user_choice", "user_custom", "monkey_paw"]
    conflict: bool
    intent: str | None = None
    interpretation: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class LoopEndEvent(EventBase):
    type: Literal[EventType.LOOP_END] = EventType.LOOP_END
    loop_n: int
    survived: bool
    anomaly_count: int
    rumor_index: int


class CookieShownEvent(EventBase):
    type: Literal[EventType.COOKIE_SHOWN] = EventType.COOKIE_SHOWN
    attempt_n: int
    cell: str
    level: Literal[1, 2, 3]
    text_id: str


class SessionEndEvent(EventBase):
    type: Literal[EventType.SESSION_END] = EventType.SESSION_END
    attempt_n: int
    final_cells: CellScores
    closed_by: Literal["clear", "doom", "understood", "understood_all"]
    identity_word_confirmed: bool


class HarnessEvent(EventBase):
    """모델정책 v1 §9 — 거부·재생성·폴백 기록. P6 누설률 계측의 원천."""

    type: Literal[EventType.HARNESS_EVENT] = EventType.HARNESS_EVENT
    loop_n: int | None
    beat: int | None
    role: str
    violations: list[str]
    attempts: int
    fallback_used: bool
    call_records: list[dict] = Field(default_factory=list)
    model: str | None = None
    version: str | None = None


class ObservationEvent(EventBase):
    type: Literal[EventType.OBSERVATION] = EventType.OBSERVATION
    loop_n: int
    observation: ObservationDTO


class RuleExecutionEvent(EventBase):
    type: Literal[EventType.RULE_EXECUTION] = EventType.RULE_EXECUTION
    loop_n: int
    beat: int
    rule_id: str
    condition: str
    actual_action: str | None
    result: Literal["obeyed", "violated", "conflict", "not_evaluable"]
    observation_ids: list[str] = Field(default_factory=list)
    side_effect: str | None = None


class RulePreviewEvent(EventBase):
    type: Literal[EventType.RULE_PREVIEW] = EventType.RULE_PREVIEW
    loop_n: int
    night_id: str
    preview: dict


GameEvent = Annotated[
    Union[
        SessionStartEvent,
        LoopStartEvent,
        UtteranceEvent,
        ToolCallEvent,
        ManagerCheckEvent,
        MonkeyPawOfferEvent,
        AnswerDraftEvent,
        AnswerNormalizedEvent,
        AnswerScoredEvent,
        AnswerWrongClaimsEvent,
        DeathEvent,
        InterventionQuestionEvent,
        InterventionOptionsEvent,
        RuleAppliedEvent,
        LoopEndEvent,
        CookieShownEvent,
        SessionEndEvent,
        HarnessEvent,
        ObservationEvent,
        RuleExecutionEvent,
        RulePreviewEvent,
    ],
    Field(discriminator="type"),
]

ALL_EVENT_TYPES: tuple[EventType, ...] = tuple(EventType)
