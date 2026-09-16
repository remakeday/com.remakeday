"""직접 쓰기 실패 시 대안 제시 — 설명한다 고정 스냅 탈피 (개선 2단계 임무 B)."""

from apps.engine.app.use_cases.intervention_interactor import suggest_alternatives
from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION

TEMPLATES = [
    {"target": "채연", "when_beat": 4, "effect": "enforce", "action": "검진을 받는다",
     "label": "채연: 검진을 받는다"},
    {"target": "채연", "when_beat": 1, "effect": "enforce", "action": "배급을 남긴다",
     "label": "채연: 배급을 남긴다"},
    {"target": "채연", "when_beat": 1, "effect": "enforce", "action": EXPLAIN_ACTION,
     "label": f"채연: {EXPLAIN_ACTION}"},
    {"target": "준", "when_beat": 6, "effect": "enforce", "action": "밤에 깨어 있는다",
     "label": "준: 밤에 깨어 있는다"},
]


def test_token_overlap_ranks_relevant_action_first():
    alts = suggest_alternatives("채연이 검진을 꼭 받게 해줘", ["채연"], TEMPLATES)
    assert alts[0] == "채연은 검진을 받는다"


def test_returns_at_most_three_and_only_named_targets():
    alts = suggest_alternatives("채연이 뭐든 하게 해", ["채연"], TEMPLATES)
    assert 1 <= len(alts) <= 3
    assert all(a.startswith("채연은") for a in alts)


def test_other_targets_actions_are_offered_for_their_own_name():
    alts = suggest_alternatives("준이 밤에 안 자고 뭘 보게 해", ["준"], TEMPLATES)
    assert alts[0] == "준은 밤에 깨어 있는다"


def test_without_templates_falls_back_to_explain():
    alts = suggest_alternatives("채연이 춤추게 해", ["채연"], [])
    assert alts == [f"채연은 {EXPLAIN_ACTION}"]
