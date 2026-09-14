from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.engine.adapter.outbound.orm_mappers.event_log_orm_mapper import (
    EventLogOrmMapper,
)
from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
from apps.engine.app.dtos.event_log_dto import GameEvent
from apps.engine.domain.value_objects.event_type import EventType
from apps.engine.adapter.outbound.repositories.scene_transaction import (
    save_game_changes, scene_transaction_active,
)


class EventLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(self, session_id: UUID, event: GameEvent) -> None:
        if event.type == EventType.HARNESS_EVENT and scene_transaction_active(self._session):
            # Model calls happened even if scene persistence later rolls back.
            # Events have no loop foreign key; this never waits on an uncommitted new loop.
            with Session(bind=self._session.get_bind()) as audit:
                audit.add(EventLogOrmMapper.to_orm(session_id, event))
                audit.commit()
            return
        self._session.add(EventLogOrmMapper.to_orm(session_id, event))
        save_game_changes(self._session)

    def query(
        self,
        session_id: UUID,
        *,
        type: EventType | None = None,
        loop_n: int | None = None,
    ) -> list[GameEvent]:
        stmt = select(EventLogOrm).where(EventLogOrm.session_id == session_id)
        if type is not None:
            stmt = stmt.where(EventLogOrm.type == str(type))
        if loop_n is not None:
            stmt = stmt.where(EventLogOrm.loop_n == loop_n)
        stmt = stmt.order_by(EventLogOrm.id)
        rows = self._session.scalars(stmt).all()
        return [EventLogOrmMapper.to_dto(r) for r in rows]
