"""시드 동기화 — 매 기동 upsert + 변경 반영 + 삭제 정리 (early-return 금지 검증)."""

from sqlalchemy import select

from apps.engine.adapter.outbound.orms.scenario_seed_orm import (
    ScenarioBeatOrm,
    ScenarioCharacterOrm,
    ScenarioCookieOrm,
    ScenarioTruthClaimOrm,
)
from apps.engine.adapter.outbound.repositories.scenario_seed_repository import (
    ScenarioSeedRepository,
)
from apps.scenarios.scenario_example.adapter import build


def _counts(session):
    return {
        "characters": len(session.scalars(select(ScenarioCharacterOrm)).all()),
        "beats": len(session.scalars(select(ScenarioBeatOrm)).all()),
        "claims": len(session.scalars(select(ScenarioTruthClaimOrm)).all()),
        "cookies": len(session.scalars(select(ScenarioCookieOrm)).all()),
    }


def test_sync_twice_no_duplicates(db_session):
    repo = ScenarioSeedRepository(db_session)
    bundle = build().bundle()

    repo.upsert_bundle(bundle)
    first = _counts(db_session)
    repo.upsert_bundle(bundle)

    assert _counts(db_session) == first
    assert first["beats"] == 6


def test_changed_seed_value_is_reflected_on_resync(db_session):
    repo = ScenarioSeedRepository(db_session)
    bundle = build().bundle()
    repo.upsert_bundle(bundle)

    changed = bundle.model_copy(deep=True)
    changed.beats[0].narration = "수정된 서술"
    repo.upsert_bundle(changed)

    row = db_session.scalars(
        select(ScenarioBeatOrm).where(
            ScenarioBeatOrm.scenario == bundle.name, ScenarioBeatOrm.n == 1
        )
    ).one()
    assert row.narration == "수정된 서술"


def test_removed_seed_row_is_pruned_on_resync(db_session):
    repo = ScenarioSeedRepository(db_session)
    bundle = build().bundle()
    repo.upsert_bundle(bundle)

    shrunk = bundle.model_copy(deep=True)
    removed = shrunk.characters.pop()
    repo.upsert_bundle(shrunk)

    codes = set(
        db_session.scalars(
            select(ScenarioCharacterOrm.code).where(
                ScenarioCharacterOrm.scenario == bundle.name
            )
        ).all()
    )
    assert removed.code not in codes
    assert len(codes) == len(shrunk.characters)
