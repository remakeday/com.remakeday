"""P1 도메인 — 상태 머신·예산·의심·신뢰·손상 (LLM 없이)."""

import pytest

from apps.engine.domain.entities import loop_rules, npc_rules
from apps.engine.domain.entities.loop_rules import DomainError


def test_budget_8_to_4():
    assert [loop_rules.initial_budget(n) for n in range(1, 6)] == [8, 7, 6, 5, 4]


def test_utterance_consumes_budget_and_exhausts():
    s = loop_rules.start_loop(5)  # 예산 4
    for _ in range(4):
        s = loop_rules.apply_utterance(s)
    assert s.budget_left == 0
    with pytest.raises(DomainError):
        loop_rules.apply_utterance(s)


def test_beat_advance_is_free_and_ends_at_night():
    s = loop_rules.start_loop(1)
    for expected in (2, 3, 4, 5, 6):
        s = loop_rules.next_beat(s)
        assert s.beat == expected and s.budget_left == 8
    s = loop_rules.next_beat(s)
    assert s.state == "night_pending"
    with pytest.raises(DomainError):
        loop_rules.apply_utterance(s)
    with pytest.raises(DomainError):
        loop_rules.next_beat(s)


def test_damage_table():
    assert [loop_rules.damage_for_loop(n) for n in range(1, 6)] == [
        (0, False), (1, False), (2, False), (2, True), (3, False),
    ]


def test_ask_budget():
    s = loop_rules.start_loop(1)
    s, ok1 = loop_rules.consume_ask_budget(s)
    s, ok2 = loop_rules.consume_ask_budget(s)
    s, ok3 = loop_rules.consume_ask_budget(s)
    assert (ok1, ok2, ok3) == (True, True, False)


def test_suspicion_threshold_60_triggers_opposite():
    g = npc_rules.NpcGauge(suspicion=52, trust=0, opposite_mode=False)
    g = npc_rules.apply_deltas(g, 5, 0)
    assert g.suspicion == 57 and not g.opposite_mode
    g = npc_rules.apply_deltas(g, 5, 0)
    assert g.suspicion == 62 and g.opposite_mode
    g = npc_rules.apply_deltas(g, -10, 0)  # 내려가도 반대 행동 유지 (회차 내)
    assert g.opposite_mode


def test_deltas_are_clamped():
    g = npc_rules.NpcGauge(0, 0, False)
    g = npc_rules.apply_deltas(g, 99, 99)
    assert g.suspicion == 10  # ±10 클램프
    assert g.trust == 6  # 신뢰 상승 상한 6


def test_carry_over_5_percent_trust():
    g = npc_rules.NpcGauge(suspicion=80, trust=60, opposite_mode=True)
    g2 = npc_rules.carry_over(g)
    assert g2 == npc_rules.NpcGauge(suspicion=0, trust=3, opposite_mode=False)


def test_memory_keeps_3_turns():
    m = npc_rules.NpcMemory()
    for i in range(5):
        m = npc_rules.remember(m, f"t{i}")
    assert m.turns == ("t2", "t3", "t4")
