"""REMAKE DAY — 파편 비트 배분·Manager 점검 축소·NPC 능동 발화(ambient)·부작용 흔적(aftermath)."""

import uuid

from apps.engine.adapter.outbound.repositories.event_log_repository import (
    EventLogRepository,
)
from apps.engine.adapter.outbound.orms.game_state_orm import RuleOrm
from apps.engine.adapter.outbound.repositories.game_repository import (
    LoopRepository,
    NoteRepository,
    RuleRepository,
)
from apps.engine.app.use_cases.game_support import build_agent_messages
from apps.engine.domain.value_objects.event_type import EventType

from apps.scenarios.scenario_a.adapter import build as build_a
from tests.engine.test_usecase_day import make_day


# ── 파편 실시간 발견 (#4) ──


def test_start_loop_accrues_only_disclosed_observations(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    notes = inter.list_notes(info["loop_id"])["notes"]
    assert notes and all(n["sources"] for n in notes)
    assert all(source["beat"] == 1 for note in notes for source in note["sources"])
    assert any(n["text"] == "소독약 냄새." for n in notes)
    assert not any(n["text"] == "트럭 소리." for n in notes)


def test_fragments_accrue_only_after_scene_disclosure(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    for beat in range(2, 7):
        res = inter.advance_beat(info["loop_id"])
        notes = inter.list_notes(info["loop_id"])["notes"]
        assert all(source["beat"] <= beat for note in notes for source in note["sources"])
    assert not any(n["text"] == "트럭 소리." for n in notes)  # outcome not yet known


# ── Manager 점검 축소 (#2) ──


def _manager_call_count(core_llm) -> int:
    return sum(
        1 for _, schema in core_llm.calls
        if schema.get("title") == "ManagerCheckOutput"
    )


def test_manager_check_skips_beat_3_and_5(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    core = inter._core_llm
    inter.advance_beat(info["loop_id"])  # → 비트 2
    assert _manager_call_count(core) == 1
    inter.advance_beat(info["loop_id"])  # → 비트 3: 점검 없음
    assert _manager_call_count(core) == 1
    inter.advance_beat(info["loop_id"])  # → 비트 4
    assert _manager_call_count(core) == 2
    inter.advance_beat(info["loop_id"])  # → 비트 5: 점검 없음
    assert _manager_call_count(core) == 2


# ── NPC 능동 발화 ambient (#3) ──


def test_advance_beat_response_has_ambient_and_note_found_keys(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    res = inter.advance_beat(info["loop_id"])
    assert "ambient" in res and "note_found" in res
    assert res["ambient"] and len(res["ambient"]["lines"]) == 3


def _chatter_pair(scenario, loop_n, beat):
    dialogue = next(d for d in scenario.bundle().scene_dialogues if d.beat == beat)
    codes = list(dict.fromkeys(line.code for line in dialogue.lines))
    chars = {c.code: c for c in scenario.bundle().characters}
    return chars[codes[0]], chars[codes[1]]


def test_ambient_chatter_two_npcs_and_utterance_events(db_session):
    scenario = build_a()
    a, b = _chatter_pair(scenario, loop_n=1, beat=2)
    chatter = {"candidate_index": 0}
    inter, scenario, attempt, info = make_day(db_session, [chatter])
    repo = LoopRepository(db_session)
    before = {
        s.code: (s.suspicion, s.trust) for s in repo.npc_states(uuid.UUID(info["loop_id"]))
    }
    res = inter.advance_beat(info["loop_id"])
    amb = res["ambient"]
    assert amb is not None
    assert [l["name"] for l in amb["lines"]] == [a.name, b.name, a.name]
    assert amb["lines"][0]["text"] == "민석아, 이 숫자 뭔지 알아?"
    assert inter._npc_llm.calls == []
    assert "충식" not in str(amb)  # No future transfer rumor from an old free-text fixture.
    assert all(set(l) == {"code", "name", "text"} for l in amb["lines"])
    # 게이지 불변
    after = {
        s.code: (s.suspicion, s.trust) for s in repo.npc_states(uuid.UUID(info["loop_id"]))
    }
    assert before == after
    # 원인 체인에 반영되도록 줄마다 UtteranceEvent 기록
    events = EventLogRepository(db_session).query(
        attempt.id, type=EventType.UTTERANCE, loop_n=1
    )
    passing = [e for e in events if e.text == "(지나가는 말)" and e.beat == 2]
    assert [(e.target, e.reply) for e in passing] == [(l["name"], l["text"]) for l in amb["lines"]]
    assert all(e.suspicion_delta == 0 and e.trust_delta == 0 for e in passing)


def test_ambient_chatter_enters_both_speakers_memory(db_session):
    # 잡담을 흘린 NPC가 직후 추궁에 "그런 말 한 적 없다"고 부정하지 않도록 —
    # 두 화자 모두의 memory에 잡담 라인이 들어간다 (utter의 "{이름}: {말}" 형식).
    scenario = build_a()
    a, b = _chatter_pair(scenario, loop_n=1, beat=2)
    chatter = {"candidate_index": 0}
    inter, scenario, attempt, info = make_day(db_session, [chatter])
    response = inter.advance_beat(info["loop_id"])
    repo = LoopRepository(db_session)
    expected = [f"{l['name']}: {l['text']}" for l in response["ambient"]["lines"]]
    for char in (a, b):
        mem = repo.npc_state(uuid.UUID(info["loop_id"]), char.code).memory or []
        for line in expected:
            assert line in mem


def test_ambient_chatter_rejects_speaker_outside_pair(db_session):
    scenario = build_a()
    a, b = _chatter_pair(scenario, loop_n=1, beat=2)
    outsider = next(
        c for c in scenario.bundle().characters
        if c.playable and c.name not in (a.name, b.name)
    )
    bad = {"lines": [
        {"name": outsider.name, "line": "나도 껴줘."},
        {"name": a.name, "line": "응."},
    ]}
    inter, scenario, attempt, info = make_day(db_session, [bad])
    res = inter.advance_beat(info["loop_id"])
    assert all(l["name"] in (a.name, b.name) for l in res["ambient"]["lines"])
    assert "나도 껴줘" not in str(res["ambient"])


def test_day_done_boundary_has_null_ambient_and_note(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    for _ in range(5):
        inter.advance_beat(info["loop_id"])
    res = inter.advance_beat(info["loop_id"])  # 비트 6 → 밤
    assert res["day_done"] is True
    assert res["ambient"] is None and res["note_found"] is None


# ── 부작용 흔적 aftermath (#6) ──


def _close_first_loop(db_session, info, *, side_effects):
    loop = LoopRepository(db_session).get(uuid.UUID(info["loop_id"]))
    loop.state = "closed"
    loop.side_effect_claims = side_effects
    db_session.commit()


def test_aftermath_when_prev_loop_had_side_effects(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    _close_first_loop(db_session, info, side_effects=["규칙이 어떤 변화를 만들었다"])
    info2 = inter.start_loop(attempt.id)
    assert info2["loop_n"] == 2
    assert info2["aftermath"] == "어제는 없던 일이 있었다."


def test_aftermath_null_without_side_effects(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    assert info["aftermath"] is None  # 첫 회차는 항상 null
    _close_first_loop(db_session, info, side_effects=[])
    info2 = inter.start_loop(attempt.id)
    assert info2["aftermath"] is None


# ── 규칙 세계 반영 (P0) ──


def _add_rule(db_session, attempt_id, *, target, action, rule_id="R1", shown_reason=None):
    RuleRepository(db_session).add(RuleOrm(
        attempt_id=attempt_id, rule_id=rule_id, source="user_choice",
        target=target, when_beat=None, effect="suppress", action=action,
        shown_reason=shown_reason, created_loop=1,
    ))


def test_chatter_candidates_follow_executed_suppression(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    _add_rule(db_session, attempt.id, target="준", action="손목띠를 만진다")
    response = inter.advance_beat(info["loop_id"])
    assert response["ambient"] is None
    assert "준은 손목띠를 건드리지 않고 앉아 있다." in response["narration"]
    assert inter._npc_llm.calls == []


def test_authored_chatter_has_scene_intent_without_model_selection(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    response = inter.advance_beat(info["loop_id"])
    assert [line["text"] for line in response["ambient"]["lines"]] == [
        "민석아, 이 숫자 뭔지 알아?", "몰라. 손목띠 빼면 안 돼.", "안 빼. 그냥 궁금해서."]
    assert inter._npc_llm.calls == []


def test_agent_prompt_marks_lost_character_absent():
    """P2 #4 — 소실 인물은 '여기 있는 사람'으로 세지 않는다 (Agent 프롬프트)."""
    bundle = build_a().bundle()
    char = next(c for c in bundle.characters if c.playable)
    lost = next(c for c in bundle.characters if c.lost)
    sys = build_agent_messages(
        bundle, char, rules_text="", suspicion=0, trust=50, opposite=False,
        memory=[], user_text="여기 누구 있어?", loop_n=1, age7_on=True,
    )[0].content
    assert f"{lost.name}은(는) 지금 여기 없다" in sys
    assert "여기 있는 사람으로 세지 않는다" in sys


def test_authored_chatter_does_not_introduce_lost_character(db_session):
    lost = next(c for c in build_a().bundle().characters if c.lost)
    inter, scenario, attempt, info = make_day(db_session, [])
    response = inter.advance_beat(info["loop_id"])
    assert lost.name not in str(response["ambient"])
    assert inter._npc_llm.calls == []


def test_agent_prompt_strengthens_rule_compliance():
    bundle = build_a().bundle()
    char = next(c for c in bundle.characters if c.playable)
    kwargs = dict(
        suspicion=0, trust=50, opposite=False, memory=[],
        user_text="검진 받았어?", loop_n=1, age7_on=True,
    )
    with_rule = build_agent_messages(
        bundle, char, rules_text="[R1] 채연은(는) 하루 종일에 검진 받기 — 반드시 하지 않는다",
        **kwargs,
    )[0].content
    without_rule = build_agent_messages(bundle, char, rules_text="", **kwargs)[0].content
    assert "실행했다고 단정하지 말고" in with_rule
    assert "하루를 실제로 바꿨다" not in without_rule


def test_start_loop_lists_active_rules(db_session):
    inter, scenario, attempt, info = make_day(db_session, [])
    assert info["active_rules"] == []  # 규칙이 없으면 빈 리스트
    npc = next(c for c in scenario.bundle().characters if c.playable)
    _add_rule(db_session, attempt.id, target=npc.name, action="검진 받기")
    _add_rule(
        db_session, attempt.id, target=npc.name, action="배급 남기기",
        rule_id="R2", shown_reason="오늘은 다 먹는다",
    )
    _close_first_loop(db_session, info, side_effects=[])
    info2 = inter.start_loop(attempt.id)
    assert info2["active_rules"] == [
        f"{npc.name}: 검진 받기 금지",  # shown_reason 없음 → 조립 문구
        "오늘은 다 먹는다",  # shown_reason 있음 → 그대로
    ]
