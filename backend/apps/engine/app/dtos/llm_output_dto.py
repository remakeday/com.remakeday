"""역할별 LLM 출력 스키마 (모델정책 v1 §3~8) — 하네스 검사 2번의 기준."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ToolCallSpec(StrictModel):
    name: Literal["ask_npc"]
    target: str
    question: str


class AgentOutput(StrictModel):
    reply: str
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
    answer: str
    said_it: bool  # 인용된 말을 실제로 했는가 — 불일치 발각의 근거


class PlanBeat(StrictModel):
    beat: int = Field(ge=1, le=6)
    action: str
    note: str = ""


class NpcPlan(StrictModel):
    npc: str
    beats: list[PlanBeat] = Field(min_length=1, max_length=6)


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
    kind: Literal["memory_delete", "plan_patch"]
    target: str
    reason: str


class ManagerCheckOutput(StrictModel):
    patches: list[ManagerPatch] = Field(default_factory=list)
    flagged_abnormal: list[str] = Field(default_factory=list)


class RuleSpec(StrictModel):
    target: str
    when_beat: int | Literal["any"]
    effect: Literal["suppress", "enforce"]
    action: str


class ManagerPawOutput(StrictModel):
    rule: RuleSpec
    shown_reason: str
    hidden_side_effect: str


class ManagerDecisionOutput(StrictModel):
    decision_reason: str


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


class RuleOption(StrictModel):
    target: str
    when_beat: int | Literal["any"]
    effect: Literal["suppress", "enforce"]
    action: str
    label: str


class AdvisorOptionsOutput(StrictModel):
    options: list[RuleOption] = Field(min_length=3, max_length=3)


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
    matched_index: int | None = None  # 후보 목록의 0-기반 번호 — 문자열 인용 대신
    verdict: Literal["confirmed", "partial", "none"]


def evaluator_verdict_output(candidate_count: int) -> type[EvaluatorVerdictOutput]:
    """구조화 출력 단계부터 실제 후보 번호 또는 null만 생성하도록 제한한다."""
    return create_model(
        "EvaluatorVerdictOutput", __base__=EvaluatorVerdictOutput,
        matched_index=(Literal[tuple(range(candidate_count))] | None, None),
    )
