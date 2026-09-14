"""하네스 파이프라인·격리(Advisor/Normalizer의 ScenarioPort 무의존) 테스트."""

import inspect

from pydantic import BaseModel

from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.app.ports.output.llm_port import MessageDTO
from apps.engine.app.use_cases.harness import (
    forbidden_word_check,
    lost_character_check,
    run_with_harness,
)


class Out(BaseModel):
    reply: str


_MSG = [MessageDTO(role="system", content="x")]


def test_schema_violation_regenerates_then_falls_back():
    llm = FakeLLM([{"bad": 1}, {"bad": 2}, {"bad": 3}])
    out, report = run_with_harness(llm, _MSG, Out, role="t")
    assert out is None and report.fallback_used and report.attempts == 3


def test_forbidden_word_regenerates_to_clean_output():
    llm = FakeLLM([{"reply": "나는 금칙어X를 말한다"}, {"reply": "괜찮은 말"}])
    checks = [forbidden_word_check(["금칙어X"], fields=["reply"])]
    out, report = run_with_harness(llm, _MSG, Out, role="t", fact_checks=checks)
    assert out.reply == "괜찮은 말"
    assert any("forbidden_word" in v for v in report.violations)


def test_harness_off_lets_forbidden_word_through():
    """ablation — OFF에서 누설 재현."""
    llm = FakeLLM([{"reply": "나는 금칙어X를 말한다"}])
    checks = [forbidden_word_check(["금칙어X"], fields=["reply"])]
    out, _ = run_with_harness(llm, _MSG, Out, role="t", fact_checks=checks, harness_on=False)
    assert "금칙어X" in out.reply


def test_unknown_person_check_blocks_invented_name():
    """기획서 8.6 — 없는 인물 언급은 거부·재생성 (실사례: '옆 사람은 민수야.')."""
    from apps.engine.app.use_cases.harness import unknown_person_check

    known = ["채연", "민석", "은상", "준", "충식"]
    check = unknown_person_check(known, fields=["reply"])

    assert check(Out(reply="옆 사람은 민수야.")) is not None  # 지어낸 이름 → 거부
    assert check(Out(reply="민서가 그랬어.")) is not None
    assert check(Out(reply="채연이야.")) is None  # 명부 안 이름
    assert check(Out(reply="충식이야? 걔 이송됐잖아.")) is None
    assert check(Out(reply="아니야. 몰라.")) is None  # 비인명 어휘
    assert check(Out(reply="배급 때문이야.")) is None
    assert check(Out(reply="그냥 배 안 고파서.")) is None


def test_unknown_person_regenerates_in_pipeline():
    from apps.engine.app.use_cases.harness import unknown_person_check

    llm = FakeLLM([{"reply": "옆 사람은 민수야."}, {"reply": "몰라. 못 봤어."}])
    checks = [unknown_person_check(["채연", "민석"], fields=["reply"])]
    out, report = run_with_harness(llm, _MSG, Out, role="t", fact_checks=checks)
    assert out.reply == "몰라. 못 봤어."
    assert any("unknown_person" in v for v in report.violations)


def test_korean_only_check_blocks_english_switch():
    """P2 #2 — 영어 질문에 NPC가 영어로 전환하는 응답을 거부한다."""
    from apps.engine.app.use_cases.harness import korean_only_check

    check = korean_only_check(fields=["reply"])
    # 위반: 영문 단어 2개 이상 / 한글 0
    assert check(Out(reply="The world is a shelter.")) is not None
    assert check(Out(reply="Hello")) is not None
    assert check(Out(reply="배급은 ration이야, food 같은 거.")) is not None
    # 통과: 한국어 / 짧은 감탄·고유명 1개 관용 / 빈 문자열
    assert check(Out(reply="몰라. 그냥 배 안 고파.")) is None
    assert check(Out(reply="OK 알았어.")) is None
    assert check(Out(reply="")) is None


def test_korean_only_regenerates_in_pipeline():
    from apps.engine.app.use_cases.harness import korean_only_check

    llm = FakeLLM([
        {"reply": "I will not tell you."},
        {"reply": "Sorry, I cannot say."},
        {"reply": "몰라."},
    ])
    checks = [korean_only_check(fields=["reply"])]
    out, report = run_with_harness(llm, _MSG, Out, role="t", fact_checks=checks)
    assert out.reply == "몰라."
    assert any("korean_only" in v for v in report.violations)


def test_lost_character_check():
    llm = FakeLLM([{"reply": "소실이 어디 갔지"}, {"reply": "아무 말"}])
    checks = [lost_character_check(["소실이"], fields=["reply"])]
    out, report = run_with_harness(llm, _MSG, Out, role="t", fact_checks=checks)
    assert out.reply == "아무 말"


def test_advisor_prompt_builder_has_no_scenario_dependency():
    """스토리보드 접근 경로가 코드상 존재하지 않는다 — import 검사."""
    import apps.engine.app.use_cases.intervention_interactor as m

    assert not any(
        getattr(v, "__module__", "").endswith("scenario_port")
        or getattr(v, "__module__", "").startswith("apps.scenarios")
        for v in vars(m).values()
    )
    assert "scenario" not in inspect.signature(m.InterventionInteractor.__init__).parameters


def test_temperature_forwarded_to_llm():
    """판정 롤은 temperature=0으로 요동을 줄인다 — 하네스가 포트로 전달."""
    llm = FakeLLM([{"reply": "ok"}])
    out, _ = run_with_harness(llm, _MSG, Out, role="t", temperature=0.0)
    assert out is not None
    assert llm.temperatures == [0.0]
