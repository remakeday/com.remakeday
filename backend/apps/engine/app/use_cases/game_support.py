"""유스케이스 공용 헬퍼 — 프롬프트 조립·하네스 체크 구성·이벤트 기록."""

import random
from uuid import UUID

from apps.engine.app.dtos import event_log_dto as ev
from apps.engine.app.dtos.scenario_dto import CharacterDTO, ScenarioBundleDTO
from apps.engine.app.ports.output.llm_port import MessageDTO
from apps.engine.app.use_cases import prompts
from apps.engine.app.use_cases.harness import HarnessReport


def system_msg(content: str) -> MessageDTO:
    return MessageDTO(role="system", content=content)


def user_msg(content: str) -> MessageDTO:
    return MessageDTO(role="user", content=content)


def applicable_ban_words(bundle: ScenarioBundleDTO, npc_code: str, loop_n: int) -> list[str]:
    words = []
    for b in bundle.utterance_bans:
        if b.exempt_code == npc_code and b.from_loop is not None and loop_n >= b.from_loop:
            continue
        words.append(b.word)
    return words


def lost_names(bundle: ScenarioBundleDTO, damage_level: int) -> list[str]:
    if damage_level < 3:
        return []
    return [c.name for c in bundle.characters if c.lost]


def absent_note(bundle: ScenarioBundleDTO) -> str:
    """소실 인물 부재 안내 — roster에 이름은 남지만 '지금 있는 사람'은 아니다."""
    names = [c.name for c in bundle.characters if c.lost]
    if not names:
        return ""
    return (
        f"{', '.join(names)}은(는) 지금 여기 없다 — 어제까지 있던 이름이다. "
        "여기 있는 사람으로 세지 않는다."
    )


def build_agent_messages(
    bundle: ScenarioBundleDTO,
    char: CharacterDTO,
    *,
    suspicion: int,
    trust: int,
    opposite: bool,
    rules_text: str,
    memory: list[str],
    user_text: str,
    loop_n: int,
    age7_on: bool,
) -> list[MessageDTO]:
    banned = applicable_ban_words(bundle, char.code, loop_n)
    age7 = (
        prompts.AGE7_POLICY.format(banned_words=", ".join(banned) or "(없음)")
        if age7_on
        else ""
    )
    other = next((c.name for c in bundle.characters if c.code != char.code and c.playable), "누군가")
    roster = ", ".join(c.name for c in bundle.characters)
    rules_block = rules_text or "(없음)"
    if rules_text:
        rules_block += "\n규칙은 해야 할 행동이다. 실행했다고 단정하지 말고 공개된 장면 기록으로 확인한다."
    sys = prompts.AGENT_SYSTEM.format(
        npc_name=char.name,
        surface_summary=bundle.surface_summary,
        persona=char.persona,
        goal=char.goal,
        relations=char.relations,
        roster=roster,
        absent_note=absent_note(bundle),
        suspicion=suspicion,
        trust=trust,
        opposite_note=(prompts.OPPOSITE_NOTE + "\n") if opposite else "",
        rules=rules_block,
        age7_policy=age7,
    )
    sys += "\n\n[예시]\n" + prompts.AGENT_FEWSHOT.format(other_npc=other)
    if memory:
        sys += "\n\n[방금 오간 말]\n" + "\n".join(memory)
    return [system_msg(sys), user_msg(user_text)]


def pick_fallback_line(char: CharacterDTO) -> str:
    if char.fallback_lines:
        return random.choice(char.fallback_lines)
    return "…뭐?"


def record_harness(event_log, session_id: UUID, report: HarnessReport, *, loop_n: int | None, beat: int | None) -> None:
    """Successful calls and all retry/check records are retained for independent review."""
    event_log.record(
        session_id,
        ev.HarnessEvent(
            loop_n=loop_n,
            beat=beat,
            role=report.role,
            violations=report.violations,
            attempts=report.attempts,
            fallback_used=report.fallback_used,
            call_records=report.call_records,
            model=report.model,
            version="connected-investigation-1",
        ),
    )


def resolve_npc_code(bundle: ScenarioBundleDTO, ref: str) -> str | None:
    """LLM이 이름으로 지목해도 코드로 해석한다."""
    for c in bundle.characters:
        if ref in (c.code, c.name):
            return c.code
    return None
