"""테스터9 F14 추가 사례 2 — 설명 규칙 대사가 장면 서술을 되풀이하기만 하면 연결된 시작 기억 문장을 붙인다."""

from types import SimpleNamespace as NS

from apps.engine.app.use_cases.explanation_grounding import explanation_line
from apps.engine.app.use_cases.npc_context import learn_scene
from apps.engine.app.use_cases.public_observations import public_observations
from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION, execute_scene
from apps.engine.domain.entities.rule_rules import Rule
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_review_failure_boundaries import Events, loop_at

KNOWLEDGE = "손목띠 숫자 밑에 작은 글자가 하나 더 있는 것을 봤다. 무슨 뜻인지는 모른다."
REPEATS_SCENE = "불빛에 비춰 봤어. 숫자가 써 있잖아. 뭔지 궁금해서."  # 09-17 실제 대사
CARRIES_KNOWLEDGE = "불빛에 비춰 봤어. 숫자 밑에 작은 글자가 하나 더 있어. 무슨 뜻인지는 몰라."


def _bundle(explanation, knowledge_ids):
    jun = NS(name="준", knowledge=[NS(id="jun-before-start-band", text=KNOWLEDGE),
                                   NS(id="jun-before-start-face", text="여기서 내 얼굴을 본 적이 없다.")])
    action = NS(actor="준", action="손목띠를 만진다", narration="준이 손목띠를 불빛에 비춰 본다.",
                explanation=explanation, explanation_knowledge=knowledge_ids)
    return NS(characters=[jun]), action


def test_scene_repeating_explanation_gets_the_linked_knowledge_appended():
    bundle, action = _bundle(REPEATS_SCENE, ["jun-before-start-band"])
    assert explanation_line(bundle, action) == f"{REPEATS_SCENE} {KNOWLEDGE}"


def test_explanation_already_carrying_the_knowledge_is_unchanged():
    bundle, action = _bundle(CARRIES_KNOWLEDGE, ["jun-before-start-band"])
    assert explanation_line(bundle, action) == CARRIES_KNOWLEDGE


def test_action_without_linked_knowledge_behaves_as_before():
    bundle, action = _bundle(REPEATS_SCENE, [])
    assert explanation_line(bundle, action) == REPEATS_SCENE
    bundle, action = _bundle("", [])
    assert explanation_line(bundle, action) == action.narration


def test_only_the_linked_entry_is_appended_and_only_once():
    bundle, action = _bundle(REPEATS_SCENE, ["jun-before-start-band"])
    line = explanation_line(bundle, action)
    assert line.count(KNOWLEDGE) == 1 and "내 얼굴" not in line


def _scenario_with(explanation, knowledge_ids):
    bundle = build().bundle()
    actions = [a.model_copy(update={"explanation": explanation, "explanation_knowledge": knowledge_ids})
               if (a.actor, a.beat, a.action) == ("준", 2, "손목띠를 만진다") else a for a in bundle.scene_actions]
    return bundle.model_copy(update={"scene_actions": actions})


def test_explain_rule_statement_carries_knowledge_and_witness_remembers_the_same_line():
    bundle, loop, events = _scenario_with(REPEATS_SCENE, ["jun-before-start-band"]), loop_at(2), Events()
    scene = execute_scene(events, loop, bundle, [Rule("R5", "user_choice", "준", 2, "enforce", EXPLAIN_ACTION, 1)])
    statement = next(line for line in scene.lines if line.kind == "statement" and line.speaker == "준")
    assert statement.text == f"준: {REPEATS_SCENE} {KNOWLEDGE}"
    states = [NS(code=c.code, name=c.name, memory=[]) for c in bundle.characters if c.playable]
    learn_scene(bundle, loop, states, public_observations(events, loop.attempt_id))
    heard = next(m for s in states if s.name == "민석" for m in s.memory if m["id"] == statement.observation_id)
    assert heard["kind"] == "들은 말" and "작은 글자" in heard["text"]


def test_current_scenario_explanation_for_jun_band_passes_the_guard_unchanged():
    bundle = build().bundle()
    action = next(a for a in bundle.scene_actions if (a.actor, a.beat, a.action) == ("준", 2, "손목띠를 만진다"))
    linked = action.model_copy(update={"explanation_knowledge": ["jun-before-start-band"]})
    assert explanation_line(bundle, linked) == action.explanation
