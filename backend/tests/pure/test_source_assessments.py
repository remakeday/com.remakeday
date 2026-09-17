"""Source-local validation and aggregation with mixed observation/statement context."""
from types import SimpleNamespace as NS
from uuid import uuid4
import pytest
from apps.engine.app.use_cases.intervention_interactor import InterventionInteractor
from apps.engine.app.use_cases.public_observations import disclose
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_review_failure_boundaries import Events, loop_at
from tests.pure.test_question_stage_isolation import Stages


def ask(question, records, assessments, kind="proposition"):
    events, loop = Events(), loop_at()
    loop.state = "intervention"
    night = NS(id=uuid4(), loop_id=loop.id, questions_left=3, questions=[])
    sources = {key: disclose(events, loop, build().bundle().beats[0], key=key, text=text, actor=actor, source_kind=source_kind)
               for key, text, actor, source_kind in records}
    mapped = [{**a, "id": sources[a["id"]].observation_id if a["id"] in sources else a["id"]} for a in assessments]
    out = {"question_kind": kind, "answer": "관찰된 내용에서 질문의 근거를 살펴볼 수 있어.", "evidence": mapped}
    model = Stages([out, out, out])
    inter = InterventionInteractor(attempts=None, loops=NS(get=lambda _: loop), notes=None, rules=None,
        nights=NS(get=lambda _: night, save=lambda: None), event_log=events, core_llm=model,
        action_vocab=[], target_names=["채연", "민석", "은상", "준"], harness_on=True, rule_cls=None)
    return inter.ask(night.id, question), model, events, night


def assessment(key, quote, relation):
    return {"id": key, "quote": quote, "relation": relation}


CHECKUP = "채연이 검진을 받았다. 결과는 공개되지 않았다."
INSTRUCTION = "관리자입니다. 오후에는 검진합니다."
RECORDS = [("checkup", CHECKUP, "채연", "scene"), ("instruction", INSTRUCTION, None, "statement")]


@pytest.mark.parametrize("context_relation", ["supported", "contradicted", "unknown"])
def test_reported_context_does_not_veto_direct_observed_negation(context_relation):
    result, _, _, _ = ask("채연의 검진 결과가 공개되었어?", RECORDS,
        [assessment("instruction", INSTRUCTION, context_relation), assessment("checkup", "결과는 공개되지 않았다.", "contradicted")])
    assert result["status"] == "contradicted" and len(result["evidence"]) == 2
    assert any(o["verification"] == "reported" for o in result["evidence"])


def test_reported_only_cannot_confirm_actual_event():
    fact = "채연의 검진 결과가 공개되었다고 들었다."
    result, _, _, _ = ask("채연의 검진 결과가 공개되었어?", [("report", fact, None, "statement")], [assessment("report", fact, "supported")])
    assert result["status"] == "unknown"


def test_reported_source_can_confirm_instruction_speech():
    result, _, _, _ = ask("관리자가 검진한다고 말했어?", RECORDS, [assessment("instruction", INSTRUCTION, "supported")])
    assert result["status"] == "supported"


@pytest.mark.parametrize(("extra", "error"), [
    (assessment("checkup", "", "supported"), "schema:"),
    (assessment("checkup", "채연이 웃었다.", "supported"), "non_verbatim_evidence"),
    (assessment("invented", CHECKUP, "supported"), "missing_public_evidence"),
    (assessment("checkup", CHECKUP, "supported"), "conflicting_evidence"),
])
def test_invalid_or_conflicting_source_retries_without_promotion(extra, error):
    result, model, events, night = ask("검진 결과가 공개되었어?", RECORDS,
        [assessment("checkup", CHECKUP, "contradicted"), extra])
    # 재시도는 한 질문으로 한 번만 센다 — unknown이라 그 한 번도 환급된다 (순서표 5번)
    assert result["status"] == "unknown" and len(model.calls) == 3 and night.questions_left == 3 and result["refunded"]
    audit = [e for e in events.rows if e.type == "harness_event"][-1]
    assert audit.fallback_used and error in str(audit.call_records[0]["checks"])
    assert error in model.calls[1][0][-1].content


def test_identical_duplicate_source_is_rendered_once():
    item = assessment("checkup", CHECKUP, "contradicted")
    result, _, _, _ = ask("검진 결과가 공개되었어?", RECORDS, [item, item])
    assert result["status"] == "contradicted" and len(result["evidence"]) == 1 and result["detail"] == CHECKUP


def test_conflicting_eligible_observations_remain_unknown():
    fact = "채연의 검진 결과를 공개했다."
    result, _, _, _ = ask("채연의 검진 결과가 공개되었어?", [RECORDS[0], ("published", fact, "채연", "scene")],
        [assessment("checkup", CHECKUP, "contradicted"), assessment("published", fact, "supported")])
    assert result["status"] == "unknown" and len(result["evidence"]) == 2


def test_reason_scope_is_per_source_so_action_context_does_not_veto_explicit_reason():
    reason, action = "채연은 배가 부르기 때문에 배급을 남겼다.", "민석이 배급을 남겼다."
    result, _, _, _ = ask("왜 배급을 남겼어?", [("reason", reason, "채연", "scene"), ("action", action, "민석", "scene")],
        [assessment("reason", reason, "supported"), assessment("action", action, "contradicted")], "lookup")
    assert result["status"] == "supported"


def test_lookup_contradiction_is_not_an_answer():
    fact = "민석은 배급을 남기지 않았다."
    result, _, _, _ = ask("누가 배급을 남겼어?", [("no", fact, "민석", "scene")], [assessment("no", fact, "contradicted")], "lookup")
    assert result["status"] == "unknown"


def test_second_receives_original_why_condition_without_first_rewrite():
    original = "열이나면 왜 검진 결과를 공개하지 않아?"
    result, model, events, night = ask(original, RECORDS, [assessment("checkup", CHECKUP, "unknown")], "lookup")
    assert result["status"] == "unknown" and night.questions_left == 3  # unknown 환급 (순서표 5번)
    assert set(model.calls[0][1]["properties"]) == {"question_kind", "evidence", "answer"}
    assert original in model.calls[0][0][0].content
    assert [e.question for e in events.rows if e.type == "intervention_question"] == [original]
