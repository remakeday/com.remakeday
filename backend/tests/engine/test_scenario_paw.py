"""F11 원숭이손 소원 표 — 시나리오 데이터 정합성 (스펙 §3 테스트: 시나리오 표·paw_only)."""

from apps.scenarios.scenario_a.adapter import build

WISH_ACTIONS = {"속마음을 말한다", "담요를 두른다", "검진 결과를 듣는다", "밤에 기침한다",
                "방송실에서 은상 얘기를 한다", "수첩을 덮어 둔다", "번호를 맞춰 본다", "번호 소문을 낸다"}


def test_paw_wish_table_is_backed_by_scene_actions():
    bundle = build().bundle()
    assert [w.key for w in bundle.paw_wishes] == ["chaeyeon-honest", "checkup-record", "broadcast-room", "band-meaning"]
    assert [w.target_cell for w in bundle.paw_wishes] == ["motive", "cause", "motive", "identity"]
    actions = {(a.beat, a.actor, a.action): a for a in bundle.scene_actions}
    for wish in bundle.paw_wishes:
        for rule in [wish.reveal, *wish.effects]:
            action = actions[(rule.beat, rule.actor, rule.action)]
            # enforce 대상은 소원 전용 잠재 행동, suppress 대상은 평소 행동
            assert (action.paw_only and action.dormant) == (rule.effect == "enforce"), (wish.key, rule)
        assert wish.reveal.effect == "enforce"
        # 공개 비트보다 앞선 효과는 억제뿐(① 아침 배급) — 받는 날엔 실행되지 않고 다음 날부터 건다
        assert all(e.beat > wish.reveal.beat >= 2 or e.effect == "suppress" for e in wish.effects), wish.key
        assert wish.reveal.beat >= 2
        assert wish.effects[-1].beat == max(e.beat for e in wish.effects), wish.key
        assert wish.observation and wish.label and wish.default_reason


def test_same_beat_effects_run_before_the_observation_rule():
    """관찰 문장 규칙은 같은 비트의 다른 숨은 규칙보다 장면 순서상 뒤에 있어야 함께 판정된다."""
    bundle = build().bundle()
    order = {(a.beat, a.actor, a.action): i for i, a in enumerate(bundle.scene_actions)}
    for wish in bundle.paw_wishes:
        last = wish.effects[-1]
        for effect in wish.effects[:-1]:
            if effect.beat == last.beat:
                assert order[(effect.beat, effect.actor, effect.action)] < order[(last.beat, last.actor, last.action)]


def test_paw_only_actions_stay_out_of_vocab_and_rule_templates():
    from apps.engine.dependencies.engine_dependency import rule_templates
    scenario = build()
    bundle = scenario.bundle()
    paw_only = [a for a in bundle.scene_actions if a.paw_only]
    assert len(paw_only) == 9
    assert {a.action for a in paw_only} == WISH_ACTIONS | {"배급을 다 먹는다"}
    assert not WISH_ACTIONS & set(bundle.action_vocab)
    templates = {(t["target"], t["action"]) for t in rule_templates(bundle)}
    assert not {(a.actor, a.action) for a in paw_only} & templates
    assert ("은상", "따라간다") in templates and ("채연", "배급을 남긴다") in templates


def test_world_effects_sit_on_counter_events_only():
    bundle = build().bundle()
    effects = {(a.beat, a.actor, a.action): a.world_effect for a in bundle.scene_actions if a.world_effect}
    assert effects == {(5, "은상", "담요를 두른다"): "flag_actor", (6, "채연", "밤에 기침한다"): "flag_actor",
                       (5, "은상", "번호 소문을 낸다"): "rumor"}


def test_wish_dialogues_precede_default_dialogue_of_their_beat():
    bundle = build().bundle()
    paw_actions = {(a.actor, a.action) for a in bundle.scene_actions if a.paw_only}
    for beat in (3, 5, 6):
        dialogues = [d for d in bundle.scene_dialogues if d.beat == beat]
        wish = [i for i, d in enumerate(dialogues) if any((r.actor, r.action) in paw_actions for r in d.required_actions)]
        plain = [i for i, d in enumerate(dialogues) if not any((r.actor, r.action) in paw_actions for r in d.required_actions)]
        assert wish and plain and max(wish) < min(plain), beat


def test_minseok_broadcast_room_reply_comes_first():
    bundle = build().bundle()
    minseok = next(c for c in bundle.characters if c.name == "민석")
    first = minseok.question_replies[0]
    assert [(r.beat, r.actor, r.action) for r in first.required_actions] == [(2, "민석", "방송실에서 은상 얘기를 한다")]
