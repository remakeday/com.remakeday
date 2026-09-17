"""Scenario facts and witnesses must support the authored conversations."""

import pytest

from apps.engine.app.use_cases.scene_execution import SOURCE_ACTION, execute_scene
from apps.engine.domain.entities.rule_rules import Rule
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_review_failure_boundaries import Events, loop_at


@pytest.mark.parametrize("beat", [2, 5])
def test_rumor_source_rule_names_the_person_who_actually_observed_it(beat):
    bundle, events, loop = build().bundle(), Events(), loop_at(beat)
    rule = Rule("source", "user_choice", "은상", beat, "enforce", SOURCE_ACTION, 1)

    execute_scene(events, loop, bundle, [rule])

    statements = [e.observation.text for e in events.rows if e.type == "observation"
                  and e.observation.source_kind == "statement"]
    assert any("준" in line and "들었" in line for line in statements)


def test_rumor_hearsay_has_a_matching_firsthand_observer_in_starting_knowledge():
    characters = {c.name: c for c in build().bundle().characters}
    hearsay = [k for k in getattr(characters["은상"], "knowledge", [])
               if k.kind == "heard" and "충식" in k.text]
    assert hearsay, "The rumor needs a removable starting memory with its source."
    assert {k.source for k in hearsay} == {"준"}
    observations = [k.text for k in characters["준"].knowledge
                    if k.kind == "observed" and "충식" in k.text]
    assert any("기침" in text for text in observations)
    assert any("실려" in text or "이송" in text for text in observations)


@pytest.mark.parametrize("beat", range(1, 6))
def test_authored_scene_companions_can_remember_the_action_they_discuss(beat):
    bundle = build().bundle()
    names = {c.code: c.name for c in bundle.characters}
    dialogue = next(d for d in bundle.scene_dialogues if d.beat == beat)
    participants = {names[line.code] for line in dialogue.lines}

    for required in dialogue.required_actions:
        action = next(a for a in bundle.scene_actions if a.beat == beat
                      and a.actor == required.actor and a.action == required.action)
        assert participants - {action.actor} <= set(getattr(action, "witnesses", []))


def test_notebook_contents_are_answerable_from_the_reading_and_the_lost_name_has_a_fallback():
    """테스터9 F14 — 수첩에 적힌 이름·날짜가 정의되지 않아 '누가 적혀 있어?'에 답할 재료가 없었다."""
    show = next(a for a in build().bundle().scene_actions if (a.actor, a.action) == ("민석", "가진 것을 보여준다"))
    texts = [a.text for a in show.experience_accounts]
    assert any("채연" in t and "충식" in t for t in texts)
    assert any("채연" in t and "충식" not in t for t in texts)  # 손상 3층용


def test_explanations_used_by_information_rules_add_what_the_actor_knows():
    bundle = build().bundle()
    action = {(a.actor, a.action): a for a in bundle.scene_actions}
    band = action[("준", "손목띠를 만진다")].explanation
    assert "작은 글자" in band  # jun-before-start-band — 장면 서술만 되풀이하지 않는다.
    shown = action[("민석", "가진 것을 보여준다")].explanation
    assert "채연" in shown and "충식" not in shown  # 설명 문장은 소실 인물 필터를 거치지 않는다.
    # 테스터9 F14 — '문 앞까지 갔다'만 적힌 기억은 '방송실에 갔어?'에 안 갔다고 답하게 했다.
    assert "방송실에 갔" in action[("민석", "방송실에 간다")].explanation


def test_wristband_numbers_are_fixed_distinct_values_in_each_owners_knowledge():
    """테스터9 F14 — 손목띠 숫자를 모델이 지어내지 않게 인물별 고정값을 지식으로 준다(준 = Q11 구멍 배열 ●● ●●●)."""
    from apps.scenarios.scenario_a.adapter import BAND_NUMBERS
    bundle = build().bundle()
    assert BAND_NUMBERS["준"] == "23"
    assert set(BAND_NUMBERS) == {c.name for c in bundle.characters if c.code != "manager"}
    assert len(set(BAND_NUMBERS.values())) == len(BAND_NUMBERS)
    assert all(len(n) == 2 and n.isdigit() for n in BAND_NUMBERS.values())
    for character in bundle.characters:
        if character.knowledge:
            assert any(f"손목띠는 {BAND_NUMBERS[character.name]}번" in k.text for k in character.knowledge), character.name


def test_defined_wristband_number_passes_the_grounded_number_check_but_invented_ones_do_not():
    from apps.engine.app.dtos.llm_output_dto import AgentOutput
    from apps.engine.app.use_cases.npc_context import grounded_number_check
    from apps.scenarios.scenario_a.adapter import BAND_NUMBERS
    bundle = build().bundle()
    for character in (c for c in bundle.characters if c.knowledge):
        check = grounded_number_check(bundle, character, [], 0, question="네 손목띠 숫자 읽어 줄래?", beat=2)
        own = BAND_NUMBERS[character.name]
        assert check(AgentOutput(reply=f"내 손목띠 숫자는 {own}이야. 무슨 뜻인지는 몰라.",
                                 suspicion_delta=0, trust_delta=0)) is None, character.name
        assert check(AgentOutput(reply="내 거는 7이야.", suspicion_delta=0, trust_delta=0)), character.name


def test_scene_narration_describes_the_wristband_mark_without_calling_it_a_number():
    """인물들은 표식을 숫자로 읽지만 사람의 숫자가 아니다 — 사람 시점 서술·캡션은 '숫자'라고 쓰지 않는다(인용 대사 제외)."""
    import re
    bundle = build().bundle()
    texts = [t for a in bundle.scene_actions for t in (a.narration, a.suppressed_narration, *(i.caption for i in a.illustrations))]
    texts += [b.narration for b in bundle.beats]
    unquoted = [re.sub(r'"[^"]*"', "", t) for t in texts if t]
    assert not [t for t in unquoted if "숫자" in t]


def test_person_view_narration_describes_the_notebook_as_marks_not_written_names():
    """민석 수첩 메타포(2026-09-18) — 인물은 수첩 표식을 이름·쟁반 수로 읽지만 사람 기준으로는 글자가 아니다.
    수첩이 나오는 사람 시점 서술·캡션·신의 공개 사다리·원숭이손 관찰 문장은 내용을 글자로 적지 않는다(인용 대사 제외)."""
    import re
    bundle = build().bundle()
    texts = [t for a in bundle.scene_actions for t in (a.narration, a.suppressed_narration, *(i.caption for i in a.illustrations))]
    texts += [b.narration for b in bundle.beats]
    texts += [r.text for r in bundle.advisor_ladder] + [w.observation for w in bundle.paw_wishes]
    notebook = [re.sub(r'"[^"]*"', "", t) for t in texts if t and "수첩" in t]
    assert notebook, "수첩 서술이 사라지면 검사가 헛돈다."
    written = ("이름", "날짜", "적혀", "적힌", "쟁반 수", "숫자", "글자")
    assert not [t for t in notebook if any(w in t for w in written)]
