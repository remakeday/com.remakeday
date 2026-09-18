"""execute_scene 줄 레코드 — 종류·순서, narration은 줄 text를 이어 붙인 것 (낮 화면 VN 설계 §3 T1)."""

from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION, execute_scene
from apps.engine.domain.entities.rule_rules import Rule
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_paw_scene_execution import run_day, wish_rules
from tests.pure.test_review_failure_boundaries import Events, loop_at


def test_scene_lines_have_kinds_in_execution_order_and_join_to_narration():
    events, loop = Events(), loop_at(beat=3)
    rules = [Rule("R1", "user_choice", "채연", 3, "suppress", "배급을 남긴다", 1),
             Rule("R2", "user_choice", "민석", 3, "enforce", EXPLAIN_ACTION, 1)]
    scene = execute_scene(events, loop, build().bundle(), rules)
    kinds = [line.kind for line in scene.lines]
    assert kinds == ["scene", "rule_result", "action", "statement"]
    assert scene.narration == " ".join(line.text for line in scene.lines)
    first, suppressed, recorded, statement = scene.lines
    assert first.text == "정오 배급이 나온다." and first.observation_id == f"{loop.id}:scene-3" and first.speaker is None
    assert suppressed.observation_id == f"{loop.id}:action-3-채연-배급을 남긴다" and suppressed.image_id is None
    assert recorded.speaker is None and recorded.observation_id == f"{loop.id}:action-3-민석-기록한다"
    assert statement.speaker == "민석" and statement.text.startswith("민석: ")
    assert statement.observation_id == f"{loop.id}:rule-3-R2"
    assert all(line.voice_id is None for line in scene.lines)


def test_action_line_carries_its_illustration_and_scene_line_the_beat_image():
    events, loop = Events(), loop_at(beat=5)
    scene = execute_scene(events, loop, build().bundle(), [])
    assert scene.lines[0].kind == "scene" and scene.lines[0].image_id == "clue-04"
    with_image = [line for line in scene.lines[1:] if line.image_id]
    assert with_image and all(line.kind == "action" for line in with_image)


def test_paw_effect_line_follows_the_hidden_rule_action():
    events, loop = Events(), loop_at()
    wish, rules = wish_rules("broadcast-room")
    scenes = run_day(events, loop, rules, [2, 3])
    lines = scenes[3].lines
    effect = next(line for line in lines if line.kind == "paw_effect")
    assert effect.text == wish.observation and effect.speaker is None
    assert effect.observation_id.startswith(f"{loop.id}:paw-effect-3-")
    assert lines.index(effect) > next(i for i, line in enumerate(lines) if line.kind == "rule_result")
    assert scenes[3].narration == " ".join(line.text for line in lines)


def test_scene_without_actions_still_has_the_scene_line():
    events, loop = Events(), loop_at(beat=1)
    bundle = build().bundle().model_copy(update={"scene_actions": []})
    scene = execute_scene(events, loop, bundle, [])
    assert [line.kind for line in scene.lines] == ["scene"]
    assert scene.lines[0].text == scene.narration
