"""밤 단서 시퀀스(밤단서 v2 P.1) — 회차별 선택·트럭 추가 줄·「소등 후」 관찰 저장·낮 파편의 밤 이동."""

import pytest

from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.adapter.outbound.orms.game_state_orm import LoopOrm, NightOrm
from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    LoopRepository,
    NightRepository,
    NoteRepository,
    RuleRepository,
)
from apps.engine.app.use_cases.night_interactor import NightInteractor
from apps.engine.app.use_cases.public_observations import public_observations
from apps.scenarios.scenario_a.adapter import build as build_a
from tests.engine.test_usecase_day import make_day

EXPECTED = {
    1: ("MA08", ["P01"], "소독약 냄새. 발 아래 콘크리트가 차다."),
    2: ("MA09", ["P02", "clue-05"], "트럭 소리."),
    3: ("MA10", ["P03"], "거울이 없다."),
    4: ("MA11", ["P04"], "배급 포대에 글자가 있다."),
    5: ("MA12", ["P05"], "손이 없어서 문을 못 연다는 것을 문득 안다."),
}
MOVED_TO_NIGHT = [
    "소독약 냄새.", "발 아래 콘크리트가 차다.", "거울이 없다.",
    "배급 포대에 글자가 있다.", "손이 없어서 문을 못 연다는 것을 문득 안다.",
]


def _night(db_session, loop_n, world_outcome):
    attempt = AttemptRepository(db_session).create(None)
    loop = LoopOrm(attempt_id=attempt.id, loop_n=loop_n, beat=6, budget_left=0, state="night_draft")
    LoopRepository(db_session).create(loop, [])
    loop.world_outcome = world_outcome
    uc = NightInteractor(
        attempts=AttemptRepository(db_session), loops=LoopRepository(db_session),
        notes=NoteRepository(db_session), rules=RuleRepository(db_session),
        nights=NightRepository(db_session), event_log=EventLogRepository(db_session),
        scenario=build_a(), core_llm=FakeLLM([]), harness_on=True, cookie_ab_on=False,
        night_cls=NightOrm,
    )
    return uc, attempt, loop


@pytest.mark.parametrize("loop_n", [1, 2, 3, 4, 5])
def test_night_clue_follows_the_loop_table(db_session, loop_n):
    uc, _, loop = _night(db_session, loop_n, "quiet")
    clue = uc._disclose_night_clue(loop)
    voice_id, image_ids, caption = EXPECTED[loop_n]
    assert clue["loop_n"] == loop_n
    assert clue["voice_id"] == voice_id
    assert clue["image_ids"] == image_ids
    assert clue["caption"] == caption
    assert clue["broadcast"]
    assert clue["outcome_line"] is None  # 조용한 밤에는 트럭 파편이 붙지 않는다


@pytest.mark.parametrize("loop_n, line", [
    (1, "트럭 소리."), (4, None), (2, None), (5, None),  # 4회차 읽힌 문자열 파편은 뺐다 — 5회차 낮 끝 MA13으로 (테스터9 F24)
])
def test_truck_nights_append_the_existing_truck_fragment(db_session, loop_n, line):
    uc, _, loop = _night(db_session, loop_n, "truck")
    assert uc._disclose_night_clue(loop)["outcome_line"] == line


def test_caption_and_broadcast_are_saved_as_lights_out_evidence(db_session):
    uc, attempt, loop = _night(db_session, 4, "quiet")
    clue = uc._disclose_night_clue(loop)
    uc._disclose_night_clue(loop)  # 재호출해도 중복 저장하지 않는다
    rows = {o.text: o for o in public_observations(EventLogRepository(db_session), attempt.id)}
    assert set(rows) == {clue["caption"], clue["broadcast"]}
    for o in rows.values():
        assert (o.loop_n, o.beat, o.scene_title) == (4, 6, "소등 후")
    assert (rows[clue["caption"]].source_kind, rows[clue["caption"]].verification) == ("scene", "observed")
    assert (rows[clue["broadcast"]].source_kind, rows[clue["broadcast"]].verification) == ("statement", "reported")
    notes = NoteRepository(db_session).list(attempt.id)
    assert sorted((n.kind, n.text, n.loop_n) for n in notes) == sorted([
        ("fragment", clue["caption"], 4), ("fragment", clue["broadcast"], 4),
    ])


def test_submit_returns_the_night_clue(db_session):
    uc, _, loop = _night(db_session, 1, None)
    night = NightRepository(db_session).create(NightOrm(
        loop_id=loop.id, free_text="상황을 이해했다.", claims=["상황을 이해했다."], tapped_note_ids=[]))
    result = uc.submit(night.id)
    assert result["night_clue"]["voice_id"] == "MA08"
    assert result["night_clue"]["outcome_line"] == ("트럭 소리." if result["world_outcome"] == "truck" else None)


def test_submit_suggests_lookup_questions_from_the_night_clue_it_just_disclosed(db_session):
    from apps.engine.domain.entities.question_suggestions import BROADCAST_QUESTION, NIGHT_CLUE_QUESTION
    uc, _, loop = _night(db_session, 1, None)
    night = NightRepository(db_session).create(NightOrm(
        loop_id=loop.id, free_text="상황을 이해했다.", claims=["상황을 이해했다."], tapped_note_ids=[]))
    result = uc.submit(night.id)
    assert result["suggested_questions"] == [BROADCAST_QUESTION, NIGHT_CLUE_QUESTION]
    assert uc.submit(night.id)["suggested_questions"] == result["suggested_questions"]  # 저장 응답 재전송에도 붙는다


def test_orphan_fragments_moved_from_day_to_night():
    bundle = build_a().bundle()
    day_texts = [f.text for f in bundle.fragments]
    assert not any(t in day_texts for t in MOVED_TO_NIGHT)
    # 발화자가 있는 전언과 4회차 아침의 시각은 낮에 남는다
    assert "7시 13분." in day_texts and any(t.startswith("같은 방에 있던 충식은 어제 이송됐다.") for t in day_texts)
    assert not any("축산" in t for t in day_texts)  # 인물은 글자를 읽지 못한다 — 트럭 표기는 5회차 낮 끝 방송이 말한다 (F24)
    assert [(b.loop_n, b.beat, b.voice_id, b.image_id) for b in bundle.day_end_broadcasts] == [(5, 6, "MA13", "P06")]
    assert [c.loop_n for c in bundle.night_clues] == [1, 2, 3, 4, 5]
    assert len({c.voice_id for c in bundle.night_clues}) == 5


def test_day_beats_no_longer_disclose_the_moved_fragments(db_session):
    inter, _, _, info = make_day(db_session, [])
    for _ in range(2, 7):
        inter.advance_beat(info["loop_id"])
    notes = [n["text"] for n in inter.list_notes(info["loop_id"])["notes"]]
    assert notes and not any(t in notes for t in MOVED_TO_NIGHT)
