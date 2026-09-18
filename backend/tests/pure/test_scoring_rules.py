"""scoring_rules 순수 함수 — 인용문으로 matched_index 보정."""

import pytest

from apps.engine.domain.entities.scoring_rules import resolve_matched_index

_CANDS = [
    "채연은 열이 나고 밥이 넘어가지 않는데도 괜찮은 척하며 배급을 남긴다.",
    "검진 때도 담요를 끌어올린 채 기다리며 몸 상태를 드러내지 않는다.",
    "검진 방송에 따르면 상태가 좋지 않은 사람은 별도 구역으로 이송된다.",
]


@pytest.mark.parametrize(("quote", "index", "expected"), [
    ("별도 구역으로 이송된다", 1, 2),          # 유일 적중 — 어긋난 번호를 덮어쓴다
    ("별도 구역으로 이송된다", 2, 2),          # 유일 적중 — 번호와 일치
    (None, 1, 1),                              # 인용 없음 → 번호 그대로
    ("검진", 1, 1),                            # 4자 미만 → 번호 그대로
    ("돼지가 출하된다", 1, 1),                 # 어느 후보에도 없음 → 번호 그대로
    ("검진 때도 담요", 0, 1),                  # 유일 적중(후보 1)
    ("몸 상태를", 0, 1),                       # 유일 적중 — 짧지만 4자 이상
    ("별도구역으로  이송된다", 1, 2),          # 인용 쪽 공백 차이 무시
    ("별도 구역으로 이송된다", None, 2),       # 번호 없음 + 유일 적중 → 그 번호
    (None, None, None),
])
def test_resolve_matched_index(quote, index, expected):
    assert resolve_matched_index(_CANDS, quote, index) == expected


def test_quote_in_two_candidates_keeps_index():
    cands = ["채연이 아픈 것 같다", "채연이 아픈 것을 숨겼다", "민석이 방송실 갔다"]
    assert resolve_matched_index(cands, "채연이 아픈 것", 2) == 2
    assert resolve_matched_index(cands, "채연이 아픈 것", None) is None


def test_candidate_whitespace_differences_still_match():
    cands = ["검진  방송에\n따르면 별도 구역으로 이송된다."]
    assert resolve_matched_index(cands, "방송에 따르면 별도", None) == 0


_C = ["채연은 열이 나고 배급을 남긴다.", "검진 때도 담요를 끌어올린 채 기다린다.", "검진 방송에 따르면 상태가 좋지 않은 사람은 별도 구역으로 이송된다."]


@pytest.mark.parametrize("quote", [
    '"별도 구역으로 이송된다"', "「별도 구역으로 이송된다」", "'별도 구역으로 이송된다.'",
    "2. 검진 방송에 따르면 상태가 좋지 않은 사람은 별도 구역으로 이송된다.",
    "“별도 구역으로 이송된다”",
])
def test_quote_marks_and_list_prefix_are_ignored(quote):
    assert resolve_matched_index(_C, quote, 1) == 2
