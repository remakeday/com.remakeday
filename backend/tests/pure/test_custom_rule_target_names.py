"""Real-model probe regression: verb endings must not become a second target."""

from types import SimpleNamespace as NS
from uuid import uuid4

import pytest

from apps.engine.app.use_cases.intervention_interactor import InterventionInteractor
from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_review_failure_boundaries import Events


def preview(text):
    bundle = build().bundle()
    loop = NS(attempt_id=uuid4(), loop_n=2, state="intervention")
    night = NS(id=uuid4(), loop_id=uuid4())
    inter = InterventionInteractor(
        attempts=None, loops=NS(get=lambda _: loop), notes=None, rules=NS(list=lambda _: []),
        nights=NS(get=lambda _: night), event_log=Events(), core_llm=None,
        action_vocab=bundle.action_vocab, target_names=[c.name for c in bundle.characters if c.playable],
        harness_on=True, rule_cls=None,
    )
    return inter.preview_rule(night.id, text)


def test_exact_probe_truth_request_keeps_its_actual_target_and_knowledge_limit():
    original = "은상은 소문의 진실을 무조건 나에게 이야기 해준다."
    assert original.index("준") == 25  # The confirmed probe's false second-name position.
    result = preview(original)
    assert result["original_text"] == original
    assert result["rule"] is None and not result["executable"]
    assert result["alternatives"] == [f"은상은 {EXPLAIN_ACTION}"]
    assert result["limitations"] == ["모르는 사실까지 알게 하거나 모든 질문에 답하게 할 수는 없다."]


@pytest.mark.parametrize("ending", ["해준다", "알려준다", "보여준다"])
@pytest.mark.parametrize("name", ["은상", "민석"])
def test_verb_endings_never_introduce_a_second_person_in_alternatives(name, ending):
    result = preview(f"{name}은 아는 일을 {ending}.")
    assert result["alternatives"] == [f"{name}은 {EXPLAIN_ACTION}"]
    assert "그런 사람은 여기 없다" not in result["limitations"]


@pytest.mark.parametrize("subject", ["준은", "준이", "준"])
def test_real_named_subject_remains_executable(subject):
    result = preview(f"{subject} {EXPLAIN_ACTION}")
    assert result["executable"] and result["rule"]["target"] == "준"


def test_question_word_control_has_no_name_collision_and_preserves_one_alternative():
    original = "민석이 내 질문에 자세하게 답할 수 있도록 한다."
    assert "준" not in original
    result = preview(original)
    assert result["alternatives"] == [f"민석은 {EXPLAIN_ACTION}"]
    assert "그런 사람은 여기 없다" not in result["limitations"]


def test_two_actual_named_people_are_not_silently_reduced_to_one_target():
    result = preview(f"은상은 준에게 {EXPLAIN_ACTION}")
    assert not result["executable"]
    assert result["alternatives"] == [f"은상은 {EXPLAIN_ACTION}", f"준은 {EXPLAIN_ACTION}"]
