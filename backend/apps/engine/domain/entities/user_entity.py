"""User 엔티티 — Google 계정으로 식별되는 이용자. 순수 도메인(프레임워크 무의존)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class User:
    google_sub: str  # Google 계정 고유 식별자(sub) — 불변 키
    email: str
    name: str
    picture: str = ""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
