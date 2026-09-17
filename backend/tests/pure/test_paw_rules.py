"""F11 원숭이손 — 소원 선택(최고 칸 겨냥)과 출현 조건 (스펙 §3 출현·선택)."""

from types import SimpleNamespace as NS

from apps.engine.domain.entities.cookie_rules import paw_should_offer
from apps.engine.domain.entities.paw_rules import choose_wish

W = [NS(key="w1", target_cell="motive"), NS(key="w2", target_cell="cause"),
     NS(key="w3", target_cell="motive"), NS(key="w4", target_cell="identity")]


def cells(cause=0.0, motive=0.0, identity=0.0, side_effect=0.0):
    return {"cause": cause, "motive": motive, "identity": identity, "side_effect": side_effect}


def test_first_loop_offers_first_wish_of_the_table():
    assert choose_wish(1, None, W, set()).key == "w1"


def test_later_loops_target_the_highest_cell():
    assert choose_wish(2, cells(cause=60), W, {"w1"}).key == "w2"
    assert choose_wish(2, cells(motive=60), W, {"w1"}).key == "w3"  # 동기 칸 첫 소원이 쓰였으면 다음 동기 소원
    assert choose_wish(2, cells(identity=60), W, {"w1"}).key == "w4"


def test_tie_prefers_the_deeper_cell_and_side_effect_is_ignored():
    assert choose_wish(3, cells(cause=50, motive=50, identity=50), W, {"w1"}).key == "w4"
    assert choose_wish(3, cells(cause=50, motive=50), W, {"w1"}).key == "w3"
    assert choose_wish(3, cells(cause=20, side_effect=100), W, {"w1"}).key == "w2"


def test_exhausted_cell_falls_to_next_highest_and_all_exhausted_is_none():
    assert choose_wish(3, cells(cause=90, identity=10), W, {"w1", "w2"}).key == "w4"
    assert choose_wish(3, cells(cause=90), W, {"w1", "w2", "w3", "w4"}) is None


def test_two_consecutive_declines_stop_offers():
    assert paw_should_offer(3, 60.0, 1, consecutive_declines=1)
    assert not paw_should_offer(3, 60.0, 1, consecutive_declines=2)
    assert not paw_should_offer(1, None, 0, consecutive_declines=2)
