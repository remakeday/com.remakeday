"""Atomic persistence boundary for a single day-scene transition."""

from contextlib import AbstractContextManager
from typing import Protocol
from uuid import UUID


class SceneTransactionPort(Protocol):
    def __call__(self, loop_id: UUID | str | None = None) -> AbstractContextManager[None]: ...
