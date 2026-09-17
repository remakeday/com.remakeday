import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
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
from core.matrix.grid_oracle_database_manager import get_audit_engine

logger = logging.getLogger(__name__)


class EventLogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(self, session_id: UUID, event: GameEvent) -> None:
        if event.type == EventType.HARNESS_EVENT and scene_transaction_active(self._session):
            self._record_audit(session_id, event)
            return
        self._session.add(EventLogOrmMapper.to_orm(session_id, event))
        save_game_changes(self._session)

    def _record_audit(self, session_id: UUID, event: GameEvent) -> None:
        """Model calls happened even if scene persistence later rolls back, so they commit on their own.

        A dedicated small pool keeps the audit from waiting on the request pool, and an audit failure is
        logged instead of raised: rolling back the scene after the model call would make the call free to repeat.
        Events have no loop foreign key; this never waits on an uncommitted new loop.
        """
        try:
            url = self._session.get_bind().url.render_as_string(hide_password=False)
            with Session(bind=get_audit_engine(url)) as audit:
                audit.add(EventLogOrmMapper.to_orm(session_id, event))
                audit.commit()
        except SQLAlchemyError:
            logger.exception("harness audit write failed; scene transaction continues (session %s)", session_id)

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
