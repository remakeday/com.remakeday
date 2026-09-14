"""FakeLLM — 테스트·개발용. 응답 큐를 순서대로 반환한다.

큐가 비면 빈 dict를 반환한다 (P0에서는 런타임 호출 경로가 없다).
"""

from collections import deque

from apps.engine.app.ports.output.llm_port import MessageDTO


class FakeLLM:
    def __init__(self, responses: list[dict] | None = None) -> None:
        self._queue: deque[dict] = deque(responses or [])
        self.calls: list[tuple[list[MessageDTO], dict]] = []
        self.temperatures: list[float | None] = []

    def complete(
        self, messages: list[MessageDTO], json_schema: dict,
        *, temperature: float | None = None,
    ) -> dict:
        self.calls.append((messages, json_schema))
        self.temperatures.append(temperature)
        if self._queue:
            return self._queue.popleft()
        return {}
