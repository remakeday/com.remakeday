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


def test_cell_feedback_reports_only_progress_in_cause_and_motive():
    # 정체는 아무도 묻지 않는 질문 — 밤 피드백이 이름을 꺼내지 않는다 (기획서 §4.8⑤)
    scores = {"cause": 100.0, "motive": 30.0, "side_effect": 50.0, "identity": 50.0}
    s = scoring_rules.cell_feedback(scores, include_side_effect=False)
    assert s == "원인은 잡혔다. 동기는 조금 잡혔다."
    assert "부작용" not in s and "정체" not in s


def test_cell_feedback_leaves_empty_cells_to_hint():
    scores = {"cause": 79.9, "motive": 0.0, "side_effect": 50.0, "identity": 0.0}
    s = scoring_rules.cell_feedback(scores, include_side_effect=True)
    assert s == "원인은 조금 잡혔다."  # 79.9는 아직 "조금", 빈 동기는 empty_hint_cells로


def test_cell_feedback_all_empty():
    scores = {"cause": 0.0, "motive": 0.0, "side_effect": 0.0, "identity": 100.0}
    assert scoring_rules.cell_feedback(scores, include_side_effect=True) == ""


def test_empty_hint_cells_are_cause_and_motive_only():
    scores = {"cause": 0.0, "motive": 0.0, "side_effect": 0.0, "identity": 0.0}
    assert scoring_rules.empty_hint_cells(scores) == ["cause", "motive"]
    assert scoring_rules.empty_hint_cells({**scores, "cause": 20.0}) == ["motive"]
    assert scoring_rules.empty_hint_cells({"cause": 80.0, "motive": 0.5, "identity": 0.0}) == []


# ── 인정된 내 문장 (테스터10 F1) ──


def _item(code, verdict, match, **extra):
    return {"id": code, "cell": code.split("-")[0], "text": "진실 명제 원문",
            "verdict": verdict, "matched_user_claim": match, **extra}


def test_accepted_claims_keep_player_order_and_dedupe_across_cells():
    candidates = ["트럭 소리가 났다.", "채연은 아픈 걸 숨겼다.", "우리는 사람이 아니다."]
    per_truth = [
        _item("cause-1", "confirmed", "채연은 아픈 걸 숨겼다.", matched_index=1),
        _item("identity-1", "partial", "우리는 사람이 아니다.", matched_index=2),
        _item("motive-1", "partial", "채연은 아픈 걸 숨겼다.", matched_index=1),
        _item("cause-5", "none", None),
    ]
    assert scoring_rules.accepted_claims(per_truth, candidates) == [
        "채연은 아픈 걸 숨겼다.", "우리는 사람이 아니다.",
    ]


def test_accepted_claims_never_carry_truth_text_or_unaccepted_match():
    candidates = ["채연이 아프다.", "민석이 방송실에 갔다."]
    per_truth = [
        _item("cause-1", "none", "민석이 방송실에 갔다.", matched_index=1),  # none 판정의 지목 문장은 인정이 아니다
        _item("cause-2", "confirmed", "채연이 아프다.", matched_index=0),
    ]
    out = scoring_rules.accepted_claims(per_truth, candidates)
    assert out == ["채연이 아프다."]
    assert "진실 명제 원문" not in out


def test_accepted_claims_include_ratcheted_verdict_as_current_wording():
    # 잠금은 공백·끝 문장부호만 다른 같은 문장을 인정한다 — 표시는 이번에 쓴 원문으로
    per_truth = [_item("cause-1", "confirmed", "채연이  아프다.", matched_index=0, ratcheted=True)]
    assert scoring_rules.accepted_claims(per_truth, ["채연이 아프다"]) == ["채연이 아프다"]


def test_accepted_claims_mark_only_the_matched_one_of_near_duplicates():
    # 리뷰 반영 — 정규화만 다른 두 후보 중 채점기가 하나만 지목하면 그 하나만 인정 문장이다
    candidates = ["트럭 소리가 났다", "트럭 소리가 났다.", "채연이 아프다."]
    per_truth = [_item("cause-1", "confirmed", "트럭 소리가 났다.", matched_index=1)]
    assert scoring_rules.accepted_claims(per_truth, candidates) == ["트럭 소리가 났다."]


def test_ratchet_points_at_exact_candidate_among_near_duplicates():
    prev = [{"id": "cause-1", "verdict": "confirmed", "matched_user_claim": "트럭 소리가 났다."}]
    cur = [{"id": "cause-1", "verdict": "none", "matched_user_claim": None, "matched_index": None}]
    out = scoring_rules.apply_ratchet(cur, prev, ["트럭 소리가 났다", "트럭 소리가 났다."])
    assert out[0]["matched_index"] == 1
    assert scoring_rules.accepted_claims(out, ["트럭 소리가 났다", "트럭 소리가 났다."]) == [
        "트럭 소리가 났다.",
    ]


def test_ratchet_points_at_normalized_candidate_when_no_exact_match():
    prev = [{"id": "cause-1", "verdict": "confirmed", "matched_user_claim": "채연이  아프다."}]
    cur = [{"id": "cause-1", "verdict": "none", "matched_user_claim": None, "matched_index": None}]
    out = scoring_rules.apply_ratchet(cur, prev, ["민석이 갔다.", "채연이 아프다"])
    assert out[0]["matched_index"] == 1


def test_accepted_claims_drop_match_not_in_candidates():
    # 테스터9 F11 — 이번 밤 후보가 아닌 문장(지난 기록 조각·어긋난 매칭)은 인덱스가 없어 비슷해도 빠진다
    candidates = ["검진 방송에 따르면 아픈 사람은 이송된다."]
    per_truth = [
        _item("motive-2", "confirmed", "오후 검진을 시작합니다."),
        _item("cause-3", "confirmed", "검진 방송에 따르면 아픈 사람은 이송된다고 한다."),
    ]
    assert scoring_rules.accepted_claims(per_truth, candidates) == []


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

