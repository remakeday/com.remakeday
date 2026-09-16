"""Authored conversations require the actual scene, participants, and action outcome."""

from types import SimpleNamespace as NS

import pytest

from apps.engine.app.use_cases.loop_interactor import LoopInteractor
from apps.engine.app.use_cases.public_observations import disclose
from apps.engine.app.use_cases.scene_execution import execute_scene
from apps.engine.domain.entities.rule_rules import Rule
from apps.engine.domain.entities.npc_memory import visible_memories
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_real_model_grounding import Model
from tests.pure.test_review_failure_boundaries import Events, loop_at


def scene_dialogue(beat=2, *, rules=(), absent=None, missing=None, damage=0, execute=True):
    bundle, events, loop = build().bundle(), Events(), loop_at(beat)
    loop.damage_level = damage
    if absent:
        bundle.characters = [c.model_copy(update={"lost": True}) if c.code == absent else c
                             for c in bundle.characters]
    states = {c.code: NS(memory=[], plan=[]) for c in bundle.characters if c.code != missing}
    notes, model = [], Model({"candidate_index": 0})
    day = LoopInteractor.__new__(LoopInteractor)
    day._events, day._npc_llm = events, model
    day._loops = NS(npc_state=lambda _, code: states.get(code))
    day._notes = NS(upsert=lambda *args, **kwargs: notes.append(kwargs))
    if execute:
        scene = execute_scene(events, loop, bundle, rules)
        disclose(events, loop, scene, key=f"scene-{beat}", text=scene.narration)
    result = day._make_ambient(loop, bundle)
    return result, model, events, states, notes, loop


def test_wristband_question_is_a_real_exchange_without_model_selection():
    result, model, *_ = scene_dialogue()
    assert [(line["code"], line["text"]) for line in result["lines"]][:2] == [
        ("jun", "민석아, 이 숫자 뭔지 알아?"),
        ("minseok", "몰라. 손목띠 빼면 안 돼."),
    ]
    assert model.calls == []


@pytest.mark.parametrize("beat", range(1, 7))
def test_every_scene_has_contextual_free_dialogue_and_reported_source_ids(beat):
    result, model, events, states, notes, loop = scene_dialogue(beat)
    assert result and 2 <= len(result["lines"]) <= 3
    assert not model.calls and loop.budget_left == 10
    statements = [e.observation for e in events.rows if e.type == "observation"
                  and ":ambient-" in e.observation.observation_id]
    assert len(statements) == len(result["lines"])
    assert all(o.verification == "reported" and o.source_kind == "statement" for o in statements)
    assert {n["source_key"] for n in notes} == {o.observation_id for o in statements}
    for code in {line["code"] for line in result["lines"]}:
        remembered = {m["id"]: m for m in visible_memories(states[code].memory)}
        assert all(remembered[o.observation_id]["text"] == f"{o.actor}: {o.text}" for o in statements)
    assert all("기록 밖" not in line["text"] and "공개된" not in line["text"] for line in result["lines"])


@pytest.mark.parametrize(("beat", "actor", "action"), [
    (1, "채연", "배급을 남긴다"), (2, "준", "손목띠를 만진다"),
    (3, "채연", "배급을 남긴다"), (3, "민석", "기록한다"),
    (4, "채연", "검진을 받는다"), (5, "민석", "방송실에 간다"),
    (5, "은상", "소문을 낸다"),
])
def test_suppressed_action_prevents_its_conversation(beat, actor, action):
    rule = Rule("R1", "user_choice", actor, beat, "suppress", action, 1)
    assert scene_dialogue(beat, rules=[rule])[0] is None


@pytest.mark.parametrize("kwargs", [{"absent": "jun", "damage": 3}, {"missing": "minseok"}, {"execute": False}])
def test_absent_participant_or_undisclosed_scene_cannot_speak(kwargs):
    result, model, _, _, notes, _ = scene_dialogue(**kwargs)
    assert result is None and not notes and not model.calls


def test_enforced_action_still_allows_its_authored_conversation():
    rule = Rule("R1", "user_choice", "준", 2, "enforce", "손목띠를 만진다", 1)
    result, model, events, *_ = scene_dialogue(rules=[rule])
    assert result["lines"][0]["code"] == "jun" and not model.calls
    action = next(e.observation for e in events.rows if e.type == "observation"
                  and "action-2-준" in e.observation.observation_id)
    assert action.source_kind == "rule_result" and action.rule_id == "R1"


@pytest.mark.parametrize("beat", range(1, 7))
def test_damage_does_not_reintroduce_lost_person_or_hide_unrelated_dialogue(beat):
    result, *_ = scene_dialogue(beat, damage=3)
    assert result is not None and "충식" not in str(result)


def test_wristband_question_is_not_duplicated_in_action_narration():
    result, _, events, *_ = scene_dialogue()
    scenes = [e.observation.text for e in events.rows if e.type == "observation"
              and e.observation.verification == "observed"]
    assert "이 숫자 뭔지 알아?" not in " ".join(scenes)
    assert "이 숫자 뭔지 알아?" in result["lines"][0]["text"]


def test_action_explanations_are_authored_in_the_actors_voice():
    actions = build().bundle().scene_actions
    assert all(action.explanation and not action.explanation.startswith(action.actor) for action in actions)
    visit = next(action for action in actions if action.action == "방송실에 간다")
    assert "문 앞까지" in visit.explanation and "보고했" not in visit.explanation
