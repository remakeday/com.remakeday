"""테스터10 F3 — 직접 쓴 규칙의 거부 사유·부정 활용형·행동 활용형·금지형 대안 (유한 문법, LLM 해석 없음)."""

from types import SimpleNamespace as NS
from uuid import uuid4

import pytest

from apps.engine.app.use_cases.intervention_interactor import InterventionInteractor
from apps.engine.dependencies.engine_dependency import rule_templates
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_review_failure_boundaries import Events


def preview(text):
    bundle = build().bundle()
    loop = NS(attempt_id=uuid4(), loop_n=1, state="intervention")
    night = NS(id=uuid4(), loop_id=uuid4())
    inter = InterventionInteractor(
        attempts=None, loops=NS(get=lambda _: loop), notes=None, rules=NS(list=lambda _: []),
        nights=NS(get=lambda _: night), event_log=Events(), core_llm=None,
        action_vocab=bundle.action_vocab, target_names=[c.name for c in bundle.characters if c.playable],
        harness_on=True, rule_cls=None, rule_templates=rule_templates(bundle),
    )
    return inter.preview_rule(night.id, text)


def reason(text):
    return " ".join(preview(text)["limitations"])


# ── 테스터10 F3 표 5건 재현 ──

@pytest.mark.parametrize("text", [
    "서로의 역할을 무조건 말하기",
    "서로 무엇을 하고있는지 어떤 목적을 가지고있는지 설명하기",
])
def test_f3_group_rule_is_rejected_as_group_not_as_missing_person(text):
    result = preview(text)
    assert not result["executable"]
    assert "그런 사람은 여기 없다" not in result["limitations"]
    assert "한 사람에게만" in reason(text) and "'서로'" in reason(text)


def test_f3_unknown_action_names_the_cause_and_usable_actions_and_offers_prohibitions():
    result = preview("은상이는 귓속말 금지")
    assert not result["executable"]
    text = reason("은상이는 귓속말 금지")
    assert "행동 목록에 없다" in text and "소문을 낸다" in text
    assert result["alternatives"] and all(a.startswith("은상은 ") and a.endswith(" 금지") for a in result["alternatives"])
    assert preview(result["alternatives"][0])["rule"]["effect"] == "suppress"  # 대안을 누르면 그대로 금지 규칙이 된다


@pytest.mark.parametrize("text", ["민석이는 기록하기를 안한다.", "민석은 기록하는걸 포기한다."])
def test_f3_inflected_prohibitions_are_executable(text):
    rule = preview(text)["rule"]
    assert (rule["target"], rule["action"], rule["effect"]) == ("민석", "기록한다", "suppress")


# ── 부정 활용형 인식 (과잉 인식 방지 포함) ──

@pytest.mark.parametrize("text, effect", [
    ("민석은 기록을 안 한다", "suppress"),
    ("민석은 기록 안 하기", "suppress"),
    ("민석은 기록하지 않는다", "suppress"),
    ("민석이 기록하지 못하게", "suppress"),
    ("민석은 기록을 하지 못하게", "suppress"),
    ("은상이 소문을 내지 못하게", "suppress"),
    ("은상은 소문 내기 금지", "suppress"),
    ("민석은 기록을 포기한다", "suppress"),
    ("민석은 기록한다 금지", "suppress"),
    ("민석은 기록한다", "enforce"),
    ("민석은 기록하기", "enforce"),
    ("은상은 소문을 낸다 강제", "enforce"),
    ("민석은 기록 안 하기 금지", None),  # 부정 두 번 — 뜻을 정하지 않는다
    ("민석은 기록 안 하면 안 된다", None),
    ("민석은 기록하지 않게 하지 마", None),
    ("민석은 안 기록하는 척한다", None),
])
def test_negation_table(text, effect):
    rule = preview(text)["rule"]
    assert (rule["effect"] if rule else None) == effect


def test_double_negation_reason_is_explicit():
    assert "하나만" in reason("민석은 기록 안 하기 금지")


# ── 행동 활용형 매칭 (오매칭 방지 포함) ──

@pytest.mark.parametrize("text, target, action", [
    ("민석은 기록하는 걸 금지", "민석", "기록한다"),
    ("은상은 소문 내기", "은상", "소문을 낸다"),
    ("민석은 방송실에 가기", "민석", "방송실에 간다"),
    ("준은 밤에 깨어 있기", "준", "밤에 깨어 있는다"),
    ("준은 가진 것을 보여주기", "준", "가진 것을 보여준다"),
    ("은상은 들은 것을 그대로 전하기", "은상", "들은 것을 그대로 전한다"),
    ("은상은 따라가기", "은상", "따라간다"),
    ("채연은 검진 받기", "채연", "검진을 받는다"),
    ("채연은 배급을 남기지 않는다", "채연", "배급을 남긴다"),
    ("은상은 알고 있는 관찰을 설명한다", "은상", "알고 있는 관찰을 설명한다"),
])
def test_inflected_action_table(text, target, action):
    rule = preview(text)["rule"]
    assert rule and (rule["target"], rule["action"]) == (target, action)


@pytest.mark.parametrize("text", [
    "민석은 기록장을 본다",
    "민석은 기록한 것을 말한다",
    "채연은 배급을 남기고 다 먹는다",
    "민석은 방송실에 가는 사람을 기록한다",
    "준은 혼자 있는 채연에게 말을 건다",
    "민석은 기록하려다 만다",
])
def test_inflection_does_not_invent_a_rule(text):
    assert preview(text)["rule"] is None


# ── 원인별 거부 문구 ──

@pytest.mark.parametrize("text, expected", [
    ("모두 설명하기", "한 사람에게만"),
    ("기록한다", "누구에게 거는 규칙인지"),
    ("은상은 준에게 소문을 낸다", "은상, 준"),
    ("민석은 방송실에 가고 기록한다", "행동 하나만"),
    ("민석은 아침 저녁 기록한다", "장면 조건은 하나만"),
    ("민석은 아침 기록한다", "정오"),
    ("채연은 기록한다", "채연에게는 '기록한다'"),
])
def test_reject_reason_matches_actual_cause(text, expected):
    result = preview(text)
    assert not result["executable"]
    assert expected in reason(text)


def test_double_negation_does_not_turn_alternatives_into_prohibitions():
    assert not any(a.endswith(" 금지") for a in preview("민석은 기록 안 하기 금지")["alternatives"])
