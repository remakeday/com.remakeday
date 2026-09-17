"""F11 원숭이손 소원 4종 — 제안·수락·수락 즉시 장면·반대 사건·세계 효과·관찰 문장 (스펙 §3 테스트)."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.adapter.outbound.orms.game_state_orm import NightOrm, RuleOrm
from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    LoopRepository,
    NightRepository,
    NoteRepository,
    RuleRepository,
)
from apps.engine.app.dtos import event_log_dto as ev
from apps.engine.app.use_cases.inspector_interactor import InspectorInteractor
from apps.engine.app.use_cases.loop_interactor import GameStateError
from apps.engine.app.use_cases.intervention_interactor import InterventionInteractor, advisor_context
from apps.engine.app.use_cases.public_observations import public_observations
from apps.engine.app.dtos.llm_output_dto import ToolCallSpec
from tests.engine.test_usecase_day import _agent_reply, make_day

NAMES = ["채연", "민석", "은상", "준"]
REPORT_RULE = "보고를 물으면 자신이 한 일을 자세히 설명한다"


def wish_of(scenario, key):
    return next(w for w in scenario.bundle().paw_wishes if w.key == key)


def force_offer(db_session, loop_id, key):
    """2비트 제안 자리에 특정 소원을 올린다 — 제안 경로(겨냥)는 아래 별도 테스트가 본다."""
    loop = LoopRepository(db_session).get(loop_id)
    loop.pending_paw = {"offer_id": "forced", "offer_index": 1, "wish_key": key,
                        "label": key, "shown_reason": "-", "show_reason": True}
    db_session.commit()
    return "forced"


def advance(day, loop_id, times):
    return [day.advance_beat(loop_id) for _ in range(times)]


def close_loop(db_session, loop_id, score):
    loop = LoopRepository(db_session).get(loop_id)
    loop.state, loop.score = "closed", score
    db_session.commit()


def executions(db_session, attempt_id, loop_n=None):
    return [e for e in EventLogRepository(db_session).query(attempt_id, loop_n=loop_n) if e.type == "rule_execution"]


def side_effects(db_session, attempt_id, loop_n=None):
    return [e.side_effect for e in executions(db_session, attempt_id, loop_n) if e.side_effect]


def state_of(db_session, loop_id, code):
    return LoopRepository(db_session).npc_state(loop_id, code)


def test_chaeyeon_honest_is_first_offer_and_runs_the_whole_chain(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    loop_id, budget = info["loop_id"], info["budget_left"]
    wish = wish_of(scenario, "chaeyeon-honest")
    second = day.advance_beat(loop_id)
    offer = second["paw_offer"]
    assert offer["rule_label"] == wish.label
    assert offer["shown_reason"] in (wish.default_reason, None)  # A/B 표시

    before = {o.observation_id for o in public_observations(EventLogRepository(db_session), attempt.id)}
    res = day.respond_paw(loop_id, offer["offer_id"], True)
    assert res["applied"] and res["rule_label"] == wish.label
    assert res["narration"] == '채연이 담요를 끌어올린 채 준에게 작게 말한다. "밥에서 소독약 냄새가 나."'
    assert [i["image_id"] for i in res["illustrations"]] == ["Q03"]
    assert res["observations"] and not {o["observation_id"] for o in res["observations"]} & before
    scene_ids = [o.observation_id for o in public_observations(EventLogRepository(db_session), attempt.id)
                 if o.observation_id.endswith(":scene-2")]
    assert len(scene_ids) == 1
    assert any("소독약 냄새" in n.text for n in NoteRepository(db_session).list(attempt.id))

    rules = RuleRepository(db_session).list(attempt.id)
    assert [(r.source, r.target, r.action, r.effect, r.when_beat) for r in rules] == [
        ("monkey_paw", "채연", "속마음을 말한다", "enforce", 2),
        ("paw_effect", "채연", "배급을 남긴다", "suppress", 3),
        ("paw_effect", "채연", "배급을 다 먹는다", "enforce", 3),
        ("paw_effect", "은상", "담요를 두른다", "enforce", 5)]
    assert [r.hidden_side_effect for r in rules] == [None, None, None, wish.observation]

    third, fourth, fifth, sixth = advance(day, loop_id, 4)
    assert "쟁반이 빈다" in third["narration"] and "채연이 쟁반을 밀어낸다" not in third["narration"]
    assert third["ambient"]["lines"][0]["text"] == "오늘은 다 먹었네."
    assert wish.observation not in third["narration"] + fourth["narration"]
    assert "담요를 두른 사람이 하나 늘었다" in fifth["narration"] and wish.observation in fifth["narration"]
    assert side_effects(db_session, attempt.id) == [wish.observation]
    assert any(n.text == wish.observation for n in NoteRepository(db_session).list(attempt.id))
    assert state_of(db_session, loop_id, "eunsang").flagged_abnormal
    assert all(r["budget_left"] == budget for r in (second, third, fourth, fifth, sixth))
    assert LoopRepository(db_session).get(loop_id).budget_left == budget

    close_loop(db_session, loop_id, 30)
    nxt = day.start_loop(attempt.id)
    assert len(nxt["active_rules"]) == 1  # 숨은 규칙은 플레이어에게 보이지 않는다
    beats = advance(day, nxt["loop_id"], 4)
    assert "밥에서 소독약 냄새가 나" in beats[0]["narration"] and beats[0]["paw_offer"] is None
    assert wish.observation in beats[3]["narration"]
    assert side_effects(db_session, attempt.id, loop_n=2) == [wish.observation]


def test_chaeyeon_honest_fact_is_recorded_and_answerable_by_the_advisor(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    loop_id = info["loop_id"]
    offer = day.advance_beat(loop_id)["paw_offer"]
    day.respond_paw(loop_id, offer["offer_id"], True)
    events = EventLogRepository(db_session)
    observations = public_observations(events, attempt.id)
    reveal = next(o for o in observations if o.source_kind == "rule_result" and "소독약 냄새" in o.text)
    question = "채연이 소독약 냄새가 난다고 말했어?"
    assert reveal in advisor_context(question, observations, NAMES)

    inter, night = _advisor(db_session, loop_id, events, reveal, "supported", "unknown")
    assert inter.ask(night.id, question)["answer"].startswith("맞다.")
    assert inter.ask(night.id, "배급이 오염됐어?")["answer"].startswith("그건 알 수 없다.")


def _advisor(db_session, loop_id, events, reveal, *relations):
    """신의 질문 — 모델 경계만 대본으로 고정하고 근거 선택·판정 접두는 실제 코드가 한다."""
    loop = LoopRepository(db_session).get(loop_id)
    loop.state = "intervention"
    night = NightRepository(db_session).create(NightOrm(loop_id=loop.id))
    quote = "밥에서 소독약 냄새가 나."
    replies = [{"question_kind": "proposition", "answer": "채연이 준에게 밥에서 소독약 냄새가 난다고 말했다.",
                "evidence": [{"id": reveal.observation_id, "quote": quote, "relation": relation}]}
               for relation in relations]
    inter = InterventionInteractor(
        attempts=AttemptRepository(db_session), loops=LoopRepository(db_session), notes=NoteRepository(db_session),
        rules=RuleRepository(db_session), nights=NightRepository(db_session), event_log=events,
        core_llm=FakeLLM(replies), action_vocab=["말 걸기"], target_names=NAMES, harness_on=True, rule_cls=RuleOrm)
    return inter, night


def test_checkup_record_shows_the_record_then_a_night_cough(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    loop_id = info["loop_id"]
    wish = wish_of(scenario, "checkup-record")
    day.advance_beat(loop_id)
    res = day.respond_paw(loop_id, force_offer(db_session, loop_id, wish.key), True)
    assert res["applied"] and res["narration"] is None and res["illustrations"] == [] and res["observations"] == []
    third, fourth, fifth, sixth = advance(day, loop_id, 4)
    assert '"여기는 이상 없음."' in fourth["narration"] and "이마를 짚고 지나간다" in fourth["narration"]
    assert {"clue-03", "clue-12"} <= {i["image_id"] for i in fourth["illustrations"]}
    assert "기침 소리" in sixth["narration"] and wish.observation in sixth["narration"]
    assert sixth["ambient"]["lines"][0]["text"] == "준아, 방금 기침 소리 들었어?"
    assert state_of(db_session, loop_id, "chaeyeon").flagged_abnormal
    assert side_effects(db_session, attempt.id) == [wish.observation]
    observations = public_observations(EventLogRepository(db_session), attempt.id)
    record = next(o for o in observations if "이상 없음" in o.text and o.source_kind == "rule_result")
    assert record in advisor_context("담당자가 채연을 이상 없음이라고 말했어?", observations, NAMES)


def test_broadcast_room_reveals_at_once_and_skips_the_record(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    loop_id = info["loop_id"]
    wish = wish_of(scenario, "broadcast-room")
    day.advance_beat(loop_id)
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="user_choice",
                                           target="민석", action=REPORT_RULE, effect="enforce", created_loop=1))
    res = day.respond_paw(loop_id, force_offer(db_session, loop_id, wish.key), True)
    assert '"은상이 이상한 소리를 퍼뜨려요."' in res["narration"]
    assert [i["image_id"] for i in res["illustrations"]] == ["Q04"]
    reply = day.utter(loop_id, "minseok", "무슨 보고를 했어?")["reply"]
    assert reply == "은상이 이상한 소리를 퍼뜨린다고 알렸어. 오늘은 수첩에 못 적었어."
    third = day.advance_beat(loop_id)
    assert "민석은 배급 자리를 보지만 수첩에는 적지 않는다" in third["narration"]
    assert "수첩은 덮여 있다" in third["narration"] and wish.observation in third["narration"]
    assert third["ambient"]["lines"][0]["text"] == "오늘은 안 적어?"
    assert side_effects(db_session, attempt.id) == [wish.observation]
    observations = public_observations(EventLogRepository(db_session), attempt.id)
    reveal = next(o for o in observations if "퍼뜨려요" in o.text and o.source_kind == "rule_result")
    assert reveal in advisor_context("민석이 방송실에서 은상 얘기를 했어?", observations, NAMES)


def test_band_meaning_adds_a_number_rumor_that_raises_the_rumor_index(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    loop_id = info["loop_id"]
    wish = wish_of(scenario, "band-meaning")
    day.advance_beat(loop_id)
    res = day.respond_paw(loop_id, force_offer(db_session, loop_id, wish.key), True)
    assert "자리 번호야" in res["narration"]
    rumor = LoopRepository(db_session).get(loop_id).rumor_index
    fifth = advance(day, loop_id, 3)[-1]
    assert '"번호 순서대로 데려간대."' in fifth["narration"] and wish.observation in fifth["narration"]
    assert "은상이 사람들 사이를 오가며 귓속말을 한다" in fifth["narration"]  # 평소 소문은 억제하지 않는다
    assert fifth["ambient"]["lines"][0]["text"] == "번호 순서대로 데려간대."
    assert LoopRepository(db_session).get(loop_id).rumor_index == rumor + 1
    assert side_effects(db_session, attempt.id) == [wish.observation]


def test_declined_day_has_no_wish_scene_counter_event_or_observation(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    loop_id, budget = info["loop_id"], info["budget_left"]
    offer = day.advance_beat(loop_id)["paw_offer"]
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="user_choice",
                                           target="민석", action=REPORT_RULE, effect="enforce", created_loop=1))
    res = day.respond_paw(loop_id, offer["offer_id"], False)
    assert res == {"applied": False, "rule_label": None, "narration": None, "illustrations": [], "observations": []}
    assert day.utter(loop_id, "minseok", "무슨 보고를 했어?")["reply"] != "은상이 이상한 소리를 퍼뜨린다고 알렸어. 오늘은 수첩에 못 적었어."
    text = " ".join(r["narration"] for r in advance(day, loop_id, 4))
    for action in scenario.bundle().scene_actions:
        if action.paw_only:
            assert action.narration not in text
    assert side_effects(db_session, attempt.id) == []
    offers = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "monkey_paw_offer"]
    assert [(e.accepted, e.wish_key) for e in offers] == [(False, "chaeyeon-honest")]
    assert LoopRepository(db_session).get(loop_id).budget_left == budget - 1  # 대화 1회만


def test_spec_question_with_rice_word_is_supported(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    offer = day.advance_beat(info["loop_id"])["paw_offer"]
    day.respond_paw(info["loop_id"], offer["offer_id"], True)
    events = EventLogRepository(db_session)
    reveal = next(o for o in public_observations(events, attempt.id)
                  if o.source_kind == "rule_result" and "소독약 냄새" in o.text)
    inter, night = _advisor(db_session, info["loop_id"], events, reveal, "supported")
    assert inter.ask(night.id, "채연이 밥에서 소독약 냄새가 난다고 했어?")["answer"].startswith("맞다.")


def _score(db_session, attempt_id, loop_n, **cells):
    scores = {"cause": 0.0, "motive": 0.0, "identity": 0.0, "side_effect": 0.0, **cells}
    EventLogRepository(db_session).record(attempt_id, ev.AnswerScoredEvent(
        loop_n=loop_n, per_truth_claim=[], cell_scores=scores, total=sum(scores.values()) / 4, passed=True))


def test_second_offer_targets_highest_previous_cell(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    offer = day.advance_beat(info["loop_id"])["paw_offer"]
    day.respond_paw(info["loop_id"], offer["offer_id"], False)
    close_loop(db_session, info["loop_id"], 60)
    _score(db_session, attempt.id, 1, cause=100.0, motive=66.7)
    info = day.start_loop(attempt.id)
    offer = day.advance_beat(info["loop_id"])["paw_offer"]
    assert offer["rule_label"] == wish_of(scenario, "checkup-record").label


def test_two_declines_end_offers_and_exhausted_table_offers_nothing(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    for loop_n in (1, 2):
        offer = day.advance_beat(info["loop_id"])["paw_offer"]
        assert offer is not None
        day.respond_paw(info["loop_id"], offer["offer_id"], False)
        close_loop(db_session, info["loop_id"], 60)
        _score(db_session, attempt.id, loop_n, motive=80.0)
        info = day.start_loop(attempt.id)
    assert day.advance_beat(info["loop_id"])["paw_offer"] is None

    day, scenario, attempt, info = make_day(db_session, [])
    offer = day.advance_beat(info["loop_id"])["paw_offer"]
    day.respond_paw(info["loop_id"], offer["offer_id"], False)
    close_loop(db_session, info["loop_id"], 60)
    _score(db_session, attempt.id, 1, motive=80.0)
    trimmed = scenario.bundle().model_copy(update={"paw_wishes": scenario.bundle().paw_wishes[:1]})
    day._scenario.bundle = lambda: trimmed
    info = day.start_loop(attempt.id)
    assert day.advance_beat(info["loop_id"])["paw_offer"] is None
    assert AttemptRepository(db_session).get(attempt.id).paw_offered_count == 1


def test_inspector_lists_hidden_paw_rules(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    offer = day.advance_beat(info["loop_id"])["paw_offer"]
    day.respond_paw(info["loop_id"], offer["offer_id"], True)
    view = InspectorInteractor(attempts=AttemptRepository(db_session), rules=RuleRepository(db_session),
                               event_log=EventLogRepository(db_session), inspector_token="t").inspector_view(attempt.id, "t")
    assert [r["source"] for r in view["paw_rules"]] == ["monkey_paw", "paw_effect", "paw_effect", "paw_effect"]
    assert view["paw_rules"][-1]["hidden_side_effect"] == wish_of(scenario, "chaeyeon-honest").observation


def test_hidden_paw_rules_never_reach_npc_dialogue_prompts(db_session):
    day, scenario, attempt, info = make_day(db_session, [_agent_reply("응."), {"answer": "몰라.", "said_it": None}])
    loop_id = info["loop_id"]
    offer = day.advance_beat(loop_id)["paw_offer"]
    day.respond_paw(loop_id, offer["offer_id"], True)
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="V1", source="user_choice",
                                           target="채연", action="담요를 두른다", effect="enforce", created_loop=1))
    hidden = [r for r in RuleRepository(db_session).list(attempt.id)
              if r.source == "paw_effect" and r.target == "채연" and r.when_beat == 3]
    assert len(hidden) == 2
    day.advance_beat(loop_id)  # 비트 3 — 채연의 숨은 규칙이 걸린 장면
    day.utter(loop_id, "chaeyeon", "오늘 밥 어때?")
    loop = LoopRepository(db_session).get(loop_id)
    bundle = scenario.bundle()
    day._run_ask_npc(loop, bundle, state_of(db_session, loop_id, "jun"),
                     next(c for c in bundle.characters if c.code == "jun"),
                     ToolCallSpec(name="ask_npc", target="채연", question="오늘 밥 어때?"))
    blocks = [messages[0].content.split("[오늘의 규칙]\n", 1)[1].split("\n이 규칙대로", 1)[0]
              for messages, _ in day._npc_llm.calls]
    assert len(blocks) == 2
    for block in blocks:
        assert "[V1]" in block  # 보이는 규칙은 그대로 실린다
        for r in hidden:
            assert f"[{r.rule_id}]" not in block and r.action not in block


def test_failed_note_write_rolls_back_paw_acceptance_and_retry_applies_once(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    loop_id = info["loop_id"]
    wish = wish_of(scenario, "band-meaning")
    day.advance_beat(loop_id)
    offer_id = force_offer(db_session, loop_id, wish.key)
    rumor = LoopRepository(db_session).get(loop_id).rumor_index
    upsert = day._notes.upsert
    failed = False
    def failing_upsert(*args, **kwargs):
        nonlocal failed
        if not failed:
            failed = True
            db_session.execute(text("SELECT 1 / 0"))
        return upsert(*args, **kwargs)
    day._notes.upsert = failing_upsert

    with pytest.raises(DBAPIError):
        day.respond_paw(loop_id, offer_id, True)
    db_session.expire_all()
    loop = LoopRepository(db_session).get(loop_id)
    assert loop.pending_paw["offer_id"] == offer_id and loop.rumor_index == rumor
    assert RuleRepository(db_session).list(attempt.id) == []
    assert not [e for e in EventLogRepository(db_session).query(attempt.id)
                if e.type in ("rule_applied", "monkey_paw_offer", "rule_execution")]

    res = day.respond_paw(loop_id, offer_id, True)
    assert res["applied"] and "자리 번호야" in res["narration"]
    loop = LoopRepository(db_session).get(loop_id)
    assert loop.pending_paw is None
    assert len(RuleRepository(db_session).list(attempt.id)) == 1 + len(wish.effects)
    events = EventLogRepository(db_session).query(attempt.id)
    assert len([e for e in events if e.type == "rule_applied"]) == 1
    assert len([e for e in events if e.type == "monkey_paw_offer"]) == 1
    observations = public_observations(EventLogRepository(db_session), attempt.id)
    assert len({o.observation_id for o in observations}) == len(observations)
    assert sum("자리 번호야" in o.text for o in observations) == 1
    sources = {n.source_key for n in NoteRepository(db_session).list(attempt.id)}
    assert res["observations"] and all(o["observation_id"] in sources for o in res["observations"])
    fifth = advance(day, loop_id, 3)[-1]
    assert wish.observation in fifth["narration"]
    assert LoopRepository(db_session).get(loop_id).rumor_index == rumor + 1
    assert side_effects(db_session, attempt.id) == [wish.observation]
    with pytest.raises(GameStateError):
        day.respond_paw(loop_id, offer_id, True)  # 이미 처리한 오퍼는 다시 적용되지 않는다
