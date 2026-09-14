"""P2·P3·P5 도메인 — 채점·멸망·규칙 충돌·쿠키·원숭이손 (LLM 없이)."""

from apps.engine.domain.entities import scoring_rules
from apps.engine.domain.entities.cookie_rules import paw_should_offer, select_cookie
from apps.engine.domain.entities.rule_rules import Rule, find_conflicts

# ── 채점 ──


def test_cell_score_80_percent_is_full():
    assert scoring_rules.cell_score(["confirmed"] * 4 + ["partial"]) == 100.0  # 0.9
    assert scoring_rules.cell_score(["confirmed", "confirmed", "confirmed", "none", "none"]) == 75.0
    assert scoring_rules.cell_score(["none"]) == 0.0
    assert scoring_rules.cell_score([]) == 0.0


def test_total_uses_situation_and_identity_weights():
    cells = {"cause": 100.0, "motive": 50.0, "side_effect": 0.0, "identity": 0.0}
    assert scoring_rules.total_score(cells, include_side_effect=False) == 52.5
    assert scoring_rules.total_score(cells, include_side_effect=True) == 52.5


def test_pass_threshold_50():
    assert scoring_rules.passed(50.0) and not scoring_rules.passed(49.9)


# ── 정성 칸 피드백 (REMAKE DAY #5) ──


def test_cell_feedback_three_levels_without_side_effect():
    scores = {"cause": 100.0, "motive": 30.0, "side_effect": 50.0, "identity": 0.0}
    s = scoring_rules.cell_feedback(scores, include_side_effect=False)
    assert s == "원인은 잡혔다. 동기는 조금 잡혔다. 정체는 비어 있다."
    assert "부작용" not in s


def test_cell_feedback_ignores_legacy_side_effect_option():
    scores = {"cause": 80.0, "motive": 0.0, "side_effect": 50.0, "identity": 79.9}
    s = scoring_rules.cell_feedback(scores, include_side_effect=True)
    assert "원인은 잡혔다." in s  # 80 경계는 만점 취급
    assert "동기는 비어 있다." in s
    assert "부작용" not in s
    assert "정체는 조금 잡혔다." in s  # 79.9는 아직 "조금"


def test_cell_feedback_all_empty():
    scores = {"cause": 0.0, "motive": 0.0, "side_effect": 0.0, "identity": 0.0}
    s = scoring_rules.cell_feedback(scores, include_side_effect=True)
    assert s == "원인은 비어 있다. 동기는 비어 있다. 정체는 비어 있다."


def test_world_outcome():
    assert scoring_rules.world_outcome(3, 0) == "closure"
    assert scoring_rules.world_outcome(0, 3) == "quiet"
    assert scoring_rules.world_outcome(1, 0) == "truck"


def test_closed_by():
    assert scoring_rules.closed_by(100.0, identity_word_confirmed=True) == "understood_all"
    assert scoring_rules.closed_by(100.0, identity_word_confirmed=False) == "understood"
    assert scoring_rules.closed_by(60.0, identity_word_confirmed=False) == "clear"
    assert scoring_rules.closed_by(40.0, identity_word_confirmed=False) == "doom"


# ── 규칙 충돌 ──


def _rule(rid, target, beat, effect, action="행동"):
    return Rule(rid, "user_choice", target, beat, effect, action, 1)


def test_conflict_same_target_beat_opposite_effect():
    existing = [_rule("R1", "A", 2, "suppress")]
    assert find_conflicts(existing, _rule("R2", "A", 2, "enforce"))
    assert find_conflicts(existing, _rule("R2", "A", None, "enforce"))  # any는 겹친다
    assert not find_conflicts(existing, _rule("R2", "A", 3, "enforce"))
    assert not find_conflicts(existing, _rule("R2", "B", 2, "enforce"))
    assert not find_conflicts(existing, _rule("R2", "A", 2, "suppress"))  # 같은 효과


# ── 원숭이손 ──


def test_paw_conditions():
    assert paw_should_offer(1, None, 0)  # 1회차 무조건
    assert not paw_should_offer(2, 39.0, 1)  # 39% → 없음
    assert paw_should_offer(2, 40.0, 1)  # 40% → 1회
    assert not paw_should_offer(3, 90.0, 2)  # 판당 최대 2


# ── 쿠키 ──

_AVAILABLE = [
    {"text_id": f"ck-{cell}-{lv}", "cell": cell, "level": lv}
    for cell in ("cause", "motive", "side_effect", "identity")
    for lv in (1, 2, 3)
]


def test_cookie_below_50_none():
    assert select_cookie({"cause": 10.0}, 40.0, [], _AVAILABLE) is None


def test_cookie_lowest_cell_tie_order():
    cells = {"cause": 60.0, "motive": 60.0, "side_effect": 80.0, "identity": 0.0}
    # identity가 최저지만 나머지 셋이 만점이 아니므로 제외 → 동점(cause·motive) 중 cause
    assert select_cookie(cells, 55.0, [], _AVAILABLE) == "ck-cause-1"


def test_cookie_level_by_score_band():
    cells = {"cause": 70.0, "motive": 100.0, "side_effect": 100.0, "identity": 100.0}
    assert select_cookie(cells, 90.0, [], _AVAILABLE) == "ck-cause-2"


def test_cookie_seen_cell_bumps_level():
    cells = {"cause": 70.0, "motive": 100.0, "side_effect": 100.0, "identity": 100.0}
    assert select_cookie(cells, 90.0, ["ck-cause-2"], _AVAILABLE) == "ck-cause-3"


def test_identity_cookie_needs_other_cells_full():
    cells = {"cause": 100.0, "motive": 100.0, "side_effect": 100.0, "identity": 60.0}
    assert select_cookie(cells, 90.0, [], _AVAILABLE) == "ck-identity-1"
    cells2 = {"cause": 100.0, "motive": 90.0, "side_effect": 100.0, "identity": 60.0}
    picked = select_cookie(cells2, 87.0, [], _AVAILABLE)
    assert picked is not None and not picked.startswith("ck-identity")


def test_cookie_all_12_seen_none():
    seen = [c["text_id"] for c in _AVAILABLE]
    assert select_cookie({"cause": 60.0}, 60.0, seen, _AVAILABLE) is None

