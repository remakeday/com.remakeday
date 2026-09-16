from types import SimpleNamespace as NS

from apps.engine.app.use_cases.advisor_advice import (
    is_why_question, verdict_prefix, polite_register_check, unbacked_confirmation_check,
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
