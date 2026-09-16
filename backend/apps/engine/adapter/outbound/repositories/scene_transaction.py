"""One scene commit: loop progress, budget, public observations and notes together."""

from contextlib import contextmanager
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.engine.adapter.outbound.orms.game_state_orm import LoopOrm

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
    def __call__(self, loop_id=None):
        self._session.info[_SCENE_SCOPE] = True
        try:
            if loop_id is not None:
                # Serializes day mutations, including duplicate requests arriving together.
                self._session.scalars(select(LoopOrm).where(LoopOrm.id == loop_id)
                    .with_for_update().execution_options(populate_existing=True)).first()
            yield
            self._session.commit()
        except BaseException:
            self._session.rollback()
            raise
        finally:
            self._session.info.pop(_SCENE_SCOPE, None)
