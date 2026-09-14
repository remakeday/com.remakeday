"""쿠키 선택·원숭이손 출현 조건 — 순수 함수 (작업지시서 §P5·P4)."""

from apps.engine.domain.value_objects.game_constants import (
    COOKIE_TIE_ORDER,
    PASS_THRESHOLD,
    PAW_MAX_PER_ATTEMPT,
    PAW_MIN_YESTERDAY,
)


def paw_should_offer(loop_n: int, yesterday_score: float | None, offered_so_far: int) -> bool:
    """1회차 무조건, 이후 전날 ≥40% 시 1회, 판당 최대 2."""
    if offered_so_far >= PAW_MAX_PER_ATTEMPT:
        return False
    if loop_n == 1:
        return True
    return yesterday_score is not None and yesterday_score >= PAW_MIN_YESTERDAY


def _level_for(score: float) -> int:
    if score >= 85.0:
        return 3
    if score >= 65.0:
        return 2
    return 1


def select_cookie(
    cell_scores: dict[str, float],
    total: float,
    seen_text_ids: list[str],
    available: list[dict],  # {text_id, cell, level}
) -> str | None:
    """반환: text_id 또는 None.

    50%↑만 / 가장 낮은 칸(동점 시 원인→동기→부작용→정체) / 강도 = 점수 구간 기본
    + 이미 본 칸이면 +1(상한 3) / 정체 칸은 나머지 세 칸이 모두 채워진 뒤에만 / 12개 소진 시 없음.
    """
    if total < PASS_THRESHOLD:
        return None
    unseen = [c for c in available if c["text_id"] not in seen_text_ids]
    if not unseen:
        return None

    ordered = sorted(
        COOKIE_TIE_ORDER, key=lambda c: (cell_scores.get(c, 0.0), COOKIE_TIE_ORDER.index(c))
    )
    others_full = all(cell_scores.get(c, 0.0) >= 100.0 for c in COOKIE_TIE_ORDER if c != "identity")

    for cell in ordered:
        if cell == "identity" and not others_full:
            continue
        seen_cells = {c["cell"] for c in available if c["text_id"] in seen_text_ids}
        level = _level_for(cell_scores.get(cell, 0.0))
        if cell in seen_cells:
            level = min(3, level + 1)
        candidates = [c for c in unseen if c["cell"] == cell]
        if not candidates:
            continue
        exact = [c for c in candidates if c["level"] == level]
        pick = exact or sorted(candidates, key=lambda c: abs(c["level"] - level))
        return pick[0]["text_id"]
    return None


def ab_assign(session_key: str) -> bool:
    """세션 해시 50:50 A/B 배정 (COOKIE_AB·PAW_REASON_AB 공용)."""
    return sum(session_key.encode()) % 2 == 0
