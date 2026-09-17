"""P3 신의개입 유스케이스 — 열린 질문 답변 유형 (FakeLLM 큐로 제어)."""

import pytest

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
                      advisor_leads=None, advisor_ladder=None):
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
        advisor_ladder=advisor_ladder or [],
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


def test_question_without_public_record_is_unknown_and_refunds_the_question(db_session):
    """순서표 5번 — "알 수 없다"는 횟수를 쓰지 않는다 (전: 1회 차감)."""
    inter, attempt, night = make_intervention(db_session, [])
    answer = inter.ask(night.id, "누가 밥을 남겼어?")
    assert answer["status"] == "unknown"
    assert (answer["remaining"], answer["refunded"], answer["kind"]) == (3, True, "answer")
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


def test_meta_question_about_asking_gets_usage_guide_without_verdict(db_session):
    """순서표 5번 — 옛 meta 경로("맞다." 판정)는 사용법 안내 답으로 흡수됐다."""
    from apps.engine.app.use_cases.advisor_advice import GUIDE_ANSWERS
    inter, attempt, night = make_intervention(db_session, [])
    res = inter.ask(night.id, "왜 너에게 질문해야 해?")
    assert (res["kind"], res["verdict"], res["answer"]) == ("guide", "", GUIDE_ANSWERS["usage"])


# F10 — 판정 접두어가 본문과 모순되면 안 된다 (2026-09-17 실플레이 사례)
_F10_HEDGED = [
    ("민석의 보고가 채연의 이송으로 이어졌는가?", "lookup",
     "민석이 채연이 남긴 배급의 양과 이름을 적어 보고한다.",
     "민석은 채연이 남긴 배급의 양과 이름을 기록했다. 이 기록이 실제 이송으로 이어졌는지는 알 수 없다."),
    ("밤에 트럭이 온 날 아침에는 비어 있는 자리가 생기는가?", "proposition",
     "밤에 트럭이 온다.",
     "밤에 트럭이 온다는 사실과 아침에 자리를 정돈한다는 방송 내용이 연결된다. "
     "트럭의 방문이 비어 있는 자리의 발생이나 이동과 관련될 가능성이 있다."),
    ('트럭 옆면의 "○○축산"은 무엇을 하는 곳인가?', "proposition",
     "트럭 옆면에 ○○축산이라고 적혀 있다.",
     '트럭이 배급 물자를 운반하는 수단으로 사용된다. "○○축산"이라는 명칭이 구체적으로 어떤 사업을 하는지 알 수 없다.'),
    ("이곳에 있는 우리는 사람이 아니라 가축으로 관리되고 있는가?", "proposition",
     "관리자가 손목띠를 절대 풀지 말라고 한다.",
     "배급 트럭의 '축산' 명칭과 관리자의 엄격한 손목띠 착용 지시가 결합된 상황이다. "
     "이 두 요소가 가축 관리 체계와 연관될 가능성이 있다."),
]


@pytest.mark.parametrize("question, kind, record, body", _F10_HEDGED)
def test_hedged_answer_body_never_gets_decisive_verdict(db_session, question, kind, record, body):
    inter, attempt, night = make_intervention(db_session, [])
    observation = publish_record(inter, attempt, night, text=record, actor=None)
    inter._llm = FakeLLM([{"question_kind": kind, "answer": body,
                           "evidence": [{"id": observation.observation_id, "quote": record, "relation": "supported"}]}])
    res = inter.ask(night.id, question)
    assert res["status"] == "unknown"
    assert res["verdict"] == "그건 알 수 없다."
    assert res["answer"] == f"그건 알 수 없다. {body}"
    assert res["detail"].startswith("확인된 기록:")
    assert not any(n.kind == "confirmed" for n in NoteRepository(db_session).list(attempt.id))


def test_unhedged_supported_proposition_keeps_yes_verdict_and_confirmed_note(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    observation = publish_record(inter, attempt, night)
    inter._llm = FakeLLM([{"question_kind": "proposition", "answer": "채연은 쟁반을 반쯤 남기고 옆으로 밀었다.",
                           "evidence": [{"id": observation.observation_id, "quote": _FACT, "relation": "supported"}]}])
    res = inter.ask(night.id, "채연이 오늘 배급을 남겼어?")
    assert res["status"] == "supported"
    assert (res["remaining"], res["refunded"]) == (2, False)
    assert res["answer"] == "맞다. 채연은 쟁반을 반쯤 남기고 옆으로 밀었다."
    assert any(n.kind == "confirmed" and n.source_key == f"confirmed-{observation.observation_id}"
               for n in NoteRepository(db_session).list(attempt.id))


def test_unhedged_contradicted_proposition_keeps_no_verdict(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    record = "채연은 쟁반을 밀어내지 않았다."
    observation = publish_record(inter, attempt, night, text=record)
    inter._llm = FakeLLM([{"question_kind": "proposition", "answer": "채연은 쟁반을 그대로 두었다.",
                           "evidence": [{"id": observation.observation_id, "quote": record, "relation": "contradicted"}]}])
    res = inter.ask(night.id, "채연이 쟁반을 밀어냈어?")
    assert res["status"] == "contradicted"
    assert res["answer"] == "아니다. 채연은 쟁반을 그대로 두었다."


def test_wh_question_answered_by_record_has_no_yes_no_verdict(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    observation = publish_record(inter, attempt, night)
    inter._llm = FakeLLM([{"question_kind": "proposition", "answer": "채연이 쟁반을 반쯤 남겼다.",
                           "evidence": [{"id": observation.observation_id, "quote": _FACT, "relation": "supported"}]}])
    res = inter.ask(night.id, "누가 밥을 남겼어?")
    assert res["status"] == "supported"
    assert res["verdict"] == ""
    assert res["answer"] == "채연이 쟁반을 반쯤 남겼다."


def test_wh_question_contradicted_by_record_is_unknown_even_if_model_says_proposition(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    record = "채연은 쟁반을 밀어내지 않았다."
    observation = publish_record(inter, attempt, night, text=record)
    inter._llm = FakeLLM([{"question_kind": "proposition", "answer": "채연은 쟁반을 그대로 두었다.",
                           "evidence": [{"id": observation.observation_id, "quote": record, "relation": "contradicted"}]}])
    res = inter.ask(night.id, "채연은 언제 쟁반을 밀어냈어?")
    assert res["status"] == "unknown"
    assert res["verdict"] == "그건 알 수 없다."


def test_rule_conflicts_shown_to_player_exclude_hidden_paw_rules(db_session):
    """F11: 숨은 규칙(paw_effect)과의 충돌도 판정·기록되지만 플레이어 응답에는 그 ID를 싣지 않는다."""
    inter, attempt, night = make_intervention(db_session, [], rules=[("채연", "기록한다", "enforce")],
                                              action_vocab=["기록한다"])
    inter._rules.add(RuleOrm(attempt_id=attempt.id, rule_id="R2", source="paw_effect", target="채연",
                             when_beat=None, effect="enforce", action="기록한다", created_loop=1))
    preview = inter.preview_rule(night.id, "채연은 기록한다 금지")
    assert preview["conflicts"] == ["R1"]
    applied = inter.choose_rule(night.id, "custom", "채연은 기록한다 금지", preview["preview_id"])
    assert applied["conflicts"] == ["R1"]
    new = [r for r in inter._rules.list(attempt.id) if r.source == "user_custom"]
    assert len(new) == 1 and new[0].conflict


def test_hidden_only_rule_conflict_is_recorded_but_not_shown(db_session):
    inter, attempt, night = make_intervention(db_session, [], action_vocab=["기록한다"])
    inter._rules.add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="paw_effect", target="채연",
                             when_beat=None, effect="enforce", action="기록한다", created_loop=1))
    preview = inter.preview_rule(night.id, "채연은 기록한다 금지")
    assert preview["conflicts"] == []
    assert "같은 행동의 충돌에서는 나중에 적용한 규칙이 우선한다." not in preview["limitations"]
    applied = inter.choose_rule(night.id, "custom", "채연은 기록한다 금지", preview["preview_id"])
    assert applied["conflicts"] == []
    assert [r.conflict for r in inter._rules.list(attempt.id) if r.source == "user_custom"] == [True]


def _many_templates():
    return [{"target": "채연", "action": action, "effect": "enforce", "when_beat": 1, "label": f"채연: {action}"}
            for action in ("알고 있는 관찰을 설명한다", "검진을 받는다", "혼자 있는다", "기록한다", "따라간다")]


def test_rule_lead_advised_tonight_is_the_first_option_even_beyond_three(db_session):
    """테스터11 O4 — 조언이 권한 규칙(대상·행동)이 앞 3개 자르기에 밀려 선택지에서 빠지지 않는다."""
    lead = make_lead(key="follow", cues=("배급",), anchor_cues=("배급",), target="채연", ask=None, rule_action="따라간다")
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    publish_scene_action(inter, night, "배급을 남긴다")
    inter._templates = _many_templates()
    advice = inter.ask(night.id, "배급이 왜 이래?")["next_observation"]
    assert advice.endswith("채연: 따라간다 규칙을 걸어 봐라.")
    options = inter.options(night.id)["options"]
    assert len(options) == 3
    assert (options[0]["target"], options[0]["action"], options[0]["index"]) == ("채연", "따라간다", 1)


def test_rule_lead_from_an_earlier_night_or_ask_lead_does_not_reorder_options(db_session):
    lead = make_lead(key="follow", target="채연", ask="배급이 어디서 오는지")
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    publish_scene_action(inter, night, "배급을 남긴다")
    inter._templates = _many_templates()
    inter.ask(night.id, "배급이 왜 이래?")
    NoteRepository(db_session).upsert(attempt.id, kind="advice", text="지난 밤 조언", loop_n=0,
                                      source_key="advisor-lead-old")
    inter._advisor_leads = [lead, make_lead(key="old", target="채연", ask=None, rule_action="따라간다")]
    actions = [o["action"] for o in inter.options(night.id)["options"]]
    assert "따라간다" not in actions


def test_rule_lead_already_applied_is_not_offered_again(db_session):
    lead = make_lead(key="follow", target="채연", ask=None, rule_action="따라간다")
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead],
                                              rules=[("채연", "따라간다", "enforce")])
    publish_scene_action(inter, night, "배급을 남긴다")
    inter._templates = _many_templates()
    inter.ask(night.id, "배급이 왜 이래?")
    assert "따라간다" not in [o["action"] for o in inter.options(night.id)["options"]]


def test_rule_lead_advised_tonight_is_offered_even_if_actor_already_does_it_without_rule(db_session):
    """6번 리뷰 — 조언이 권한 규칙은 '규칙 없이도 하는 행동' 제외보다 먼저 판정해 선택지에서 빠지지 않는다."""
    lead = make_lead(key="leave", target="채연", ask=None, rule_action="배급을 남긴다")
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    publish_scene_action(inter, night, "배급을 남긴다")  # rule_id 없음 = 규칙 없이도 하는 행동
    inter._templates = _ration_templates()
    assert inter.ask(night.id, "배급이 왜 이래?")["next_observation"].endswith("채연: 배급을 남긴다 규칙을 걸어 봐라.")
    options = inter.options(night.id)["options"]
    assert (options[0]["target"], options[0]["action"]) == ("채연", "배급을 남긴다")


def _applied_intent(inter, attempt):
    return [e for e in inter._events.query(attempt.id) if e.type == "rule_applied"][-1].intent


def test_recommended_rule_intent_is_the_option_label_not_the_night_claims(db_session):
    """테스터9 F25 — 추천 규칙을 고르면 그날 추리문 전문이 아니라 그 선택지의 규칙 설명이 의도로 남는다."""
    inter, attempt, night = make_intervention(db_session, [])
    publish_scene_action(inter, night, "배급을 남긴다", rule_id="R1")
    inter._templates = _ration_templates()
    night.claims = ["채연은 아픈 걸 숨기려고 배급을 남긴 것 같다. 트럭은 이상자를 데려간다."]
    options = inter.options(night.id)["options"]
    inter.choose_rule(night.id, "1", None)
    intent = _applied_intent(inter, attempt)
    assert intent == options[0]["label"]
    assert "트럭" not in intent


def test_rule_intent_strategy_by_source():
    from apps.engine.app.use_cases.intervention_interactor import rule_intent
    assert rule_intent("user_choice", {"label": "채연: 배급을 남긴다"}, None) == "채연: 배급을 남긴다"
    assert rule_intent("user_choice", {"target": "채연", "action": "배급을 남긴다"}, None) is None
    assert rule_intent("user_custom", {"label": "해석"}, "채연은 기록한다 금지") == "채연은 기록한다 금지"


def test_custom_rule_intent_keeps_player_original_text(db_session):
    inter, attempt, night = make_intervention(db_session, [], action_vocab=["기록한다"])
    night.claims = ["긴 추리문"]
    preview = inter.preview_rule(night.id, "채연은 기록한다 금지")
    inter.choose_rule(night.id, "custom", "채연은 기록한다 금지", preview["preview_id"])
    assert _applied_intent(inter, attempt) == "채연은 기록한다 금지"


# 순서표 5번 — 환급 규칙 · 안내 질문 · 공개 사다리
def _events_of(inter, attempt):
    return [e for e in inter._events.query(attempt.id) if e.type == "intervention_question"]


def test_unknown_refunds_stop_after_three_in_one_night(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    results = [inter.ask(night.id, q) for q in ("트럭이 왔어?", "방송은 몇 번 나와?", "충식은 어디 갔어?", "문은 잠겨 있어?")]
    assert [(r["refunded"], r["remaining"]) for r in results] == [(True, 3), (True, 3), (True, 3), (False, 2)]
    assert [(e.q_index, e.refunded) for e in _events_of(inter, attempt)] == [(1, True), (2, True), (3, True), (4, False)]


def test_same_question_asked_again_is_not_refunded(db_session):
    inter, attempt, night = make_intervention(db_session, [])
    first = inter.ask(night.id, "트럭이 왔어?")
    again = inter.ask(night.id, "트럭이  왔어")
    assert (first["refunded"], again["refunded"], again["remaining"]) == (True, False, 2)


@pytest.mark.parametrize("question, kind", [("이 게임이 뭔지 이해가 안되 목적이뭐야?", "purpose"),
                                            ("세상이 멸망한다는게 뭔소린가", "purpose"),
                                            ("어떻게 질문해?", "usage")])
def test_guide_question_answers_without_verdict_model_call_notes_or_count(db_session, question, kind):
    from apps.engine.app.use_cases.advisor_advice import GUIDE_ANSWERS
    lead = make_lead()
    inter, attempt, night = make_intervention(db_session, [], advisor_leads=[lead])
    publish_scene_action(inter, night, "배급을 남긴다")
    res = inter.ask(night.id, question)
    assert (res["kind"], res["verdict"], res["answer"], res["remaining"], res["refunded"]) == \
        ("guide", "", GUIDE_ANSWERS[kind], 3, False)
    assert (res["evidence"], res["detail"], res["next_observation"]) == ([], None, None)
    assert inter._llm.calls == []
    assert NoteRepository(db_session).list(attempt.id) == []
    assert night.questions == []
    assert [e.kind for e in _events_of(inter, attempt)] == ["guide"]
    # 안내 질문은 환급 상한도 쓰지 않는다
    assert [inter.ask(night.id, q)["refunded"] for q in ("트럭이 왔어?", "문은 잠겨 있어?", "충식은 어디 갔어?")] == [True] * 3


_PAPER = "오후 검진 뒤 종이에 적힌 이름은 저녁에 방송실로 전달된다."


def _rung(stage=1, key="paper"):
    from apps.engine.app.dtos.scenario_dto import AdvisorRungDTO
    return AdvisorRungDTO(key=key, stage=stage, cues=["검진", "방송실"], text=_PAPER)


def _ladder_reply(relation="supported"):
    return [{"question_kind": "proposition", "answer": "검진 뒤 적힌 이름은 저녁에 방송실로 간다.",
             "evidence": [{"id": "ladder:paper", "quote": _PAPER, "relation": relation}]}]


def test_open_rung_is_judgment_material_for_a_matching_question(db_session):
    inter, attempt, night = make_intervention(db_session, _ladder_reply(), advisor_ladder=[_rung()])
    res = inter.ask(night.id, "검진 뒤 적힌 이름은 방송실로 가?")
    assert _PAPER in inter._llm.calls[0][0][0].content
    assert (res["status"], res["verdict"], res["evidence_ids"], res["remaining"]) == ("supported", "맞다.", ["ladder:paper"], 2)
    assert res["evidence"][0]["scene_title"] == "세계에 알려진 사실"
    assert any(n.kind == "confirmed" and n.source_key == "confirmed-ladder:paper" for n in NoteRepository(db_session).list(attempt.id))


def test_rung_is_not_given_for_an_unrelated_question(db_session):
    inter, attempt, night = make_intervention(db_session, [], advisor_ladder=[_rung()])
    publish_record(inter, attempt, night)
    inter.ask(night.id, "채연이 오늘 배급을 남겼어?")
    assert _PAPER not in inter._llm.calls[0][0][0].content


def test_locked_rung_is_not_given_until_its_stage(db_session):
    inter, attempt, night = make_intervention(db_session, [], advisor_ladder=[_rung(stage=2)])
    res = inter.ask(night.id, "검진 뒤 적힌 이름은 방송실로 가?")
    assert inter._llm.calls == []
    assert res["status"] == "unknown"


def test_night_score_opens_the_next_rung_early(db_session):
    from apps.engine.app.dtos import event_log_dto as ev
    inter, attempt, night = make_intervention(db_session, _ladder_reply(), advisor_ladder=[_rung(stage=2)])
    inter._events.record(attempt.id, ev.AnswerScoredEvent(
        loop_n=1, per_truth_claim=[], total=30.0, passed=False,
        cell_scores=ev.CellScores(cause=30.0, motive=30.0, identity=0.0, side_effect=0.0)))
    res = inter.ask(night.id, "검진 뒤 적힌 이름은 방송실로 가?")
    assert _PAPER in inter._llm.calls[0][0][0].content
    assert res["status"] == "supported"


def test_unknown_answer_never_shows_rung_text_as_a_confirmed_record(db_session):
    """opus 리뷰 I2 — 사다리 칸은 판정 재료다. 판정이 서지 않은(환급되는) 답의 폴백 근거로 원문을 보여 주지 않는다."""
    reply = [{"question_kind": "proposition", "answer": "기록으로는 판단할 수 없다.", "evidence": []}]
    inter, attempt, night = make_intervention(db_session, reply, advisor_ladder=[_rung()])
    res = inter.ask(night.id, "검진 결과는 어디로 가?")
    assert (res["status"], res["refunded"]) == ("unknown", True)
    assert _PAPER not in (res["detail"] or "") and _PAPER not in res["answer"]
    assert not any(i.startswith("ladder:") for i in res["evidence_ids"])
    assert _PAPER not in (_events_of(inter, attempt)[-1].detail or "")


def test_unknown_answer_drops_a_rung_the_model_cited(db_session):
    reply = [{"question_kind": "proposition", "answer": "검진 결과가 어디로 가는지는 확실치 않다.",
              "evidence": [{"id": "ladder:paper", "quote": _PAPER, "relation": "supported"}]}]
    inter, attempt, night = make_intervention(db_session, reply, advisor_ladder=[_rung()])
    res = inter.ask(night.id, "검진 뒤 적힌 이름은 방송실로 가?")
    assert res["status"] == "unknown"  # 헤지 강등
    assert _PAPER not in (res["detail"] or "") and res["evidence_ids"] == []


def test_same_question_after_a_model_failure_is_refunded_again_within_the_cap(db_session):
    """모델 실패로 답하지 못한 질문은 "같은 질문 재입력"으로 치지 않는다 — 환급 상한 집계에는 든다."""
    inter, attempt, night = make_intervention(db_session, [], advisor_ladder=[_rung()])  # 빈 응답 → 모델 실패
    first = inter.ask(night.id, "검진 결과는 어디로 가?")
    again = inter.ask(night.id, "검진 결과는 어디로 가?")
    third = inter.ask(night.id, "검진 결과는 어디로 가?")
    fourth = inter.ask(night.id, "검진 결과는 어디로 가?")
    assert [(r["refunded"], r["remaining"]) for r in (first, again, third, fourth)] == \
        [(True, 3), (True, 3), (True, 3), (False, 2)]


def test_same_question_after_an_answered_unknown_is_still_charged(db_session):
    reply = {"question_kind": "proposition", "answer": "기록으로는 판단할 수 없다.", "evidence": []}
    inter, attempt, night = make_intervention(db_session, [dict(reply), dict(reply)], advisor_ladder=[_rung()])
    first = inter.ask(night.id, "검진 결과는 어디로 가?")
    again = inter.ask(night.id, "검진 결과는 어디로 가?")
    assert (first["refunded"], again["refunded"], again["remaining"]) == (True, False, 2)


def test_guide_question_is_not_part_of_the_recent_conversation(db_session):
    from apps.engine.app.use_cases.advisor_advice import GUIDE_ANSWERS
    inter, attempt, night = make_intervention(db_session, _ladder_reply(), advisor_ladder=[_rung()])
    inter.ask(night.id, "어떻게 질문해?")
    inter.ask(night.id, "검진 뒤 적힌 이름은 방송실로 가?")
    prompt = inter._llm.calls[0][0][0].content
    assert "어떻게 질문해?" not in prompt and GUIDE_ANSWERS["usage"] not in prompt


# 리뷰 반영(A등급) — 같은 밤 요청은 밤 행 잠금으로 직렬화한다. 실제 DB 세션 + 컴포지션 루트 배선.
# opus 최종 리뷰 C1: 잠금은 기다리지 않는다(NOWAIT) — 앞 요청이 쥐고 있으면 곧바로 409. 기다리는 요청이 연결 풀을 채우지 않는다.
def _concurrent_night(db_session, *, questions_left, questions):
    attempt = AttemptRepository(db_session).create(None)
    loop = LoopOrm(attempt_id=attempt.id, loop_n=1, budget_left=0, state="intervention", cause_chain=[])
    LoopRepository(db_session).create(loop, [])
    return NightRepository(db_session).create(
        NightOrm(loop_id=loop.id, questions_left=questions_left, questions=list(questions)))


_UNKNOWN_REPLY = {"question_kind": "proposition", "answer": "기록으로는 판단할 수 없다.", "evidence": []}
_HOLD_LIMIT = 10  # 안전 상한 — 정상 경로에서는 테스트가 곧바로 풀어 준다


class _HeldModel:
    """모델 호출 안에서 멈춘다 — 테스트가 풀어 줄 때까지 앞 요청이 밤 잠금을 쥐고 있다."""
    def __init__(self):
        import threading
        self.calls, self.entered, self.release = 0, threading.Event(), threading.Event()

    def complete(self, *_args, **_kwargs):
        self.calls += 1
        self.entered.set()
        self.release.wait(_HOLD_LIMIT)
        return dict(_UNKNOWN_REPLY)


def _in_own_session(db_session, work):
    """요청 하나 = 실제 세션 하나 — 라우터와 같은 컴포지션 루트로 인터랙터를 만든다. 예외도 결과로 돌려준다."""
    from sqlalchemy.orm import Session
    from apps.engine.dependencies.engine_dependency import get_intervention_interactor
    with Session(db_session.get_bind()) as session:
        try:
            return work(get_intervention_interactor(session))
        except Exception as exc:  # 결과로 비교한다
            return exc


def _while_first_is_held(db_session, first, second, *, entered, release):
    """앞 요청을 다른 스레드에서 보내 잠금 안에서 멈춘 동안 뒤 요청을 보낸다.

    뒤 요청이 돌아온 순간 앞 요청이 아직 멈춰 있어야 "기다리지 않고" 답한 것이다 — 기다렸다면 앞 요청이 안전 상한으로 먼저 끝난다."""
    import threading
    outcome = {}
    worker = threading.Thread(target=lambda: outcome.update(first=_in_own_session(db_session, first)))
    worker.start()
    try:
        assert entered.wait(_HOLD_LIMIT)
        outcome["second"] = _in_own_session(db_session, second)
        outcome["first_still_held"] = worker.is_alive()
    finally:
        release.set()
        worker.join(_HOLD_LIMIT * 2)
    db_session.expire_all()
    return outcome


def test_question_while_the_same_night_is_answering_is_409_without_waiting(db_session):
    from apps.engine.app.use_cases.intervention_interactor import GameStateError
    night = _concurrent_night(db_session, questions_left=1,
                              questions=["하나", "둘", "셋", "넷", "다섯"])  # 환급 3회 다 씀, 남은 1
    model = _HeldModel()

    def ask(text):
        def work(inter):
            inter._llm = model
            return inter.ask(night.id, text)
        return work
    outcome = _while_first_is_held(db_session, ask("트럭은 언제 와?"), ask("문은 잠겨 있어?"),
                                   entered=model.entered, release=model.release)
    assert isinstance(outcome["second"], GameStateError) and "앞 질문에 답하는 중" in str(outcome["second"])
    assert outcome["first_still_held"]
    assert model.calls == 1  # 한 밤 모델 호출 상한 6
    assert isinstance(outcome["first"], dict) and outcome["first"]["refunded"] is False
    saved = NightRepository(db_session).get(night.id)
    assert (saved.questions_left, len(saved.questions)) == (0, 6)


def test_refund_cap_holds_when_a_second_question_arrives_during_an_answer(db_session):
    night = _concurrent_night(db_session, questions_left=3, questions=["앞 질문 하나", "앞 질문 둘"])  # 환급 2회 사용
    model = _HeldModel()

    def ask(text):
        def work(inter):
            inter._llm = model
            return inter.ask(night.id, text)
        return work
    outcome = _while_first_is_held(db_session, ask("트럭은 언제 와?"), ask("문은 잠겨 있어?"),
                                   entered=model.entered, release=model.release)
    assert outcome["first"]["refunded"] is True  # 세 번째 환급
    again = _in_own_session(db_session, ask("문은 잠겨 있어?"))  # 409를 받은 질문을 다시 보낸다
    assert again["refunded"] is False  # 상한 3
    db_session.expire_all()
    saved = NightRepository(db_session).get(night.id)
    assert (saved.questions_left, len(saved.questions)) == (2, 4)
    assert {"트럭은 언제 와?", "문은 잠겨 있어?"} <= set(saved.questions)


def test_rule_choice_while_another_choice_is_applying_is_409_and_one_rule_applies(db_session):
    import threading
    from apps.engine.app.use_cases.intervention_interactor import GameStateError
    night = _concurrent_night(db_session, questions_left=3, questions=[])
    loop = LoopRepository(db_session).get(night.loop_id)
    option = {"target": "채연", "when_beat": "any", "effect": "enforce", "action": "말 걸기", "label": "채연: 말 걸기"}
    night.options = [option, {**option, "target": "민석", "label": "민석: 말 걸기"}]
    NightRepository(db_session).save()
    entered, release = threading.Event(), threading.Event()

    def choose(i, *, hold):
        def work(inter):
            if hold:
                next_rule_id = inter._rules.next_rule_id

                def held(*args):  # 규칙 번호를 받기 직전(잠금 안)에서 멈춘다
                    entered.set()
                    release.wait(_HOLD_LIMIT)
                    return next_rule_id(*args)
                inter._rules.next_rule_id = held
            return inter.choose_rule(night.id, str(i + 1), None)
        return work
    outcome = _while_first_is_held(db_session, choose(0, hold=True), choose(1, hold=False),
                                   entered=entered, release=release)
    assert isinstance(outcome["second"], GameStateError) and outcome["first_still_held"]
    assert outcome["first"]["ok"]
    assert len(RuleRepository(db_session).list(loop.attempt_id)) == 1


def _last_question_night(db_session):
    return _concurrent_night(db_session, questions_left=1, questions=["하나", "둘", "셋", "넷", "다섯"])  # 환급 소진, 남은 1


class _CountingModel:
    def __init__(self):
        self.calls = 0

    def complete(self, *_args, **_kwargs):
        self.calls += 1
        return dict(_UNKNOWN_REPLY)


def test_model_call_audit_failure_does_not_roll_back_the_charge(db_session, monkeypatch, caplog):
    """opus 리뷰 C1 — 감사 기록(harness_event)이 실패해도 차감·질문 기록은 커밋된다. 같은 질문을 다시 보내도 모델을 다시 부르지 않는다."""
    from sqlalchemy.exc import TimeoutError as PoolTimeout
    from apps.engine.adapter.outbound.repositories import event_log_repository
    from apps.engine.app.use_cases.intervention_interactor import GameStateError

    def no_audit_connection(_url):
        raise PoolTimeout("audit pool exhausted")
    monkeypatch.setattr(event_log_repository, "get_audit_engine", no_audit_connection)
    night = _last_question_night(db_session)
    model = _CountingModel()

    def ask(inter):
        inter._llm = model
        return inter.ask(night.id, "트럭은 언제 와?")
    results = [_in_own_session(db_session, ask) for _ in range(3)]
    assert isinstance(results[0], dict) and all(isinstance(r, GameStateError) for r in results[1:])
    assert model.calls == 1
    db_session.expire_all()
    saved = NightRepository(db_session).get(night.id)
    assert (saved.questions_left, len(saved.questions)) == (0, 6)
    loop = LoopRepository(db_session).get(night.loop_id)
    kinds = [e.type for e in EventLogRepository(db_session).query(loop.attempt_id)]
    assert "intervention_question" in kinds and "harness_event" not in kinds
    assert "harness audit" in caplog.text


def test_full_request_pool_does_not_make_the_last_question_free(db_session):
    """opus 리뷰 C1 probe — 요청 풀 2개 중 1개를 다른 요청이 쥔 상태에서 남은 1회 밤에 네 번 묻는다. 모델 호출은 1회뿐이다."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session
    from apps.engine.app.use_cases.intervention_interactor import GameStateError
    from apps.engine.dependencies.engine_dependency import get_intervention_interactor
    night = _last_question_night(db_session)
    model = _CountingModel()
    small = create_engine(db_session.get_bind().url, pool_size=2, max_overflow=0, pool_timeout=1)
    hog = small.connect()
    hog.execute(text("select 1"))  # 다른 요청이 쥔 연결
    results = []
    try:
        for i in range(4):
            with Session(small) as session:
                inter = get_intervention_interactor(session)
                inter._llm = model
                try:
                    results.append(inter.ask(night.id, f"질문 {i}은 무엇"))
                except GameStateError as exc:
                    results.append(exc)
    finally:
        hog.close()
        small.dispose()
    assert model.calls <= 1
    assert sum(isinstance(r, GameStateError) for r in results) == 3
    db_session.expire_all()
    assert NightRepository(db_session).get(night.id).questions_left == 0


def test_question_waiting_behind_rule_choice_sees_the_closed_loop(db_session):
    """라우터 소유 확인이 밤·회차를 먼저 읽어 둔 세션도, 잠금을 얻은 뒤에는 닫힌 회차를 본다 — 모델 호출 없음."""
    from sqlalchemy.orm import Session
    from apps.engine.app.use_cases.intervention_interactor import GameStateError
    from apps.engine.dependencies.engine_dependency import get_intervention_interactor
    night = _concurrent_night(db_session, questions_left=3, questions=[])
    option = {"target": "채연", "when_beat": "any", "effect": "enforce", "action": "말 걸기", "label": "채연: 말 걸기"}
    night.options = [option]
    NightRepository(db_session).save()
    engine = db_session.get_bind()
    with Session(engine) as asking, Session(engine) as choosing:
        late = get_intervention_interactor(asking)
        late._llm = _CountingModel()
        seen_night = NightRepository(asking).get(night.id)  # 소유 확인이 먼저 읽어 세션에 들고 있다
        seen_loop = LoopRepository(asking).get(seen_night.loop_id)
        assert get_intervention_interactor(choosing).choose_rule(night.id, "1", None)["ok"]
        with pytest.raises(GameStateError):
            late.ask(night.id, "트럭은 언제 와?")
        assert late._llm.calls == 0 and seen_loop.state == "closed"
