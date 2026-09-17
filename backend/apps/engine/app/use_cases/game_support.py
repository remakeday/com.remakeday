"""유스케이스 공용 헬퍼 — 프롬프트 조립·하네스 체크 구성·이벤트 기록."""

import json
import random
from uuid import UUID

from apps.engine.app.dtos import event_log_dto as ev
from apps.engine.app.dtos.scenario_dto import CharacterDTO, ScenarioBundleDTO
from apps.engine.app.ports.output.llm_port import MessageDTO
from apps.engine.app.use_cases import prompts
from apps.engine.app.use_cases.harness import HarnessReport
from apps.engine.app.use_cases.npc_context import evidence_reference_map
from apps.engine.domain.entities.npc_memory import hidden_memory_ids, visible_memories


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
    memory: list,
    user_text: str,
    loop_n: int,
    age7_on: bool,
    damage_level: int = 0,
    reply_field: str = "reply",
    include_knowledge: bool = True,
    player_asker: bool = True,
) -> list[MessageDTO]:
    banned = applicable_ban_words(bundle, char.code, loop_n)
    age7 = (
        prompts.AGE7_POLICY.format(banned_words=", ".join(banned) or "(없음)")
        if age7_on
        else ""
    )
    absent = tuple(lost_names(bundle, damage_level))
    roster = ", ".join(c.name for c in bundle.characters if c.name not in absent)
    rules_block = rules_text or "(없음)"
    sys = prompts.AGENT_SYSTEM.format(
        npc_name=char.name,
        surface_summary=bundle.surface_summary,
        persona="\n".join(s for s in char.persona.splitlines() if not any(n in s for n in absent)),
        goal=char.goal,
        relations="" if any(n in char.relations for n in absent) else char.relations,
        roster=roster,
        absent_note=absent_note(bundle) if not absent else "",
        suspicion=suspicion,
        trust=trust,
        opposite_note=(prompts.OPPOSITE_NOTE + "\n") if opposite else "",
        rules=rules_block,
        age7_policy=age7,
        asker_note=prompts.PLAYER_ASKER_NOTE.format(others=", ".join(
            c.name for c in bundle.characters if c.name not in absent and c.name != char.name))
        if player_asker else "",
    )
    if reply_field != "reply":
        sys = sys.replace("reply에는", f"{reply_field}에는")
    labels = {"observed": "직접 본 경험", "heard": "전해 들은 말", "belief": "내가 믿는 것", "body": "내 몸과 기분"}
    knowledge = [k for k in char.knowledge if not any(n in k.text or n == k.source for n in absent)]
    references = {source: ref for ref, source in evidence_reference_map(bundle, char, memory, damage_level).items()}
    if knowledge and include_knowledge:
        sys += "\n\n[하루 시작 전부터 아는 것]\n" + "\n".join(json.dumps(
            {"id": references[k.id], "종류": labels[k.kind], "출처": k.source, "내용": k.text}, ensure_ascii=False)
            for k in knowledge)
    visible = visible_memories(memory, excluded_names=absent)
    own_actions = {"내가 한 일", "하지 않은 일"}
    for title, entries in [
        ("오늘 보고 들은 일과 나눈 대화", [m for m in visible if m["kind"] not in own_actions]),
        ("오늘 내 행동 — 실제로 한 일과 하지 않은 일", [m for m in visible if m["kind"] in own_actions]),
    ]:
        if not entries:
            continue
        sys += f"\n\n[{title}]\n" + "\n".join(json.dumps(
            {"id": references[m["id"]], "장면": m["beat"], "종류": m["kind"], "당사자": m.get("speaker"),
             "함께 있던 사람": m.get("listeners", []), "내용": m["text"]}, ensure_ascii=False)
            for m in entries)
    if hidden_memory_ids(memory):
        sys += ("\n\n[지금 기억 상태]\n오늘 기억 중에 비어 있는 부분이 있어. 무엇을 했고 무슨 말을 했는지 "
                "떠오르지 않는 부분은 떠오르지 않는다고 말해. 예전의 습관으로 그 빈 내용을 채우지 마. "
                "상대가 지금 알려 주는 말은 새로 들을 수 있어.")
    sys += (
        "\n\n[지금 질문에 답할 근거]\n"
        "오늘 한 행동은 위 '오늘 내 행동'이 기준이야. '하지 않은 일'에 있는 행동은 오늘 안 했어. "
        "질문이 했다고 전제해도, 네가 안 했으면 안 했다고 바로 알려 줘. "
        "이전부터 하던 습관, 하고 싶은 일, 다른 사람을 본 일은 오늘 네가 실행했다는 뜻이 아니야. "
        "남아 있는 기억으로 내용이 확인되지 않으면 그 내용은 떠올릴 수 없어. "
        "상대가 방금 말해 준 내용은 지금 들은 말로 알아. 그 말을 듣고 이전 기억이 돌아온 건 아니야.\n"
        "evidence_ids에는 답변의 근거인 항목의 id 값을 그대로 복사해. "
        "글자를 고치거나 대괄호를 붙이지 마. 인사·감정이나 마지막 상대 메시지 자체가 근거일 때는 빈 배열이야. "
        "아래 짧은 문답은 목소리 연습용 예시야. 오늘 실제로 나눈 대화가 아니야. 마지막 질문이 지금 듣는 질문이야."
    )
    messages = [system_msg(sys)]
    examples = [
        "어제 내가 문 앞에서 기다렸어. 방금 알려 준 건 어떻게 알게 됐어?\n네가 지금 말해 줘서 알았어. 내가 본 건 아니야.",
        *char.dialogue_examples,
    ]
    for example in examples:
        if any(name in example for name in absent):
            continue
        question, reply = example.split("\n", 1)
        output = {reply_field: reply, "evidence_ids": []}
        if reply_field == "reply":
            output.update(suspicion_delta=0, trust_delta=0, tool_call=None, plan_change=None, mood="calm")
        else:
            output["said_it"] = None
        messages.extend([user_msg(question), MessageDTO(role="assistant", content=json.dumps(output, ensure_ascii=False))])
    messages.append(user_msg(user_text))
    return messages


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
            version=(
                "npc-dialogue-2" if report.role in ("agent", "ask_npc")
                else "f2-classifier-1" if report.role == "classifier"
                else "connected-investigation-1"
            ),
        ),
    )


def resolve_npc_code(bundle: ScenarioBundleDTO, ref: str) -> str | None:
    """LLM이 이름으로 지목해도 코드로 해석한다."""
    for c in bundle.characters:
        if ref in (c.code, c.name):
            return c.code
    return None
