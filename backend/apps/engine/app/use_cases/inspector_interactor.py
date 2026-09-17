"""인스펙터·하네스 공개 (P5) — 읽기 전용 관찰가능성 (기획서 8.9)."""

import hmac
import uuid

from apps.engine.domain.entities import scoring_rules
from apps.engine.domain.value_objects.game_constants import LOOPS_PER_ATTEMPT


class AccessDenied(Exception):
    pass


class InspectorDisabled(Exception):
    """INSPECTOR_TOKEN 미설정 — 인스펙터를 열지 않는다."""


class InspectorInteractor:
    def __init__(self, *, attempts, rules, event_log, inspector_token: str,
                 notes=None, scenario=None) -> None:
        self._attempts = attempts
        self._rules = rules
        self._events = event_log
        self._token = inspector_token
        self._notes = notes
        self._scenario = scenario

    def journey_view(self, attempt_id: uuid.UUID) -> dict:
        """유저용 추리 여정 — 회차별 알아낸 것·해금 단서·최종 공개(스포일러는 서버가 거른다)."""
        attempt = self._attempts.get(attempt_id)
        if attempt is None:
            raise AccessDenied("판이 없다")
        if attempt.status != "closed":
            raise AccessDenied("다섯 번째 밤을 마치면 열린다")
        events = self._events.query(attempt_id)
        scored = sorted((e for e in events if e.type == "answer_scored"),
                        key=lambda e: e.loop_n)
        notes = self._notes.list(attempt_id) if self._notes else []
        unlocked_by_loop: dict[int, list[str]] = {}
        for note in notes:
            if str(getattr(note, "source_key", "") or "").startswith("advisor-lead-"):
                unlocked_by_loop.setdefault(note.loop_n, []).append(note.text)

        confirmed_seen: set[str] = set()
        loops = []
        for e in scored:
            new_confirmed = []
            for v in e.per_truth_claim:
                if v.verdict == "confirmed" and v.id not in confirmed_seen:
                    confirmed_seen.add(v.id)
                    new_confirmed.append({"code": v.id, "my_claim": v.matched_user_claim})
            loops.append({
                "loop_n": e.loop_n, "total": e.total, "passed": e.passed,
                "new_confirmed": new_confirmed,
                "unlocked_notes": unlocked_by_loop.get(e.loop_n, []),
            })

        final = None
        unresolved: list[dict] = []
        if scored and attempt.status == "closed" and self._scenario is not None:
            last = scored[-1]
            truth = [t for t in self._scenario.truth_claims() if t.cell != "side_effect"]
            per_truth = [{"id": v.id, "verdict": v.verdict,
                          "matched_user_claim": v.matched_user_claim}
                         for v in last.per_truth_claim]
            cells = last.cell_scores.model_dump()
            final = {"cells": cells, "closed_by": attempt.closed_by,
                     "truth_reveal": scoring_rules.truth_reveal(truth, per_truth)}
            # 못 맞춘 셀에는 리드의 direction(비스포일러 설계)을 힌트로 돌려쓴다
            directions = [
                (f"내일 {lead.target}에게 {lead.ask} 물어봐라." if lead.ask
                 else f"{lead.target}: {lead.rule_action} 규칙을 걸어 봐라.")
                for lead in getattr(self._scenario.bundle(), "advisor_leads", [])]
            locked_cells = sorted({t.cell for t in truth}
                                  & {c for c, s in cells.items()
                                     if s < scoring_rules.REVEAL_THRESHOLD})
            for i, cell in enumerate(locked_cells):
                hint = directions[i % len(directions)] if directions else \
                    "낮의 질문과 규칙으로 그 자리를 열 수 있다."
                unresolved.append({"cell": cell, "hint": hint})

        return {"loops": loops, "final": final, "unresolved": unresolved}

    def harness_view(self, attempt_id: uuid.UUID) -> dict:
        attempt = self._attempts.get(attempt_id)
        if attempt is None:
            raise AccessDenied("판이 없다")
        events = self._events.query(attempt_id)
        completed_five = any(e.type == "answer_scored" and e.loop_n == LOOPS_PER_ATTEMPT
                             for e in events)
        if attempt.status != "closed" or not completed_five:
            raise AccessDenied("다섯 번째 밤을 마치면 열린다")
        rules = self._rules.list(attempt_id)
        harness_events = [e for e in events if str(e.type) == "harness_event"]
        executions = [e for e in events if e.type == "rule_execution"]
        evaluable = [e for e in executions if e.result in ("obeyed", "violated")]
        observations = {e.observation.observation_id for e in events if e.type == "observation"}
        notes = self._notes.list(attempt_id) if self._notes else []
        starts = [e for e in events if e.type == "loop_start"]
        measured_loops = {e.loop_n for e in starts if e.measurement_version == "connected-investigation-1"}
        measured_notes = [n for n in notes if n.loop_n in measured_loops]
        coverage = (len(starts) == LOOPS_PER_ATTEMPT and len(measured_loops) == LOOPS_PER_ATTEMPT
                    and all(e.version == "connected-investigation-1" for e in harness_events))
        def metric(numerator, denominator, method, reviewed=0):
            return {"numerator": numerator, "denominator": denominator,
                    "value": numerator / denominator if numerator is not None and denominator else None,
                    "reviewed": reviewed, "method": method}
        compliance = metric(sum(e.result == "obeyed" for e in evaluable), len(evaluable),
                            "deterministic_scene_action; conflicts and no opportunity excluded")
        applications = {e.rule_id: e for e in events if e.type == "rule_applied"}
        return {
            "rules": [self._rule_dict(r, hide_hidden=False) for r in rules],
            "harness_summary": {
                "total_events": len(events),
                "harness_interventions": sum(bool(e.violations) or e.fallback_used for e in harness_events),
                "model_calls": len(harness_events) if coverage else None,
                "model_attempts": sum(e.attempts for e in harness_events) if coverage else None,
                "model_call_coverage": "complete_logged_calls" if coverage else "legacy_partial_or_unavailable",
                "fallbacks": sum(1 for e in harness_events if e.fallback_used),
                "paw_accepted": sum(r.source == "monkey_paw" for r in rules),
                "recommended_rules": sum(r.source == "user_choice" for r in rules),
                "custom_rules": sum(r.source == "user_custom" for r in rules),
                "rule_conflicts": sum(bool(r.conflict) for r in rules),
                "questions_asked": sum(e.type == "intervention_question" and e.kind == "answer" for e in events),  # 안내 답 제외
                # 규칙 등록 로그는 실제 행동 이행 검증이 아니다. 분모 없는 성공률을 만들지 않는다.
                "rule_success_rate": compliance["value"],
                "tool_side_effects": [
                    {"loop_n": e.loop_n, "beat": e.beat, "text": e.side_effect}
                    for e in events if e.type == "tool_call" and e.side_effect
                ],
            },
            "experiments": [
                {"rule_id": r.rule_id,
                 "intent": applications[r.rule_id].intent if r.rule_id in applications else None,
                 "interpretation": (applications[r.rule_id].interpretation if r.rule_id in applications else None)
                                   or r.shown_reason or f"{r.target}: {r.action} / {r.effect}",
                 "opportunities": [{"loop_n": e.loop_n, "beat": e.beat, "condition": e.condition,
                    "actual_action": e.actual_action, "result": e.result, "observation_ids": e.observation_ids,
                    "side_effect": e.side_effect} for e in executions if e.rule_id == r.rule_id]}
                for r in rules
            ],
            "metrics": {
                "note_source_linkage": {
                    **metric(sum(n.source_key in observations for n in measured_notes) if measured_notes else None,
                             len(measured_notes), "instrumented_loops_only; legacy notes unmeasured"),
                    "unmeasured": len(notes) - len(measured_notes),
                },
                "rule_compliance": compliance,
                "question_grounding": metric(None, 0, "independent semantic review required; no reviewed sample"),
                "recommendation_relevance": metric(None, 0, "independent semantic review required; no reviewed sample"),
                "custom_semantics": metric(None, 0, "independent semantic review required; rejections are not failures"),
                "checker_accuracy": metric(None, 0, "independent false-positive/false-negative review required"),
            },
            "measurement_version": "connected-investigation-1",
        }

    def inspector_view(self, attempt_id: uuid.UUID, token: str) -> dict:
        if not self._token:
            raise InspectorDisabled
        if not hmac.compare_digest(token.encode(), self._token.encode()):
            raise AccessDenied("토큰이 다르다")
        attempt = self._attempts.get(attempt_id)
        if attempt is None:
            raise AccessDenied("판이 없다")
        events = self._events.query(attempt_id)
        rules = self._rules.list(attempt_id)
        dumped = [e.model_dump(mode="json") for e in events]
        return {
            "events": dumped,
            "patches": [e for e in dumped if e["type"] == "manager_check"],
            "paw_rules": [self._rule_dict(r, hide_hidden=False) for r in rules if r.source in ("monkey_paw", "paw_effect")],
            "scoring": [e for e in dumped if e["type"] == "answer_scored"],
        }

    @staticmethod
    def _rule_dict(r, *, hide_hidden: bool) -> dict:
        return {
            "rule_id": r.rule_id, "source": r.source, "target": r.target,
            "when_beat": r.when_beat, "effect": r.effect, "action": r.action,
            "shown_reason": r.shown_reason,
            "hidden_side_effect": None if hide_hidden else r.hidden_side_effect,
            "created_loop": r.created_loop, "conflict": r.conflict,
        }
