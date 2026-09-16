"""P3 신의개입 유스케이스 — 열린 질문 답변 유형 (FakeLLM 큐로 제어)."""

from tests.pure.test_real_model_grounding import model_assessment, question_responses

from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.adapter.outbound.orms.game_state_orm import LoopOrm, NightOrm, RuleOrm
from apps.engine.adapter.outbound.repositories.event_log_repository import (
    EventLogRepository,
)
from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    LoopRepository,
    NightRepository,
    NoteRepository,
    RuleRepository,
)
from apps.engine.app.use_cases.intervention_interactor import (
    InterventionInteractor,
    nearest_action,
    render_cause_chain,
)

_FACT = "채연이 자기 몫을 반쯤 남기고 옆으로 민다."


def make_intervention(db_session, core_queue, cause_chain=None, rules=None, action_vocab=None,
                      advisor_leads=None):
    attempt = AttemptRepository(db_session).create(None)
    loop = LoopOrm(
        attempt_id=attempt.id, loop_n=1, budget_left=0,
        state="intervention",
        cause_chain=[{"fact": _FACT}] if cause_chain is None else cause_chain,
    )
    LoopRepository(db_session).create(loop, [])
    night = NightRepository(db_session).create(NightOrm(loop_id=loop.id))
    rule_repo = RuleRepository(db_session)
    for i, (target, action, effect) in enumerate(rules or []):
        rule_repo.add(RuleOrm(
            attempt_id=attempt.id, rule_id=f"R{i + 1}", source="user_choice",
            target=target, when_beat=None, effect=effect, action=action,
            created_loop=1,
        ))
    interactor = InterventionInteractor(
        attempts=AttemptRepository(db_session),
        loops=LoopRepository(db_session),
        notes=NoteRepository(db_session),
        rules=RuleRepository(db_session),
        nights=NightRepository(db_session),
        event_log=EventLogRepository(db_session),
        core_llm=FakeLLM(core_queue),
        action_vocab=action_vocab or ["말 걸기"], target_names=["채연"],
        harness_on=True, rule_cls=RuleOrm,
        advisor_leads=advisor_leads or [],
    )
    return interactor, attempt, night


def make_lead(key="k1", loop_n=1, cues=("배급",), anchor_cues=("배급",), target="채연",
              ask="배급이 어디서 오는지", rule_action=None):
    from apps.engine.app.dtos.scenario_dto import AdvisorLeadDTO
    return AdvisorLeadDTO(key=key, loop_n=loop_n, cues=list(cues), anchor_cues=list(anchor_cues),
                          target=target, ask=ask, rule_action=rule_action)


# The old chain-confirmation/forced-three-options/nearest-action assertions were
# superseded by the approved connected investigation contract. Verify public grounding
# and explicit semantic confirmation instead of preserving unsafe behavior.


def publish_record(inter, attempt, night, text=_FACT, actor="채연", kind="scene"):
    from apps.engine.app.use_cases.public_observations import disclose
    from apps.engine.app.dtos.scenario_dto import BeatDTO
    loop = inter._loops.get(night.loop_id)
    return disclose(inter._events, loop, BeatDTO(n=1, title="아침", narration=text),
                    key="proof", text=text, actor=actor, source_kind=kind)


def test_open_question_cites_original_observation_without_promoting_a_new_fact(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    observation = publish_record(inter, attempt, night)
    inter._llm = FakeLLM(question_responses(model_assessment('supported', detail=_FACT, evidence_ids=[observation.observation_id])))
    answer = inter.ask(night.id, "채연은 무슨 행동을 했어?")
    assert answer["detail"] == _FACT
    assert answer["evidence_ids"] == [observation.observation_id]
    notes = NoteRepository(db_session).list(attempt.id)
    assert [n.source_key for n in notes] == [f"confirmed-{observation.observation_id}"]  # Task 5: supported → confirmed note.


def test_question_rejects_fabricated_evidence_id_and_falls_back(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    publish_record(inter, attempt, night)
    inter._llm = FakeLLM(question_responses(model_assessment('supported', detail=_FACT, evidence_ids=['invented']), evidence_attempts=3))
    answer = inter.ask(night.id, "채연이 뭐 했어?")
    assert answer["status"] == "unknown"
    assert [o["text"] for o in answer["evidence"]] == [_FACT]  # Preserve public known facts after invalid IDs.
    assert answer["next_observation"] is None  # No advisor lead is anchored here; advice is the only hint now.


def test_question_uses_public_observation_when_chain_is_missing(db_session):
    inter, attempt, night = make_intervention(db_session, [], cause_chain=[])
    observation = publish_record(inter, attempt, night)
    inter._llm = FakeLLM(question_responses(model_assessment('supported', detail=_FACT, evidence_ids=[observation.observation_id])))
    assert inter.ask(night.id, "채연은 무슨 행동을 했어?")["status"] == "supported"


def test_question_without_public_record_is_unknown_and_consumes_one_question(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    answer = inter.ask(night.id, "누가 밥을 남겼어?")
    assert answer["status"] == "unknown"
    assert answer["remaining"] == 2
    assert inter._llm.calls == []


def test_options_are_empty_without_executable_observed_context(db_session):
    inter, _, night = make_intervention(db_session, [])
    assert inter.options(night.id) == {"options": []}


def test_contextual_option_retains_action_reason_and_original_evidence(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    observation = publish_record(inter, attempt, night)
    inter._templates = [{"target": "채연", "action": "알고 있는 관찰을 설명한다", "effect": "enforce",
                         "when_beat": 1, "label": "채연의 관찰을 듣는다"}]
    options = inter.options(night.id)["options"]
    assert len(options) == 1
    assert options[0]["evidence_ids"] == [observation.observation_id]
    assert _FACT in options[0]["reason"]


def publish_scene_action(inter, night, action, rule_id=None):
    from apps.engine.app.use_cases.public_observations import disclose
    from apps.engine.app.dtos.scenario_dto import BeatDTO
    loop = inter._loops.get(night.loop_id)
    observation = disclose(inter._events, loop, BeatDTO(n=1, title="아침", narration=_FACT),
                    key=f"action-1-채연-{action}", text=f"채연이 {action}.", actor="채연",
                    source_kind="rule_result" if rule_id else "scene", rule_id=rule_id)
    return observation.observation_id


def _ration_templates():
    return [{"target": "채연", "action": action, "effect": "enforce", "when_beat": 1,
             "label": f"채연: {action}"} for action in ("알고 있는 관찰을 설명한다", "배급을 남긴다")]


def test_options_skip_action_the_actor_already_performs_without_a_rule(db_session):
    inter, _, night = make_intervention(db_session, [])
    publish_scene_action(inter, night, "배급을 남긴다")
    inter._templates = _ration_templates()
    labels = [o["label"] for o in inter.options(night.id)["options"]]
    assert "채연: 배급을 남긴다" not in labels
    assert "채연: 알고 있는 관찰을 설명한다" in labels


def test_options_keep_action_observed_only_under_a_rule(db_session):
    inter, _, night = make_intervention(db_session, [])
    publish_scene_action(inter, night, "배급을 남긴다", rule_id="R1")
    inter._templates = _ration_templates()
    labels = [o["label"] for o in inter.options(night.id)["options"]]
    assert "채연: 배급을 남긴다" in labels


def test_exact_action_only_preserves_polarity_and_rejects_unknown_recipient(db_session):
    inter, _, night = make_intervention(db_session, [], action_vocab=["기록한다"])
    assert nearest_action("기록한다", ["기록한다"]) == "기록한다"
    assert nearest_action("기록에 답한다", ["기록한다"]) is None
    assert not inter.preview_rule(night.id, "채연은 관리자에게 기록한다")["executable"]
    preview = inter.preview_rule(night.id, "채연은 기록한다 금지")
    assert preview["rule"]["effect"] == "suppress"


def test_tester1_answer_requests_offer_explicit_alternatives_without_reversal(db_session):
    inter, _, night = make_intervention(db_session, [], action_vocab=["질문한다", "알고 있는 관찰을 설명한다"])
    preview = inter.preview_rule(night.id, "채연은 묻는말에 자세하게 대답한다.")
    assert not preview["executable"]
    assert preview["rule"] is None
    assert preview["alternatives"] == ["채연은 알고 있는 관찰을 설명한다"]


def test_full_question_response_is_retained_for_independent_review(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    answer = inter.ask(night.id, "기록 밖의 일은 뭐야?")
    event = [e for e in inter._events.query(attempt.id) if e.type == "intervention_question"][0]
    assert event.detail == answer["detail"]
    assert event.next_observation == answer["next_observation"]
    assert event.status == "unknown"


def test_explicit_observed_negative_can_contradict_a_question(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    observation = publish_record(inter, attempt, night, text="채연은 쟁반을 밀어내지 않았다.")
    inter._llm = FakeLLM(question_responses(model_assessment('contradicted', detail=observation.text, evidence_ids=[observation.observation_id])))
    answer = inter.ask(night.id, "채연이 쟁반을 밀어냈어?")
    assert answer["status"] == "contradicted"
    assert answer["evidence_ids"] == [observation.observation_id]


def test_synonymous_question_can_reach_the_original_public_record(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    observation = publish_record(inter, attempt, night)
    inter._llm = FakeLLM(question_responses(model_assessment('supported', detail=_FACT, evidence_ids=[observation.observation_id])))
    answer = inter.ask(night.id, "누가 밥을 남겼어?")
    assert answer["status"] == "supported"
    assert _FACT in inter._llm.calls[0][0][0].content


def test_unknown_owner_keeps_available_three_tray_evidence_without_inventing_people(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    observation = publish_record(inter, attempt, night, text="음식이 남은 쟁반 세 개가 보인다.", actor=None)
    inter._llm = FakeLLM(question_responses(model_assessment('unknown', detail=observation.text, evidence_ids=[observation.observation_id])))
    answer = inter.ask(night.id, "채연 말고 밥을 남긴 사람이 있어?")
    assert answer["status"] == "unknown"
    assert answer["evidence_ids"] == [observation.observation_id]
    assert "쟁반 세 개" in answer["detail"]
    assert "세 사람" not in answer["detail"]


def test_recipient_question_retains_broadcast_instruction_as_partial_evidence(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    observation = publish_record(inter, attempt, night, text="이상한 점은 방송실로 알립니다.", actor=None, kind="statement")
    inter._llm = FakeLLM(question_responses(model_assessment('unknown', detail=observation.text, evidence_ids=[observation.observation_id])))
    answer = inter.ask(night.id, "민석은 누구에게 보고하는거야?")
    assert answer["status"] == "unknown"
    assert answer["evidence_ids"] == [observation.observation_id]


def test_advice_is_anchored_to_player_record_and_not_a_hidden_fact(db_session):
    lead = make_lead(anchor_cues=("배급",), target="준", ask="배급이 어디서 오는지")
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    publish_scene_action(inter, night, "배급을 남긴다")
    res = inter.ask(night.id, "배급이 왜 이래?")
    assert res["unlocked_note"] is None
    assert "한 가지 더" not in res["answer"]
    assert res["next_observation"].startswith("네 기록의 「")
    assert res["next_observation"].endswith("내일 준에게 배급이 어디서 오는지 물어봐라.")
    assert res["answer"].startswith("왜인지는 내가 말할 수 없다.")
    notes = NoteRepository(db_session).list(attempt.id)
    assert any(n.source_key == "advisor-lead-k1" and n.kind == "advice" for n in notes)


def test_advice_is_skipped_without_anchor(db_session):
    lead = make_lead(anchor_cues=("거울",))
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    res = inter.ask(night.id, "배급이 왜 이래?")
    assert res["next_observation"] is None or "네 기록의" not in res["next_observation"]
    assert not any(n.source_key.startswith("advisor-lead-") for n in NoteRepository(db_session).list(attempt.id))


def test_same_lead_is_not_advised_twice(db_session):
    lead = make_lead()
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    publish_scene_action(inter, night, "배급을 남긴다")
    first = inter.ask(night.id, "배급이 왜 이래?")
    second = inter.ask(night.id, "배급 얘기 또 물을게")
    assert "네 기록의" in first["next_observation"]
    assert second["next_observation"] is None or "네 기록의" not in second["next_observation"]


def test_future_loop_lead_stays_locked(db_session):
    lead = make_lead(loop_n=3)
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    publish_scene_action(inter, night, "배급을 남긴다")
    res = inter.ask(night.id, "배급이 왜 이래?")
    assert res["next_observation"] is None or "네 기록의" not in res["next_observation"]


def test_fact_question_gets_verdict_prefix(db_session):
    inter, attempt, night = make_intervention(db_session, [
        {"question_kind": "proposition", "answer": "채연은 쟁반을 반쯤 남기고 옆으로 밀었다.",
         "evidence": []}])
    publish_scene_action(inter, night, "배급을 남긴다")
    res = inter.ask(night.id, "채연이 오늘 배급을 남겼어?")
    assert res["answer"].split(" ", 1)[0] in {"맞다.", "그건", "아니다."}
    assert res["verdict"] in {"맞다.", "아니다.", "그건 알 수 없다."}


def test_polite_register_triggers_regeneration(db_session):
    polite = {"question_kind": "proposition", "answer": "채연은 쟁반을 남겼습니다.", "evidence": []}
    plain = {"question_kind": "proposition", "answer": "채연은 쟁반을 남겼다.", "evidence": []}
    inter, attempt, night = make_intervention(db_session, [polite, plain])
    publish_scene_action(inter, night, "배급을 남긴다")
    res = inter.ask(night.id, "채연이 오늘 배급을 남겼어?")
    assert "습니다" not in res["answer"]
    reports = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "harness_event"]
    assert reports[-1].attempts == 2


def test_supported_fact_is_saved_as_confirmed_note(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    obs_id = publish_scene_action(inter, night, "배급을 남긴다")
    from apps.engine.app.use_cases.public_observations import public_observations
    observation = next(o for o in public_observations(EventLogRepository(db_session), attempt.id)
                       if o.observation_id == obs_id)
    inter._llm = FakeLLM([
        {"question_kind": "proposition", "answer": "채연은 쟁반을 남겼다.",
         "evidence": [{"id": obs_id, "quote": observation.text, "relation": "supported"}]}])
    res = inter.ask(night.id, "채연이 오늘 배급을 남겼어?")
    assert res["status"] == "supported"
    notes = NoteRepository(db_session).list(attempt.id)
    assert any(n.kind == "confirmed" and n.source_key == f"confirmed-{obs_id}" for n in notes)


def test_question_without_public_record_has_plain_unknown_fallback(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    res = inter.ask(night.id, "누가 밥을 남겼어?")
    assert res["answer"] == "그건 알 수 없다."


def test_meta_question_with_why_cue_still_gets_supported_verdict(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    res = inter.ask(night.id, "왜 너에게 질문해야 해?")
    assert res["answer"].startswith("맞다.")
