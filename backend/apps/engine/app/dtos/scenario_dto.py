"""ScenarioPort가 내려주는 시나리오 데이터 DTO (v2 — 모델정책 §10 반영).

시나리오 고유 명사는 값(value)으로만 흐른다. 코드·식별자·주석에 쓰지 않는다.
"""

from pydantic import BaseModel, ConfigDict, Field


class QuestionReplyActionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    beat: int = Field(ge=1, le=6)
    actor: str
    action: str


class QuestionReplyDTO(BaseModel):
    """An authored reply for a question rule, selected by actual prior actions."""
    model_config = ConfigDict(extra="forbid")

    action: str
    required_actions: list[QuestionReplyActionDTO] = Field(default_factory=list)
    reply: str


class CharacterDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str  # 시나리오 내부 식별자 (로마자)
    name: str  # 표시 이름
    role: str
    persona: str = ""  # 프롬프트용 인물 설정 조각
    goal: str = ""  # 오늘의 목표 한 줄
    relations: str = ""  # 관계 요약 한 줄
    fallback_lines: list[str] = Field(default_factory=list)  # 하네스 폴백 대사 3줄
    question_replies: list[QuestionReplyDTO] = Field(default_factory=list)
    initial_suspicion: int = 0
    initial_trust: int = 0
    lost: bool = False  # 소실 인물 여부 (손상 3층에서 소거)
    playable: bool = True  # False면 대화 대상 아님 (예: 방송으로만 존재)


class IllustrationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image_id: str  # 프론트 이미지 매핑의 식별자. LLM 출력으로 선택하지 않는다.
    caption: str  # 그림에서 관찰 가능한 모습 (진단·결과 판정 아님)


class BeatDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    n: int = Field(ge=1, le=6)
    title: str
    narration: str
    morning_text: str = ""
    broadcast: str | None = None  # 이 비트 진입 시 관리자 방송 문구 (없으면 null)
    illustrations: list[IllustrationDTO] = Field(default_factory=list)


class TruthClaimDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str  # 예: "cause-1"
    cell: str  # cause | motive | side_effect | identity
    text: str
    is_identity_word: bool = False  # 정체 칸의 핵심 단어 주장 (understood_all 판정용)
    world_outcomes: list[str] = Field(default_factory=list)


class CookieTextDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text_id: str
    cell: str
    level: int = Field(ge=1, le=3)
    text: str  # 부작용 칸은 {rule}/{npc}/{observation} 템플릿 포함 가능


class UtteranceBanDTO(BaseModel):
    """NPC 발화 금칙어 (하네스 검사 4번). 코어 소스 CI용 forbidden_words와 별개."""

    model_config = ConfigDict(extra="forbid")

    word: str
    exempt_code: str | None = None  # 이 인물은 예외
    from_loop: int | None = None  # 예외가 시작되는 회차 (exempt_code와 함께)


class FragmentDTO(BaseModel):
    """감각 파편 — 회차 시작 시 노트에 적립 (부록 A.3)."""

    model_config = ConfigDict(extra="forbid")

    loop_n: int = Field(ge=1, le=5)
    text: str
    beat: int = Field(default=1, ge=1, le=6)
    actor: str | None = None
    source_kind: str = "scene"
    world_outcome: str | None = None


class SceneActionDTO(BaseModel):
    """Finite scenario-provided action opportunities; execution is owned by the engine."""
    model_config = ConfigDict(extra="forbid")
    beat: int = Field(ge=1, le=6)
    actor: str
    action: str
    narration: str
    suppressed_narration: str
    illustrations: list[IllustrationDTO] = Field(default_factory=list)
    known_source: str | None = None
    explanation: str = ""  # Authored first-person account of this action, not an inferred outcome.
    illustration_participants: list[str] = Field(default_factory=list)


class SceneDialogueActionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor: str
    action: str


class SceneDialogueLineDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    text: str


class SceneDialogueDTO(BaseModel):
    """Authored speech; required actions must have happened in the disclosed scene."""
    model_config = ConfigDict(extra="forbid")

    beat: int = Field(ge=1, le=6)
    required_actions: list[SceneDialogueActionDTO] = Field(default_factory=list)
    lines: list[SceneDialogueLineDTO] = Field(min_length=2, max_length=4)


class ScenarioBundleDTO(BaseModel):
    """시드 upsert + 프롬프트 조립의 단위. ScenarioPort 구현체가 통째로 내려준다."""

    model_config = ConfigDict(extra="forbid")

    name: str
    surface_summary: str = ""  # 표면 세계 3~4문장 (Agent·Planner)
    hidden_truth: str = ""  # 숨겨진 진실 2문장 (Manager 전용)
    characters: list[CharacterDTO]
    beats: list[BeatDTO]
    truth_claims: list[TruthClaimDTO]
    cookies: list[CookieTextDTO]
    forbidden_words: list[str]  # 코어 소스 CI grep용
    utterance_bans: list[UtteranceBanDTO] = Field(default_factory=list)
    action_vocab: list[str] = Field(default_factory=list)  # Planner·규칙 행동 어휘
    fragments: list[FragmentDTO] = Field(default_factory=list)
    scene_actions: list[SceneActionDTO] = Field(default_factory=list)
    scene_dialogues: list[SceneDialogueDTO] = Field(default_factory=list)
    first_morning_illustrations: list[IllustrationDTO] = Field(default_factory=list)
    entry_lines: list[str] = Field(default_factory=list)  # 진입 화면 3줄
    ending_lines: list[str] = Field(default_factory=list)  # 5회차 제출 완료 후에만 공개
    ending_outcomes: dict[str, list[str]] = Field(default_factory=dict)
    morning_lines: dict[int, str] = Field(default_factory=dict)  # damage_level → 둘째 문장
    prompt_fragments: dict[str, str] = Field(default_factory=dict)  # role -> fragment
