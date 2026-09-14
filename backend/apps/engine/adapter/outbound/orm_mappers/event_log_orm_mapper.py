from uuid import UUID

from pydantic import TypeAdapter

from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
from apps.engine.app.dtos.event_log_dto import GameEvent

_event_adapter: TypeAdapter[GameEvent] = TypeAdapter(GameEvent)


class EventLogOrmMapper:
    @staticmethod
    def to_orm(session_id: UUID, event: GameEvent) -> EventLogOrm:
        payload = event.model_dump(mode="json")
        return EventLogOrm(
            session_id=session_id,
            attempt_n=getattr(event, "attempt_n", None),
            loop_n=getattr(event, "loop_n", None),
            type=str(event.type),
            payload=payload,
        )

    @staticmethod
    def to_dto(orm: EventLogOrm) -> GameEvent:
        return _event_adapter.validate_python(orm.payload)
