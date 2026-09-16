"""쉬운 말투 정책은 같은 하루의 대화를 잊게 하지 않는다."""

from apps.engine.app.use_cases.game_support import build_agent_messages
from apps.scenarios.scenario_a.adapter import build

MEMORY = [
    "유저: 내 이름은 도윤이야. 기억해.", "준: 응.",
    "유저: 밥 먹었어?", "준: 응, 먹었어.",
    "유저: 오늘 춥다.", "준: 응, 추워.",
]


def system_prompt(age7_on: bool) -> str:
    bundle = build().bundle()
    char = next(c for c in bundle.characters if c.code == "jun")
    return build_agent_messages(
        bundle, char, suspicion=0, trust=0, opposite=False,
        rules_text="", memory=MEMORY, user_text="아까 내 이름 뭐라고 했지?",
        loop_n=1, age7_on=True if age7_on else False,
    )[0].content


def test_age7_on_retains_earlier_exchange():
    sys = system_prompt(True)
    assert "도윤" in sys
    assert "춥다" in sys  # 직전 교환은 남는다


def test_age7_off_keeps_full_memory():
    sys = system_prompt(False)
    assert "도윤" in sys
