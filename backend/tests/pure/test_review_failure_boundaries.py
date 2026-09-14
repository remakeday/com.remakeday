"""Boundary regressions runnable without database fixtures or an integration reset."""

from types import SimpleNamespace as NS
from threading import Lock
from uuid import uuid4

from apps.engine.app.use_cases.harness import run_with_harness
from apps.engine.app.use_cases.loop_interactor import LoopInteractor
from apps.engine.app.use_cases.night_interactor import NightInteractor
from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION, execute_scene
from apps.engine.app.dtos.llm_output_dto import AmbientOutput
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


def test_two_legacy_paws_share_one_explanation_and_one_cost():
    events, loop = Events(), loop_at()
    rules = [Rule(f"R{i}", "monkey_paw", "채연", 3, "enforce", EXPLAIN_ACTION, i) for i in (1, 2)]
    scene = execute_scene(events, loop, build().bundle(), rules)
    assert scene.narration.count("채연: 쟁반 밀었어. 지금은 안 먹고 싶어.") == 1
    assert loop.budget_left == 9
    executions = [e for e in events.rows if e.type == "rule_execution"]
    assert [e.result for e in executions] == ["obeyed", "obeyed"]
    assert sum(bool(e.side_effect) for e in executions) == 1
    costs = [e.observation for e in events.rows if e.type == "observation" and "여유가 줄었다" in e.observation.text]
    assert len(costs) == 1
    assert costs[0].observation_id in executions[1].observation_ids


def test_authored_explanation_is_speech_not_independently_verified_truth():
    events, loop = Events(), loop_at()
    rule = Rule("R1", "user_choice", "민석", 3, "enforce", EXPLAIN_ACTION, 1)
    execute_scene(events, loop, build().bundle(), [rule])
    speech = [e.observation for e in events.rows if e.type == "observation"
              and e.observation.rule_id == "R1"]
    assert len(speech) == 1 and speech[0].verification == "reported"
    assert speech[0].text == "민석: 배급 자리 보고 적었어. 잊으면 안 되잖아."


def test_next_paw_does_not_offer_an_already_active_explanation():
    day, loop = LoopInteractor.__new__(LoopInteractor), loop_at(2)
    loop.pending_paw = None
    attempt = NS(paw_offered_count=1)
    existing = Rule("R1", "monkey_paw", "채연", 3, "enforce", EXPLAIN_ACTION, 1)
    day._attempts = NS(get=lambda _: attempt, save=lambda: None)
    day._rules = NS(list=lambda _: [existing])
    day._prev_score = lambda _: 50
    day._paw_reason_ab_on = False
    offer = day._maybe_offer_paw(loop, build().bundle())
    assert offer is None or loop.pending_paw["rule"]["target"] != "채연" or loop.pending_paw["rule"]["when_beat"] != 3


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
