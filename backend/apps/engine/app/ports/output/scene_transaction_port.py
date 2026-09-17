"""Atomic persistence boundary for one use-case step, serialized on a row (loop for a day scene, night for a night request, attempt for a loop start)."""

from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import Protocol
from uuid import UUID


class RowBusy(Exception):
    """Another request holds the row; the transaction refuses at once instead of waiting for it."""


class RequestInFlight(Exception):
    """앞 요청이 같은 행을 처리 중이다 — 기다리지 않고 409. 라우터가 재시도 코드(request_in_flight)를 붙인다.

    유스케이스는 자기 상태 오류와 함께 상속한다(예: `class RequestInFlight(GameStateError, port.RequestInFlight)`)."""


class SceneTransactionPort(Protocol):
    def __call__(self, row_id: UUID | str | None = None) -> AbstractContextManager[None]: ...


@contextmanager
def one_request_per_row(transaction: SceneTransactionPort, row_id, busy: type[RequestInFlight], message: str) -> Iterator[None]:
    """한 행에 요청 하나씩 — 앞 요청이 잠금을 쥐고 있으면(RowBusy) 기다리지 않고 `busy(message)`로 돌려보낸다(opus 리뷰 C1, 5b)."""
    try:
        with transaction(row_id):
            yield
    except RowBusy as exc:
        raise busy(message) from exc
