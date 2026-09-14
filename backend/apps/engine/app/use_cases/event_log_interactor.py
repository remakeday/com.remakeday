from uuid import UUID

from apps.engine.app.dtos.event_log_dto import GameEvent
from apps.engine.app.ports.output.event_log_port import EventLogPort
from apps.engine.domain.value_objects.event_type import EventType


class EventLogInteractor:
    def __init__(self, event_log: EventLogPort) -> None:
        self._event_log = event_log

    def record(self, session_id: UUID, event: GameEvent) -> None:
        self._event_log.record(session_id, event)

    def list_events(
        self,
        session_id: UUID,
        *,
        type: EventType | None = None,
        loop_n: int | None = None,
    ) -> list[GameEvent]:
        return self._event_log.query(session_id, type=type, loop_n=loop_n)
