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


def make_lead(key="k1", loop_n=1, cues=("배급",), text="배급 포대는 트럭에서 내려온다.",
              direction="내일 배급 자리를 지켜봐라."):
    from apps.engine.app.dtos.scenario_dto import AdvisorLeadDTO
    return AdvisorLeadDTO(key=key, loop_n=loop_n, cues=list(cues), text=text, direction=direction)


def test_question_unlocks_lead_note_and_direction_even_on_fallback(db_session):
    lead = make_lead()
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    res = inter.ask(night.id, "배급이 왜 이래?")
    assert res["unlocked_note"] == lead.text
    assert lead.text in res["answer"]
    assert res["next_observation"] == lead.direction
    notes = NoteRepository(db_session).list(attempt.id)
    assert any(n.source_key == "advisor-lead-k1" and n.text == lead.text for n in notes)


def test_same_lead_is_not_unlocked_twice(db_session):
    lead = make_lead()
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    first = inter.ask(night.id, "배급이 왜 이래?")
    second = inter.ask(night.id, "배급 얘기 또 물을게")
    assert first["unlocked_note"] == lead.text
    assert second["unlocked_note"] is None
    notes = [n for n in NoteRepository(db_session).list(attempt.id)
             if n.source_key.startswith("advisor-lead-")]
    assert len(notes) == 1


def test_future_loop_lead_stays_locked(db_session):
    lead = make_lead(key="late", loop_n=3)
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    res = inter.ask(night.id, "배급이 왜 이래?")
    assert res["unlocked_note"] is None
    assert not [n for n in NoteRepository(db_session).list(attempt.id)
                if n.source_key.startswith("advisor-lead-")]


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
    assert not NoteRepository(db_session).list(attempt.id)  # Never add an unrelated confirmed note.


def test_question_rejects_fabricated_evidence_id_and_falls_back(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    publish_record(inter, attempt, night)
    inter._llm = FakeLLM(question_responses(model_assessment('supported', detail=_FACT, evidence_ids=['invented']), evidence_attempts=3))
    answer = inter.ask(night.id, "채연이 뭐 했어?")
    assert answer["status"] == "unknown"
    assert [o["text"] for o in answer["evidence"]] == [_FACT]  # Preserve public known facts after invalid IDs.
    assert answer["next_observation"]


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
    return disclose(inter._events, loop, BeatDTO(n=1, title="아침", narration=_FACT),
                    key=f"action-1-채연-{action}", text=_FACT, actor="채연",
                    source_kind="rule_result" if rule_id else "scene", rule_id=rule_id)


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
