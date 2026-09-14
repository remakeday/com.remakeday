"""시나리오 시드 동기화 — 매 기동 시 upsert + 시드에서 사라진 행 삭제.

ensure_seeded early-return 패턴 금지 (작업지시서 "하지 말 것").
"""

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from apps.engine.adapter.outbound.orms.scenario_seed_orm import (
    ScenarioBeatOrm,
    ScenarioCharacterOrm,
    ScenarioCookieOrm,
    ScenarioFragmentOrm,
    ScenarioTruthClaimOrm,
)
from apps.engine.app.dtos.scenario_dto import ScenarioBundleDTO


class ScenarioSeedRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_bundle(self, bundle: ScenarioBundleDTO) -> None:
        self._sync(
            ScenarioCharacterOrm,
            key="code",
            rows=[
                {
                    "scenario": bundle.name,
                    "code": c.code,
                    "name": c.name,
                    "role": c.role,
                    "persona": c.persona,
                    "initial_suspicion": c.initial_suspicion,
                    "initial_trust": c.initial_trust,
                    "lost": c.lost,
                }
                for c in bundle.characters
            ],
        )
        self._sync(
            ScenarioBeatOrm,
            key="n",
            rows=[
                {
                    "scenario": bundle.name,
                    "n": b.n,
                    "title": b.title,
                    "narration": b.narration,
                    "morning_text": b.morning_text,
                }
                for b in bundle.beats
            ],
        )
        self._sync(
            ScenarioTruthClaimOrm,
            key="code",
            rows=[
                {"scenario": bundle.name, "code": t.code, "cell": t.cell, "text": t.text}
                for t in bundle.truth_claims
            ],
        )
        self._sync(
            ScenarioCookieOrm,
            key="text_id",
            rows=[
                {
                    "scenario": bundle.name,
                    "text_id": k.text_id,
                    "cell": k.cell,
                    "level": k.level,
                    "text": k.text,
                }
                for k in bundle.cookies
            ],
        )
        self._sync(
            ScenarioFragmentOrm,
            key="code",
            rows=[
                {
                    "scenario": bundle.name,
                    "code": f"fr-{f.loop_n}-{i}",
                    "loop_n": f.loop_n,
                    "text": f.text,
                }
                for i, f in enumerate(bundle.fragments)
            ],
        )
        self._session.commit()

    def _sync(self, orm_cls, *, key: str, rows: list[dict]) -> None:
        if not rows:
            return
        scenario = rows[0]["scenario"]
        stmt = insert(orm_cls).values(rows)
        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in orm_cls.__table__.columns
            if c.name not in ("id", "scenario", key)
        }
        self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=["scenario", key], set_=update_cols
            )
        )
        keep = [r[key] for r in rows]
        self._session.execute(
            delete(orm_cls).where(
                orm_cls.__table__.c.scenario == scenario,
                orm_cls.__table__.c[key].notin_(keep),
            )
        )
