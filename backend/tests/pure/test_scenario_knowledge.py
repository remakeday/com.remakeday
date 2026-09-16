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
