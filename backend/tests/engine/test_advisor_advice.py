import pytest
from types import SimpleNamespace as NS

from apps.engine.app.dtos.scenario_dto import AdvisorLeadDTO
from apps.engine.app.use_cases.advisor_advice import (
    is_why_question, verdict_prefix, polite_register_check, unbacked_confirmation_check,
    find_anchor, advice_sentence,
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
