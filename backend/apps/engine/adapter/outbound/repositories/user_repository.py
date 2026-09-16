"""UserRepository — users 테이블 어댑터. UserRepositoryPort 구현."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

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
