"""장면 이미지가 현재 비트의 API 응답으로만 전달되는지 검증한다."""

from tests.engine.test_usecase_day import make_day
from apps.engine.app.use_cases.game_support import lost_names


def test_illustration_captions_do_not_restore_erased_people(db_session):
    inter, scenario, _, info = make_day(db_session, [])
    loop = inter._loops.get(info["loop_id"])
    loop.loop_n, loop.damage_level = 5, 3
    response = inter.advance_beat(info["loop_id"])
    captions = " ".join(i["caption"] for i in response["illustrations"])
    assert not any(name in captions for name in lost_names(scenario.bundle(), 3))


def test_day_delivers_only_current_scene_illustrations(db_session):
    inter, _, _, info = make_day(db_session, [])
    assert [i["image_id"] for i in info.get("illustrations", [])] == ["clue-07", "clue-01"]
    expected = [["clue-11", "clue-10"], ["clue-08"], ["clue-12"], ["clue-04", "clue-10", "clue-09"], []]
    for image_ids in expected:
        response = inter.advance_beat(info["loop_id"])
        assert [i["image_id"] for i in response["illustrations"]] == image_ids
        assert all(i["caption"] for i in response["illustrations"])
    end = inter.advance_beat(info["loop_id"])
    assert end["day_done"] and end["illustrations"] == []
