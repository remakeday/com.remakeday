"""F11 원숭이손 — 장면 실행: 부작용 관찰 문장 공개 조건·새 행동 콜백·예산 대가 없음 (스펙 §3 새 개념 3·5)."""

from apps.engine.app.use_cases.scene_execution import execute_scene
from apps.engine.domain.entities.rule_rules import Rule
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_review_failure_boundaries import Events, loop_at


def wish_rules(key, *, start=1):
    """respond_paw가 저장하는 모양 그대로 — 보이는 규칙 1 + 숨은 규칙 N(마지막에 관찰 문장)."""
    wish = next(w for w in build().bundle().paw_wishes if w.key == key)
    rules = [Rule(f"R{start}", "monkey_paw", wish.reveal.actor, wish.reveal.beat, wish.reveal.effect,
                  wish.reveal.action, 1)]
    for i, effect in enumerate(wish.effects):
        rules.append(Rule(f"R{start + 1 + i}", "paw_effect", effect.actor, effect.beat, effect.effect, effect.action, 1,
                          hidden_side_effect=wish.observation if i == len(wish.effects) - 1 else None))
    return wish, rules


def run_day(events, loop, rules, beats, on_action=None):
    scenes = {}
    for beat in beats:
        loop.beat = beat
        scenes[beat] = execute_scene(events, loop, build().bundle(), rules, on_action=on_action)
    return scenes


def side_effects(events):
    return [e.side_effect for e in events.rows if e.type == "rule_execution" and e.side_effect]


def test_fulfilled_wish_discloses_observation_once_at_last_hidden_beat():
    events, loop = Events(), loop_at()
    wish, rules = wish_rules("chaeyeon-honest")
    budget = loop.budget_left
    scenes = run_day(events, loop, rules, [2, 3, 4, 5, 6])
    assert "밥에서 소독약 냄새가 나" in scenes[2].narration
    assert "쟁반이 빈다" in scenes[3].narration and "채연이 쟁반을 밀어낸다" not in scenes[3].narration
    assert wish.observation not in scenes[3].narration
    assert wish.observation in scenes[5].narration
    assert side_effects(events) == [wish.observation]
    observations = [e.observation for e in events.rows if e.type == "observation" and e.observation.text == wish.observation]
    assert len(observations) == 1 and observations[0].source_kind == "rule_result" and observations[0].beat == 5
    assert loop.budget_left == budget


def test_conflicting_player_rule_blocks_the_observation():
    events, loop = Events(), loop_at()
    wish, rules = wish_rules("chaeyeon-honest")
    rules.append(Rule("R9", "user_choice", "채연", 3, "enforce", "배급을 남긴다", 2))  # 나중 규칙이 이긴다
    scenes = run_day(events, loop, rules, [2, 3, 4, 5])
    assert "채연이 쟁반을 밀어낸다" in scenes[3].narration
    assert "담요를 두른 사람이 하나 늘었다" in scenes[5].narration  # 반대 사건 행동 자체는 일어난다
    assert side_effects(events) == []
    assert not any(e.type == "observation" and e.observation.text == wish.observation for e in events.rows)


def test_same_beat_hidden_rules_are_judged_together():
    events, loop = Events(), loop_at()
    wish, rules = wish_rules("broadcast-room")
    scenes = run_day(events, loop, rules, [2, 3])
    assert "민석은 배급 자리를 보지만 수첩에는 적지 않는다" in scenes[3].narration
    assert "수첩은 덮여 있다" in scenes[3].narration
    assert side_effects(events) == [wish.observation]


def test_on_action_fires_once_per_new_action_even_when_scene_reruns():
    events, loop = Events(), loop_at()
    _, rules = wish_rules("band-meaning")
    seen = []
    run_day(events, loop, rules, [5, 5], on_action=lambda action: seen.append((action.actor, action.action)))
    assert seen.count(("은상", "번호 소문을 낸다")) == 1
    assert seen.count(("민석", "방송실에 간다")) == 1


def test_wish_scenes_do_not_happen_without_wish_rules():
    events, loop = Events(), loop_at()
    scenes = run_day(events, loop, [], [2, 3, 4, 5, 6])
    text = " ".join(s.narration for s in scenes.values())
    for action in build().bundle().scene_actions:
        if action.paw_only:
            assert action.narration not in text
    assert side_effects(events) == []
