"""게임 상태 저장소 — attempts·loops·npc_states·notes·rules·nights.

집계 루트(attempt→loop)가 좁고 서로 얽혀 있어 한 모듈에 둔다 (테이블별 클래스 분리).
"""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from apps.engine.adapter.outbound.repositories.scene_transaction import save_game_changes
from apps.engine.domain.entities.guard_rules import kst_day_start

from apps.engine.adapter.outbound.orms.game_state_orm import (
    AttemptOrm,
    LoopOrm,
    NightOrm,
    NoteOrm,
    NpcStateOrm,
    RuleOrm,
)


class AttemptRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, prior: AttemptOrm | None, user_id: uuid.UUID | None = None) -> AttemptOrm:
        row = AttemptOrm(
            attempt_n=(prior.attempt_n + 1) if prior else 1,
            prior_attempt_id=prior.id if prior else None,
            prior_cell_results=prior.prior_cell_results if prior else None,
            cookies_seen=list(prior.cookies_seen or []) if prior else [],
            user_id=user_id,
        )
        self._s.add(row)
        save_game_changes(self._s)
        return row

    def get(self, attempt_id: uuid.UUID) -> AttemptOrm | None:
        return self._s.get(AttemptOrm, attempt_id)

    def count_today(self, user_id: uuid.UUID, now: datetime) -> int:
        start = kst_day_start(now)
        stmt = (
            select(func.count())
            .select_from(AttemptOrm)
            .where(AttemptOrm.user_id == user_id, AttemptOrm.created_at >= start)
        )
        return self._s.scalar(stmt)

    def count_today_all(self, now: datetime) -> int:
        start = kst_day_start(now)
        stmt = select(func.count()).select_from(AttemptOrm).where(AttemptOrm.created_at >= start)
        return self._s.scalar(stmt)

    def save(self) -> None:
        save_game_changes(self._s)


class LoopRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, loop: LoopOrm, npc_states: list[NpcStateOrm]) -> LoopOrm:
        self._s.add(loop)
        self._s.flush()
        for st in npc_states:
            st.loop_id = loop.id
            self._s.add(st)
        save_game_changes(self._s)
        return loop

    def get(self, loop_id: uuid.UUID) -> LoopOrm | None:
        return self._s.get(LoopOrm, loop_id)

    def latest_for(self, attempt_id: uuid.UUID) -> LoopOrm | None:
        return self._s.scalars(
            select(LoopOrm)
            .where(LoopOrm.attempt_id == attempt_id)
            .order_by(LoopOrm.loop_n.desc())
        ).first()

    def score_of(self, attempt_id: uuid.UUID, loop_n: int) -> float | None:
        row = self._s.scalars(
            select(LoopOrm).where(
                LoopOrm.attempt_id == attempt_id, LoopOrm.loop_n == loop_n
            )
        ).first()
        return row.score if row else None

    def npc_states(self, loop_id: uuid.UUID) -> list[NpcStateOrm]:
        return list(
            self._s.scalars(
                select(NpcStateOrm).where(NpcStateOrm.loop_id == loop_id)
            ).all()
        )

    def npc_state(self, loop_id: uuid.UUID, code: str) -> NpcStateOrm | None:
        return self._s.scalars(
            select(NpcStateOrm).where(
                NpcStateOrm.loop_id == loop_id, NpcStateOrm.code == code
            )
        ).first()

    def save(self) -> None:
        save_game_changes(self._s)


class NoteRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def upsert(self, attempt_id: uuid.UUID, *, kind: str, text: str, loop_n: int, source_key: str) -> NoteOrm:
        """적립(또는 이미 있던) row를 돌려준다 — 실시간 발견(note_found) 반환용."""
        stmt = insert(NoteOrm).values(
            attempt_id=attempt_id, kind=kind, text=text, loop_n=loop_n, source_key=source_key
        ).on_conflict_do_nothing(index_elements=["attempt_id", "source_key"])
        self._s.execute(stmt)
        save_game_changes(self._s)
        return self._s.scalars(
            select(NoteOrm).where(
                NoteOrm.attempt_id == attempt_id, NoteOrm.source_key == source_key
            )
        ).first()

    def list(self, attempt_id: uuid.UUID) -> list[NoteOrm]:
        return list(
            self._s.scalars(
                select(NoteOrm).where(NoteOrm.attempt_id == attempt_id).order_by(NoteOrm.id)
            ).all()
        )

    def by_ids(self, attempt_id: uuid.UUID, ids: list[int]) -> list[NoteOrm]:
        if not ids:
            return []
        return list(
            self._s.scalars(
                select(NoteOrm).where(NoteOrm.attempt_id == attempt_id, NoteOrm.id.in_(ids))
            ).all()
        )


class RuleRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, rule: RuleOrm) -> RuleOrm:
        self._s.add(rule)
        save_game_changes(self._s)
        return rule

    def list(self, attempt_id: uuid.UUID) -> list[RuleOrm]:
        return list(
            self._s.scalars(
                select(RuleOrm).where(RuleOrm.attempt_id == attempt_id).order_by(RuleOrm.id)
            ).all()
        )

    def next_rule_id(self, attempt_id: uuid.UUID) -> str:
        return f"R{len(self.list(attempt_id)) + 1}"


class NightRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, night: NightOrm) -> NightOrm:
        self._s.add(night)
        save_game_changes(self._s)
        return night

    def get(self, night_id: uuid.UUID) -> NightOrm | None:
        return self._s.get(NightOrm, night_id)

    def for_loop(self, loop_id: uuid.UUID) -> NightOrm | None:
        return self._s.scalars(
            select(NightOrm).where(NightOrm.loop_id == loop_id)
        ).first()

    def previous_submitted(self, attempt_id: uuid.UUID, loop_n: int):
        return self._s.execute(
            select(NightOrm, LoopOrm.loop_n).join(LoopOrm, NightOrm.loop_id == LoopOrm.id)
            .where(LoopOrm.attempt_id == attempt_id, LoopOrm.loop_n < loop_n, NightOrm.submitted.is_(True))
            .order_by(LoopOrm.loop_n.desc()).limit(1)
        ).first()

    def save(self) -> None:
        save_game_changes(self._s)
