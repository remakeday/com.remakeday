from uuid import UUID

from apps.engine.app.dtos import event_log_dto as ev


class SessionInteractor:
    def __init__(self, *, attempts, event_log, scenario) -> None:
        self._attempts = attempts
        self._events = event_log
        self._scenario = scenario

    def start(self, prior_attempt_id: UUID | None) -> dict:
        prior = self._attempts.get(prior_attempt_id) if prior_attempt_id else None
        attempt = self._attempts.create(prior)
        prior_cells = attempt.prior_cell_results
        self._events.record(
            attempt.id,
            ev.SessionStartEvent(
                session=str(attempt.id),
                attempt_n=attempt.attempt_n,
                prior_cell_results=ev.CellScores(**prior_cells) if prior_cells else None,
            ),
        )
        return {
            "attempt_id": str(attempt.id),
            "attempt_n": attempt.attempt_n,
            "entry_lines": self._scenario.entry_lines(),
            "prior_cell_results": prior_cells,
        }
