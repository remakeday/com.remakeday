"""밤 — 원문 정리·채점(Evaluator)·판정·판 종료 (P2·P5).

정리는 시나리오 데이터 없이 사용자가 직접 쓴 원문만 주장으로 보존한다.
고른 노트는 참고 목록 표시 복원용으로만 저장하고 채점 후보에 넣지 않는다 (테스터9 F17).
"""

import json
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext

from apps.engine.app.dtos import event_log_dto as ev
from apps.engine.app.ports.output.scene_transaction_port import RequestInFlight as InFlight
from apps.engine.app.ports.output.scene_transaction_port import SceneTransactionPort, one_request_per_row
from apps.engine.app.dtos.llm_output_dto import (
    EvaluatorSideEffectOutput,
    evaluator_verdict_output,
)
from apps.engine.app.use_cases import prompts
from apps.engine.app.use_cases.game_support import record_harness, system_msg
from apps.engine.app.use_cases.harness import run_with_harness
from apps.engine.app.use_cases.public_observations import public_observations, disclose
from apps.engine.domain.entities import scoring_rules
from apps.engine.domain.entities.claim_rules import is_question_claim
from apps.engine.domain.entities.question_suggestions import suggest_questions
from apps.engine.domain.entities.rule_rules import Rule, narration_with_rule_note
from apps.engine.domain.value_objects.event_type import EventType
from apps.engine.domain.value_objects.game_constants import CELLS, LOOPS_PER_ATTEMPT, MAX_CLAIMS


class GameStateError(Exception):
    pass


class RequestInFlight(GameStateError, InFlight):
    """같은 밤의 앞 요청(제출·수정)이 처리 중이다 — 기다리지 않고 409, 라우터가 request_in_flight 코드를 붙인다."""


def source_claims(free_text: str) -> list[str]:
    """직접 쓴 원문을 보존해 문장·줄 단위로 나눈다. 상한을 넘는 문장만 마지막 칸에 모은다."""
    claims = list(dict.fromkeys(s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", free_text) if s.strip()))
    if len(claims) > MAX_CLAIMS:
        return claims[: MAX_CLAIMS - 1] + [" ".join(claims[MAX_CLAIMS - 1 :])]
    return claims


def _question_flags(claims: list[str]) -> list[bool]:
    """확인 화면 안내용 — 채점에는 쓰지 않는다 (테스터11 O2)."""
    return [is_question_claim(c) for c in claims]


def judge_candidates(claims: list[str]) -> list[str]:
    """채점 후보 — 칸을 다시 문장 단위로 푼다.

    8칸 UI 계약(마지막 칸에 초과분을 모은다)은 그대로 두고, 채점기에는 문장을
    개별 후보로 준다. 덩어리 칸이 매칭을 가리던 결함(A.8) 해소."""
    return list(dict.fromkeys(
        s.strip() for c in claims for s in re.split(r"(?<=[.!?])\s+|\n+", c) if s.strip()))


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
        night_transaction: SceneTransactionPort = nullcontext,
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
        self._night_transaction = night_transaction

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

        # 요약 모델의 누락·바꿔 쓰기와 어휘 필터의 오탐을 피한다.
        # 원문만 옮기므로 정답을 보충할 수 없고, 의미의 정오는 채점기가 판정한다.
        # 고른 노트 원문은 넣지 않는다 — 관찰 조각이 무관한 명제에 인정되던 오인정(테스터9 F11) 차단.
        kept = source_claims(free_text)

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
        return {"night_id": str(night.id), "claims": kept, "is_question": _question_flags(kept)}

    def edit_claims(self, night_id: uuid.UUID, claims: list[str]) -> dict:
        # 밤 행 잠금 안에서 — 채점 중 수정이 잠금을 기다렸다가 커밋 뒤 옛 submitted=False로 통과해 제출한 답을 덮어쓰지 않게.
        # 잠금을 얻은 뒤 다시 읽은 submitted·edit_count로 판정한다(opus 리뷰 I1).
        with one_request_per_row(self._night_transaction, night_id, RequestInFlight, "답을 처리하는 중이다. 잠시 뒤 다시 시도해 주세요."):
            return self._edit_claims(night_id, claims)

    def _edit_claims(self, night_id: uuid.UUID, claims: list[str]) -> dict:
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
        return {"claims": night.claims, "is_question": _question_flags(night.claims)}

    # ── 채점·판정 ──────────────────────────────────────────────

    def submit(self, night_id: uuid.UUID) -> dict:
        # 제출 판정부터 채점·기록·회차 종료까지 밤 행 잠금 안에서 한 커밋 — 동시 제출이 둘 다 "미제출"을 보고 채점 모델을 N배 부르지 않는다.
        # 잠금은 기다리지 않는다: 앞 제출이 채점 중이면 곧바로 409 request_in_flight (opus 리뷰 C1, 5b).
        with one_request_per_row(self._night_transaction, night_id, RequestInFlight, "제출한 답을 채점하는 중이다. 잠시 뒤 다시 시도해 주세요."):
            return self._submit(night_id)

    def _submit(self, night_id: uuid.UUID) -> dict:
        night = self._nights.get(night_id)
        if night is None:
            raise GameStateError("정리가 없다")
        loop = self._loops.get(night.loop_id)
        if night.submitted:
            return self._with_suggested_questions(loop, self._stored_submit_response(loop))
        attempt = self._attempts.get(loop.attempt_id)

        # 다음 아침의 변화 기록은 유지하되, 부작용을 답안으로 요구하지 않는다.
        self._make_side_effect_claims(loop)
        anomaly = sum(1 for s in self._loops.npc_states(loop.id) if s.flagged_abnormal)
        world = scoring_rules.world_outcome(anomaly, loop.rumor_index)
        truth = [t for t in self._scenario.truth_claims() if t.cell != "side_effect"
                 and (not t.world_outcomes or world in t.world_outcomes)]

        candidates = judge_candidates(night.claims)
        per_truth, wrong = self._judge(loop, truth, [], candidates)
        previous = self._nights.previous_submitted(loop.attempt_id, loop.loop_n)
        if previous is not None:
            per_truth = scoring_rules.apply_ratchet(
                per_truth, previous[0].per_truth_claim or [], candidates)
            matched = {i["matched_index"] for i in per_truth if i.get("matched_index") is not None}
            wrong = [c for j, c in enumerate(candidates) if j not in matched]
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

        is_final = loop.loop_n >= LOOPS_PER_ATTEMPT
        world = scoring_rules.world_outcome(anomaly, loop.rumor_index)
        loop.world_outcome = world
        identity_ok = is_final and any(
            i["verdict"] == "confirmed" and i.get("is_identity_word")
            for i in per_truth
        )
        closed = scoring_rules.closed_by(total, identity_word_confirmed=identity_ok) if is_final else None
        feedback = scoring_rules.cell_feedback(cell_scores, include_side_effect=False)
        # 응답은 기록 전에 확정해 채점 이벤트에 함께 저장한다 — 연결이 끊긴 뒤 재제출이 모델 호출 없이 같은 응답을 받는다(opus 리뷰 I2).
        # 모든 값이 이 제출 시점에 정해진다(밤 단서도 시나리오 데이터·이번 결말로만 정해진다).
        response = {
            "total": total, "passed": passed, "loop_n": loop.loop_n,
            "world_outcome": world, "is_final": is_final,
            "closed_by": closed, "cells": cell_scores if is_final else None,
            "cookie": None, "intervention_available": not is_final,
            "ending_lines": self._ending_lines(cell_scores, world) if is_final else None,
            "truth_reveal": scoring_rules.truth_reveal(truth, per_truth) if is_final else None,
            "cell_feedback": feedback or None, "wrong_claim_count": len(wrong),
            "accepted_claims": scoring_rules.accepted_claims(per_truth, candidates),
            "empty_cells": scoring_rules.empty_hint_cells(cell_scores),
            "night_clue": self._night_clue_view(loop),
        }

        self._events.record(loop.attempt_id, ev.AnswerScoredEvent(
            loop_n=loop.loop_n,
            per_truth_claim=[ev.TruthClaimVerdict(
                id=i["id"], verdict=i["verdict"],
                matched_user_claim=i["matched_user_claim"], cited_chunks=i["cited"],
                ratcheted=i.get("ratcheted", False),
            ) for i in per_truth],
            cell_scores=ev.CellScores(**cell_scores), total=total, passed=passed,
            response=response,
        ))
        if wrong:
            self._events.record(loop.attempt_id, ev.AnswerWrongClaimsEvent(
                loop_n=loop.loop_n, claims=wrong,
            ))
        self._events.record(loop.attempt_id, ev.LoopEndEvent(
            loop_n=loop.loop_n, survived=False, anomaly_count=anomaly,
            rumor_index=loop.rumor_index,
        ))

        self._make_cause_chain(loop)
        self._disclose_night_clue(loop)
        self._record_death(loop, world)

        if is_final:
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

        self._attempts.save()
        return self._with_suggested_questions(loop, response)

    def _with_suggested_questions(self, loop, response: dict) -> dict:
        """신의 질문 추천 — 저장 응답이 아니라 지금 공개된 기록(밤 단서 포함)에서 매번 만든다(테스터9 F19 방향 3)."""
        observations = public_observations(self._events, loop.attempt_id, through_loop=loop.loop_n)
        return {**response, "suggested_questions": suggest_questions(observations, loop_n=loop.loop_n, asked=[])}

    def _stored_submit_response(self, loop) -> dict:
        """이미 제출한 밤 — 저장된 제출 응답을 그대로 돌려준다(모델 호출 0). 저장 응답이 없는 과거 제출은 기존대로 409."""
        stored = [e.response for e in self._events.query(loop.attempt_id, type=EventType.ANSWER_SCORED, loop_n=loop.loop_n)
                  if e.response]
        if not stored:
            raise GameStateError("이미 제출했다")
        return stored[-1]

    def _ending_lines(self, cell_scores: dict, world: str) -> list[str]:
        """결말은 이해한 만큼만 — 셀 ≥ REVEAL_THRESHOLD의 줄만 연다. 매핑 없는 시나리오는 구 거동."""
        bundle = self._scenario.bundle()
        by_cell = getattr(bundle, "ending_lines_by_cell", None) or {}
        if by_cell:
            lines = [line for cell, cell_lines in by_cell.items()
                     if cell_scores.get(cell, 0.0) >= scoring_rules.REVEAL_THRESHOLD
                     for line in cell_lines]
        else:
            lines = list(bundle.ending_lines)
        return lines + list(bundle.ending_outcomes.get(world, []))

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
                [{**it, "verdict": "none", "matched_user_claim": None, "matched_index": None,
                  "cited": []} for it in items],
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
                # 인용이 후보를 유일하게 가리키면 번호가 틀려도 보정되므로 재생성하지 않는다
                resolved = scoring_rules.resolve_matched_index(user_claims, o.matched_quote, o.matched_index)
                if resolved is not None and not (0 <= resolved < len(user_claims)):
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
            match = index = None  # 이벤트 스키마는 문자열 유지 — 인덱스는 이번 밤 인정 문장 계산용
            if out and out.verdict != "none":
                # 인용이 유일하게 가리키는 후보가 번호보다 우선 — 원본 출력은 harness_event에 남는다.
                # none 판정은 인용이 남아 있어도 매칭하지 않는다(인용이 verdict보다 먼저 생성된다)
                index = scoring_rules.resolve_matched_index(
                    user_claims, out.matched_quote, out.matched_index)
            if index is not None and 0 <= index < len(user_claims):
                match = user_claims[index]
                matched.add(match)
            else:
                index = None
            per_truth.append({
                **it, "verdict": verdict, "matched_user_claim": match, "matched_index": index,
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

    def _night_clue(self, loop):
        return next((c for c in getattr(self._scenario.bundle(), "night_clues", None) or []
                     if c.loop_n == loop.loop_n), None)

    def _disclose_night_clue(self, loop) -> dict | None:
        """밤 단서(밤단서 v2 P.1) — 캡션은 「N회차 · 소등 후」 관찰, 방송은 전언(statement)으로 저장한다.

        둘 다 노트에 적혀 다음 밤 글을 쓸 때 펼쳐 보는 참고 목록에 오른다(채점 후보는 아니다)."""
        clue = self._night_clue(loop)
        if clue is None:
            return None
        lights_out = self._scenario.beats()[-1]
        for key, text, kind in (("night-clue", clue.caption, "scene"),
                                ("night-broadcast", clue.broadcast, "statement")):
            o = disclose(self._events, loop, lights_out, key=key, text=text, source_kind=kind)
            self._notes.upsert(loop.attempt_id, kind="fragment", text=o.text,
                               loop_n=loop.loop_n, source_key=o.observation_id)
        return self._night_clue_view(loop)

    def _night_clue_view(self, loop) -> dict | None:
        """제출 응답의 밤 단서 — 시나리오 데이터와 이번 결말로만 정해진다. 트럭 결말 밤에는 결말 파편이 한 줄 더 붙는다."""
        clue = self._night_clue(loop)
        if clue is None:
            return None
        bundle = self._scenario.bundle()
        outcome_lines = [f.text for f in bundle.fragments
                         if f.world_outcome is not None and f.loop_n == loop.loop_n
                         and f.world_outcome == loop.world_outcome]
        return {
            "loop_n": clue.loop_n, "caption": clue.caption, "image_ids": list(clue.image_ids),
            "voice_id": clue.voice_id, "broadcast": clue.broadcast,
            "outcome_line": " ".join(outcome_lines) or None,
        }

    def _record_death(self, loop, world: str) -> None:
        low = min(CELLS, key=lambda c: (loop.score or 0))
        self._events.record(loop.attempt_id, ev.DeathEvent(
            loop_n=loop.loop_n, cause_chain=[c["fact"] for c in (loop.cause_chain or [])],
            world_outcome=world, ending_cell=low,
        ))
