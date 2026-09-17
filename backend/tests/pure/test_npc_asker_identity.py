"""테스터8 F5 — 플레이어의 말을 명부 속 다른 인물(채연)의 말로 받아들이지 않는다."""

from apps.engine.app.use_cases.game_support import build_agent_messages
from apps.scenarios.scenario_a.adapter import build


def system_prompt(code: str, **kwargs) -> str:
    bundle = build().bundle()
    char = next(c for c in bundle.characters if c.code == code)
    return build_agent_messages(
        bundle, char, suspicion=0, trust=0, opposite=False, rules_text="", memory=[],
        user_text="민석아 나 밥을 전부 남겼다고 기록해", loop_n=1, age7_on=True, **kwargs,
    )[0].content


def test_player_asker_is_named_as_nobody_in_roster():
    sys = system_prompt("minseok")
    note = sys[sys.index("[지금 말을 거는 상대]"):sys.index("[오늘의 규칙]")]
    assert "이름은 몰라" in note
    assert "채연, 은상, 준, 충식, 관리자 중 누구도 아니야" in note
    assert "민석" not in note  # 자기 자신은 목록에 넣지 않는다
    assert '"플레이어"로 적힌 사람이 이 친구야' in note


def test_friend_asker_path_has_no_player_identity_note():
    assert "[지금 말을 거는 상대]" not in system_prompt("minseok", player_asker=False)


def test_lost_character_is_not_listed_in_asker_note():
    bundle = build().bundle()
    lost = [c.name for c in bundle.characters if c.lost]
    sys = build_agent_messages(
        bundle, next(c for c in bundle.characters if c.code == "jun"), suspicion=0, trust=0, opposite=False,
        rules_text="", memory=[], user_text="안녕", loop_n=3, age7_on=True, damage_level=3,
    )[0].content
    note = sys[sys.index("[지금 말을 거는 상대]"):sys.index("[오늘의 규칙]")]
    assert not any(name in note for name in lost)
