"""Real use-case boundaries: question interpretation cannot see public evidence."""

from types import SimpleNamespace as NS
from uuid import uuid4

import pytest

from apps.engine.app.use_cases.intervention_interactor import InterventionInteractor
from apps.engine.app.use_cases.public_observations import disclose
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_review_failure_boundaries import Events, loop_at


class Stages:
    def __init__(self, outputs):
        self.outputs, self.calls = list(outputs), []

    def complete(self, messages, schema, **kwargs):
        self.calls.append((messages, schema))
        result = self.outputs.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def ask(first, second, question, fact="채연의 검진 결과는 공개되지 않았다.", first_attempts=None):
    loop, events = loop_at(), Events()
    loop.state = "intervention"
    night = NS(id=uuid4(), loop_id=loop.id, questions_left=3, questions=[])
    observation = disclose(events, loop, build().bundle().beats[0], key="source",
                           text=fact, actor="채연")
    if isinstance(second, dict):
        second = {"evidence": [{"id": observation.observation_id, "quote": fact, "relation": second["relation"]}]} if "relation" in second else second
    if second is None:
        second = {"evidence": []}
    def reply(kind):
        if isinstance(kind, Exception):
            return kind
        if isinstance(second, Exception):
            return second
        return {**kind, **second, "answer": "검진 결과는 아직 공개되지 않았어."}
    model = Stages([reply(item) for item in (first_attempts or [first])])
    inter = InterventionInteractor(attempts=None, loops=NS(get=lambda _: loop), notes=None, rules=None,
        nights=NS(get=lambda _: night, save=lambda: None), event_log=events, core_llm=model,
        action_vocab=[], target_names=["채연", "민석", "은상", "준"], harness_on=True, rule_cls=None)
    return inter.ask(night.id, question), model, night, events, observation


def interpretation(kind="proposition"):
    return {"question_kind": kind}


def test_one_call_keeps_original_question_budget_and_audit():
    original = "채연의 검진 결과가 공개되지 않았어?"
    result, model, night, events, source = ask(interpretation(), {"relation": "supported"}, original)
    assert result["status"] == "supported" and len(model.calls) == 1
    context = "\n".join(m.content for m in model.calls[0][0])
    assert original in context and source.text in context and source.observation_id in context
    assert night.questions_left == result["remaining"] == 2 and night.questions == [original]
    audits = [e for e in events.rows if e.type == "harness_event"]
    assert [e.role for e in audits] == ["advisor_answer"]
    assert audits[0].call_records[0]["temperature"] == 0
    assert [e.question for e in events.rows if e.type == "intervention_question"] == [original]


@pytest.mark.parametrize(("fact", "original", "relation"), [
    ("검진 결과는 공개되지 않았다.", "검진 결과가 공개되었어?", "contradicted"),
    ("검진 결과는 공개되지 않았다.", "검진 결과가 공개되지 않았어?", "supported"),
    ("검진 결과를 공개했다.", "검진 결과가 공개되었어?", "supported"),
    ("검진 결과를 공개했다.", "검진 결과가 공개되지 않았어?", "contradicted"),
])
def test_original_polarity_is_not_rewritten_or_inverted(fact, original, relation):
    result, model, _, _, _ = ask(interpretation(), {"relation": relation}, original, fact)
    assert result["status"] == relation and original in model.calls[0][0][0].content


@pytest.mark.parametrize("original", ["열이나면 죽나?", "왜 배급을 남겼어?", "내일 검진 결과가 공개될까?", "말한 지시가 실제로 이행됐어?"])
def test_original_spelling_reason_time_and_execution_reach_evidence_unchanged(original):
    _, model, _, _, _ = ask(interpretation(), {"relation": "unknown"}, original)
    assert original in model.calls[0][0][0].content
    assert set(model.calls[0][1]["properties"]) == {"question_kind", "evidence", "answer"}


def test_provider_failure_keeps_cost_and_partial_record():
    result, model, night, events, source = ask(RuntimeError("unavailable"), {}, "채연의 검진 결과는?")
    assert result["status"] == "unknown" and result["evidence"][0]["text"] == source.text
    # 모델 실패도 unknown이니 그대로 차감한다 (환급 철회 2026-09-18, 테스터12 F5)
    assert len(model.calls) == 1 and night.questions_left == 2 and not result["refunded"]
    assert next(e for e in events.rows if e.type == "harness_event").fallback_used


def test_invalid_rewrite_is_rejected_with_feedback_and_original_context():
    bad = {"question_kind": "proposition", "claim": "열리면 죽는다."}
    result, model, night, events, source = ask(bad, {"relation": "unknown"}, "열이나면 죽나?", first_attempts=[bad, interpretation()])
    assert result["status"] == "unknown" and len(model.calls) == 2 and night.questions_left == 2  # unknown도 차감
    retry = "\n".join(m.content for m in model.calls[1][0])
    assert "schema:" in retry and source.text in retry and source.observation_id in retry
    assert "열이나면 죽나?" in model.calls[1][0][0].content


def test_retry_feedback_is_opt_in_and_preserves_other_role_inputs():
    from apps.engine.app.dtos.llm_output_dto import AdvisorInterpretationOutput
    from apps.engine.app.use_cases.harness import run_with_harness
    from apps.engine.app.use_cases.game_support import system_msg
    messages = [system_msg("original")]
    provider = Stages([{}, {}, {}])
    _, report = run_with_harness(provider, messages, AdvisorInterpretationOutput, role="other")
    assert report.fallback_used and len(provider.calls) == 3
    assert all(call[0] == messages for call in provider.calls) and len(messages) == 1


def test_lookup_is_not_rewritten_into_a_known_action():
    original = "왜 배급을 남겼어?"
    result, model, _, _, _ = ask(interpretation("lookup"), {"relation": "unknown"}, original, "채연이 배급을 남겼다.")
    assert result["status"] == "unknown" and original in model.calls[0][0][0].content


def test_empty_evidence_keeps_partial_instruction_without_confirming_execution():
    result, _, _, _, source = ask(interpretation(), None, "관리자의 방송 지시가 실제로 이행됐어?", "관리자입니다. 이상한 점은 방송실로 알립니다.")
    assert result["status"] == "unknown" and result["evidence"][0]["text"] == source.text
