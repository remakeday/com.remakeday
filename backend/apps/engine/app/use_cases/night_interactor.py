"""밤 — 원문 정리·채점(Evaluator)·판정·판 종료 (P2·P5).

정리는 시나리오 데이터 없이 사용자 원문과 선택한 노트만 보존한다.
"""

import json
import re
import uuid
from concurrent.futures import ThreadPoolExecutor

from apps.engine.app.dtos import event_log_dto as ev
from apps.engine.app.dtos.llm_output_dto import (
    EvaluatorSideEffectOutput,
    evaluator_verdict_output,
)
from apps.engine.app.use_cases import prompts
from apps.engine.app.use_cases.game_support import record_harness, system_msg
from apps.engine.app.use_cases.harness import run_with_harness
from apps.engine.app.use_cases.public_observations import public_observations, disclose
from apps.engine.domain.entities import scoring_rules
from apps.engine.domain.entities.rule_rules import Rule, narration_with_rule_note
from apps.engine.domain.value_objects.event_type import EventType
from apps.engine.domain.value_objects.game_constants import CELLS, LOOPS_PER_ATTEMPT


class GameStateError(Exception):
    pass


def source_claims(free_text: str, tapped_notes: list[str]) -> list[str]:
    """원문을 보존해 분할한다. 8칸을 넘는 문장은 마지막 칸에 모은다."""
    source = "\n".join([free_text, *tapped_notes])
    claims = list(dict.fromkeys(s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", source) if s.strip()))
    if len(claims) > 8:
        return claims[:7] + [" ".join(claims[7:])]
    return claims


# 원인 체인의 사실 원천 — 세계에서 실제 일어난 일만.
# ANSWER_*(유저 주장·채점)·INTERVENTION_*·세션 메타를 넣으면 유저 문장이 "기록"으로 반사된다.
_CHAIN_EVENT_TYPES = frozenset({
    EventType.UTTERANCE, EventType.TOOL_CALL, EventType.MANAGER_CHECK,
    EventType.MONKEY_PAW_OFFER, EventType.RULE_APPLIED,
})


def chain_source_events(events: list) -> list:
    return [e for e in events if e.type in _CHAIN_EVENT_TYPES]


class NightInteractor:
    def __init__(
        self, *, attempts, loops, notes, rules, nights, event_log, scenario,
        core_llm, harness_on: bool, cookie_ab_on: bool, night_cls,
    ) -> None:
        self._attempts = attempts
        self._loops = loops
        self._notes = notes
        self._rules = rules
        self._nights = nights
        self._events = event_log
        self._scenario = scenario
        self._llm = core_llm
        self._harness_on = harness_on
        self._cookie_ab_on = cookie_ab_on
        self._night_cls = night_cls

    # ── 정리 ──────────────────────────────────────────────────

    def previous_answer(self, loop_id: uuid.UUID) -> dict:
        loop = self._loops.get(loop_id)
        if loop is None:
            raise GameStateError("회차가 없다")
        previous = self._nights.previous_submitted(loop.attempt_id, loop.loop_n)
        if previous is None:
            return {"previous_answer": None}
        night, loop_n = previous
        return {"previous_answer": {
            "loop_n": loop_n, "free_text": night.free_text, "claims": list(night.claims),
            "tapped_note_ids": list(night.tapped_note_ids), "draft_text": night.free_text,
        }}

    def draft(self, loop_id: uuid.UUID, tapped_note_ids: list[int], free_text: str,
              inherited_note_ids: list[int] | None = None) -> dict:
        loop = self._loops.get(loop_id)
        if loop is None or loop.state != "night_pending":
            raise GameStateError("밤이 아니다")
        if self._nights.for_loop(loop_id) is not None:
            raise GameStateError("이미 정리를 시작했다")

        note_rows = self._notes.by_ids(loop.attempt_id, tapped_note_ids)
        tapped_texts = [n.text for n in note_rows]

        # 요약 모델의 누락·바꿔 쓰기와 어휘 필터의 오탐을 피한다.
        # 원문만 옮기므로 정답을 보충할 수 없고, 의미의 정오는 채점기가 판정한다.
        kept = source_claims(free_text, tapped_texts)

        night = self._night_cls(
            loop_id=loop_id, tapped_note_ids=tapped_note_ids, free_text=free_text,
            claims=kept, fabricated_dropped=[],
        )
        self._nights.create(night)
        loop.state = "night_draft"
        self._loops.save()

        self._events.record(loop.attempt_id, ev.AnswerDraftEvent(
            loop_n=loop.loop_n, tapped_note_ids=[str(i) for i in tapped_note_ids],
            free_text=free_text,
        ))
        self._events.record(loop.attempt_id, ev.AnswerNormalizedEvent(
            loop_n=loop.loop_n, claims=kept, user_edited=False, edit_diff=None,
        ))
        return {"night_id": str(night.id), "claims": kept}

    def edit_claims(self, night_id: uuid.UUID, claims: list[str]) -> dict:
        night = self._nights.get(night_id)
        if night is None:
            raise GameStateError("정리가 없다")
        if night.edit_count >= 1 or night.submitted:
            raise GameStateError("수정은 1회만 가능하다")
        loop = self._loops.get(night.loop_id)
        before = list(night.claims)
        night.claims = claims[:8]
        night.user_edited = True
        night.edit_count = 1
        self._nights.save()
        self._events.record(loop.attempt_id, ev.AnswerNormalizedEvent(
            loop_n=loop.loop_n, claims=night.claims, user_edited=True,
            edit_diff=f"{before} -> {night.claims}",
        ))
        return {"claims": night.claims}

    # ── 채점·판정 ──────────────────────────────────────────────

    def submit(self, night_id: uuid.UUID) -> dict:
        night = self._nights.get(night_id)
        if night is None:
            raise GameStateError("정리가 없다")
        if night.submitted:
            raise GameStateError("이미 제출했다")
        loop = self._loops.get(night.loop_id)
        attempt = self._attempts.get(loop.attempt_id)

        # 다음 아침의 변화 기록은 유지하되, 부작용을 답안으로 요구하지 않는다.
        self._make_side_effect_claims(loop)
        anomaly = sum(1 for s in self._loops.npc_states(loop.id) if s.flagged_abnormal)
        world = scoring_rules.world_outcome(anomaly, loop.rumor_index)
        truth = [t for t in self._scenario.truth_claims() if t.cell != "side_effect"
                 and (not t.world_outcomes or world in t.world_outcomes)]

        per_truth, wrong = self._judge(loop, truth, [], night.claims)
        verdicts_by_cell: dict[str, list[str]] = {c: [] for c in CELLS}
        for item in per_truth:
            verdicts_by_cell[item["cell"]].append(item["verdict"])
        cell_scores = {c: scoring_rules.cell_score(v) for c, v in verdicts_by_cell.items()}
        total = scoring_rules.total_score(cell_scores)
        passed = scoring_rules.passed(total)

        anomaly = sum(1 for s in self._loops.npc_states(loop.id) if s.flagged_abnormal)
        loop.anomaly_count, night.cell_scores = anomaly, cell_scores
        night.per_truth_claim, night.total, night.passed = per_truth, total, passed
        night.submitted = True
        loop.score = total

        self._events.record(loop.attempt_id, ev.AnswerScoredEvent(
            loop_n=loop.loop_n,
            per_truth_claim=[ev.TruthClaimVerdict(
                id=i["id"], verdict=i["verdict"],
                matched_user_claim=i["matched_user_claim"], cited_chunks=i["cited"],
            ) for i in per_truth],
            cell_scores=ev.CellScores(**cell_scores), total=total, passed=passed,
        ))
        if wrong:
            self._events.record(loop.attempt_id, ev.AnswerWrongClaimsEvent(
                loop_n=loop.loop_n, claims=wrong,
            ))
        self._events.record(loop.attempt_id, ev.LoopEndEvent(
            loop_n=loop.loop_n, survived=False, anomaly_count=anomaly,
            rumor_index=loop.rumor_index,
        ))

        is_final = loop.loop_n >= LOOPS_PER_ATTEMPT
        world = scoring_rules.world_outcome(anomaly, loop.rumor_index)
        loop.world_outcome = world
        self._make_cause_chain(loop)
        self._record_death(loop, world)
        cookie = None
        closed = None
        intervention = False

        if is_final:
            identity_ok = any(
                i["verdict"] == "confirmed" and i.get("is_identity_word")
                for i in per_truth
            )
            closed = scoring_rules.closed_by(total, identity_word_confirmed=identity_ok)
            attempt.status = "closed"
            attempt.closed_by = closed
            attempt.prior_cell_results = cell_scores
            loop.state = "closed"
            self._events.record(loop.attempt_id, ev.SessionEndEvent(
                attempt_n=attempt.attempt_n, final_cells=ev.CellScores(**cell_scores),
                closed_by=closed, identity_word_confirmed=identity_ok,
            ))
        else:
            loop.state = "intervention"
            intervention = True

        self._attempts.save()
        feedback = scoring_rules.cell_feedback(cell_scores, include_side_effect=False)
        return {
            "total": total, "passed": passed, "loop_n": loop.loop_n,
            "world_outcome": world, "is_final": is_final,
            "closed_by": closed, "cells": cell_scores if is_final else None,
            "cookie": cookie, "intervention_available": intervention,
            "ending_lines": (list(self._scenario.bundle().ending_lines)
                             + list(self._scenario.bundle().ending_outcomes.get(world, []))) if is_final else None,
            "cell_feedback": feedback, "wrong_claim_count": len(wrong),
        }

    # ── 내부 ──────────────────────────────────────────────────

    def _judge(self, loop, truth, side_claims, user_claims):
        per_truth, matched = [], set()
        items = [
            {"id": t.code, "cell": t.cell, "text": t.text, "is_identity_word": t.is_identity_word}
            for t in truth
        ] + [
            {"id": f"side-{i+1}", "cell": "side_effect", "text": c, "is_identity_word": False}
            for i, c in enumerate(side_claims)
        ]
        if not user_claims:
            return (
                [{**it, "verdict": "none", "matched_user_claim": None, "cited": []} for it in items],
                [],
            )
        # 유저 주장은 최대 8개 — 자르지 않고 전부 후보로 넣는다 (top-k 절단이 매칭 실패 원인)
        candidates = "\n".join(f"{j}. {c}" for j, c in enumerate(user_claims))
        output_model = evaluator_verdict_output(len(user_claims))

        # verdict LLM 콜만 병렬 — SQLAlchemy 세션은 스레드 안전이 아니므로
        # 스레드 안에서는 (out, report)만 만들고, 이벤트 기록은 메인 스레드에서 한다
        def _verdict_call(i: int):
            sys = prompts.EVALUATOR_VERDICT_SYSTEM.format(
                truth_claim=items[i]["text"],
                user_claims=candidates,
            )

            def index_check(o) -> str | None:
                if o.matched_index is not None and not (0 <= o.matched_index < len(user_claims)):
                    return f"matched_index: {o.matched_index} (후보 {len(user_claims)}개)"
                return None

            return run_with_harness(
                self._llm, [system_msg(sys)], output_model,
                role="evaluator_verdict", fact_checks=[index_check], harness_on=True,
                temperature=0.0,  # 판정 요동 억제 — 같은 제출은 같은 verdict
            )  # 인덱스 정합성 검사라 ablation과 무관하게 항상 켠다

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(_verdict_call, range(len(items))))  # items 순서 유지

        for it, (out, report) in zip(items, results):
            record_harness(self._events, loop.attempt_id, report, loop_n=loop.loop_n, beat=None)
            verdict = out.verdict if out else "none"
            match = None  # per_truth·이벤트 스키마는 문자열 유지 — 인덱스를 후보 원문으로 되돌린다
            if out and out.matched_index is not None and 0 <= out.matched_index < len(user_claims):
                match = user_claims[out.matched_index]
                matched.add(match)
            per_truth.append({
                **it, "verdict": verdict, "matched_user_claim": match,
                "cited": list(user_claims),
            })
        wrong = [c for c in user_claims if c not in matched]
        return per_truth, wrong

    def _make_side_effect_claims(self, loop) -> list[str]:
        claims = [e.side_effect for e in self._events.query(loop.attempt_id, loop_n=loop.loop_n)
                  if e.type == "rule_execution" and e.side_effect]
        loop.side_effect_claims = claims
        return claims

    def _make_cause_chain(self, loop) -> None:
        # Retain original disclosed observations; no model summary may promote a statement to truth.
        loop.cause_chain = [{"beat": o.beat, "fact": o.text,
                             "observation_id": o.observation_id, "verification": o.verification}
                            for o in public_observations(self._events, loop.attempt_id, through_loop=loop.loop_n)
                            if o.loop_id == str(loop.id)]
        for index, fragment in enumerate(self._scenario.bundle().fragments):
            if fragment.world_outcome is not None and fragment.loop_n == loop.loop_n and fragment.world_outcome == loop.world_outcome:
                o = disclose(self._events, loop, self._scenario.beats()[-1], key=f"outcome-fragment-{index}", text=fragment.text)
                self._notes.upsert(loop.attempt_id, kind="fragment", text=o.text,
                                   loop_n=loop.loop_n, source_key=o.observation_id)

    def _record_death(self, loop, world: str) -> None:
        low = min(CELLS, key=lambda c: (loop.score or 0))
        self._events.record(loop.attempt_id, ev.DeathEvent(
            loop_n=loop.loop_n, cause_chain=[c["fact"] for c in (loop.cause_chain or [])],
            world_outcome=world, ending_cell=low,
        ))
