"""Driven Port — User 애그리거트 저장소."""

from __future__ import annotations

import uuid
from typing import Protocol

from apps.engine.app.dtos.auth_dto import GoogleProfileDTO
from apps.engine.domain.entities.user_entity import User


class UserRepositoryPort(Protocol):
    def upsert_from_google(self, profile: GoogleProfileDTO) -> User:
        """google_sub 기준으로 사용자를 만들거나 갱신하고, 저장된 엔티티를 돌려준다."""
        ...

    def get_by_sub(self, sub: str) -> User | None:
        """google_sub로 사용자를 찾는다. 없으면 None."""
        ...

    def delete_with_data(self, user_id: uuid.UUID, sub: str) -> None:
        """회원탈퇴 — 그 사용자의 판·기록·계정을 한 트랜잭션에서 지운다."""
        ...
