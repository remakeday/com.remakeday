"""RM1–3: proposition polarity, focused evidence, and trusted scene quotations."""

from tests.pure.test_real_model_grounding import model_assessment

import pytest

from tests.pure.test_real_model_grounding import FOOD, ambient, question


@pytest.mark.parametrize(("text", "claim", "relation"), [
    ("검진 결과가 공개되었어?", "검진 결과가 공개되었다.", "contradicted"),
    ("검진 결과가 공개 안 됐어?", "검진 결과가 공개 안 됐다.", "supported"),
])
def test_explicit_relation_drives_status_in_both_question_polarities(text, claim, relation):
    result, model, _ = question(model_assessment(relation, claim=claim, evidence_ids=["checkup"]), text,
                                [("checkup", "검진 결과는 공개되지 않았다.", None, "scene")])
    assert result["status"] == relation
    assert result["answer"] == ("맞다" if relation == "supported" else "틀리다")
    assert {"question_kind", "evidence", "answer"} == set(model.calls[0][1]["required"])
    assert "claim" not in model.calls[0][1]["properties"]


def test_positive_record_can_contradict_a_negative_question_without_negative_source_words():
    result, _, _ = question(model_assessment("contradicted", claim="검진 결과가 공개되지 않았다.", evidence_ids=["checkup"]),
                            "검진 결과가 공개 안 됐어?",
                            [("checkup", "검진 결과를 공개했다.", None, "scene")])
    assert result["status"] == "contradicted"


@pytest.mark.parametrize(("text", "relation"), [
    ("관리자가 방송실로 알리라고 말했어?", "supported"),
    ("관리자가 말한 대로 방송실로 보고했어?", "unknown"),
])
def test_statement_occurrence_and_execution_have_separate_relations(text, relation):
    result, _, _ = question(model_assessment('supported', evidence_ids=['broadcast']), text,
                            [("broadcast", "관리자입니다. 이상한 점은 방송실로 알립니다.", None, "statement")])
    assert result["status"] == relation
    assert result["evidence"][0]["verification"] == "reported"


def test_valid_tray_evidence_is_not_expanded_to_excluded_actor_or_general_ration_records():
    records = [*FOOD, ("instruction", "배급은 순서대로 받습니다.", None, "statement"),
               ("record", "민석이 배급 자리를 보고 기록한다.", "민석", "scene")]
    result, _, _ = question(model_assessment('unknown', evidence_ids=['public-7']),
                            "채연 말고 밥을 남긴 사람은 누구야?", records)
    assert [o["text"] for o in result["evidence"]] == [FOOD[1][1]]
    assert "채연에게" not in result["next_observation"]
    assert "방금" not in result["next_observation"]
    assert result["evidence"][0]["scene_title"] in result["next_observation"]


def test_truck_identity_never_adds_unrelated_transfer_record():
    records = [("truck", "트럭 옆면의 일부 글자를 보았다.", None, "image"),
               ("transfer", "누군가 어제 이송됐다는 말을 들었다.", None, "statement")]
    result, _, _ = question(model_assessment('unknown', evidence_ids=['truck']), "트럭의 정체는?", records)
    assert [o["text"] for o in result["evidence"]] == [records[0][1]]


def test_valid_but_unrelated_truck_id_is_removed_from_band_relationship_evidence():
    records = [("band", "준이 손목띠를 들여다본다.", "준", "scene"),
               ("term", "준이 귀표라는 말을 썼다.", "준", "statement"),
               ("truck", "트럭 옆면의 일부 글자를 보았다.", None, "image")]
    result, _, _ = question(model_assessment('unknown', evidence_ids=['band', 'term', 'truck']),
                            "손목띠와 귀표는 무슨 관계야?", records)
    assert len(result["evidence"]) == 2
    assert "트럭" not in result["detail"]
    assert "준에게" in result["next_observation"]


def test_empty_unknown_recovers_only_narrow_public_partial_evidence():
    result, _, _ = question(model_assessment('unknown', evidence_ids=[]),
                            "채연 말고 밥을 남긴 사람은 누구야?", FOOD)
    assert [o["text"] for o in result["evidence"]] == [FOOD[1][1]]


def test_unrelated_current_source_cannot_enable_authored_action_conversation():
    result, model, _, _ = ambient({"candidate_index": 0},
                                  fact="은상: 소문의 출처는 직접 확인하지 못했어. 들은 말이야.")
    assert result is None and not model.calls
