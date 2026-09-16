"""Connected investigation regressions; test database only."""

from tests.pure.test_real_model_grounding import model_assessment, question_responses

from types import SimpleNamespace

from apps.engine.adapter.outbound.repositories.game_repository import LoopRepository, NightRepository
from apps.engine.adapter.outbound.orms.game_state_orm import NightOrm
from apps.engine.app.use_cases.night_interactor import NightInteractor, source_claims
from tests.engine.test_usecase_day import make_day, _agent_reply


def test_notes_have_public_scene_sources_and_never_arrive_before_the_scene(db_session):
    day, _, _, info = make_day(db_session, [])
    first = day.list_notes(info["loop_id"])["notes"]
    assert first and all(n.get("sources") for n in first)
    assert not any("트럭 소리" in n["text"] for n in first)
    day.advance_beat(info["loop_id"])
    assert not any("트럭 소리" in n["text"] for n in day.list_notes(info["loop_id"])["notes"])


def test_public_observation_read_is_free_and_statement_is_not_verified_truth(db_session):
    day, _, _, info = make_day(db_session, [_agent_reply("누가 아프대.")])
    reply = day.utter(info["loop_id"], "eunsang", "무슨 일이야?")
    before = LoopRepository(db_session).get(info["loop_id"]).budget_left
    rows = day.list_observations(info["loop_id"])["observations"]
    assert any(o["verification"] == "reported" and o["text"] == reply["reply"] for o in rows)
    assert LoopRepository(db_session).get(info["loop_id"]).budget_left == before


def test_previous_answer_uses_direct_writing_and_stays_inside_attempt(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    previous_loop = LoopRepository(db_session).get(info["loop_id"])
    night = NightOrm(loop_id=previous_loop.id, free_text="처음 글", claims=["확인 화면에서 고친 주장"],
                     tapped_note_ids=[1], submitted=True)
    NightRepository(db_session).create(night)
    previous_loop.state = "closed"
    db_session.commit()
    next_info = day.start_loop(attempt.id)
    uc = NightInteractor(attempts=None, loops=LoopRepository(db_session), notes=None, rules=None,
                         nights=NightRepository(db_session), event_log=None, scenario=scenario,
                         core_llm=None, harness_on=True, cookie_ab_on=False, night_cls=NightOrm)
    assert uc.previous_answer(next_info["loop_id"])["previous_answer"]["draft_text"] == "처음 글"
    assert uc.previous_answer(info["loop_id"])["previous_answer"] is None


def test_source_composition_deduplicates_selected_evidence():
    assert source_claims("첫 주장.\n소독약 냄새.", ["소독약 냄새."]) == ["첫 주장.", "소독약 냄새."]


def test_each_night_restores_only_its_own_attempts_latest_direct_writing(db_session):
    day, scenario, attempt, info = make_day(db_session, [])
    _, _, _, other_info = make_day(db_session, [])
    loops, nights = LoopRepository(db_session), NightRepository(db_session)
    uc = NightInteractor(attempts=None, loops=loops, notes=None, rules=None, nights=nights,
        event_log=None, scenario=scenario, core_llm=None, harness_on=True,
        cookie_ab_on=False, night_cls=NightOrm)
    raw = "  채연은 왜 배급을 남겼을까?\n"
    for loop_n in range(1, 5):
        loop = loops.get(info["loop_id"])
        raw += f"\n{loop_n}번째 밤의 새 추측.  "
        nights.create(NightOrm(loop_id=loop.id, free_text=raw, claims=["별도로 수정한 채점 문장"],
                               tapped_note_ids=[], submitted=True))
        loop.state = "closed"
        db_session.commit()
        info = day.start_loop(attempt.id)
        previous = uc.previous_answer(info["loop_id"])["previous_answer"]
        assert previous["loop_n"] == loop_n and previous["draft_text"] == raw
        assert uc.previous_answer(other_info["loop_id"])["previous_answer"] is None


def test_suppressed_actual_scene_action_removes_its_narration_and_image(db_session):
    from apps.engine.adapter.outbound.orms.game_state_orm import RuleOrm
    from apps.engine.adapter.outbound.repositories.game_repository import RuleRepository
    from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
    day, _, attempt, info = make_day(db_session, [])
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="user_choice",
        target="민석", action="기록한다", effect="suppress", when_beat=3, created_loop=0))
    day.advance_beat(info["loop_id"])
    result = day.advance_beat(info["loop_id"])
    assert "수첩에 뭔가 적는다" not in result["narration"]
    assert "clue-08" not in [i["image_id"] for i in result["illustrations"]]
    executions = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "rule_execution"]
    assert len(executions) == 1 and executions[0].result == "obeyed"
    assert executions[0].actual_action is None


def test_information_rule_uses_only_public_actor_knowledge(db_session):
    from apps.engine.adapter.outbound.orms.game_state_orm import RuleOrm
    from apps.engine.adapter.outbound.repositories.game_repository import RuleRepository
    day, _, attempt, info = make_day(db_session, [])
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="user_custom",
        target="은상", action="소문의 알려진 출처를 밝힌다", effect="enforce", when_beat=2, created_loop=0))
    result = day.advance_beat(info["loop_id"])
    assert any(o["rule_id"] == "R1" and "준에게 들었어" in o["text"]
               and o["verification"] == "reported" for o in result["observations"])
    assert "감염원" not in result["narration"]


def test_rule_with_no_matching_scene_has_no_success_event(db_session):
    from apps.engine.adapter.outbound.orms.game_state_orm import RuleOrm
    from apps.engine.adapter.outbound.repositories.game_repository import RuleRepository
    from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
    day, _, attempt, info = make_day(db_session, [])
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="user_choice",
        target="준", action="기록한다", effect="enforce", when_beat=3, created_loop=0))
    for _ in range(5):
        day.advance_beat(info["loop_id"])
    assert not any(e.type == "rule_execution" for e in EventLogRepository(db_session).query(attempt.id))


def test_custom_answering_is_never_approximated_to_asking():
    from apps.engine.app.use_cases.intervention_interactor import nearest_action
    assert nearest_action("질문에 답한다", ["질문한다", "말을 건다"]) is None


def test_ordinary_korean_endings_are_not_invented_people():
    from apps.engine.app.use_cases.harness import unknown_person_check
    check = unknown_person_check(["채연", "민석"], fields=["reply"])
    assert check(SimpleNamespace(reply="그냥 소문이야. 아직 모르는 일이야.")) is None


def test_unseen_model_chain_is_not_public_question_evidence(db_session):
    from tests.engine.test_usecase_intervention import make_intervention
    inter, attempt, night = make_intervention(db_session, [{"answer": "맞다", "detail": "숨은 결론"}])
    answer = inter.ask(night.id, "숨은 정체가 뭐야?")
    assert answer["answer"] == "그건 알 수 없다. 그건 알 수 없다"
    assert answer["evidence_ids"] == []


def test_custom_rule_requires_preview_and_confirm_applies_stored_exact_meaning(db_session):
    from tests.engine.test_usecase_intervention import make_intervention
    inter, attempt, night = make_intervention(db_session, [], action_vocab=["알고 있는 관찰을 설명한다"])
    text = "채연은 알고 있는 관찰을 설명한다"
    assert inter.choose_rule(night.id, "custom", text)["ok"] is False
    preview = inter.preview_rule(night.id, text)
    assert preview["executable"] is True
    changed = inter.choose_rule(night.id, "custom", text + " 언제나", preview["preview_id"])
    assert changed["ok"] is False
    result = inter.choose_rule(night.id, "custom", text, preview["preview_id"])
    assert result["ok"] is True


def test_successful_model_calls_are_auditable_with_output_and_check_trace():
    from apps.engine.app.use_cases.harness import run_with_harness
    from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
    from apps.engine.app.dtos.llm_output_dto import AdvisorAnswerOutput
    _, report = run_with_harness(FakeLLM([{"answer": "그건 알 수 없다"}]), [], AdvisorAnswerOutput, role="advisor_answer")
    assert report.call_records[0]["output"]["answer"] == "그건 알 수 없다"
    assert report.call_records[0]["accepted"] is True


def test_tester1_non_names_do_not_trigger_unknown_person():
    from apps.engine.app.use_cases.harness import unknown_person_check
    check = unknown_person_check(["채연", "민석"], fields=["reply"])
    assert all(check(SimpleNamespace(reply=text)) is None for text in
               ["그건 차량이야.", "그건 번호야.", "그건 소문이야.", "그런 뜻이야."])


def test_repeated_note_deselection_and_reselection_preserve_direct_writing(db_session):
    from apps.engine.adapter.outbound.repositories.game_repository import NoteRepository
    from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
    from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
    day, scenario, attempt, info = make_day(db_session, [])
    uc = NightInteractor(attempts=None, loops=LoopRepository(db_session), notes=NoteRepository(db_session),
                         rules=None, nights=NightRepository(db_session), event_log=EventLogRepository(db_session),
                         scenario=scenario, core_llm=FakeLLM(), harness_on=True, cookie_ab_on=False, night_cls=NightOrm)
    note_id = day.list_notes(info["loop_id"])["notes"][0]["id"]
    loop = LoopRepository(db_session).get(info["loop_id"])
    first = NightRepository(db_session).create(NightOrm(loop_id=loop.id, free_text="원문",
             claims=["최종 편집으로 근거 문장은 지웠다."], tapped_note_ids=[note_id], submitted=True))
    loop.state = "closed"
    db_session.commit()
    next_info = day.start_loop(attempt.id)
    next_loop = LoopRepository(db_session).get(next_info["loop_id"])
    next_loop.state = "night_pending"
    db_session.commit()
    previous = uc.previous_answer(next_loop.id)["previous_answer"]
    draft = uc.draft(next_loop.id, [note_id], previous["draft_text"], [note_id])
    assert previous["draft_text"] == first.free_text == "원문"
    assert draft["claims"] == source_claims("원문", [NoteRepository(db_session).by_ids(attempt.id, [note_id])[0].text])
    second = NightRepository(db_session).get(draft["night_id"])
    second.submitted = True
    second.tapped_note_ids = []  # user detached the old source while retaining edited prose
    next_loop.state = "closed"
    db_session.commit()
    third_info = day.start_loop(attempt.id)
    restored = uc.previous_answer(third_info["loop_id"])["previous_answer"]
    assert restored["tapped_note_ids"] == []
    assert restored["draft_text"] == previous["draft_text"]


def test_definition_question_cannot_be_answered_with_unrelated_action(db_session):
    from tests.engine.test_usecase_intervention import make_intervention, publish_record
    from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
    inter, attempt, night = make_intervention(db_session, [])
    observation = publish_record(inter, attempt, night, text='준이 "귀표"라는 단어를 썼다.')
    inter._llm = FakeLLM(question_responses(model_assessment('supported', detail=observation.text, evidence_ids=[observation.observation_id])))
    answer = inter.ask(night.id, "귀표는 무엇인가?")
    assert answer["status"] == "unknown"


def test_paw_benefit_and_cost_occur_in_linked_scene_only(db_session):
    from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
    day, _, attempt, info = make_day(db_session, [])
    first_loop = LoopRepository(db_session).get(info["loop_id"])
    first_loop.state, first_loop.score = "closed", 50
    db_session.commit()
    info = day.start_loop(attempt.id)
    scene = day.advance_beat(info["loop_id"])
    offer = scene["paw_offer"]
    assert offer is not None
    day.respond_paw(info["loop_id"], offer["offer_id"], True)
    before = LoopRepository(db_session).get(info["loop_id"]).budget_left
    result = day.advance_beat(info["loop_id"])
    executions = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "rule_execution"]
    assert executions and executions[-1].side_effect
    assert executions[-1].actual_action == "알고 있는 관찰을 설명한다"
    assert LoopRepository(db_session).get(info["loop_id"]).budget_left == before - 1
    assert result["budget_left"] == before - 1


def test_conflicting_rule_result_is_not_counted_as_compliance_success(db_session):
    from apps.engine.adapter.outbound.orms.game_state_orm import RuleOrm
    from apps.engine.adapter.outbound.repositories.game_repository import RuleRepository
    from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
    day, _, attempt, info = make_day(db_session, [])
    rules = RuleRepository(db_session)
    for rule_id, effect in [("R1", "enforce"), ("R2", "suppress")]:
        rules.add(RuleOrm(attempt_id=attempt.id, rule_id=rule_id, source="user_choice", target="민석",
                         action="기록한다", effect=effect, when_beat=3, created_loop=0))
    day.advance_beat(info["loop_id"])
    day.advance_beat(info["loop_id"])
    executions = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "rule_execution"]
    assert [(e.rule_id, e.result) for e in executions] == [("R1", "conflict"), ("R2", "obeyed")]


def test_first_morning_image_does_not_reappear_in_next_loop(db_session):
    day, _, attempt, info = make_day(db_session, [])
    assert "clue-07" in [i["image_id"] for i in info["illustrations"]]
    loop = LoopRepository(db_session).get(info["loop_id"])
    loop.state = "closed"
    db_session.commit()
    next_info = day.start_loop(attempt.id)
    assert "clue-07" not in [i["image_id"] for i in next_info["illustrations"]]


def test_image_of_recording_is_hidden_when_its_other_depicted_person_is_erased(db_session):
    day, scenario, _, info = make_day(db_session, [])
    character = next(c for c in scenario.bundle().characters if c.code == "chaeyeon")
    character.lost = True
    loop = LoopRepository(db_session).get(info["loop_id"])
    loop.damage_level = 3
    db_session.commit()
    day.advance_beat(info["loop_id"])
    third = day.advance_beat(info["loop_id"])
    assert "clue-08" not in [i["image_id"] for i in third["illustrations"]]


def test_retrospective_legacy_logs_have_unknown_model_count_and_no_fake_denominator():
    from tests.engine.test_five_loop_rules import submit_night, Memory
    from apps.engine.app.use_cases.inspector_interactor import InspectorInteractor
    _, attempt, _, events = submit_night(5, "none")
    # Old events had no per-attempt trace/version; absence is unmeasured, not zero model calls.
    for event in events.recorded:
        if event.type == "harness_event":
            event.version = None
    inspector = InspectorInteractor(attempts=Memory(attempt), rules=Memory(), event_log=events, inspector_token="x")
    result = inspector.harness_view(attempt.id)
    assert result["harness_summary"]["model_calls"] is None
    assert result["metrics"]["rule_compliance"]["denominator"] == 0
    assert result["metrics"]["rule_compliance"]["value"] is None
    assert result["metrics"]["checker_accuracy"]["reviewed"] == 0


def test_final_world_outcomes_do_not_claim_unseen_closure():
    from apps.scenarios.scenario_a.adapter import build
    bundle = build().bundle()
    assert bundle.ending_outcomes["truck"] != bundle.ending_outcomes["closure"]
    assert "폐쇄된 것으로 확인되지는 않았다" in " ".join(bundle.ending_outcomes["truck"])
    assert "폐쇄된 것으로 확인되지는 않았다" in " ".join(bundle.ending_outcomes["quiet"])


def test_suppressed_second_loop_actions_cannot_reappear_as_observed_fragments(db_session):
    from apps.engine.adapter.outbound.orms.game_state_orm import RuleOrm
    from apps.engine.adapter.outbound.repositories.game_repository import RuleRepository
    day, _, attempt, info = make_day(db_session, [])
    loop = LoopRepository(db_session).get(info["loop_id"])
    loop.state = "closed"
    db_session.commit()
    for rule_id, target, action in [("R1", "채연", "배급을 남긴다"), ("R2", "민석", "방송실에 간다")]:
        RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id=rule_id, source="user_choice",
            target=target, action=action, effect="suppress", when_beat=None, created_loop=1))
    info = day.start_loop(attempt.id)
    for _ in range(4):
        day.advance_beat(info["loop_id"])
    forbidden = {"채연이 아침에 배급을 남긴다.", "민석이 방송실 근처를 서성인다."}
    observations = day.list_observations(info["loop_id"])["observations"]
    assert not any(o["loop_n"] == 2 and o["text"] in forbidden for o in observations)
    notes = day.list_notes(info["loop_id"])["notes"]
    assert not any(n["loop_n"] == 2 and n["text"] in forbidden for n in notes)


def test_same_polarity_rules_share_one_real_action_without_false_conflict(db_session):
    from apps.engine.adapter.outbound.orms.game_state_orm import RuleOrm
    from apps.engine.adapter.outbound.repositories.game_repository import RuleRepository
    from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
    day, _, attempt, info = make_day(db_session, [])
    for rule_id, source in [("R1", "user_custom"), ("R2", "monkey_paw")]:
        RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id=rule_id, source=source,
             target="민석", action="알고 있는 관찰을 설명한다", effect="enforce", when_beat=3, created_loop=0))
    day.advance_beat(info["loop_id"])
    before = LoopRepository(db_session).get(info["loop_id"]).budget_left
    result = day.advance_beat(info["loop_id"])
    executions = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "rule_execution"]
    assert [e.result for e in executions] == ["obeyed", "obeyed"]
    assert result["narration"].count("민석: 배급 자리 보고 적었어. 잊으면 안 되잖아.") == 1
    assert result["budget_left"] == before - 1


def test_legacy_notes_are_unmeasured_instead_of_failed_source_links():
    from tests.engine.test_five_loop_rules import submit_night, Memory
    from apps.engine.app.use_cases.inspector_interactor import InspectorInteractor
    _, attempt, _, events = submit_night(5, "none")
    inspector = InspectorInteractor(attempts=Memory(attempt), rules=Memory(), event_log=events,
        inspector_token="x", notes=Memory(rows=[SimpleNamespace(source_key="legacy-fragment", loop_n=1)]))
    metric = inspector.harness_view(attempt.id)["metrics"]["note_source_linkage"]
    assert metric["value"] is None
    assert metric["denominator"] == 0
