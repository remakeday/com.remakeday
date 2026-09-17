from types import SimpleNamespace as NS

from apps.engine.app.use_cases.npc_context import learn_scene, context_ids, response_sources
from apps.engine.app.use_cases.public_observations import public_observations
from apps.engine.app.use_cases.scene_execution import execute_scene
from apps.engine.domain.entities.npc_memory import forget_memory, visible_memories
from apps.engine.domain.entities.rule_rules import Rule
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_review_failure_boundaries import Events, loop_at


def test_actor_gets_own_account_witness_only_sees_public_action():
    bundle, loop, events = build().bundle(), loop_at(2), Events()
    execute_scene(events, loop, bundle, [])
    states = [NS(code=c.code, name=c.name, memory=[]) for c in bundle.characters if c.playable]
    learn_scene(bundle, loop, states, public_observations(events, loop.attempt_id))
    actor = next(s for s in states if s.name == "은상")
    own = next(m for m in visible_memories(actor.memory) if "action-2-은상" in m["id"])
    assert own["kind"] == "내가 한 일" and "준" in own["text"]
    outsider = next(s for s in states if s.name == "채연")
    assert not any("action-2-은상" in m["id"] for m in outsider.memory)


def test_suppressed_action_never_gives_actor_the_original_explanation():
    bundle, loop, events = build().bundle(), loop_at(3), Events()
    execute_scene(events, loop, bundle, [Rule("R1", "user_choice", "민석", 3, "suppress", "기록한다", 1)])
    npc = NS(code="minseok", name="민석", memory=[])
    learn_scene(bundle, loop, [npc], public_observations(events, loop.attempt_id))
    own = next(m for m in npc.memory if "action-3-민석" in m["id"])
    assert own["kind"] == "하지 않은 일"
    assert "적었어" not in own["text"]


def test_deleted_source_is_unavailable_even_when_observations_are_replayed():
    bundle, loop, events = build().bundle(), loop_at(3), Events()
    execute_scene(events, loop, bundle, [])
    npc = NS(code="minseok", name="민석", memory=[])
    observations = public_observations(events, loop.attempt_id)
    learn_scene(bundle, loop, [npc], observations)
    source = f"{loop.id}:action-3-민석-기록한다"
    npc.memory, _ = forget_memory(npc.memory, source)
    learn_scene(bundle, loop, [npc], observations)
    assert source not in context_ids(bundle, bundle.characters[1], npc.memory, loop.damage_level)


def test_missing_model_citations_conservatively_preserve_memory_dependencies():
    memory = [{"id": "first", "text": "answered", "source_ids": []}]
    assert response_sources(memory, []) == ["first"]


def test_rule_disclosed_speech_is_remembered_by_speaker_and_witness():
    bundle, loop, events = build().bundle(), loop_at(5), Events()
    execute_scene(events, loop, bundle, [Rule("R1", "user_choice", "은상", 5, "enforce", "소문의 알려진 출처를 밝힌다", 1)])
    states = [NS(code=c.code, name=c.name, memory=[]) for c in bundle.characters if c.playable]
    learn_scene(bundle, loop, states, public_observations(events, loop.attempt_id))
    source_id = f"{loop.id}:rule-5-R1"
    for name in ["은상", "민석"]:
        remembered = next(m for s in states if s.name == name for m in s.memory if m["id"] == source_id)
        assert "준에게 들었어" in remembered["text"]
    assert not any(m["id"] == source_id for s in states if s.name == "채연" for m in s.memory)


def test_authored_fragment_speech_is_the_speakers_current_memory():
    from apps.engine.app.use_cases.public_observations import disclose
    bundle, loop, events = build().bundle(), loop_at(2), Events()
    loop.loop_n = 3
    fragment = next(f for f in bundle.fragments if "귀표" in f.text)
    disclose(events, loop, bundle.beats[1], key=f"fragment-{bundle.fragments.index(fragment)}",
             text=fragment.text, actor=fragment.actor, source_kind="statement")
    npc = NS(code="jun", name="준", memory=[])
    learn_scene(bundle, loop, [npc], public_observations(events, loop.attempt_id))
    assert any("귀표" in m["text"] for m in npc.memory)


def test_enforced_hearsay_cannot_restore_erased_person_at_high_damage():
    bundle, loop, events = build().bundle(), loop_at(2), Events()
    loop.damage_level = 3
    rule = Rule("R1", "user_choice", "은상", 2, "enforce", "들은 것을 그대로 전한다", 1)
    scene = execute_scene(events, loop, bundle, [rule])
    assert "충식" not in scene.narration
    assert all("충식" not in o.text for o in public_observations(events, loop.attempt_id))


def test_record_contents_follow_actual_ration_action_not_an_unrelated_wristband():
    bundle, loop, events = build().bundle(), loop_at(3), Events()
    execute_scene(events, loop, bundle, [])
    npc = NS(code="minseok", name="민석", memory=[])
    learn_scene(bundle, loop, [npc], public_observations(events, loop.attempt_id))
    account = next(m for m in npc.memory if m["id"] == f"{loop.id}:action-3-민석-기록한다")
    assert "채연" in account["text"] and "남긴" in account["text"]


def test_suppressed_ration_does_not_create_the_conditional_record_contents():
    bundle, loop, events = build().bundle(), loop_at(3), Events()
    execute_scene(events, loop, bundle, [Rule("R1", "user_choice", "채연", 3, "suppress", "배급을 남긴다", 1)])
    npc = NS(code="minseok", name="민석", memory=[])
    learn_scene(bundle, loop, [npc], public_observations(events, loop.attempt_id))
    account = next(m for m in npc.memory if m["id"] == f"{loop.id}:action-3-민석-기록한다")
    assert "채연" not in account["text"]


def test_notebook_contents_require_a_current_reading_and_can_be_learned_after_deletion():
    bundle, loop, events = build().bundle(), loop_at(3), Events()
    char = next(c for c in bundle.characters if c.code == "minseok")
    assert not any("쟁반 수" in k.text for k in char.knowledge)
    execute_scene(events, loop, bundle, [])
    npc = NS(code=char.code, name=char.name, memory=[])
    learn_scene(bundle, loop, [npc], public_observations(events, loop.attempt_id))
    source = f"{loop.id}:action-3-민석-기록한다"
    npc.memory, _ = forget_memory(npc.memory, source)
    execute_scene(events, loop, bundle, [Rule("R1", "user_choice", "민석", 3, "enforce", "가진 것을 보여준다", 1)])
    learn_scene(bundle, loop, [npc], public_observations(events, loop.attempt_id))
    assert source not in context_ids(bundle, char, npc.memory, 0)
    assert any("날짜와 이름, 남은 쟁반 수" in m["text"] for m in visible_memories(npc.memory))


def test_lost_name_account_falls_back_to_one_without_the_absent_name():
    """테스터9 F14 — 소실 인물이 든 경험은 통째로 빠지므로 다음 경험으로 수첩을 기억한다."""
    bundle, loop, events = build().bundle(), loop_at(3), Events()
    loop.damage_level = 3
    execute_scene(events, loop, bundle, [Rule("R1", "user_choice", "민석", 3, "enforce", "가진 것을 보여준다", 1)])
    npc = NS(code="minseok", name="민석", memory=[])
    learn_scene(bundle, loop, [npc], public_observations(events, loop.attempt_id))
    shown = next(m for m in npc.memory if m["id"] == f"{loop.id}:action-3-민석-가진 것을 보여준다")
    assert "채연" in shown["text"] and "충식" not in shown["text"]


def test_notebook_reading_names_everyone_written_before_damage():
    bundle, loop, events = build().bundle(), loop_at(3), Events()
    execute_scene(events, loop, bundle, [Rule("R1", "user_choice", "민석", 3, "enforce", "가진 것을 보여준다", 1)])
    npc = NS(code="minseok", name="민석", memory=[])
    learn_scene(bundle, loop, [npc], public_observations(events, loop.attempt_id))
    shown = next(m for m in npc.memory if m["id"] == f"{loop.id}:action-3-민석-가진 것을 보여준다")
    assert "충식" in shown["text"] and "채연" in shown["text"]
