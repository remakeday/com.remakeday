"""LLMPort — 역할 무관 단일 인터페이스.

역할(NPC/Advisor/Normalizer/Manager/Evaluator) 차이는 컴포지션 루트에서
프롬프트 빌더 + provider 조합으로 만든다. 스키마 검증·재시도는 하네스(P1)의 일이며
이 포트는 1회 호출만 책임진다.
"""

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict


class MessageDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant"]
    content: str


class LLMParseError(ValueError):
    """LLM 출력이 JSON이 아님 — 하네스 재생성 트리거."""


class LLMRefusalError(Exception):
    """모델이 거부·절단됨 — 재시도해도 같은 결과이므로 하네스가 즉시 폴백한다."""


class LLMPort(Protocol):
    def complete(
        self, messages: list[MessageDTO], json_schema: dict,
        *, temperature: float | None = None,
    ) -> dict: ...
