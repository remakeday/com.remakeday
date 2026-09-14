"""Whole-claim entailment preserves negation without a second polarity inversion."""

import pytest

from tests.pure.test_real_model_grounding import model_assessment, question


@pytest.mark.parametrize(("fact", "text", "claim", "relation"), [
    ("채연의 검진 결과는 공개되지 않았다.", "채연의 검진 결과가 공개되었어?", "채연의 검진 결과가 공개되었다.", "contradicted"),
    ("채연의 검진 결과는 공개되지 않았다.", "채연의 검진 결과가 공개되지 않았어?", "채연의 검진 결과가 공개되지 않았다.", "supported"),
    ("채연의 검진 결과를 공개했다.", "채연의 검진 결과가 공개되었어?", "채연의 검진 결과가 공개되었다.", "supported"),
    ("채연의 검진 결과를 공개했다.", "채연의 검진 결과가 공개되지 않았어?", "채연의 검진 결과가 공개되지 않았다.", "contradicted"),
])
def test_direct_relation_for_both_complete_claims_and_opposite_sources(fact, text, claim, relation):
    result, model, _ = question(model_assessment(relation, claim=claim, evidence_ids=["checkup"]), text,
                                [("checkup", fact, "채연", "scene")])
    assert result["status"] == relation
    assert text in model.calls[0][0][0].content
    assert set(model.calls[0][1]["properties"]) == {"question_kind", "evidence", "answer"}


@pytest.mark.parametrize("claim", ["채연의 검진 결과가 공개되었다.", "채연의 검진 결과가 공개되지 않았다."])
def test_unknown_is_not_inverted_for_a_negative_claim(claim):
    result, _, _ = question(model_assessment("unknown", claim=claim, evidence_ids=["checkup"]), claim[:-1] + "?",
                            [("checkup", "채연이 검진을 받았다.", "채연", "scene")])
    assert result["status"] == "unknown"


@pytest.mark.parametrize(("text", "claim", "kind", "relation"), [
    ("누가 배급을 남기는 모습을 봤어?", None, "lookup", "supported"),
    ("왜 배급을 남겼어?", None, "lookup", "unknown"),
    ("채연의 검진 결과 내용은 뭐야?", None, "lookup", "unknown"),
    ("채연의 검진 결과가 다음에는 공개될까?", "다음에 채연의 검진 결과를 공개한다.", "proposition", "unknown"),
    ("채연의 검진 결과에 이상이 있으면 돌아와?", "이상이 있으면 채연이 돌아온다.", "proposition", "unknown"),
])
def test_lookup_and_scope_preserve_requested_information(text, claim, kind, relation):
    fact = "채연이 배급을 남겼다. 검진 결과는 공개되지 않았다."
    result, _, _ = question(model_assessment(relation, claim=claim, kind=kind, evidence_ids=["checkup"]), text,
                            [("checkup", fact, "채연", "scene")])
    assert result["status"] == relation and result["evidence"][0]["text"] == fact


def test_explicit_public_reason_can_answer_why():
    fact = "채연은 배가 부르기 때문에 배급을 남겼다."
    result, _, _ = question(model_assessment("supported", kind="lookup", evidence_ids=["checkup"]),
                            "왜 배급을 남겼어?", [("checkup", fact, "채연", "scene")])
    assert result["status"] == "supported" and result["detail"] == fact


def test_contradicted_lookup_is_not_a_direct_answer():
    result, _, _ = question(model_assessment("contradicted", kind="lookup", evidence_ids=["checkup"]),
                            "누가 배급을 남겼어?", [("checkup", "민석은 배급을 남기지 않았다.", "민석", "scene")])
    assert result["status"] == "unknown"


def test_first_stage_has_no_claim_to_omit_or_rewrite():
    result, model, _ = question(model_assessment("supported", claim=None, evidence_ids=["checkup"]),
                            "검진 결과가 공개되지 않았어?", [("checkup", "검진 결과는 공개되지 않았다.", None, "scene")])
    assert result["status"] == "supported"
    assert set(model.calls[0][1]["properties"]) == {"question_kind", "evidence", "answer"}


def test_subordinate_negation_and_main_predicate_are_preserved():
    fact = "민석이 채연이 배급을 남기지 않는 모습을 봤다."
    result, model, events = question(model_assessment("supported", claim=fact, evidence_ids=["checkup"]),
                                   "민석이 채연이 배급을 남기지 않는 모습을 봤어?", [("checkup", fact, "민석", "scene")])
    assert result["status"] == "supported" and "민석이 채연이 배급을 남기지 않는 모습을 봤어?" in model.calls[0][0][0].content
    assert "claim" not in next(e for e in events.rows if e.type == "harness_event").call_records[0]["output"]


@pytest.mark.parametrize(("text", "expected"), [
    ("관리자가 방송실로 알리라고 말했어?", "supported"),
    ("실제로 방송실로 보고했어?", "unknown"),
])
def test_reported_truth_guard_still_applies_after_direct_relation(text, expected):
    result, _, _ = question(model_assessment("supported", evidence_ids=["checkup"]), text,
                            [("checkup", "관리자입니다. 이상한 점은 방송실로 알립니다.", None, "statement")])
    assert result["status"] == expected
