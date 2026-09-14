"""ToolPort — 도구 디스패치 (ask_npc, search_notes).

P0는 인터페이스만. ask_npc 실구현·부작용은 P1, search_notes는 P2.
"""

from typing import Protocol

from pydantic import BaseModel, ConfigDict


class ToolCallDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str  # ask_npc | search_notes
    args: dict


class ToolResultDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: str
    side_effect: str | None = None


class ToolPort(Protocol):
    def dispatch(self, call: ToolCallDTO) -> ToolResultDTO: ...
