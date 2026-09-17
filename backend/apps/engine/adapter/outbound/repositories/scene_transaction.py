"""One scene commit: loop progress, budget, public observations and notes together."""

from contextlib import contextmanager
from psycopg.errors import LockNotAvailable
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from apps.engine.adapter.outbound.orms.game_state_orm import AttemptOrm, LoopOrm, NightOrm
from apps.engine.app.ports.output.scene_transaction_port import RowBusy

_SCENE_SCOPE = "engine_scene_transaction"


def scene_transaction_active(session: Session) -> bool:
    return bool(session.info.get(_SCENE_SCOPE))


def save_game_changes(session: Session) -> None:
    if scene_transaction_active(session):
        session.flush()
    else:
        session.commit()


class SceneTransaction:
    def __init__(self, session: Session) -> None:
        self._session = session

    @contextmanager
    def __call__(self, row_id=None):
        self._session.info[_SCENE_SCOPE] = True
        try:
            if row_id is not None:
                self._lock(row_id)
            yield
            self._session.commit()
        except BaseException:
            self._session.rollback()
            raise
        finally:
            self._session.info.pop(_SCENE_SCOPE, None)

    def _fresh(self, statement):
        return self._session.scalars(statement.execution_options(populate_existing=True)).first()

    def _lock_row(self, statement, row_id):
        """잠금은 기다리지 않는다(NOWAIT). 앞 요청이 모델 응답을 기다리며 행을 쥐고 있으면 곧바로 RowBusy —
        기다리는 요청이 연결을 쥔 채 쌓여 풀을 채우지 않는다 (opus 리뷰 C1, 5b)."""
        try:
            return self._fresh(statement)
        except OperationalError as exc:
            if isinstance(exc.orig, LockNotAvailable):
                raise RowBusy(str(row_id)) from exc
            raise

    def _lock(self, loop_id) -> None:
        # 낮 장면 한 요청 — 같은 회차 요청(발화·다음 장면·원숭이손 응답)을 회차 행 잠금으로 직렬화한다.
        # 회차 PK는 바뀌지 않는다 — FOR NO KEY UPDATE로 그 회차를 참조하는 INSERT(밤 정리 등)의 외래 키 검사와 부딪히지 않는다 (opus 리뷰 M1).
        self._lock_row(select(LoopOrm).where(LoopOrm.id == loop_id).with_for_update(nowait=True, key_share=True), loop_id)


class NightTransaction(SceneTransaction):
    """밤 한 요청 — 같은 밤 요청(제출·질문·규칙 선택)을 밤 행 잠금으로 직렬화하고, 잠금을 얻은 뒤의 밤·회차 상태로 판정한다."""

    def _lock(self, night_id) -> None:
        night = self._lock_row(select(NightOrm).where(NightOrm.id == night_id).with_for_update(nowait=True), night_id)
        if night is not None:  # 앞 요청(규칙 선택)이 회차를 닫았을 수 있다 — 소유 확인이 올려 둔 옛 회차를 새로 읽는다
            self._fresh(select(LoopOrm).where(LoopOrm.id == night.loop_id))


class AttemptTransaction(SceneTransaction):
    """회차 시작 한 요청 — 같은 판의 회차 시작을 판 행 잠금으로 직렬화한다.

    판 행은 회차·노트·규칙이 외래 키로 참조한다. FOR NO KEY UPDATE는 외래 키 검사(FOR KEY SHARE)와 부딪히지 않고
    회차 시작끼리·판 상태 갱신과만 부딪힌다."""

    def _lock(self, attempt_id) -> None:
        self._lock_row(select(AttemptOrm).where(AttemptOrm.id == attempt_id)
                       .with_for_update(nowait=True, key_share=True), attempt_id)
