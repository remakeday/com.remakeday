"""원숭이손 소원 선택 — 순수 함수 (스펙 §3 선택).

1회차는 표의 첫 소원, 이후는 전날 밤 가장 높은 칸(가장 가까이 다가간 칸)을 겨냥한다(기획서 5.7 '유혹').
"""

# 7.1 깊이 순 — 동점이면 깊은 칸을 먼저 흔든다. 부작용 칸은 겨냥 대상이 아니다.
TARGET_DEPTH = ("identity", "motive", "cause")


def choose_wish(loop_n: int, prev_cells: dict[str, float] | None, wishes: list, used_keys: set[str]):
    """반환: 소원 또는 None(전부 소진). 이미 제안한 소원(수락·거절 무관)은 다시 내지 않는다."""
    unused = [w for w in wishes if w.key not in used_keys]
    if loop_n == 1:
        return unused[0] if unused else None
    scores = prev_cells or {}
    ranked = sorted(TARGET_DEPTH, key=lambda cell: (-scores.get(cell, 0.0), TARGET_DEPTH.index(cell)))
    return next((w for cell in ranked for w in unused if w.target_cell == cell), None)
