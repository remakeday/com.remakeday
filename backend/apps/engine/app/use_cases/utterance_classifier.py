"""플레이어 입력 분류 — 질문·부탁·잡담·무의미. 라벨 하나만 낸다 (테스터6 F2)."""

from apps.engine.app.dtos.llm_output_dto import UtteranceClassOutput
from apps.engine.app.use_cases.game_support import system_msg, user_msg
from apps.engine.app.use_cases.harness import run_with_harness

_SYSTEM = (
    "플레이어가 대피소의 친구에게 건넨 한 줄을 넷 중 하나로 분류한다. "
    "question: 무엇을 묻는다(오타·줄임말이어도 뜻이 잡히면 포함). "
    "request: 무엇을 해 달라고 한다. "
    "chat: 인사·감탄·잡담처럼 정보를 묻지도 시키지도 않는다. "
    "nonsense: 뜻을 잡을 수 없는 글자·기호·반복. "
    "출력은 JSON {\"label\": ...} 하나뿐이다."
)


def classify(llm, text: str):
    out, report = run_with_harness(
        llm, [system_msg(_SYSTEM), user_msg(text)], UtteranceClassOutput,
        role="classifier", harness_on=True, temperature=0,
    )
    return (out.label if out else None), report
