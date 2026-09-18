"""Boundary regressions runnable without database fixtures or an integration reset."""

from types import SimpleNamespace as NS
from threading import Lock
from uuid import uuid4

from apps.engine.app.use_cases.harness import run_with_harness
from apps.engine.app.use_cases.night_interactor import NightInteractor
from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION, execute_scene
from apps.engine.app.dtos.llm_output_dto import AdvisorOptionsOutput, AdvisorReplyOutput, AmbientOutput
from apps.engine.domain.entities.rule_rules import Rule
from apps.scenarios.scenario_a.adapter import build


class Events:
    def __init__(self):
        self.rows = []

    def query(self, _attempt, *, loop_n=None, **_kwargs):
        return [e for e in self.rows if loop_n is None or e.loop_n == loop_n]

    def record(self, _attempt, event):
        self.rows.append(event)


def loop_at(beat=3):
    return NS(id=uuid4(), attempt_id=uuid4(), loop_n=2, beat=beat, damage_level=0, budget_left=10)


def test_two_legacy_paws_share_one_explanation_without_budget_cost():
    """F11: 원숭이손 예산 대가는 폐기됐다. 옛 설명 규칙이 남아 있어도 설명 1회, 예산 불변."""
    events, loop = Events(), loop_at()
    rules = [Rule(f"R{i}", "monkey_paw", "채연", 3, "enforce", EXPLAIN_ACTION, i) for i in (1, 2)]
    scene = execute_scene(events, loop, build().bundle(), rules)
    assert scene.narration.count("채연: 쟁반 밀었어. 지금은 안 먹고 싶어.") == 1
    assert loop.budget_left == 10
    executions = [e for e in events.rows if e.type == "rule_execution"]
    assert [e.result for e in executions] == ["obeyed", "obeyed"]
    assert not any(e.side_effect for e in executions)


def test_authored_explanation_is_speech_not_independently_verified_truth():
    events, loop = Events(), loop_at()
    rule = Rule("R1", "user_choice", "민석", 3, "enforce", EXPLAIN_ACTION, 1)
    execute_scene(events, loop, build().bundle(), [rule])
    speech = [e.observation for e in events.rows if e.type == "observation"
              and e.observation.rule_id == "R1"]
    assert len(speech) == 1 and speech[0].verification == "reported"
    assert speech[0].text == "민석: 배급 자리 보고 적었어. 잊으면 안 되잖아."


def test_provider_error_is_retained_and_uses_optional_ambient_fallback():
    class DownProvider:
        def complete(self, *_args, **_kwargs):
            raise RuntimeError("provider unavailable")

    output, report = run_with_harness(DownProvider(), [], AmbientOutput, role="ambient")
    assert output is None and report.fallback_used
    assert report.attempts == 1
    assert report.call_records[0]["error"] == "provider: RuntimeError: provider unavailable"


def test_parallel_judge_retains_successful_siblings_and_provider_failure_report():
    class FlakyProvider:
        def __init__(self):
            self.calls = 0
            self.lock = Lock()

        def complete(self, *_args, **_kwargs):
            with self.lock:
                self.calls += 1
                number = self.calls
            if number == 2:
                raise RuntimeError("provider unavailable")
            return {"verdict": "confirmed", "matched_index": 0}

    judge, events, provider = NightInteractor.__new__(NightInteractor), Events(), FlakyProvider()
    judge._llm, judge._events = provider, events
    per_truth, _ = judge._judge(loop_at(), build().bundle().truth_claims[:3], [], ["내가 쓴 주장"])
    calls = [e for e in events.rows if e.type == "harness_event"]
    assert len(calls) == provider.calls == 3
    assert sum(e.fallback_used for e in calls) == 1
    assert [p["verdict"] for p in per_truth].count("confirmed") == 2
    assert sum(len(e.call_records) for e in calls) == 3


# Anthropic 구조화 출력은 maxItems를 벗겨 보내므로 core_llm 목록 필드는 초과분을 잘라 받는다(재생성 없음).


def test_advisor_options_over_cap_are_cut_to_first_three():
    option = {"target": "채연", "when_beat": "any", "effect": "suppress", "action": "혼자 있는다", "label": "L"}
    raw = {"options": [{**option, "label": f"L{i}"} for i in range(4)]}
    assert [o.label for o in AdvisorOptionsOutput.model_validate(raw).options] == ["L0", "L1", "L2"]


def test_advisor_reply_evidence_over_cap_is_cut_to_first_two():
    source = {"quote": "그대로", "relation": "supported"}
    raw = {"question_kind": "lookup", "answer": "기록은 이렇다.",
           "evidence": [{**source, "id": f"E{i}"} for i in range(3)]}
    assert [e.id for e in AdvisorReplyOutput.model_validate(raw).evidence] == ["E0", "E1"]
