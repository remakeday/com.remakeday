from collections.abc import Callable

from apps.engine.app.dtos.health_dto import HealthDTO


class HealthInteractor:
    """공개 경로 — 기동 확인용 DB 상태만 돌려준다. 모델·시나리오·하네스 구성은 노출하지 않는다."""

    def __init__(self, db_ping: Callable[[], bool]) -> None:
        self._db_ping = db_ping

    def check(self) -> HealthDTO:
        try:
            db = "ok" if self._db_ping() else "error"
        except Exception:
            db = "error"
        return HealthDTO(db=db)
