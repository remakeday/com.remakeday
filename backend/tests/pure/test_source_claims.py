"""밤 제출문 분할 — 8칸 뭉침 제거 (사용자 실플레이 보고 2026-09-19).

증상: 9번째 문장부터 한 칸에 뭉쳐 확인 화면에 줄글로 나왔다(실제 판 4회차 마지막 칸 436자·9문장).
채점은 judge_candidates가 칸을 다시 풀어 왔으므로 점수에는 영향이 없었고, 이 수정도 점수를 바꾸지 않는다.
"""

import pytest

from apps.engine.app.use_cases.night_interactor import MAX_CLAIMS, judge_candidates, source_claims


def _sentences(n: int, *, prefix: str = "사실") -> list[str]:
    return [f"{prefix}{i}이다." for i in range(1, n + 1)]


def test_ninth_sentence_no_longer_collapses_into_one_box():
    text = " ".join(_sentences(9))
    assert source_claims(text) == _sentences(9)


@pytest.mark.parametrize("count", [1, 7, 8, 16, MAX_CLAIMS])
def test_every_sentence_keeps_its_own_box_up_to_the_limit(count):
    assert source_claims(" ".join(_sentences(count))) == _sentences(count)


def test_beyond_the_limit_the_remainder_still_gathers_in_the_last_box():
    claims = source_claims(" ".join(_sentences(MAX_CLAIMS + 3)))
    assert len(claims) == MAX_CLAIMS
    assert claims[:-1] == _sentences(MAX_CLAIMS - 1)
    assert claims[-1] == " ".join(_sentences(MAX_CLAIMS + 3)[MAX_CLAIMS - 1 :])


def test_duplicates_and_blank_lines_are_dropped_as_before():
    assert source_claims("첫 주장.\n소독약 냄새.\n\n첫 주장.") == ["첫 주장.", "소독약 냄새."]


def test_line_break_without_punctuation_is_its_own_box():
    # 마침표 없이 줄만 바꾼 문장은 예전에는 뭉친 칸에 섞여 다시 나뉘지 않았다.
    claims = source_claims("\n".join(["배급이 왔다"] + _sentences(8)))
    assert claims[0] == "배급이 왔다"
    assert len(claims) == 9


def test_scoring_candidates_are_identical_to_the_old_eight_box_behaviour():
    """점수 회귀 방지 — 옛 분할(7칸 + 뭉친 칸)과 새 분할의 채점 후보가 같아야 한다."""
    written = _sentences(16)
    old_boxes = written[:7] + [" ".join(written[7:])]  # 수정 전 source_claims 결과
    assert judge_candidates(old_boxes) == judge_candidates(source_claims(" ".join(written)))
