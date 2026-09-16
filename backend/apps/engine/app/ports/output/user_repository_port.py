"""Driven Port — User 애그리거트 저장소."""

from __future__ import annotations

from typing import Protocol

from apps.engine.app.dtos.auth_dto import GoogleProfileDTO
from apps.engine.domain.entities.user_entity import User


class UserRepositoryPort(Protocol):
    def upsert_from_google(self, profile: GoogleProfileDTO) -> User:
        """google_sub 기준으로 사용자를 만들거나 갱신하고, 저장된 엔티티를 돌려준다."""
        ...
