"""ScenarioPort 계약 테스트 — example·a·audit 모두 같은 계약을 통과해야 한다."""

import pytest

from apps.scenarios.scenario_a.adapter import build as build_a
from apps.scenarios.scenario_audit.adapter import build as build_audit
from apps.scenarios.scenario_example.adapter import build as build_example

_CELLS = {"cause", "motive", "side_effect", "identity"}


@pytest.fixture(params=["example", "a", "audit"])
def scenario(request):
    return {"example": build_example, "a": build_a, "audit": build_audit}[
        request.param
    ]()


def test_name_matches(scenario):
    assert scenario.name() in ("example", "a", "audit")
    assert scenario.bundle().name == scenario.name()


def test_has_characters(scenario):
    chars = scenario.characters()
    assert len(chars) >= 3
    assert len({c.code for c in chars}) == len(chars)


def test_has_6_beats_in_order(scenario):
    beats = scenario.beats()
    assert [b.n for b in beats] == [1, 2, 3, 4, 5, 6]


def test_truth_claims_have_valid_cells(scenario):
    claims = scenario.truth_claims()
    assert claims
    assert {c.cell for c in claims} <= _CELLS
    assert len({c.code for c in claims}) == len(claims)


def test_cookies_have_valid_cell_and_level(scenario):
    cookies = scenario.cookie_texts()
    assert cookies
    for k in cookies:
        assert k.cell in _CELLS
        assert k.level in (1, 2, 3)
    assert len({k.text_id for k in cookies}) == len(cookies)


def test_forbidden_words_not_empty(scenario):
    assert scenario.forbidden_words()


def test_prompt_fragment_unknown_role_is_empty(scenario):
    assert scenario.prompt_fragment("npc") != "" or scenario.name() == "example"
    assert scenario.prompt_fragment("no-such-role") == ""


def test_scenario_a_full_seed():
    a = build_a()
    assert len(a.cookie_texts()) == 12
    assert len(a.forbidden_words()) == 10
    assert any(c.lost for c in a.characters())
    for role in ("npc", "advisor", "normalizer", "manager", "evaluator"):
        assert a.prompt_fragment(role)
