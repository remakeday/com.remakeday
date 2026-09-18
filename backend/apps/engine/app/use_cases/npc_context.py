"""Give participants the experience they acquired, without reading player notes."""

import re

from apps.engine.domain.entities.npc_memory import add_memory, visible_memories
from apps.engine.app.use_cases.explanation_grounding import explanation_line
from apps.engine.app.use_cases.question_replies import actions_occurred


def context_ids(bundle, character, memory, damage_level):
    return set(evidence_reference_map(bundle, character, memory, damage_level).values())


def evidence_reference_map(bundle, character, memory, damage_level):
    """Short prompt references resolve to persistent sources before any memory is saved."""
    absent = tuple(c.name for c in bundle.characters if c.lost and damage_level >= 3)
    knowledge = [k for k in character.knowledge
                 if not any(name in k.text or name == k.source for name in absent)]
    visible = visible_memories(memory, excluded_names=absent)
    return {**{f"k{i}": k.id for i, k in enumerate(knowledge, 1)},
            **{f"m{i}": m["id"] for i, m in enumerate(visible, 1)}}


def resolve_output_sources(output, bundle, character, memory, damage_level):
    references = evidence_reference_map(bundle, character, memory, damage_level)
    output.evidence_ids = [references.get(key, key) for key in output.evidence_ids]
    tool = getattr(output, "tool_call", None)
    if tool and tool.statement_id is not None:
        tool.statement_id = references.get(tool.statement_id, tool.statement_id)


def response_sources(memory, evidence_ids):
    """Uncited model text may depend on any supplied memory; never restore it after deletion."""
    visible = visible_memories(memory)
    ids = {m["id"] for m in visible}
    return [key for key in evidence_ids if key in ids] if evidence_ids else [m["id"] for m in visible]


def learn_scene(bundle, loop, states, observations):
    current = {o.observation_id: o for o in observations
               if o.loop_id == str(loop.id) and o.beat == loop.beat}
    absent = tuple(c.name for c in bundle.characters if c.lost and loop.damage_level >= 3)
    for state in states:
        if state.name in absent:
            continue
        memory = list(state.memory or [])
        broadcast = current.get(f"{loop.id}:broadcast-{loop.beat}")
        if broadcast and not any(name in broadcast.text for name in absent):
            memory = add_memory(memory, memory_id=broadcast.observation_id, beat=loop.beat,
                kind="들은 방송", text=broadcast.text, speaker=broadcast.actor,
                listeners=[state.name])
        for action in bundle.scene_actions:
            if action.beat != loop.beat or (state.name != action.actor and state.name not in action.witnesses):
                continue
            observation = current.get(f"{loop.id}:action-{loop.beat}-{action.actor}-{action.action}")
            if observation is None:
                continue
            occurred = observation.verification == "observed" and observation.text == action.narration
            if state.name == action.actor:
                kind = "내가 한 일" if occurred else "하지 않은 일"
                detail = (action.explanation or action.narration) if occurred else f"오늘은 {action.action} 행동을 하지 않았다."
                account = next((a for a in action.experience_accounts if occurred
                                and not any(name in a.text for name in absent)
                                and actions_occurred(bundle, loop, observations, a.required_actions)), None)
                if account:
                    detail = account.text
                if occurred and action.known_source:
                    detail += " " + action.known_source
            else:
                kind, detail = "직접 본 일", observation.text
            if any(name in detail for name in absent):
                continue
            memory = add_memory(memory, memory_id=observation.observation_id, beat=loop.beat,
                kind=kind, text=detail, speaker=action.actor, listeners=[state.name],
                source_ids=[f"{loop.id}:action-{r.beat}-{r.actor}-{r.action}" for r in account.required_actions]
                if state.name == action.actor and account else [])
            if occurred:
                spoken_details = {f"{action.actor}: {line}" for line in (action.known_source, explanation_line(bundle, action)) if line}
                for speech in current.values():
                    if (speech.source_kind != "statement" or not speech.rule_id
                            or speech.actor != action.actor or speech.text not in spoken_details
                            or any(name in speech.text for name in absent)):
                        continue
                    memory = add_memory(memory, memory_id=speech.observation_id, beat=loop.beat,
                        kind="내가 한 말" if state.name == action.actor else "들은 말",
                        text=speech.text, speaker=action.actor, listeners=[state.name],
                        source_ids=[observation.observation_id])
        for index, fragment in enumerate(bundle.fragments):
            if fragment.source_kind != "statement" or (state.name != fragment.actor and state.name not in fragment.witnesses):
                continue
            speech = current.get(f"{loop.id}:fragment-{index}")
            if speech and not any(name in speech.text for name in absent):
                memory = add_memory(memory, memory_id=speech.observation_id, beat=loop.beat,
                    kind="내가 한 말" if state.name == fragment.actor else "들은 말",
                    text=speech.text, speaker=fragment.actor, listeners=[state.name])
        state.memory = memory


_DIGITS_RE = re.compile(r"\d+")
_TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2})|시\s*(\d{1,2})분)")
_HOUR_RE = re.compile(r"(\d{1,2})시")
# 근거 쪽 수사 표기 — 겹치는 일상어("한"·"네"·"세")까지 허용 쪽으로만 넓혀 오탐을 줄인다.
_NUMERAL_WORDS = {"1": ("하나", "한"), "2": ("둘", "두"), "3": ("셋", "세"), "4": ("넷", "네"),
                  "5": ("다섯",), "6": ("여섯",), "7": ("일곱",), "8": ("여덟",), "9": ("아홉",), "10": ("열",)}


def _numbers(text):
    """시각(시·분 쌍), 분 없는 시, 나머지 맨숫자를 나눠 뽑는다. '07:05'와 '7시 5분'은 같은 쌍이다."""
    times = [(str(int(h)), str(int(m or m2))) for h, m, m2 in _TIME_RE.findall(text)]
    rest = _TIME_RE.sub(" ", text)
    return times, [str(int(h)) for h in _HOUR_RE.findall(rest)], _DIGITS_RE.findall(_HOUR_RE.sub(" ", rest))


def grounded_number_check(bundle, character, memory, damage_level, *, question, beat, field="reply"):
    """테스터9 F14 — 지식·보이는 기억·지금 질문·지금까지의 공개 장면 텍스트 어디에도 없는 아라비아 숫자는 지어낸 값으로 본다.

    공개 장면 텍스트는 오늘 지나온 비트의 제목·서술·방송이다("기상 — 7:12"). 시각은 시·분 쌍으로 대조해
    "7:12"와 "7시 12분"을 같게 보고, 근거 시각의 7·12가 맨숫자("내 거는 7이야")의 근거가 되지는 않는다.
    엔진 아침 문장의 4회차 "7시 13분"은 주인공 시점 손상 연출이라 넣지 않는다.
    """
    absent = tuple(c.name for c in bundle.characters if c.lost and damage_level >= 3)
    public = [text for b in bundle.beats if b.n <= beat for text in (b.title, b.narration, b.broadcast or "")
              if not any(name in text for name in absent)]
    sources = " ".join([question, *(k.text for k in character.knowledge),
                        *(m["text"] for m in visible_memories(memory, excluded_names=absent)), *public])
    times, hours, digits = _numbers(sources)
    allowed = set(digits) | set(hours) | {
        digit for digit, words in _NUMERAL_WORDS.items() if any(w in sources for w in words)}
    allowed_hours = allowed | {h for h, _ in times}

    def check(output):
        said_times, said_hours, said_digits = _numbers(str(getattr(output, field, None) or ""))
        invented = ([f"{h}:{m}" for h, m in said_times if (h, m) not in times]
                    + [h for h in said_hours if h not in allowed_hours]
                    + [n for n in said_digits if n not in allowed])
        if invented:
            return (f"unsupported_number: {invented[:3]} in {field} — 기억과 질문에 없는 숫자 값은 말하지 않는다. "
                    "모르는 값은 모른다고 답한다")
        return None
    return check


_WENT_RE = re.compile(r"([가-힣]{2,})(?:에|까지)\s*갔")
_DENIAL = r"(?:에|엔|에는|까지는?|까진)?\s*(?:(?:직접|오늘은?)\s*)*(?:가지 않았|안 갔|못 갔|간 (?:적|일|게)[은이]? 없)"


_CLAUSE_BREAK_RE = re.compile(r"[.!?\n,]|는데|지만")
_OTHER_DAY_RE = re.compile(r"어제|그저께|전에|내일")
_FIRST_PERSON_RE = re.compile(r"(?<![가-힣])(?:난|내가|나[는도만]?|우리[는도가]?)(?![가-힣])")


def own_action_denial_check(memory, *, names, field="reply"):
    """테스터9 F14 — 보이는 '내가 한 일' 기억에 간 곳을 안 갔다고 부정하면 거부한다.

    부정이 든 절(문장·쉼표·'는데'·'지만'으로 자른 앞부분)에 다른 시점어가 있거나,
    나를 가리키는 말 없이 다른 인물 이름이 있으면 내 오늘 행동의 부정이 아니다.
    """
    own = [m for m in visible_memories(memory) if m["kind"] == "내가 한 일"]
    places = {place for m in own for place in _WENT_RE.findall(m["text"])}
    denials = {place: re.compile(re.escape(place) + _DENIAL) for place in places}
    others = re.compile("|".join(f"(?<![가-힣]){re.escape(n)}" for n in names
                                 if n not in {m["speaker"] for m in own}) or r"(?!)")

    def denies_own_visit(text, match):
        start = max((b.end() for b in _CLAUSE_BREAK_RE.finditer(text, 0, match.start())), default=0)
        clause = text[start:match.end()]
        about_other = bool(others.search(clause)) and not _FIRST_PERSON_RE.search(clause)
        return not (_OTHER_DAY_RE.search(clause) or about_other)

    def check(output):
        text = str(getattr(output, field, None) or "")
        denied = next((place for place, pattern in denials.items()
                       if any(denies_own_visit(text, m) for m in pattern.finditer(text))), None)
        if denied:
            return (f"own_action_denial: '{denied}' in {field} — 오늘 내 행동 기억에 그곳에 간 일이 있다. "
                    "안 갔다고 하지 말고 기억에 적힌 만큼 말한다")
        return None
    return check


def context_output_check(bundle, character, memory, damage_level):
    references = evidence_reference_map(bundle, character, memory, damage_level)
    allowed = set(references) | set(references.values())
    targets = {ref for c in bundle.characters if c.playable and not (c.lost and damage_level >= 3)
               for ref in (c.code, c.name)}

    def check(output):
        if any(key not in allowed for key in output.evidence_ids):
            return "evidence_ids: 제공된 지식·기억 ID만 사용할 수 있다"
        tool = getattr(output, "tool_call", None)
        if tool and (tool.target not in targets or tool.target in (character.code, character.name)):
            return "tool_target: 현재 대화 가능한 다른 인물만 선택한다"
        if tool and tool.statement_id is not None and tool.statement_id not in allowed:
            return "statement_id: 오늘 직접 들은 발언의 ID만 사용할 수 있다"
        return None
    return check
