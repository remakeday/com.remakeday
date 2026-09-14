"""Model comparison context and guards for same-event elliptical statements."""

from tests.pure.test_real_model_grounding import model_assessment

import pytest

from tests.pure.test_real_model_grounding import question


RECORD = "채연은 담요를 끌어올린 채 자기 차례를 기다린다. 담당자가 이마를 짚고 지나간다. 결과는 공개되지 않았다."


def test_question_model_selects_evidence_before_generating_relation():
    _, model, _ = question(model_assessment('contradicted', evidence_ids=['checkup']),
                           "채연의 검진 결과가 공개되었어?", [("checkup", RECORD, "채연", "scene")])
    fields = list(model.calls[0][1]["$defs"]["AdvisorSourceAssessment"]["properties"])
    assert fields.index("quote") < fields.index("relation")


def test_elliptical_record_keeps_actor_loop_and_scene_in_model_context():
    result, model, _ = question(model_assessment('contradicted', evidence_ids=['checkup']),
                                "채연의 검진 결과가 공개되었어?", [("checkup", RECORD, "채연", "scene")])
    context = model.calls[0][0][0].content
    observation = result["evidence"][0]
    assert f"행위자: {observation['actor']}" in context
    assert f"{observation['loop_n']}회차" in context
    assert observation["scene_title"] in context
    assert RECORD in context  # Preserve the original multi-sentence source, including omitted subject.


@pytest.mark.parametrize(("text", "evidence", "polarity", "relation"), [
    ("채연의 검진 결과가 공개되었어?", "denied", "positive", "contradicted"),
    ("채연의 검진 결과가 공개되지 않았어?", "denied", "negative", "supported"),
    ("채연의 검진 결과 내용은 뭐야?", "unknown", "open", "unknown"),
    ("채연의 검진 결과가 왜 공개되지 않았어?", "unknown", "open", "unknown"),
    ("채연의 검진 결과가 다음에 공개될까?", "unknown", "positive", "unknown"),
])
def test_source_negative_does_not_override_content_reason_or_future_relation(text, evidence, polarity, relation):
    result, _, _ = question(model_assessment(relation, kind="lookup" if polarity == "open" else "proposition",
                                            claim=None if polarity == "open" else ("채연의 검진 결과가 다음에 공개된다." if "다음" in text else ("채연의 검진 결과가 공개되지 않았다." if polarity == "negative" else "채연의 검진 결과가 공개되었다.")), evidence_ids=["checkup"]), text,
                            [("checkup", RECORD, "채연", "scene")])
    assert result["status"] == relation
    assert result["evidence"][0]["text"] == RECORD
