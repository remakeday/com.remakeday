"""하루(낮) 유스케이스 — 회차 시작·발화·비트·원숭이손·노트."""

import json
import uuid
from base64 import urlsafe_b64encode
from contextlib import nullcontext

from apps.engine.app.dtos import event_log_dto as ev
from apps.engine.app.dtos.llm_output_dto import (
    AgentOutput,
    AskNpcOutput,
    PlannerOutput,
    planner_output,
)
from apps.engine.app.use_cases import prompts
from apps.engine.app.ports.output.scene_transaction_port import SceneTransactionPort
from apps.engine.app.use_cases.public_observations import disclose, public_observations
from apps.engine.app.use_cases.question_replies import question_reply
from apps.engine.app.use_cases.npc_context import learn_scene, context_output_check, resolve_output_sources, response_sources
from apps.engine.app.use_cases.scene_execution import execute_scene, EXPLAIN_ACTION
from apps.engine.app.use_cases.game_support import (
    build_agent_messages,
    lost_names,
    pick_fallback_line,
    record_harness,
    resolve_npc_code,
    system_msg,
    user_msg,
)
from apps.engine.app.use_cases.utterance_classifier import classify
from apps.engine.app.use_cases.harness import (
    action_vocab_check,
    forbidden_word_check,
    korean_only_check,
    lost_character_check,
    run_with_harness,
    unknown_person_check,
)
from apps.engine.domain.entities import loop_rules, npc_rules
from apps.engine.domain.entities.npc_memory import add_memory, forget_memory, hidden_memory_ids, visible_memories
from apps.engine.domain.entities.question_rules import is_question_action, question_matches
from apps.engine.domain.entities.cookie_rules import ab_assign, paw_should_offer
from apps.engine.domain.entities.utterance_rules import is_nonsense
from apps.engine.domain.entities.rule_rules import (
    Rule,
    enforce_rules_on_plan,
    narration_with_rule_note,
    rules_for_npc,
)
from apps.engine.domain.value_objects.game_constants import (
    ASK_TARGET_SUSPICION,
    LOOPS_PER_ATTEMPT,
    MANAGER_BUDGET_PER_LOOP,
    MANAGER_CHECK_BEATS,
    MISMATCH_SPEAKER_SUSPICION,
)

MORNING_FIRST = "7시 12분. 눈을 뜬다."
MORNING_SHIFTED = "7시 13분. 눈을 뜬다."

# suppress 치환용 중립 행동 후보 — 시나리오 vocab에 있는 것을 고른다
_NEUTRAL_ACTION_CANDIDATES = ("혼자 있는다", "쉰다", "말을 아낀다")


def neutral_action_for(vocab: list[str]) -> str:
    return next((c for c in _NEUTRAL_ACTION_CANDIDATES if c in vocab), vocab[0])


class GameStateError(Exception):
    """잘못된 상태 전이 — 라우터가 409로 매핑."""


class DialogueUnavailable(Exception):
    """A failed provider response is not a character's ignorance or a paid turn."""


class LoopInteractor:
    def __init__(
        self, *, attempts, loops, notes, rules, event_log, scenario,
        npc_llm, core_llm, manager, harness_on: bool, age7_on: bool,
        paw_reason_ab_on: bool, loop_cls, npc_state_cls, rule_cls,
        scene_transaction: SceneTransactionPort = nullcontext,
    ) -> None:
        self._loop_cls = loop_cls
        self._npc_state_cls = npc_state_cls
        self._rule_orm_cls = rule_cls
        self._attempts = attempts
        self._loops = loops
        self._notes = notes
        self._rules = rules
        self._events = event_log
        self._scenario = scenario
        self._npc_llm = npc_llm
        self._core_llm = core_llm
        self._manager = manager
        self._harness_on = harness_on
        self._age7_on = age7_on
        self._paw_reason_ab_on = paw_reason_ab_on
        self._scene_transaction = scene_transaction

    # ── 회차 시작 ──────────────────────────────────────────────

    def start_loop(self, attempt_id: uuid.UUID) -> dict:
        with self._scene_transaction():
            return self._start_loop(attempt_id)

    def _start_loop(self, attempt_id: uuid.UUID) -> dict:
        loop_orm_cls, npc_state_orm_cls = self._loop_cls, self._npc_state_cls
        attempt = self._attempts.get(attempt_id)
        if attempt is None or attempt.status != "active":
            raise GameStateError("활성 판이 아니다")
        prev = self._loops.latest_for(attempt_id)
        if prev is not None and prev.state != "closed":
            raise GameStateError("이전 회차가 아직 닫히지 않았다")
        loop_n = (prev.loop_n + 1) if prev else 1
        if loop_n > LOOPS_PER_ATTEMPT:
            raise GameStateError("5회차가 끝났다 — 판이 닫혔어야 한다")

        damage, shifted = loop_rules.damage_for_loop(loop_n)
        state = loop_rules.start_loop(loop_n)
        bundle = self._scenario.bundle()

        prev_states = {s.code: s for s in self._loops.npc_states(prev.id)} if prev else {}
        npc_states = []
        for c in bundle.characters:
            if not c.playable:
                continue
            gauge = npc_rules.NpcGauge(c.initial_suspicion, c.initial_trust, False)
            if c.code in prev_states:
                p = prev_states[c.code]
                gauge = npc_rules.carry_over(
                    npc_rules.NpcGauge(p.suspicion, p.trust, p.opposite_mode)
                )
            npc_states.append(
                npc_state_orm_cls(
                    code=c.code, name=c.name,
                    suspicion=gauge.suspicion, trust=gauge.trust,
                    opposite_mode=gauge.opposite_mode, memory=[], plan=None,
                )
            )

        loop = loop_orm_cls(
            attempt_id=attempt_id, loop_n=loop_n, beat=1,
            budget_left=state.budget_left, ask_budget_left=state.ask_budget_left,
            manager_budget_left=MANAGER_BUDGET_PER_LOOP,
            state="day", damage_level=damage, morning_shifted=shifted,
        )
        self._loops.create(loop, npc_states)

        self._run_planner(loop, bundle)

        rule_rows = self._rules.list(attempt_id)
        self._events.record(
            attempt_id,
            ev.LoopStartEvent(
                session=str(attempt_id), loop_n=loop_n,
                cumulative_loop_n=(attempt.attempt_n - 1) * LOOPS_PER_ATTEMPT + loop_n,
                budget=state.budget_left, rule_count=len(rule_rows), damage=damage,
                measurement_version="connected-investigation-1",
            ),
        )

        first = MORNING_SHIFTED if shifted else MORNING_FIRST
        beat1 = execute_scene(self._events, loop, bundle, rule_rows)
        observations, note_found = self._disclose_scene(loop, bundle, beat1)
        ambient = self._make_ambient(loop, bundle)
        observations = [o.model_dump() for o in public_observations(self._events, loop.attempt_id)
                        if o.loop_id == str(loop.id) and o.beat == 1]
        self._loops.save()
        # 직전 회차의 규칙 부작용 흔적 — 내용은 밝히지 않는다 (엔진 고정 문장)
        aftermath = (
            "어제는 없던 일이 있었다."
            if prev is not None and (prev.side_effect_claims or [])
            else None
        )
        return {
            "loop_id": str(loop.id),
            "loop_n": loop_n,
            "morning_text": f"{first} {self._scenario.morning_line(damage)}".strip(),
            "damage_level": damage,
            "budget_left": loop.budget_left,
            "beat": 1,
            "beat_title": beat1.title,
            "narration": beat1.narration,
            "broadcast": beat1.broadcast,
            "illustrations": [i.model_dump() for i in beat1.illustrations],
            "aftermath": aftermath,
            "observations": observations,
            "note_found": note_found,
            "ambient": ambient,
            "active_rules": [
                r.shown_reason
                or f"{r.target}: {r.action} {'금지' if r.effect == 'suppress' else '강제'}"
                for r in rule_rows
            ],
        }

    def _run_planner(self, loop, bundle) -> None:
        npcs_desc = "\n".join(
            f"- {c.name}: {c.persona} / 목표: {c.goal} / {c.relations}"
            for c in bundle.characters if c.playable
        )
        rule_rows = [r for r in self._rules.list(loop.attempt_id) if not is_question_action(r.action)]
        sys = prompts.PLANNER_SYSTEM.format(
            action_vocab=", ".join(bundle.action_vocab),
            surface_summary=bundle.surface_summary,
            npcs=npcs_desc,
            rules="\n".join(self._rule_text(r) for r in rule_rows) or "(없음)",
            damage_level=loop.damage_level,
        )
        checks = [action_vocab_check(
            bundle.action_vocab,
            getter=lambda o: [b.action for p in o.plans for b in p.beats],
        )]
        out, report = run_with_harness(
            self._core_llm, [system_msg(sys)], planner_output(bundle.action_vocab),
            role="planner", fact_checks=checks, harness_on=self._harness_on,
        )
        record_harness(self._events, loop.attempt_id, report, loop_n=loop.loop_n, beat=None)
        by_code = {s.code: s for s in self._loops.npc_states(loop.id)}
        if out is not None:
            for plan in out.plans:
                code = resolve_npc_code(bundle, plan.npc)
                if code and code in by_code:
                    by_code[code].plan = [b.model_dump() for b in plan.beats]
        # 규칙 결정적 강제 — Planner 출력·폴백과 무관하게 계획을 기계 보정한다.
        # 폴백(계획 없음)이어도 enforce 규칙은 최소 계획을 만들어 저장한다.
        domain_rules = [self._to_domain_rule(r) for r in rule_rows]
        neutral = neutral_action_for(bundle.action_vocab)
        for s in by_code.values():
            npc_rule_list = [r for r in domain_rules if r.target == s.name]
            if not npc_rule_list:
                continue
            s.plan = enforce_rules_on_plan(
                list(s.plan or []), npc_rule_list, neutral_action=neutral
            ) or None
        self._loops.save()

    # ── 발화 ──────────────────────────────────────────────────

    def utter(self, loop_id: uuid.UUID, target: str, text: str, *, request_id=None) -> dict:
        with self._scene_transaction(loop_id):
            return self._utter(loop_id, target, text, request_id=request_id)

    def _utter(self, loop_id: uuid.UUID, target: str, text: str, *, request_id=None) -> dict:
        loop = self._loops.get(loop_id)
        if loop is None:
            raise GameStateError("회차가 없다")
        if not text.strip():
            raise GameStateError("질문을 적어 주세요")
        bundle = self._scenario.bundle()
        code = resolve_npc_code(bundle, target)
        utterance_id = str(request_id or uuid.uuid4())
        # Full UUID entropy in 22 characters fits existing note source_key VARCHAR(64).
        observation_key = "u-" + urlsafe_b64encode(uuid.UUID(utterance_id).bytes).decode().rstrip("=")
        if request_id:
            for event in self._events.query(loop.attempt_id, type=ev.EventType.UTTERANCE, loop_n=loop.loop_n):
                if getattr(event, "utterance_id", None) != utterance_id or not event.response:
                    continue
                if resolve_npc_code(bundle, event.target) != code or event.text != text:
                    raise GameStateError("같은 요청 번호에 다른 질문을 보낼 수 없다")
                return event.response
        npc = self._loops.npc_state(loop_id, code) if code else None
        char = next((c for c in bundle.characters if c.code == code), None)
        if npc is None or char is None:
            raise GameStateError("대화할 수 없는 상대다")
        if char.lost and loop.damage_level >= 3:
            raise GameStateError("대화할 수 없는 상대다")
        if npc.uttered_beat == loop.beat:
            raise GameStateError("이 장면에서는 이미 대화했다. 다른 인물을 고르거나 다음 장면으로 이동해 주세요.")
        if loop.state != "day":
            raise GameStateError("낮이 아니면 발화할 수 없다")

        classification = None
        if is_nonsense(text):
            return self._gated_reply(loop, char, text, utterance_id, classification)

        try:
            state = loop_rules.apply_utterance(self._loop_state(loop))
        except loop_rules.DomainError as e:
            raise GameStateError(str(e)) from e

        label, report = classify(self._core_llm, text)
        record_harness(self._events, loop.attempt_id, report, loop_n=loop.loop_n, beat=loop.beat)
        classification = label
        if classification == "nonsense":
            return self._gated_reply(loop, char, text, utterance_id, classification)
        include_knowledge = classification != "chat"

        rule_rows = self._rules.list(loop.attempt_id)
        domain_rules = [self._to_domain_rule(r) for r in rule_rows]
        active_rules = [r for r in rules_for_npc(domain_rules, char.name, loop.beat)
                        if not is_question_action(r.action) or question_matches(r.action, text)]
        question_rules = [r for r in active_rules if is_question_action(r.action) and r.effect == "enforce"]
        npc_rule_text = "\n".join(
            self._rule_line(r) for r in active_rules
        )

        messages = build_agent_messages(
            bundle, char,
            suspicion=npc.suspicion, trust=npc.trust, opposite=npc.opposite_mode,
            rules_text=npc_rule_text, memory=list(npc.memory or []),
            user_text=text, loop_n=loop.loop_n, age7_on=self._age7_on, damage_level=loop.damage_level,
            include_knowledge=include_knowledge,
        )
        messages[0].content += f"\n현재 장면: {bundle.beats[loop.beat - 1].title}. 아직 하지 않은 행동을 지어내지 않는다."
        seen = public_observations(self._events, loop.attempt_id, through_loop=loop.loop_n)
        authored_reply = (question_reply(bundle, char, loop, seen, question_rules[-1].action,
                                        hidden_ids=hidden_memory_ids(npc.memory or []))
                          if question_rules else None)
        from apps.engine.app.use_cases.game_support import applicable_ban_words

        checks = [
            forbidden_word_check(
                applicable_ban_words(bundle, char.code, loop.loop_n),
                fields=["reply"],
            ),
            lost_character_check(lost_names(bundle, loop.damage_level), fields=["reply"]),
            unknown_person_check([c.name for c in bundle.characters], fields=["reply"]),
            korean_only_check(fields=["reply"]),
            context_output_check(bundle, char, npc.memory or [], loop.damage_level),
        ]
        if authored_reply is not None:
            out = AgentOutput(reply=authored_reply, suspicion_delta=0, trust_delta=0, mood=npc.mood)
        else:
            out, report = run_with_harness(
                self._npc_llm, messages, AgentOutput,
                role="agent", fact_checks=checks, harness_on=self._harness_on, retry_feedback=True, temperature=0.3,
            )
            record_harness(self._events, loop.attempt_id, report, loop_n=loop.loop_n, beat=loop.beat)

        if out is None:
            raise DialogueUnavailable("답변을 받지 못했습니다. 같은 질문을 다시 보내 주세요. 대화 횟수는 줄지 않았습니다.")
        resolve_output_sources(out, bundle, char, npc.memory or [], loop.damage_level)
        reply, sd, td, tool_call, mood = (
            out.reply, out.suspicion_delta, out.trust_delta, out.tool_call, out.mood
        )

        gauge = npc_rules.apply_deltas(
            npc_rules.NpcGauge(npc.suspicion, npc.trust, npc.opposite_mode), sd, td
        )
        npc.suspicion, npc.trust, npc.opposite_mode = (
            gauge.suspicion, gauge.trust, gauge.opposite_mode
        )
        npc.mood = mood
        npc.uttered_beat = loop.beat
        memory_sources = response_sources(npc.memory or [], out.evidence_ids)
        npc.memory = add_memory(npc.memory or [], memory_id=f"{loop.id}:{observation_key}",
            beat=loop.beat, kind="플레이어와 나눈 말", text=f"플레이어: {text}\n{char.name}: {reply}",
            speaker=char.name, listeners=["플레이어", char.name], source_ids=memory_sources)

        loop.budget_left = state.budget_left
        tool_used = False
        if tool_call is not None:
            tool_used = self._run_ask_npc(loop, bundle, npc, char, tool_call)

        observation = disclose(
            self._events, loop, bundle.beats[loop.beat - 1],
            key=observation_key, text=reply, actor=char.name, source_kind="statement",
        )
        for rule in question_rules:
            self._events.record(loop.attempt_id, ev.RuleExecutionEvent(
                loop_n=loop.loop_n, beat=loop.beat, rule_id=rule.rule_id,
                condition=f"직접 받은 질문: {text}", actual_action=reply if out else None,
                result="obeyed" if authored_reply is not None else "not_evaluable",
                observation_ids=[observation.observation_id],
            ))
        self._notes.upsert(loop.attempt_id, kind="fragment", text=observation.text,
                           loop_n=loop.loop_n, source_key=observation.observation_id)
        response = {
            "utterance_id": utterance_id,
            "observations": [observation.model_dump()],
            "reply": reply,
            "npc": {"code": char.code, "name": char.name, "mood": mood, "uttered": True},
            "budget_left": loop.budget_left,
            "beat": loop.beat,
            "tool_used": tool_used,
        }
        self._events.record(loop.attempt_id, ev.UtteranceEvent(
            loop_n=loop.loop_n, beat=loop.beat, target=char.name, text=text,
            reply=reply, budget_left=loop.budget_left, suspicion_delta=sd, trust_delta=td,
            disclosure_level=0, utterance_id=utterance_id, response=response,
            classification=classification, gated=False, budget_charged=True))
        self._loops.save()
        return response

    def _gated_reply(self, loop, char, text, utterance_id, classification):
        """무의미 입력 — 모델 호출 없이 인물 말투로 되묻는다. 같은 비트 첫 1회는 예산 면제."""
        prior = [e for e in self._events.query(loop.attempt_id, type=ev.EventType.UTTERANCE, loop_n=loop.loop_n)
                 if e.beat == loop.beat and e.gated]
        charged = bool(prior)
        if charged:
            try:
                state = loop_rules.apply_utterance(self._loop_state(loop))
            except loop_rules.DomainError as e:
                raise GameStateError(str(e)) from e
            loop.budget_left = state.budget_left
        reply = pick_fallback_line(char)
        response = {
            "utterance_id": utterance_id, "observations": [], "reply": reply,
            "npc": {"code": char.code, "name": char.name, "mood": "calm", "uttered": False},
            "budget_left": loop.budget_left, "beat": loop.beat, "tool_used": False, "gated": True,
        }
        self._events.record(loop.attempt_id, ev.UtteranceEvent(
            loop_n=loop.loop_n, beat=loop.beat, target=char.name, text=text, reply=reply,
            budget_left=loop.budget_left, suspicion_delta=0, trust_delta=0, disclosure_level=0,
            utterance_id=utterance_id, response=response,
            classification=classification, gated=True, budget_charged=charged))
        self._loops.save()
        return response

    def _run_ask_npc(self, loop, bundle, asker_state, asker_char, tool_call) -> bool:
        target_code = resolve_npc_code(bundle, tool_call.target)
        target_state = self._loops.npc_state(loop.id, target_code) if target_code else None
        target_char = next((c for c in bundle.characters if c.code == target_code), None)
        if target_state is None or target_char is None:
            return False
        if target_code == asker_char.code or (target_char.lost and loop.damage_level >= 3):
            return False
        new_state, ok = loop_rules.consume_ask_budget(self._loop_state(loop))
        if not ok:
            return False
        rule_rows = [self._to_domain_rule(r) for r in self._rules.list(loop.attempt_id)]
        active = [r for r in rules_for_npc(rule_rows, target_char.name, loop.beat)
                  if not is_question_action(r.action) or question_matches(r.action, tool_call.question)]
        messages = build_agent_messages(bundle, target_char,
            suspicion=target_state.suspicion, trust=target_state.trust, opposite=target_state.opposite_mode,
            rules_text="\n".join(self._rule_line(r) for r in active), memory=target_state.memory or [],
            user_text=f"{asker_char.name}: {tool_call.question}", loop_n=loop.loop_n,
            age7_on=self._age7_on, damage_level=loop.damage_level, reply_field="answer")
        messages[0].content += (
            "\n다른 사람이 와서 묻는다. answer에 답한다. said_it은 현재 기억하는지이며 "
            "기억이 없으면 null이다. 기억나지 않는다는 이유로 실제로 말한 적 없다고 단정하지 않는다."
        )
        seen = public_observations(self._events, loop.attempt_id, through_loop=loop.loop_n)
        question_rules = [r for r in active if is_question_action(r.action) and r.effect == "enforce"]
        authored = (question_reply(bundle, target_char, loop, seen, question_rules[-1].action,
                                   hidden_ids=hidden_memory_ids(target_state.memory or []))
                    if question_rules else None)
        from apps.engine.app.use_cases.game_support import applicable_ban_words
        if authored is not None:
            out = AskNpcOutput(answer=authored)
        else:
            out, report = run_with_harness(self._npc_llm, messages, AskNpcOutput, role="ask_npc",
                fact_checks=[
                    forbidden_word_check(applicable_ban_words(bundle, target_char.code, loop.loop_n), fields=["answer"]),
                    lost_character_check(lost_names(bundle, loop.damage_level), fields=["answer"]),
                    unknown_person_check([c.name for c in bundle.characters], fields=["answer"]),
                    korean_only_check(fields=["answer"]),
                    context_output_check(bundle, target_char, target_state.memory or [], loop.damage_level),
                ], harness_on=self._harness_on, retry_feedback=True, temperature=0.3)
            record_harness(self._events, loop.attempt_id, report, loop_n=loop.loop_n, beat=loop.beat)
        if out is None:
            raise DialogueUnavailable("답변을 받지 못했습니다. 같은 질문을 다시 보내 주세요. 대화 횟수는 줄지 않았습니다.")
        resolve_output_sources(out, bundle, target_char, target_state.memory or [], loop.damage_level)
        answer = out.answer
        loop.ask_budget_left = new_state.ask_budget_left
        # The model's current recollection cannot establish who actually spoke.
        cited = next((o for o in seen if o.observation_id == tool_call.statement_id
                      and o.loop_id == str(loop.id) and o.source_kind == "statement"), None)
        statement_verified = cited.actor == target_char.name if cited is not None else None

        t_gauge = npc_rules.apply_event_suspicion(
            npc_rules.NpcGauge(target_state.suspicion, target_state.trust, target_state.opposite_mode),
            ASK_TARGET_SUSPICION,
        )
        target_state.suspicion, target_state.opposite_mode = t_gauge.suspicion, t_gauge.opposite_mode
        side_effect = f"{target_char.name}.suspicion +{ASK_TARGET_SUSPICION}"
        if statement_verified is False:
            a_gauge = npc_rules.apply_event_suspicion(
                npc_rules.NpcGauge(asker_state.suspicion, asker_state.trust, asker_state.opposite_mode),
                MISMATCH_SPEAKER_SUSPICION,
            )
            asker_state.suspicion, asker_state.opposite_mode = a_gauge.suspicion, a_gauge.opposite_mode
            side_effect += f" / 불일치: {asker_char.name}.suspicion +{MISMATCH_SPEAKER_SUSPICION}"
        loop.rumor_index = loop.rumor_index + 1
        utterance_id = str(uuid.uuid4())
        memory_id = f"{loop.id}:ask-{utterance_id}"
        target_state.memory = add_memory(target_state.memory or [], memory_id=memory_id,
            beat=loop.beat, kind="친구와 나눈 말", text=f"{asker_char.name}: {tool_call.question}\n{target_char.name}: {answer}",
            speaker=target_char.name, listeners=[asker_char.name, target_char.name],
            source_ids=response_sources(target_state.memory or [], out.evidence_ids))
        asker_state.memory = add_memory(asker_state.memory or [], memory_id=memory_id,
            beat=loop.beat, kind="친구에게 들은 말", text=f"{target_char.name}: {answer}",
            speaker=target_char.name, listeners=[asker_char.name, target_char.name])
        asker_state.memory = add_memory(asker_state.memory, memory_id=f"{memory_id}-question",
            beat=loop.beat, kind="친구에게 물은 말", text=tool_call.question,
            speaker=asker_char.name, listeners=[asker_char.name, target_char.name],
            source_ids=[m["id"] for m in visible_memories(asker_state.memory) if m["id"] != memory_id])
        self._events.record(
            loop.attempt_id,
            ev.ToolCallEvent(
                loop_n=loop.loop_n, beat=loop.beat, caller=asker_char.name,
                tool="ask_npc", args={"target": target_char.name, "question": tool_call.question},
                result=answer, side_effect=side_effect, utterance_id=utterance_id,
                statement_verified=statement_verified, recalled=out.said_it,
            ),
        )
        return True

    # ── 비트 경계 ──────────────────────────────────────────────

    def advance_beat(self, loop_id: uuid.UUID) -> dict:
        with self._scene_transaction(loop_id):
            return self._advance_beat(loop_id)

    def _advance_beat(self, loop_id: uuid.UUID) -> dict:
        loop = self._loops.get(loop_id)
        if loop is None:
            raise GameStateError("회차가 없다")
        try:
            state = loop_rules.next_beat(self._loop_state(loop))
        except loop_rules.DomainError as e:
            raise GameStateError(str(e)) from e

        loop.beat, loop.state = state.beat, state.state
        if state.state == "night_pending":
            self._loops.save()
            return {"beat": loop.beat, "beat_title": "", "narration": "", "broadcast": None,
                    "paw_offer": None, "day_done": True, "ambient": None, "note_found": None,
                    "illustrations": [], "observations": [], "budget_left": loop.budget_left}

        bundle = self._scenario.bundle()
        if loop.beat in MANAGER_CHECK_BEATS:
            self._manager_check(loop, bundle)
        paw_offer = self._maybe_offer_paw(loop, bundle)
        beat = execute_scene(self._events, loop, bundle, self._rules.list(loop.attempt_id))
        observations, note_found = self._disclose_scene(loop, bundle, beat)
        ambient = self._make_ambient(loop, bundle)
        observations = [o.model_dump() for o in public_observations(self._events, loop.attempt_id)
                        if o.loop_id == str(loop.id) and o.beat == loop.beat]
        self._loops.save()

        narration = beat.narration
        return {
            "beat": loop.beat, "beat_title": beat.title, "narration": narration,
            "budget_left": loop.budget_left,
            "broadcast": beat.broadcast, "paw_offer": paw_offer, "day_done": False,
            "illustrations": [i.model_dump() for i in beat.illustrations],
            "ambient": ambient, "note_found": note_found, "observations": observations,
        }

    def _make_ambient(self, loop, bundle) -> dict | None:
        """Play eligible authored scene speech without a model call or conversation cost."""
        current = {o.observation_id: o for o in public_observations(self._events, loop.attempt_id)
                   if o.loop_id == str(loop.id) and o.beat == loop.beat}
        if f"{loop.id}:scene-{loop.beat}" not in current:
            return None
        available = {c.code: c for c in bundle.characters
                     if c.playable and not (c.lost and loop.damage_level >= 3)}
        actions = {(a.actor, a.action): a for a in bundle.scene_actions if a.beat == loop.beat}
        absent = lost_names(bundle, loop.damage_level)
        for dialogue in bundle.scene_dialogues:
            if dialogue.beat != loop.beat:
                continue
            codes = list(dict.fromkeys(line.code for line in dialogue.lines))
            if any(code not in available for code in codes):
                continue
            states = {code: self._loops.npc_state(loop.id, code) for code in codes}
            if any(state is None for state in states.values()):
                continue
            if any(name in line.text for name in absent for line in dialogue.lines):
                continue
            eligible = True
            for required in dialogue.required_actions:
                action = actions.get((required.actor, required.action))
                observation = current.get(f"{loop.id}:action-{loop.beat}-{required.actor}-{required.action}")
                if (action is None or observation is None or observation.verification != "observed"
                        or observation.actor != required.actor or observation.text != action.narration):
                    eligible = False
                    break
            if not eligible:
                continue
            required_ids = {f"{loop.id}:action-{loop.beat}-{r.actor}-{r.action}" for r in dialogue.required_actions}
            if any(required_ids & hidden_memory_ids(s.memory or []) for s in states.values()):
                continue
            lines = [{"code": line.code, "name": available[line.code].name, "text": line.text}
                     for line in dialogue.lines]
            for index, line in enumerate(lines):
                observation = disclose(self._events, loop, bundle.beats[loop.beat - 1],
                    key=f"ambient-{loop.beat}-{index}", text=line["text"], actor=line["name"],
                    source_kind="statement")
                for npc in states.values():
                    npc.memory = add_memory(npc.memory or [], memory_id=observation.observation_id,
                        beat=loop.beat, kind="함께 나눈 말", text=f"{line['name']}: {line['text']}",
                        speaker=line["name"], listeners=[available[code].name for code in codes],
                        source_ids=sorted(required_ids))
                self._notes.upsert(loop.attempt_id, kind="fragment", text=observation.text,
                    loop_n=loop.loop_n, source_key=observation.observation_id)
                self._events.record(loop.attempt_id, ev.UtteranceEvent(
                    loop_n=loop.loop_n, beat=loop.beat, target=line["name"],
                    text="(지나가는 말)", reply=line["text"], budget_left=loop.budget_left,
                    suspicion_delta=0, trust_delta=0, disclosure_level=0,
                    utterance_id=observation.observation_id))
            return {"lines": lines}
        return None

    def _disclose_scene(self, loop, bundle, beat=None):
        beat = beat or bundle.beats[loop.beat - 1]
        observations = []
        scene = disclose(self._events, loop, beat, key=f"scene-{beat.n}",
                         text=beat.narration, illustrations=beat.illustrations)
        observations.append(scene)
        if beat.broadcast:
            observations.append(disclose(self._events, loop, beat, key=f"broadcast-{beat.n}",
                                         text=beat.broadcast, source_kind="statement"))
        for image in beat.illustrations:
            observations.append(disclose(self._events, loop, beat, key=f"image-{beat.n}-{image.image_id}",
                                         text=image.caption, source_kind="image", illustrations=[image]))
        for i, fragment in enumerate(bundle.fragments):
            if fragment.loop_n != loop.loop_n or fragment.beat != loop.beat or fragment.world_outcome:
                continue
            if loop.damage_level >= 3 and any(c.lost and c.name in fragment.text for c in bundle.characters):
                continue
            observations.append(disclose(self._events, loop, beat, key=f"fragment-{i}", text=fragment.text,
                                         actor=fragment.actor, source_kind=fragment.source_kind))
        observations = [o for o in public_observations(self._events, loop.attempt_id)
                        if o.loop_id == str(loop.id) and o.beat == loop.beat]
        first = None
        for observation in observations:
            row = self._notes.upsert(loop.attempt_id, kind="rule_observation" if observation.rule_id else "fragment", text=observation.text,
                                     loop_n=loop.loop_n, source_key=observation.observation_id)
            if row is not None and first is None:
                first = {"id": row.id, "kind": row.kind, "text": row.text}
        current = [o for o in public_observations(self._events, loop.attempt_id)
                   if o.loop_id == str(loop.id) and o.beat == loop.beat]
        learn_scene(bundle, loop, self._loops.npc_states(loop.id), current)
        return [o.model_dump() for o in current], first

    def _manager_check(self, loop, bundle) -> None:
        if loop.manager_budget_left <= 0:
            return
        states = self._loops.npc_states(loop.id)
        utter_events = self._events.query(loop.attempt_id, type=ev.EventType.UTTERANCE, loop_n=loop.loop_n)
        rule_rows = self._rules.list(loop.attempt_id)
        prev = self._prev_score(loop)
        patches, flagged, report = self._manager.check(
            npc_states=[
                {"name": s.name, "suspicion": s.suspicion, "trust": s.trust,
                 "memory": visible_memories(s.memory or []), "plan": s.plan}
                for s in states
            ],
            user_utterances=[e.text for e in utter_events if not getattr(e, "gated", False)],
            rules=[self._rule_text(r) for r in rule_rows],
            budget_left=loop.manager_budget_left,
            yesterday_score=prev,
        )
        if report:
            record_harness(self._events, loop.attempt_id, report, loop_n=loop.loop_n, beat=loop.beat)
        by_name = {ref: s for s in states for ref in (s.name, s.code)}
        outcomes = []
        for p in patches:
            s = by_name.get(p.npc)
            applied, failure = False, None
            if s is None:
                failure = "대상 인물이 없음"
            elif loop.manager_budget_left <= 0:
                failure = "보정 예산 없음"
            elif p.kind == "memory_delete":
                s.memory, applied = forget_memory(s.memory or [], p.target)
                if not applied:
                    failure = "현재 기억에 없는 ID"
            else:
                failure = "적용 가능한 계획 수정이 없음"
            outcomes.append(ev.ManagerPatch(npc=p.npc, kind=p.kind, detail=p.target, reason=p.reason,
                                             applied=applied, failure_reason=failure))
            if applied:
                loop.manager_budget_left -= 1
        for name in flagged:
            if name in by_name:
                by_name[name].flagged_abnormal = True
        if outcomes or flagged:
            self._events.record(
                loop.attempt_id,
                ev.ManagerCheckEvent(
                    loop_n=loop.loop_n, beat=loop.beat,
                    patches=outcomes,
                    budget_left=loop.manager_budget_left,
                ),
            )

    def _maybe_offer_paw(self, loop, bundle) -> dict | None:
        if loop.beat != 2 or loop.pending_paw is not None:
            return None
        attempt = self._attempts.get(loop.attempt_id)
        if not paw_should_offer(loop.loop_n, self._prev_score(loop), attempt.paw_offered_count):
            return None
        active_rules = self._rules.list(loop.attempt_id)
        future = next((a for a in bundle.scene_actions if a.beat > loop.beat
                       and not any(r.target == a.actor and r.action == EXPLAIN_ACTION
                                   and (r.when_beat is None or r.when_beat == a.beat)
                                   for r in active_rules)), None)
        if future is None:
            return None
        spec = {"target": future.actor, "when_beat": future.beat,
                "action": EXPLAIN_ACTION, "effect": "enforce"}
        shown_reason = f"{future.actor}이(가) 다음에 직접 한 일을 말로 설명한다. 놓친 관찰을 들을 수 있다."
        hidden_side_effect = "설명을 듣는 장면에서 발화 여유가 남아 있으면 1회 줄어든다. 없으면 대가는 발생하지 않는다."
        attempt.paw_offered_count += 1
        offer_id = str(uuid.uuid4())[:8]
        show_reason = (not self._paw_reason_ab_on) or ab_assign(str(loop.attempt_id))
        label = f"{future.actor}: {EXPLAIN_ACTION} — 강제"
        loop.pending_paw = {
            "offer_id": offer_id, "offer_index": attempt.paw_offered_count,
            "rule": spec, "shown_reason": shown_reason,
            "hidden_side_effect": hidden_side_effect, "label": label,
            "show_reason": show_reason,
        }
        self._attempts.save()
        return {
            "offer_id": offer_id, "rule_label": label,
            "shown_reason": shown_reason if show_reason else None,
        }

    def respond_paw(self, loop_id: uuid.UUID, offer_id: str, accept: bool) -> dict:
        loop = self._loops.get(loop_id)
        if loop is None or not loop.pending_paw or loop.pending_paw["offer_id"] != offer_id:
            raise GameStateError("유효한 원숭이손 오퍼가 없다")
        paw = loop.pending_paw
        rule_label = None
        rule_id = self._rules.next_rule_id(loop.attempt_id)
        if accept:
            spec = paw["rule"]
            when = spec["when_beat"]
            self._rules.add(self._rule_orm_cls(
                attempt_id=loop.attempt_id, rule_id=rule_id, source="monkey_paw",
                target=spec["target"], when_beat=None if when == "any" else when,
                effect=spec["effect"], action=spec["action"],
                shown_reason=paw["shown_reason"] if paw["show_reason"] else None,
                hidden_side_effect=paw["hidden_side_effect"], created_loop=loop.loop_n,
            ))
            self._events.record(loop.attempt_id, ev.RuleAppliedEvent(
                loop_n=loop.loop_n, rule_id=rule_id, source="monkey_paw", conflict=False,
            ))
            rule_label = paw["label"]
        self._events.record(loop.attempt_id, ev.MonkeyPawOfferEvent(
            loop_n=loop.loop_n, beat=loop.beat, offer_index=paw["offer_index"],
            rule_id=rule_id if accept else "-",
            reason_shown=paw["shown_reason"] if paw["show_reason"] else None,
            accepted=accept,
        ))
        loop.pending_paw = None
        self._loops.save()
        return {"applied": accept, "rule_label": rule_label}

    # ── 조회 ──────────────────────────────────────────────────

    def list_notes(self, loop_id: uuid.UUID) -> dict:
        loop = self._loops.get(loop_id)
        if loop is None:
            raise GameStateError("회차가 없다")
        rows = self._notes.list(loop.attempt_id)
        observations = {o.observation_id: o.model_dump() for o in
                        public_observations(self._events, loop.attempt_id, through_loop=loop.loop_n)}
        return {"notes": [
            {"id": r.id, "kind": r.kind, "text": r.text, "loop_n": r.loop_n,
             "observation_ids": [r.source_key] if r.source_key in observations else [],
             "sources": [observations[r.source_key]] if r.source_key in observations else []}
            for r in rows if r.loop_n <= loop.loop_n
        ]}

    def list_observations(self, loop_id):
        loop = self._loops.get(loop_id)
        if loop is None:
            raise GameStateError("회차가 없다")
        return {"observations": [o.model_dump() for o in
                public_observations(self._events, loop.attempt_id, through_loop=loop.loop_n)]}

    def list_npcs(self, loop_id: uuid.UUID) -> dict:
        loop = self._loops.get(loop_id)
        if loop is None:
            raise GameStateError("회차가 없다")
        bundle = self._scenario.bundle()
        states = {s.code: s for s in self._loops.npc_states(loop.id)}
        npcs = []
        for c in bundle.characters:
            if not c.playable or (c.lost and loop.damage_level >= 3):
                continue
            st = states.get(c.code)
            npcs.append({
                "code": c.code, "name": c.name, "mood": st.mood if st else "calm",
                "uttered": bool(st and st.uttered_beat == loop.beat),
            })
        return {"npcs": npcs}

    # ── 내부 ──────────────────────────────────────────────────

    def _loop_state(self, loop) -> loop_rules.LoopState:
        return loop_rules.LoopState(
            loop_n=loop.loop_n, beat=loop.beat, budget_left=loop.budget_left,
            ask_budget_left=loop.ask_budget_left, state=loop.state,
        )

    def _prev_score(self, loop) -> float | None:
        if loop.loop_n <= 1:
            return None
        return self._loops.score_of(loop.attempt_id, loop.loop_n - 1)

    def _to_domain_rule(self, r) -> Rule:
        return Rule(
            rule_id=r.rule_id, source=r.source, target=r.target,
            when_beat=r.when_beat, effect=r.effect, action=r.action,
            created_loop=r.created_loop,
        )

    @staticmethod
    def _rule_line(r: Rule) -> str:
        beat = "하루 종일" if r.when_beat is None else f"비트 {r.when_beat}"
        verb = "하지 않는다" if r.effect == "suppress" else "한다"
        return f"[{r.rule_id}] {r.target}은(는) {beat}에 {r.action} — 반드시 {verb}"

    def _rule_text(self, r) -> str:
        return self._rule_line(self._to_domain_rule(r))
