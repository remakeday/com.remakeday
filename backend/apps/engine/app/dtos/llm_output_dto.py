"""역할별 LLM 출력 스키마 (모델정책 v1 §3~8) — 하네스 검사 2번의 기준."""

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, create_model, field_validator


def _bare_evidence_id(value: str) -> str:
    # Presentation brackets are not part of the identifier; membership is checked separately.
    return value[1:-1] if value.startswith("[") and value.endswith("]") else value


EvidenceId = Annotated[str, AfterValidator(_bare_evidence_id)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def max_length_of(model: type[BaseModel], field: str) -> int:
    """Field(max_length=N)에 적힌 목록 상한 — 스키마 밖에 숫자를 따로 두지 않는다."""
    return next(m.max_length for m in model.model_fields[field].metadata if hasattr(m, "max_length"))


def cut_to_max_length(model: type[BaseModel], field: str, value):
    """Anthropic 구조화 출력은 maxItems를 못 받아 목록이 상한을 넘겨 올 수 있다 — 재생성 대신 앞부터 상한까지만 받는다."""
    if not isinstance(value, list):
        return value
    return value[:max_length_of(model, field)]


class ToolCallSpec(StrictModel):
    name: Literal["ask_npc"]
    target: str
    question: str
    statement_id: str | None = None  # Optional source of the attributed statement.


class AgentOutput(StrictModel):
    reply: str = Field(min_length=1)
    evidence_ids: list[EvidenceId] = Field(default_factory=list)
    suspicion_delta: int = Field(ge=-10, le=10)
    trust_delta: int = Field(ge=-10, le=10)
    tool_call: ToolCallSpec | None = None
    plan_change: str | None = None
    mood: Literal["calm", "uneasy", "wary"] = "calm"


class ChatterLine(StrictModel):
    name: str
    line: str


class AmbientOutput(StrictModel):
    """NPC 능동 대화 — 비트 경계에서 둘이 지나가며 주고받는 2~4줄."""

    lines: list[ChatterLine] = Field(max_length=4)

    @property
    def text_all(self) -> str:
        """하네스 필드 검사용 — 전 줄을 한 텍스트로."""
        return " ".join(f"{l.name}: {l.line}" for l in self.lines)


def ambient_selection_output(candidate_count: int) -> type[StrictModel]:
    """The model can select public-record dialogue, never author another event."""
    return create_model("AmbientSelectionOutput", __base__=StrictModel,
                        candidate_index=(Literal[tuple(range(candidate_count))] | None, ...))


class AskNpcOutput(StrictModel):
    answer: str = Field(min_length=1)
    said_it: bool | None = None  # Current recollection, not proof that the speech occurred.
    evidence_ids: list[EvidenceId] = Field(default_factory=list)


class PlanBeat(StrictModel):
    beat: int = Field(ge=1, le=6)
    action: str
    note: str = ""


class NpcPlan(StrictModel):
    npc: str
    beats: list[PlanBeat] = Field(min_length=1, max_length=6)

    @field_validator("beats", mode="before")
    @classmethod
    def _cut_to_max_beats(cls, value):
        cut = cut_to_max_length(cls, "beats", value)
        # 꽉 찬 계획은 목록 순서가 곧 일정이라 번호를 위치로 되돌린다(maximum도 벗겨져 beat 7이 섞여 올 수 있다).
        # 성긴 계획의 beat 번호는 규칙 when_beat와 맞물리는 슬롯이므로 손대지 않는다.
        if isinstance(cut, list) and len(cut) == max_length_of(cls, "beats"):
            cut = [{**b, "beat": i + 1} if isinstance(b, dict) else b for i, b in enumerate(cut)]
        return cut


class PlannerOutput(StrictModel):
    plans: list[NpcPlan]


def planner_output(action_vocab: list[str]) -> type[PlannerOutput]:
    action_beat = create_model("PlanBeat", __base__=PlanBeat,
                              action=(Literal[tuple(action_vocab)], ...))
    npc_plan = create_model("NpcPlan", __base__=NpcPlan,
                            beats=(list[action_beat], Field(min_length=1, max_length=6)))
    return create_model("PlannerOutput", __base__=PlannerOutput, plans=(list[npc_plan], ...))


class ManagerPatch(StrictModel):
    npc: str
    kind: Literal["memory_delete"]
    target: str
    reason: str


# 적용 경로가 없어 선택지에서 뺀 예전 보정 종류. 모델이 습관처럼 내도 스키마 위반으로 재생성하지 않고 버린다.
_RETIRED_PATCH_KINDS = ("plan_patch",)


class ManagerCheckOutput(StrictModel):
    patches: list[ManagerPatch] = Field(default_factory=list)
    flagged_abnormal: list[str] = Field(default_factory=list)

    @field_validator("patches", mode="before")
    @classmethod
    def _drop_retired_kinds(cls, value):
        if not isinstance(value, list):
            return value
        return [p for p in value if not (isinstance(p, dict) and p.get("kind") in _RETIRED_PATCH_KINDS)]


class ManagerPawOutput(StrictModel):
    """원숭이손 제안 문구만 — 소원 선택은 코드가 한다 (스펙 §3 선택)."""
    shown_reason: str = Field(min_length=1, max_length=120)


class ManagerDecisionOutput(StrictModel):
    decision_reason: str


class UtteranceClassOutput(StrictModel):
    label: Literal["question", "request", "chat", "nonsense"]


class AdvisorAnswerOutput(StrictModel):
    answer: Literal["맞다", "틀리다", "그런 일은 없었다", "그건 알 수 없다", "기록은 이렇다"]
    detail: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class AdvisorInterpretationOutput(StrictModel):
    """Classify the question without rewriting any of its content."""
    question_kind: Literal["proposition", "lookup"]


class AdvisorSourceAssessment(StrictModel):
    id: str
    quote: str = Field(min_length=1, description="이 원본에서 그대로 가져온 짧은 인용. 해석이나 새로운 사실을 쓰지 않는다.")
    relation: Literal["supported", "contradicted", "unknown"] = Field(
        description="이 근거만으로 원래 질문 전체를 확인/반박/판단불가. 관련 정보가 있다는 것만으로 supported가 아니다.")


class AdvisorEvidenceOutput(StrictModel):
    """Extract original evidence before judging each source independently."""
    evidence: list[AdvisorSourceAssessment]


class AdvisorReplyOutput(StrictModel):
    question_kind: Literal["proposition", "lookup"]
    evidence: list[AdvisorSourceAssessment] = Field(max_length=2)
    answer: str = Field(min_length=1, max_length=400, description="질문에 직접 답하는 짧은 한국어 2~3문장. 기록 목록을 나열하지 않는다.")

    @field_validator("evidence", mode="before")
    @classmethod
    def _cut_to_max_evidence(cls, value):
        return cut_to_max_length(cls, "evidence", value)


class RuleOption(StrictModel):
    target: str
    when_beat: int | Literal["any"]
    effect: Literal["suppress", "enforce"]
    action: str
    label: str


class AdvisorOptionsOutput(StrictModel):
    options: list[RuleOption] = Field(min_length=3, max_length=3)

    @field_validator("options", mode="before")
    @classmethod
    def _cut_to_max_options(cls, value):
        return cut_to_max_length(cls, "options", value)


class AdvisorMapOutput(StrictModel):
    ok: bool
    rule: RuleOption | None = None
    reason: str | None = None


class ChainItem(StrictModel):
    beat: int | Literal["night"]
    fact: str


class EvaluatorChainOutput(StrictModel):
    chain: list[ChainItem]


class SideEffectClaim(StrictModel):
    rule_id: str
    claim: str


class EvaluatorSideEffectOutput(StrictModel):
    side_effect_claims: list[SideEffectClaim] = Field(default_factory=list)


class EvaluatorVerdictOutput(StrictModel):
    # 필드 순서 = 생성 순서 (스키마 제약 디코딩) — 근거를 먼저 쓰게 해 판정을 안정화한다
    why: str = ""
    # 고른 후보 문장의 일부를 한 글자도 고치지 않고 옮긴 것 — 번호보다 먼저 쓰게 하고,
    # 인용이 유일하게 가리키는 후보로 matched_index를 보정한다(번호만 하나 어긋나는 사례 대응)
    matched_quote: str | None = None
    matched_index: int | None = None  # 후보 목록의 0-기반 번호 — 문자열 인용 대신
    verdict: Literal["confirmed", "partial", "none"]


def evaluator_verdict_output(candidate_count: int) -> type[EvaluatorVerdictOutput]:
    """구조화 출력 단계부터 실제 후보 번호 또는 null만 생성하도록 제한한다."""
    return create_model(
        "EvaluatorVerdictOutput", __base__=EvaluatorVerdictOutput,
        matched_index=(Literal[tuple(range(candidate_count))] | None, None),
    )
