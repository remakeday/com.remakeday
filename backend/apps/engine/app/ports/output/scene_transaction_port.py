"""Atomic persistence boundary for a single day-scene transition."""

from contextlib import AbstractContextManager
from typing import Protocol


class SceneTransactionPort(Protocol):
    def __call__(self) -> AbstractContextManager[None]: ...
