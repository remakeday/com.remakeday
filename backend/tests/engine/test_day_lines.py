"""네 낮 응답의 `lines` — 회차 시작·다음 장면·발화·원숭이손 (낮 화면 VN 설계 §3 T1)."""

from tests.engine.test_paw_wishes import close_loop, force_offer, wish_of
from tests.engine.test_usecase_day import _agent_reply, _first_npc, make_day

NARRATED = {"scene", "action", "rule_result", "statement", "paw_effect"}


def narrated(lines):
    return " ".join(line["text"] for line in lines if line["kind"] in NARRATED)


def test_loop_start_lines_open_with_scene_then_broadcast(db_session):
    _, _, _, info = make_day(db_session, [])
    lines = info["lines"]
    assert [line["kind"] for line in lines[:2]] == ["scene", "broadcast"]
    scene, broadcast = lines[:2]
    assert scene["text"] == "스피커가 켜지고 배급 줄이 생긴다." and scene["speaker"] is None
    assert scene["observation_id"] == f"{info['loop_id']}:scene-1" and scene["image_id"] == "clue-07"
    assert broadcast == {"kind": "broadcast", "speaker": "관리자", "text": info["broadcast"], "image_id": None,
                         "voice_id": None, "observation_id": f"{info['loop_id']}:broadcast-1"}
    assert info["narration"] == narrated(lines)
    assert lines[-1] == {"kind": "system", "speaker": None, "text": "단서 기록에 새 내용을 저장했다.",
                         "image_id": None, "voice_id": None, "observation_id": None}
    ambient = [line for line in lines if line["kind"] == "npc"]
    assert [line["speaker"] for line in ambient] == [line["name"] for line in info["ambient"]["lines"]]
    assert ambient[0]["observation_id"] == f"{info['loop_id']}:ambient-1-0"
    assert set(line["kind"] for line in lines) <= NARRATED | {"broadcast", "npc", "fragment", "system"}


def test_next_beat_lines_put_fragments_after_ambient_and_keep_narration(db_session):
    day, _, attempt, info = make_day(db_session, [])
    close_loop(db_session, info["loop_id"], 0.0)
    second = day.start_loop(attempt.id)
    close_loop(db_session, second["loop_id"], 0.0)
    third = day.start_loop(attempt.id)
    res = day.advance_beat(third["loop_id"])
    lines = res["lines"]
    assert lines[0]["kind"] == "scene" and lines[0]["observation_id"] == f"{third['loop_id']}:scene-2"
    assert res["narration"] == narrated(lines)
    fragments = [line for line in lines if line["kind"] == "fragment"]
    assert fragments and all(f["observation_id"].startswith(f"{third['loop_id']}:fragment-") for f in fragments)
    quoted = next(line for line in fragments if line["speaker"] == "준")
    assert quoted["text"].startswith('준: "')  # 이름: "…" 꼴은 그대로 — 프론트가 그린다
    kinds = [line["kind"] for line in lines]
    assert kinds.index("fragment") > max((i for i, k in enumerate(kinds) if k in NARRATED | {"npc"}), default=-1)
    assert kinds[-1] == "system"


def test_loop_five_lights_out_ends_with_the_truck_broadcast(db_session):
    """5회차 소등 장면 끝에만 관리자 낮 끝 방송(MA13)이 마지막 줄로 붙는다 — 결말과 무관, 4회차엔 없다 (Q군 v2 Q2.4·F24)."""
    day, _, attempt, info = make_day(db_session, [])
    loop_id = info["loop_id"]
    for _ in range(3):
        close_loop(db_session, loop_id, 0.0)
        loop_id = day.start_loop(attempt.id)["loop_id"]
    for _ in range(5):
        fourth = day.advance_beat(loop_id)
    assert fourth["beat"] == 6 and [line["kind"] for line in fourth["lines"]].count("broadcast") == 1
    close_loop(db_session, loop_id, 0.0)
    fifth = day.start_loop(attempt.id)
    assert fifth["loop_n"] == 5
    for _ in range(5):
        res = day.advance_beat(fifth["loop_id"])
    lines = res["lines"]
    assert res["beat"] == 6 and res["broadcast"] == "소등하겠습니다. 모두 자리에서 움직이지 않습니다."
    in_world = [line for line in lines if line["kind"] != "system"]
    assert in_world[-1] == {"kind": "broadcast", "speaker": "관리자", "image_id": "P06", "voice_id": "MA13",
                            "text": "축산 차량이 출발합니다. 문이 닫힐 때까지 자리에서 움직이지 마십시오.",
                            "observation_id": f"{fifth['loop_id']}:broadcast-6-end"}
    assert [line["kind"] for line in lines].count("broadcast") == 2  # 소등 방송은 둘째 줄, 낮 끝 방송은 맨 끝
    assert res["narration"] == narrated(lines)  # 방송은 서술에 섞이지 않는다
    assert any(o["observation_id"] == in_world[-1]["observation_id"] and o["source_kind"] == "statement"
               for o in res["observations"])
    assert day.advance_beat(fifth["loop_id"])["day_done"]


def test_day_done_response_has_no_lines(db_session):
    day, _, _, info = make_day(db_session, [])
    last = [day.advance_beat(info["loop_id"]) for _ in range(6)][-1]
    assert last["day_done"] and last["lines"] == []


def test_reply_is_split_into_npc_lines_linked_to_its_observation(db_session):
    day, scenario, _, info = make_day(db_session, [_agent_reply('배 안 고파. "그냥. 싫어." 그게 다야.')])
    npc = _first_npc(scenario)
    res = day.utter(info["loop_id"], npc.code, "왜 안 먹어?")
    observation_id = res["observations"][0]["observation_id"]
    assert res["lines"] == [
        {"kind": "npc", "speaker": npc.name, "text": "배 안 고파.", "image_id": None, "voice_id": None,
         "observation_id": observation_id},
        {"kind": "npc", "speaker": npc.name, "text": '"그냥. 싫어." 그게 다야.', "image_id": None, "voice_id": None,
         "observation_id": observation_id},
    ]
    assert res["reply"] == " ".join(line["text"] for line in res["lines"])


def test_gated_reply_is_one_system_line(db_session):
    day, scenario, _, info = make_day(db_session, [])
    npc = _first_npc(scenario)
    res = day.utter(info["loop_id"], npc.code, "ㅋㅋㅋㅋ")
    assert res["gated"] and res["lines"] == [{"kind": "system", "speaker": None, "text": res["reply"],
                                              "image_id": None, "voice_id": None, "observation_id": None}]


def test_paw_accept_scene_lines_match_its_narration_and_decline_has_none(db_session):
    day, scenario, _, info = make_day(db_session, [])
    loop_id = info["loop_id"]
    wish = wish_of(scenario, "broadcast-room")
    day.advance_beat(loop_id)
    res = day.respond_paw(loop_id, force_offer(db_session, loop_id, wish.key), True)
    assert res["narration"] and res["narration"] == " ".join(line["text"] for line in res["lines"])
    assert [line["kind"] for line in res["lines"]] == ["rule_result"]
    assert res["lines"][0]["image_id"] == "Q04"
    assert res["lines"][0]["observation_id"] == res["observations"][0]["observation_id"]

    day2, scenario2, _, info2 = make_day(db_session, [])
    second = day2.advance_beat(info2["loop_id"])
    declined = day2.respond_paw(info2["loop_id"], second["paw_offer"]["offer_id"], False)
    assert declined["lines"] == [] and declined["narration"] is None
