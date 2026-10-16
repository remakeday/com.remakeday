"""이어하기 전제 — 같은 비트에 execute_scene을 다시 불러도 기록·관찰·세계 효과가 늘지 않는다 (설계 2026-10-16 §2.2·§4).

이 전제가 깨지면 이어하기는 낮 장면을 execute_scene으로 다시 그릴 수 없다 — 쓰기 없는 읽기 전용 경로가 따로 필요하다.
"""

import pytest

from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION, SOURCE_ACTION, execute_scene
from apps.engine.domain.entities.rule_rules import Rule
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_paw_scene_execution import wish_rules
from tests.pure.test_review_failure_boundaries import Events, loop_at

BUNDLE = build().bundle()
ACTORS = sorted({a.actor for a in BUNDLE.scene_actions})


def _rule_sets() -> dict[str, list[Rule]]:
    """규칙 없음 · 원숭이손 소원 네 가지 · 모든 인물 설명 · 모든 인물 출처 — 규칙 실행·부작용 문장 경로를 전부 지난다."""
    sets = {"규칙 없음": []}
    sets.update({f"소원 {w.key}": wish_rules(w.key)[1] for w in BUNDLE.paw_wishes})
    sets["모두 설명"] = [Rule(f"R{i}", "user_choice", a, None, "enforce", EXPLAIN_ACTION, 1)
                       for i, a in enumerate(ACTORS, 1)]
    sets["모두 출처"] = [Rule(f"R{i}", "user_choice", a, None, "enforce", SOURCE_ACTION, 1)
                       for i, a in enumerate(ACTORS, 1)]
    return sets


RULE_SETS = _rule_sets()


@pytest.mark.parametrize("damage", [0, 3])
@pytest.mark.parametrize("loop_n", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("name", list(RULE_SETS))
def test_rerunning_the_current_beat_records_nothing_new(name, loop_n, damage):
    events, loop = Events(), loop_at(1)
    loop.loop_n, loop.damage_level = loop_n, damage
    rules = RULE_SETS[name]
    for beat in range(1, 7):
        loop.beat = beat
        effects = []
        execute_scene(events, loop, BUNDLE, rules, on_action=effects.append)
        rows, fired = len(events.rows), len(effects)
        execute_scene(events, loop, BUNDLE, rules, on_action=effects.append)  # 이어하기의 재실행
        assert len(events.rows) == rows, f"{beat}비트 재실행이 기록(관찰·규칙 실행)을 더했다"
        assert len(effects) == fired, f"{beat}비트 재실행이 세계 효과(on_action)를 다시 불렀다"


@pytest.mark.parametrize("key", [w.key for w in BUNDLE.paw_wishes])
def test_rerun_after_paw_accepted_mid_beat_records_nothing_new(key):
    """원숭이손은 2비트 장면 뒤에 받는다. 받은 즉시 재실행(_replay_wish_scene)한 뒤 이어하기가 또 그려도 새 기록이 없다."""
    events, loop = Events(), loop_at(2)
    loop.loop_n = 1
    rules = wish_rules(key)[1]
    execute_scene(events, loop, BUNDLE, [])      # 2비트 첫 장면 — 제안은 이 장면과 함께 뜬다
    execute_scene(events, loop, BUNDLE, rules)   # 수락 즉시 재실행과 같은 호출
    rows = len(events.rows)
    execute_scene(events, loop, BUNDLE, rules)   # 이어하기
    assert len(events.rows) == rows


def test_rerun_drops_only_rule_statement_and_paw_effect_lines():
    """이어하기가 되살리는 줄의 근거 — 재실행은 이미 실행한 규칙의 설명(statement)·부작용(paw_effect) 줄만 빠뜨린다."""
    dropped = set()
    for rules in RULE_SETS.values():
        events, loop = Events(), loop_at(1)
        loop.loop_n = 1
        for beat in range(1, 7):
            loop.beat = beat
            first = execute_scene(events, loop, BUNDLE, rules)
            again = execute_scene(events, loop, BUNDLE, rules)
            kept = {line.observation_id for line in again.lines}
            dropped |= {line.kind for line in first.lines if line.observation_id not in kept}
    assert dropped <= {"statement", "paw_effect"}
    assert dropped  # 이 시나리오에 설명·소원 규칙 줄이 실제로 있다 — 비어 있으면 위 단언이 아무것도 확인하지 않는다
