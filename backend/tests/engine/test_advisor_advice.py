import pytest
from types import SimpleNamespace as NS

from apps.engine.app.dtos.scenario_dto import AdvisorLeadDTO
from apps.engine.app.use_cases.advisor_advice import (
    is_why_question, verdict_prefix, polite_register_check, unbacked_confirmation_check,
    find_anchor, advice_sentence, strip_leading_verdict,
)


def test_why_question_detection():
    assert is_why_question("충식이는 왜 이송된거야?")
    assert is_why_question("이송된 이유가 뭐야")
    assert is_why_question("어떻게 아는 거야?")
    assert not is_why_question("채연이 오늘 배급을 남겼어?")


def test_verdict_prefix_by_status():
    assert verdict_prefix("supported", False) == "맞다."
    assert verdict_prefix("contradicted", False) == "아니다."
    assert verdict_prefix("unknown", False) == "그건 알 수 없다."
    assert verdict_prefix("unknown", True) == "왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다."
    assert verdict_prefix("supported", True) == "왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다."


def test_strip_leading_verdict_removes_only_the_leading_verdict_word():
    assert strip_leading_verdict("맞다. 기록은 이렇다") == "기록은 이렇다"
    assert strip_leading_verdict("아니다 틀리다") == "틀리다"
    assert strip_leading_verdict("그건 알 수 없다, 확인되지 않았다") == "확인되지 않았다"
    assert strip_leading_verdict("채연이 배급을 남겼다") == "채연이 배급을 남겼다"


def test_polite_register_is_rejected():
    assert polite_register_check(NS(answer="충식이는 기침을 많이 했다고 합니다.")) == "register: 합니다체"
    assert polite_register_check(NS(answer="충식이는 기침을 많이 했다.")) is None


def test_confirmation_without_evidence_is_rejected():
    assert unbacked_confirmation_check(NS(answer="트럭 옆면 글자를 확인했습니다.", evidence=[])) == "unbacked_confirmation"
    assert unbacked_confirmation_check(NS(answer="트럭 옆면 글자를 확인했다.", evidence=[NS(id="x")])) is None
    assert unbacked_confirmation_check(NS(answer="네 기록에는 없다.", evidence=[])) is None


def _lead(**kw):
    base = dict(key="band", loop_n=2, cues=["손목띠"], anchor_cues=["손목띠", "띠"], target="준",
                rule_action="가진 것을 보여준다")
    base.update(kw)
    return AdvisorLeadDTO(**base)


def test_lead_requires_exactly_one_of_ask_or_rule_action():
    with pytest.raises(ValueError):
        AdvisorLeadDTO(key="x", loop_n=1, cues=[], anchor_cues=["a"], target="준")
    with pytest.raises(ValueError):
        AdvisorLeadDTO(key="x", loop_n=1, cues=[], anchor_cues=["a"], target="준", ask="a", rule_action="b")


def test_find_anchor_prefers_latest_matching_observation():
    obs = [NS(text="준이 손목띠를 불빛에 비춰 본다.", actor="준", loop_n=1, scene_title="오전"),
           NS(text="채연이 쟁반을 밀어낸다.", actor="채연", loop_n=1, scene_title="정오"),
           NS(text="준이 숫자가 적힌 띠를 들여다본다.", actor="준", loop_n=2, scene_title="오전")]
    assert find_anchor(_lead(), obs) is obs[2]
    assert find_anchor(_lead(anchor_cues=["거울"]), obs) is None


def test_advice_sentence_forms():
    anchor = NS(text="준이 손목띠를 불빛에 비춰 본다.", actor="준", loop_n=1, scene_title="오전")
    assert advice_sentence(_lead(), anchor) == "네 기록의 「준이 손목띠를 불빛에 비춰 본다.」. 준: 가진 것을 보여준다 규칙을 걸어 봐라."
    ask = _lead(rule_action=None, ask="손목띠 밑에 뭐가 있는지")
    assert advice_sentence(ask, anchor) == "네 기록의 「준이 손목띠를 불빛에 비춰 본다.」. 내일 준에게 손목띠 밑에 뭐가 있는지 물어봐라."


def test_wh_question_detection():
    from apps.engine.app.use_cases.advisor_advice import is_wh_question
    assert is_wh_question('방송에서 말한 "축산 차량"은 무엇을 하는 차량인가?')
    assert is_wh_question("누가 밥을 남겼어?")
    assert is_wh_question("트럭은 언제 와?")
    assert not is_wh_question("채연이 오늘 배급을 남겼어?")
    assert not is_wh_question("채연은 언제나 배급을 남겨?")
    assert not is_wh_question("누구나 손목띠를 차?")


def test_hedged_answer_detection():
    from apps.engine.app.use_cases.advisor_advice import is_hedged
    assert is_hedged("이 기록이 실제 이송으로 이어졌는지는 알 수 없다.")
    assert is_hedged("가축 관리 체계와 연관될 가능성이 있다.")
    assert is_hedged("아직 확인되지 않았다.")
    # 2026-09-18 스모크(gemma4:12b) — "맞다." 뒤 본문이 "…가는지는 확실치 않다."로 끝난 사례
    assert is_hedged("따라서 모든 이름이 방송실로 가는지는 확실치 않다.")
    assert is_hedged("트럭이 그 이동 수단인지는 확실하지 않다.")
    assert not is_hedged("채연은 쟁반을 반쯤 남기고 옆으로 밀었다.")


def test_settle_status_downgrades_hedged_or_wh_decisions():
    from apps.engine.app.use_cases.advisor_advice import settle_status
    hedged = "트럭의 방문이 비어 있는 자리와 관련될 가능성이 있다."
    assert settle_status("supported", "비어 있는 자리가 생기는가?", hedged, lookup=False) == "unknown"
    assert settle_status("contradicted", "채연이 쟁반을 밀어냈어?", "그런지는 알 수 없다.", lookup=False) == "unknown"
    assert settle_status("supported", "채연이 배급을 남겼어?", "채연은 쟁반을 남겼다.", lookup=False) == "supported"
    assert settle_status("contradicted", "채연이 쟁반을 밀어냈어?", "채연은 그대로 두었다.", lookup=False) == "contradicted"
    assert settle_status("contradicted", "채연이 쟁반을 밀어냈어?", "채연은 그대로 두었다.", lookup=True) == "unknown"
    assert settle_status("contradicted", "채연은 언제 쟁반을 밀어냈어?", "채연은 그대로 두었다.", lookup=False) == "unknown"
    assert settle_status("supported", "누가 밥을 남겼어?", "채연이 남겼다.", lookup=True) == "supported"


def test_wh_question_supported_has_no_yes_no_verdict():
    assert verdict_prefix("supported", False, wh=True) == ""
    assert verdict_prefix("unknown", False, wh=True) == "그건 알 수 없다."
    assert verdict_prefix("supported", True, wh=True) == "왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다."


# 순서표 5번 — 안내 질문 분류(규칙 표), 공개 사다리 단계
NAMES = ["채연", "민석", "은상", "준"]


@pytest.mark.parametrize("question, kind", [
    ("이 게임이 뭔지 이해가 안되 목적이뭐야?", "purpose"),
    ("목적이 뭐야", "purpose"),
    ("세상이 멸망한다는게 뭔소린가", "purpose"),
    ("세상이 멸망한다는 게 뭔 소리야", "purpose"),
    ("뭘 해야 돼", "purpose"),
    ("그럼 나는 뭘 해야 해?", "purpose"),
    ("뭘 해야 돼요?", "purpose"),  # opus 리뷰 I1 — 끝을 좁혀도 짧은 어미는 안내로 남는다
    ("뭘 해야 하는 거야?", "purpose"),
    ("왜 너에게 질문해야 해?", "usage"),
    ("어떻게 질문해?", "usage"),
    ("질문하는 법 알려줘", "usage"),
    ("이 게임 기준이 뭐야?", "purpose"),  # "기준"의 준은 인물 이름이 아니다
])
def test_guide_question_is_classified_by_keyword_table(question, kind):
    from apps.engine.app.use_cases.advisor_advice import guide_kind
    assert guide_kind(question, NAMES) == kind


@pytest.mark.parametrize("question", [
    "관리자의 목적이 뭐야?",
    "채연은 뭘 해야 돼?",
    "왜 멸망해?",
    "트럭이 오면 멸망한다는 거야?",
    "민석의 목적이 뭐야",
    "채연이 오늘 배급을 남겼어?",
    "뭐가 궁금한건가?",
])
def test_world_question_is_not_a_guide_question(question):
    from apps.engine.app.use_cases.advisor_advice import guide_kind
    assert guide_kind(question, NAMES) is None


@pytest.mark.parametrize("question", [
    "뭘 하면 이송돼?",
    "뭘 해야 검진을 통과해?",
    "무엇을 하면 구역이 폐쇄돼?",
    "뭐 하면 멸망을 막아?",
    "너한테 물어봐도 돼? 트럭 언제 와",
])
def test_question_with_a_world_goal_or_a_follow_up_is_not_a_guide_question(question):
    """opus 리뷰 I1 — "해야/하면" 뒤에 세계 사건이 오거나, 사용법 말 뒤에 다른 질문이 붙으면 판정 질문이다."""
    from apps.engine.app.use_cases.advisor_advice import guide_kind
    assert guide_kind(question, NAMES) is None


@pytest.mark.parametrize("question", [
    "게임 준비 어떻게 해?",
    "이 게임 준비물이 뭐야?",
    "게임 규칙은 준수해야 해?",
    "이 게임 수준이 뭐야?",
])
def test_word_starting_or_ending_with_a_name_is_not_that_person(question):
    """리뷰 반영 — 준비·준수·기준·수준의 "준"은 인물 이름이 아니다 (이름 뒤 경계)."""
    from apps.engine.app.use_cases.advisor_advice import guide_kind
    assert guide_kind(question, NAMES) == "purpose"


@pytest.mark.parametrize("question", [
    "준한테 물어봐도 돼?",
    "준이 뭐 했어?",
    "준이 게임 얘기를 했어?",
    "준한테 게임 규칙을 물어봐도 돼?",
    "준아, 게임이 뭐야?",
    "준은 게임을 알아?",
    "준의 게임이 뭐야?",
    "준이가 게임이라고 했어?",
    "게임 얘기는 준",
    "채연이랑 게임 얘기했어?",
])
def test_name_followed_by_a_particle_is_that_person(question):
    from apps.engine.app.use_cases.advisor_advice import guide_kind
    assert guide_kind(question, NAMES) is None


def test_guide_answers_stay_within_cause_and_motive():
    from apps.engine.app.use_cases.advisor_advice import GUIDE_ANSWERS
    for answer in GUIDE_ANSWERS.values():
        assert not any(word in answer for word in ("정체", "부작용", "돼지", "사람이 아니", "점수", "%"))
        assert not polite_register_check(NS(answer=answer))


@pytest.mark.parametrize("loop_n, best_total, stage", [
    (1, 0.0, 1), (2, 0.0, 2), (4, 10.0, 4),
    (1, 25.0, 2), (1, 50.0, 3), (1, 75.0, 4), (2, 30.0, 2), (2, 60.0, 3),
])
def test_ladder_stage_is_loop_floor_raised_one_rung_per_25_points(loop_n, best_total, stage):
    from apps.engine.app.use_cases.advisor_advice import ladder_stage
    assert ladder_stage(loop_n, best_total) == stage


def test_open_rungs_needs_both_stage_and_cue_and_prefers_higher_stage():
    from apps.engine.app.dtos.scenario_dto import AdvisorRungDTO
    from apps.engine.app.use_cases.advisor_advice import open_rungs
    low = AdvisorRungDTO(key="low", stage=1, cues=["검진"], text="검진 사실.")
    high = AdvisorRungDTO(key="high", stage=3, cues=["검진", "방송실"], text="검진 뒤 사실.")
    other = AdvisorRungDTO(key="other", stage=1, cues=["트럭"], text="트럭 사실.")
    ladder = [low, high, other]
    assert open_rungs(ladder, 1, "검진 때 뭐 했어?") == [low]
    assert open_rungs(ladder, 3, "검진 때 뭐 했어?") == [high, low]
    assert open_rungs(ladder, 4, "배급은 어디서 와?") == []
