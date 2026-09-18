"""대사창 줄 — 응답 조립 때 계산하고 저장하지 않는다 (낮 화면 VN 설계 §3). kind는 값이다 — 서버는 kind로 분기하지 않는다."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

LineKind = Literal["scene", "action", "rule_result", "statement", "broadcast", "npc", "paw_effect", "fragment", "system"]


class LineDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: LineKind
    speaker: str | None = None  # 인물 이름·"관리자"·None
    text: str
    image_id: str | None = None  # 이 줄에서 바꿔 보여 줄 장면 그림
    voice_id: str | None = None  # 음성이 있는 줄만 — 서버에 낮 방송 음원 ID가 없어 지금은 항상 None
    observation_id: str | None = None  # 단서 기록과 연결 (NEW·그림 열기)
