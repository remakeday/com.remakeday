"""공개용 예시 시나리오 어댑터.

실제 시나리오의 형태만 보여주는 중립 더미다. 시나리오 고유 명사는 없다.
"""

from apps.engine.app.dtos.scenario_dto import (
    BeatDTO,
    CharacterDTO,
    CookieTextDTO,
    FragmentDTO,
    ScenarioBundleDTO,
    TruthClaimDTO,
    UtteranceBanDTO,
)
from apps.scenarios.base_scenario import StaticScenario

_FALLBACKS = {
    "A": ["…뭐?", "몰라.", "그래."],
    "B": ["응?", "글쎄.", "나중에."],
    "C": ["왜?", "아니야.", "그런가."],
}


def build() -> StaticScenario:
    bundle = ScenarioBundleDTO(
        name="example",
        surface_summary=(
            "이곳은 예시 구역이다. 하루는 여섯 비트로 흘러간다. "
            "인물들은 정해진 시간에 모이고 흩어진다."
        ),
        hidden_truth="이 구역의 진실은 예시로만 존재한다. 숨겨진 것도 예시다.",
        characters=[
            CharacterDTO(
                code="A",
                name="A",
                role="core",
                persona="중립 인물 A.",
                goal="예시 목표 A.",
                relations="B와 자주 말한다.",
                fallback_lines=_FALLBACKS["A"],
            ),
            CharacterDTO(
                code="B",
                name="B",
                role="core",
                persona="중립 인물 B.",
                goal="예시 목표 B.",
                relations="A를 지켜본다.",
                fallback_lines=_FALLBACKS["B"],
            ),
            CharacterDTO(
                code="C",
                name="C",
                role="core",
                persona="중립 인물 C.",
                goal="예시 목표 C.",
                relations="모두와 거리를 둔다.",
                fallback_lines=_FALLBACKS["C"],
            ),
        ],
        beats=[
            BeatDTO(n=1, title="비트 1", narration="하루가 시작된다."),
            BeatDTO(n=2, title="비트 2", narration="오전이 지나간다."),
            BeatDTO(n=3, title="비트 3", narration="정오가 된다."),
            BeatDTO(n=4, title="비트 4", narration="오후가 지나간다."),
            BeatDTO(n=5, title="비트 5", narration="저녁이 된다."),
            BeatDTO(n=6, title="비트 6", narration="하루가 끝난다."),
        ],
        truth_claims=[
            TruthClaimDTO(code="cause-1", cell="cause", text="예시 원인 주장."),
            TruthClaimDTO(code="motive-1", cell="motive", text="예시 동기 주장."),
            TruthClaimDTO(
                code="identity-1",
                cell="identity",
                text="예시 정체 주장.",
                is_identity_word=True,
            ),
        ],
        cookies=[
            CookieTextDTO(text_id="ex-1", cell="cause", level=1, text="예시 파편 1."),
            CookieTextDTO(text_id="ex-2", cell="motive", level=1, text="예시 파편 2."),
            CookieTextDTO(text_id="ex-3", cell="identity", level=1, text="예시 파편 3."),
        ],
        forbidden_words=["EXAMPLE_FORBIDDEN"],
        utterance_bans=[UtteranceBanDTO(word="EXAMPLE_BAN")],
        action_vocab=[
            "말을 건다",
            "혼자 있는다",
            "질문한다",
            "기록한다",
            "자리를 옮긴다",
        ],
        fragments=[
            FragmentDTO(loop_n=1, text="예시 감각 파편 1."),
            FragmentDTO(loop_n=2, text="예시 감각 파편 2."),
            FragmentDTO(loop_n=3, text="예시 감각 파편 3."),
            FragmentDTO(loop_n=4, text="예시 감각 파편 4."),
            FragmentDTO(loop_n=5, text="예시 감각 파편 5."),
        ],
        entry_lines=[
            "예시 진입 첫 줄.",
            "예시 진입 둘째 줄.",
            "예시 진입 셋째 줄.",
        ],
        morning_lines={
            0: "예시 아침 둘째 문장 — 평상.",
            1: "예시 아침 둘째 문장 — 미세 변형.",
            2: "예시 아침 둘째 문장 — 불일치.",
            3: "예시 아침 둘째 문장 — 소실 이후.",
        },
        prompt_fragments={
            "npc": "짧고 단순하게 답한다.",
        },
    )
    return StaticScenario(bundle)
