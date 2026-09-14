from typing import Protocol
from uuid import UUID

from apps.engine.app.dtos.event_log_dto import GameEvent
from apps.engine.domain.value_objects.event_type import EventType


class EventLogPort(Protocol):
    def record(self, session_id: UUID, event: GameEvent) -> None: ...

    def query(
        self,
        session_id: UUID,
        *,
        type: EventType | None = None,
        loop_n: int | None = None,
    ) -> list[GameEvent]: ...
