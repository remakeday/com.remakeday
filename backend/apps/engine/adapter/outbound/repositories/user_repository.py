"""UserRepository — users 테이블 어댑터. UserRepositoryPort 구현."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
from apps.engine.adapter.outbound.orms.game_state_orm import (
    AttemptOrm,
    LoopOrm,
    NightOrm,
    NoteOrm,
    NpcStateOrm,
    RuleOrm,
    SurveyVoteOrm,
)
from apps.engine.adapter.outbound.orms.user_orm import UserOrm
from apps.engine.app.dtos.auth_dto import GoogleProfileDTO
from apps.engine.domain.entities.user_entity import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_sub(self, sub: str) -> User | None:
        row = self._s.execute(
            select(UserOrm).where(UserOrm.google_sub == sub)
        ).scalar_one_or_none()
        if row is None:
            return None
        return User(
            id=row.id,
            google_sub=row.google_sub,
            email=row.email,
            name=row.name,
            picture=row.picture,
        )

    def upsert_from_google(self, profile: GoogleProfileDTO) -> User:
        row = self._s.execute(
            select(UserOrm).where(UserOrm.google_sub == profile.sub)
        ).scalar_one_or_none()
        if row is None:
            row = UserOrm(google_sub=profile.sub)
            self._s.add(row)
        row.email = profile.email
        row.name = profile.name
        row.picture = profile.picture
        self._s.commit()
        self._s.refresh(row)
        return User(
            id=row.id,
            google_sub=row.google_sub,
            email=row.email,
            name=row.name,
            picture=row.picture,
        )

    def delete_with_data(self, user_id: uuid.UUID, sub: str) -> None:
        """회원탈퇴 — 이 사용자의 판과 하위 행, 기록, 계정을 한 트랜잭션에서 지운다(설계 2026-10-16 §2.4).

        FK에 ON DELETE CASCADE가 없어 자식부터 지운다. 중간에 실패하면 전부 되돌리고 예외를 다시 던진다.
        평가는 user_id와 판 ID 어느 쪽으로든 이 사용자 것이면 지운다(구판 표의 user_id가 비어 있어도 남지 않게).
        """
        attempt_ids = select(AttemptOrm.id).where(AttemptOrm.user_id == user_id)
        loop_ids = select(LoopOrm.id).where(LoopOrm.attempt_id.in_(attempt_ids))
        statements = (
            delete(NightOrm).where(NightOrm.loop_id.in_(loop_ids)),
            delete(NpcStateOrm).where(NpcStateOrm.loop_id.in_(loop_ids)),
            delete(LoopOrm).where(LoopOrm.attempt_id.in_(attempt_ids)),
            delete(NoteOrm).where(NoteOrm.attempt_id.in_(attempt_ids)),
            delete(RuleOrm).where(RuleOrm.attempt_id.in_(attempt_ids)),
            delete(SurveyVoteOrm).where(or_(SurveyVoteOrm.user_id == user_id,
                                            SurveyVoteOrm.attempt_id.in_(attempt_ids))),
            delete(EventLogOrm).where(EventLogOrm.session_id.in_(attempt_ids)),
            delete(EventLogOrm).where(EventLogOrm.type == "guard", EventLogOrm.payload["user_sub"].astext == sub),
            delete(AttemptOrm).where(AttemptOrm.user_id == user_id),
            delete(UserOrm).where(UserOrm.id == user_id),
        )
        try:
            for statement in statements:
                self._s.execute(statement)
            self._s.commit()
        except Exception:
            self._s.rollback()
            raise
