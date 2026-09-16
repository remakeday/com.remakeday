"""잠재(dormant) 장면 기회 — 규칙을 걸어야만 일어나는 탐사 행동 (개선 2단계 임무 B)."""

from apps.engine.app.use_cases.scene_execution import execute_scene
from apps.engine.domain.entities.rule_rules import Rule
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_review_failure_boundaries import Events, loop_at

DORMANT = [
    (2, "준", "가진 것을 보여준다"),
    (3, "민석", "가진 것을 보여준다"),
    (5, "은상", "따라간다"),
    (6, "준", "밤에 깨어 있는다"),
    (2, "은상", "들은 것을 그대로 전한다"),
]


def run_scene(beat, rules=()):
    bundle, events, loop = build().bundle(), Events(), loop_at(beat)
    scene = execute_scene(events, loop, bundle, list(rules))
    return bundle, events, scene


def test_scenario_declares_dormant_opportunities():
    bundle = build().bundle()
    declared = {(o.beat, o.actor, o.action) for o in bundle.scene_actions if o.dormant}
    assert set(DORMANT) <= declared
    for beat, actor, action in DORMANT:
        assert action in bundle.action_vocab


def test_dormant_action_is_invisible_without_rule():
    for beat, actor, action in DORMANT:
        bundle, events, scene = run_scene(beat)
        opportunity = next(o for o in bundle.scene_actions
                           if (o.beat, o.actor, o.action) == (beat, actor, action))
        assert opportunity.narration not in scene.narration
        assert opportunity.suppressed_narration not in scene.narration
        assert not any(e.type == "rule_execution" for e in events.rows)


def test_dormant_action_fires_under_enforce_rule():
    beat, actor, action = 6, "준", "밤에 깨어 있는다"
    rule = Rule("R1", "user_custom", actor, beat, "enforce", action, 1)
    bundle, events, scene = run_scene(beat, [rule])
    opportunity = next(o for o in bundle.scene_actions
                       if (o.beat, o.actor, o.action) == (beat, actor, action))
    assert opportunity.narration in scene.narration
    executions = [e for e in events.rows if e.type == "rule_execution"]
    assert executions and executions[-1].result == "obeyed"
    assert executions[-1].actual_action == action


def test_dormant_action_suppress_stays_invisible():
    beat, actor, action = 6, "준", "밤에 깨어 있는다"
    rule = Rule("R1", "user_custom", actor, beat, "suppress", action, 1)
    bundle, events, scene = run_scene(beat, [rule])
    opportunity = next(o for o in bundle.scene_actions
                       if (o.beat, o.actor, o.action) == (beat, actor, action))
    assert opportunity.narration not in scene.narration
