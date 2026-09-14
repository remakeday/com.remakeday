"""One scene commit: loop progress, budget, public observations and notes together."""

from contextlib import contextmanager
from sqlalchemy.orm import Session

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
    def __call__(self):
        self._session.info[_SCENE_SCOPE] = True
        try:
            yield
            self._session.commit()
        except BaseException:
            self._session.rollback()
            raise
        finally:
            self._session.info.pop(_SCENE_SCOPE, None)
