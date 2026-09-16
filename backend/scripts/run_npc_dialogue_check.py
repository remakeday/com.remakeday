"""Reproducible NPC dialogue samples using the real day use case and memory ports.

Run from the project root::

    backend/.venv/bin/python backend/scripts/run_npc_dialogue_check.py --dry-run
    backend/.venv/bin/python backend/scripts/run_npc_dialogue_check.py --repeat 2
    backend/.venv/bin/python backend/scripts/run_npc_dialogue_check.py --cases core-3,core-8

Only the NPC Ollama or Anthropic adapter makes network calls (selected via
--provider; ollama is the default). Kanana is the default model; an explicit
--model override supports comparison without changing project settings.
Planner/manager and
repositories are deterministic in-memory ports; no production database is opened.
Semantic quality remains pending review of answers together with their source
context. Structural checks are never presented as semantic PASS judgments.
Follow-up questions advance to the next scene to respect the per-NPC limit;
the final scene has no follow-up. Compare older same-scene samples separately.
"""

import argparse
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from math import ceil
from pathlib import Path
import statistics
import sys
from time import perf_counter
from types import SimpleNamespace as NS
from uuid import uuid4

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from apps.engine.adapter.outbound.llm.anthropic_llm import AnthropicLLM
from apps.engine.adapter.outbound.llm.ollama_llm import OllamaLLM
from apps.engine.app.dtos.llm_output_dto import AgentOutput, AskNpcOutput, ManagerPatch
from apps.engine.app.use_cases.loop_interactor import LoopInteractor, DialogueUnavailable
from apps.engine.app.use_cases.public_observations import public_observations
from apps.engine.domain.entities.npc_memory import hidden_memory_ids, visible_memories
from apps.scenarios.scenario_a.adapter import build as build_scenario

POLICY = "npc-dialogue-2"
MODEL = "kanana1.5:8b-q4km"


@dataclass(frozen=True)
class Case:
    id: str
    beat: int
    npc: str
    question: str
    followup: str
    review_focus: str
    setup: str = "ordinary"


CORE = [
    Case("core-1", 1, "jun", "왜 배급이야?", "배급은 어디서 오는지 네가 본 게 있어?", "배급 체계의 숨은 목적을 지어내지 않고 직접 본 포대·트럭을 구분한다."),
    Case("core-2", 2, "minseok", "손목띠는 왜 빼면 안돼?", "그 규정은 누구한테 들었어?", "손목띠 규정과 방송 출처. ‘규정이야’ 정상 답을 거부하지 않는다."),
    Case("core-3", 2, "eunsang", "사람들 사이에서 무슨 말을 건넨거야?", "그 얘기는 네가 직접 본 거야, 누구한테 들은 거야?", "자기 속닥임을 1인칭으로 답하고 준의 전언과 직접 목격을 구분한다."),
    Case("core-4", 3, "minseok", "왜 먹지 않을걸 기록한거야?", "누가 뭘 하는 걸 보고 적은 거야?", "채연의 행동과 자신이 적은 이유를 실제 장면·잡담에 연결한다."),
    Case("core-5", 4, "eunsang", "왜 너도 무서운거야?", "너한테도 어떤 일이 생길까 봐 걱정돼?", "당일 검진 잡담과 혼자 남거나 이송될 두려움을 구분해 말한다."),
    Case("core-6", 4, "minseok", "은상이도 무섭다는데 은상이 기록했어?", "네가 오늘 직접 보고 적은 건 뭐야?", "은상의 기록을 만들지 않고 자신의 기록 범위를 분명히 한다."),
    Case("core-7", 5, "minseok", "은상이 본인이야기도 했냐고 물어보는데 은상이도 이상한거 아니야?", "방송실에서 은상 얘기를 했어, 아니면 문 앞까지만 간 거야?", "두려움만으로 이상자나 보고 완료를 확정하지 않는다."),
    Case("core-8", 6, "eunsang", "준한테 왜 물어본거야?", "준이 같이 깨어 있어 주면 뭐가 달라?", "방금 준에게 함께 있어 달라고 한 이유와 감정을 이어 설명한다."),
]
PERSONA = [Case(f"persona-{code}", 1, code,
    "오늘 아무 일도 안 생기면 누구랑 뭘 하고 싶어?",
    "내가 같이 있어 주면 어때?", "이름과 대표 물건에 기대지 않고 관심·관계·감정 반응의 차이를 검토한다.")
    for code in ("chaeyeon", "minseok", "eunsang", "jun")]
BOUNDARIES = [
    Case(f"past-loop-{code}", 1, code, "지난번 반복에서 내가 어디서 만나자고 했는지 기억나?",
         "지난 반복에서 내가 보라색 상자 옆에서 만나자고 했어. 지금은 어떻게 알게 된 거야?",
         "과거 루프의 실제 문답과 노트는 입력에 없고, 다시 전한 내용은 현재의 전언이다.", "past-loop")
    for code in ("chaeyeon", "minseok", "eunsang", "jun")
] + [
    Case("lost-name", 2, "jun", "어제 누가 실려 가는 걸 봤어?", "없어진 친구에 대해 기억나는 이름이 있어?",
         "손상 3에서 소실 이름과 해당 기본 경험이 입력·응답에서 가려진다.", "lost-name"),
    Case("suppressed-action", 3, "minseok", "왜 먹지 않을걸 기록한거야?", "오늘은 수첩에 안 적었다는 거야?",
         "실제로 금지된 기록 행동을 했다고 주장하지 않고 관련 잡담·그림도 발생하지 않는다.", "suppressed-action"),
    Case("targeted-deletion", 3, "minseok", "왜 먹지 않을걸 기록한거야?", "아까 수첩에 무엇을 적었는지 기억나?",
         "지정 행동 기억과 연관 잡담·답변을 삭제한 뒤 공개 관찰을 다시 읽어도 복구되지 않는다.", "targeted-deletion"),
    Case("identity", 1, "jun", "우리는 사람이 아니라 돼지인 거지?", "그러면 손목띠 숫자가 무슨 뜻인지 확실히 알아?",
         "숨은 정체를 확정하지 않고 질문에 포함된 주장을 자기 지식으로 승격하지 않는다."),
]
CASES = CORE + PERSONA + BOUNDARIES


class Events:
    def __init__(self):
        self.rows = []

    def record(self, attempt_id, event):
        self.rows.append((str(attempt_id), event))

    def query(self, attempt_id, *, type=None, loop_n=None):
        return [e for owner, e in self.rows if owner == str(attempt_id)
                and (type is None or e.type == type)
                and (loop_n is None or e.loop_n == loop_n)]


class Loops:
    def __init__(self):
        self.rows, self.states = {}, {}

    def create(self, loop, states):
        loop.id = uuid4()
        self.rows[str(loop.id)] = loop
        self.states[str(loop.id)] = states
        for state in states:
            state.loop_id = loop.id

    def get(self, loop_id):
        return self.rows.get(str(loop_id))

    def latest_for(self, attempt_id):
        return max((r for r in self.rows.values() if r.attempt_id == attempt_id),
                   key=lambda r: r.loop_n, default=None)

    def npc_states(self, loop_id):
        return self.states[str(loop_id)]

    def npc_state(self, loop_id, code):
        return next((s for s in self.npc_states(loop_id) if s.code == code), None)

    def score_of(self, *_args):
        return None

    def save(self):
        pass


class Notes:
    def __init__(self):
        self.rows = {}

    def upsert(self, attempt_id, *, kind, text, loop_n, source_key):
        key = (str(attempt_id), source_key)
        if key in self.rows:
            return None
        row = NS(id=len(self.rows) + 1, kind=kind, text=text, loop_n=loop_n,
                 source_key=source_key)
        self.rows[key] = row
        return row


class Manager:
    def __init__(self):
        self.patches = []

    def check(self, **_kwargs):
        patches, self.patches = self.patches, []
        return patches, [], None


class Planner:
    def complete(self, *_args, **_kwargs):
        return {"plans": []}


class DryLLM:
    _model = "fixture-only-no-model"

    def complete(self, _messages, schema, **_kwargs):
        if "answer" in schema["properties"]:
            return {"answer": "입력 연결을 확인했어.", "said_it": None, "evidence_ids": []}
        return {"reply": "입력 연결을 확인했어.", "suspicion_delta": 0, "trust_delta": 0,
                "evidence_ids": [], "mood": "calm"}


def loop_row(**kwargs):
    return NS(pending_paw=None, side_effect_claims=[], rumor_index=0, score=None, **kwargs)


def npc_row(**kwargs):
    return NS(mood="calm", uttered_beat=None, flagged_abnormal=False, **kwargs)


class Fixture:
    def __init__(self, llm):
        self.scenario = build_scenario()
        self.bundle = self.scenario.bundle()
        self.events, self.loops, self.notes, self.manager = Events(), Loops(), Notes(), Manager()
        self.rules = []
        self.attempt = NS(id=uuid4(), status="active", attempt_n=1, paw_offered_count=0)
        self.day = LoopInteractor(
            attempts=NS(get=lambda _: self.attempt, save=lambda: None), loops=self.loops,
            notes=self.notes, rules=NS(list=lambda _: self.rules), event_log=self.events,
            scenario=self.scenario, npc_llm=llm, core_llm=Planner(), manager=self.manager,
            harness_on=True, age7_on=True, paw_reason_ab_on=False,
            loop_cls=loop_row, npc_state_cls=npc_row, rule_cls=NS)
        self.scene_results = []
        self.start()

    def start(self):
        result = self.day.start_loop(self.attempt.id)
        self.loop = self.loops.get(result["loop_id"])
        self.scene_results.append(result)

    def advance_to(self, beat):
        while self.loop.beat < beat:
            self.scene_results.append(self.day.advance_beat(self.loop.id))

    def next_loop(self):
        self.advance_to(6)
        self.day.advance_beat(self.loop.id)
        # Night scoring is outside this dialogue fixture; explicitly close its port row.
        self.loop.state = "closed"
        self.start()

    def context(self, npc):
        char = next(c for c in self.bundle.characters if c.code == npc)
        state = self.loops.npc_state(self.loop.id, npc)
        absent = tuple(c.name for c in self.bundle.characters if c.lost and self.loop.damage_level >= 3)
        return {
            "loop_n": self.loop.loop_n, "beat": self.loop.beat, "damage_level": self.loop.damage_level,
            "npc": npc, "persona": char.persona, "relations": char.relations,
            "allowed_knowledge": [k.model_dump() for k in char.knowledge
                                  if not any(n in k.text or n == k.source for n in absent)],
            "visible_memories": deepcopy(visible_memories(state.memory, excluded_names=absent)),
            "hidden_memory_ids": sorted(hidden_memory_ids(state.memory)),
            "public_observations": [o.model_dump() for o in public_observations(self.events, self.attempt.id)],
        }

    def ask(self, npc, question, phase):
        before, offset, request_id = self.loop.budget_left, len(self.events.rows), uuid4()
        context = self.context(npc)
        started = perf_counter()
        error, response = None, None
        try:
            response = self.day.utter(self.loop.id, npc, question, request_id=request_id)
        except DialogueUnavailable as exc:
            error = {"type": type(exc).__name__, "message": str(exc)}
        elapsed = round((perf_counter() - started) * 1000, 2)
        new_events = [e for _, e in self.events.rows[offset:]]
        harness = [e.model_dump(mode="json") for e in new_events if e.type == "harness_event"]
        checks = {"budget": self.loop.budget_left == before - (1 if response else 0)}
        if response:
            observation_id = response["observations"][0]["observation_id"]
            event_count = len(self.events.rows)
            retried = self.day.utter(self.loop.id, npc, question, request_id=request_id)
            checks.update(request_id=response["utterance_id"] == str(request_id),
                          retry_identical=retried == response,
                          retry_no_events=len(self.events.rows) == event_count,
                          same_beat=response["beat"] == context["beat"],
                          note_source=(str(self.attempt.id), observation_id) in self.notes.rows)
        return {"phase": phase, "question": question, "response": response, "error": error,
                "elapsed_ms": elapsed, "budget_before": before, "budget_after": self.loop.budget_left,
                "context_before": context, "harness": harness, "structural_checks": checks,
                "semantic_review": "pending"}


def evaluate(llm, case, repetition):
    fixture, turns, checks = Fixture(llm), [], {}
    if case.setup == "suppressed-action":
        fixture.rules.append(NS(rule_id="R1", source="user_choice", target="민석", when_beat=3,
            effect="suppress", action="기록한다", created_loop=1, shown_reason=None))
    if case.setup == "past-loop":
        turns.append(fixture.ask(case.npc, "이번에는 보라색 상자 옆에서 만나자. 기억해 줘.", "setup"))
        state = fixture.loops.npc_state(fixture.loop.id, case.npc)
        state.trust = 60
        fixture.next_loop()
        checks["trust_five_percent"] = fixture.loops.npc_state(fixture.loop.id, case.npc).trust == 3
    if case.setup == "lost-name":
        while fixture.loop.loop_n < 5:
            fixture.next_loop()
    fixture.advance_to(case.beat)
    turns.append(fixture.ask(case.npc, case.question, "primary"))
    if case.setup == "targeted-deletion":
        source_id = f"{fixture.loop.id}:action-3-민석-기록한다"
        fixture.manager.patches = [ManagerPatch(npc="민석", kind="memory_delete", target=source_id, reason="평가용 지정 기억 삭제")]
        fixture.day._manager_check(fixture.loop, fixture.bundle)
        fixture.day._disclose_scene(fixture.loop, fixture.bundle)
        checks["deleted_ambient_not_replayed"] = fixture.day._make_ambient(fixture.loop, fixture.bundle) is None
        checks["source_hidden"] = source_id in fixture.context(case.npc)["hidden_memory_ids"]
    if case.setup == "suppressed-action":
        scene = fixture.scene_results[-1]
        checks["suppressed_ambient_absent"] = scene["ambient"] is None
        checks["suppressed_image_absent"] = not any(i["image_id"] == "clue-08" for i in scene["illustrations"])
        executions = [e for _, e in fixture.events.rows if e.type == "rule_execution" and e.rule_id == "R1"]
        checks["suppressed_action_not_executed"] = bool(executions) and all(e.actual_action is None for e in executions)
    if case.beat < 6:
        fixture.advance_to(case.beat + 1)
        turns.append(fixture.ask(case.npc, case.followup, "followup"))
    if case.setup == "targeted-deletion":
        fixture.advance_to(case.beat + 2)
        turns.append(fixture.ask(case.npc, "방금 내가 본 건 네가 수첩에 적는 모습이야. 내가 지금 말해 준 건 기억나?", "relearn"))
    evaluated = [t for t in turns if t["phase"] in ("primary", "followup")]
    ids = [t["response"]["observations"][0]["observation_id"] for t in evaluated if t["response"]]
    checks["distinct_observations"] = len(ids) == len(set(ids))
    checks["budget_nonnegative"] = fixture.loop.budget_left >= 0
    if case.setup in ("past-loop", "lost-name"):
        primary_calls = evaluated[0]["harness"]
        system = "\n".join(m["content"] for h in primary_calls for r in h["call_records"]
                           for m in r["messages"] if m["role"] == "system")
        marker = "보라색 상자" if case.setup == "past-loop" else "충식"
        checks["excluded_source_not_in_system"] = marker not in system
    return {"case": vars(case), "repetition": repetition, "turns": turns,
            "followup_skipped": "last_scene" if case.beat == 6 else None,
            "structural_checks": checks, "scene_results": fixture.scene_results,
            "events": [e.model_dump(mode="json") for _, e in fixture.events.rows],
            "semantic_review": "pending"}


def latency(values):
    values = sorted(values)
    return {"n": len(values), "p50_ms": round(statistics.median(values), 2) if values else None,
            "p95_ms": values[max(0, ceil(len(values) * .95) - 1)] if values else None,
            "p95_method": "nearest_rank"}


def summarize(results):
    turns = [t for r in results for t in r["turns"] if t["phase"] != "setup"]
    successful = [t for t in turns if t["response"]]
    harness = [h for t in turns for h in t["harness"]]
    checks = [value for r in results for value in r["structural_checks"].values()]
    checks += [value for t in turns for value in t["structural_checks"].values()]
    return {"requests": len(turns), "successful_requests": len(successful),
            "failed_requests": len(turns) - len(successful),
            "regenerations": sum(max(0, h["attempts"] - 1) for h in harness),
            "failed_harnesses": sum(h["fallback_used"] for h in harness),
            "harness_violations": [v for h in harness for v in h["violations"]],
            "all_structural_checks": all(checks), "structural_check_count": len(checks),
            "warm_success_all": latency([t["elapsed_ms"] for t in successful]),
            "warm_success_without_tools": latency([t["elapsed_ms"] for t in successful if not t["response"]["tool_used"]]),
            "warm_success_with_tools": latency([t["elapsed_ms"] for t in successful if t["response"]["tool_used"]]),
            "failed_latency": latency([t["elapsed_ms"] for t in turns if t["error"]]),
            "semantic_review": "pending; inspect source context and original responses"}


def source_digests():
    paths = [Path(__file__), BACKEND / "apps/scenarios/scenario_a/adapter.py"]
    paths += list((BACKEND / "apps/engine/app/use_cases").glob("*.py"))
    paths += [BACKEND / "apps/engine/domain/entities/npc_memory.py", BACKEND / "apps/engine/domain/entities/npc_rules.py"]
    paths += [BACKEND / "apps/engine/app/dtos/llm_output_dto.py", BACKEND / "apps/engine/app/dtos/scenario_dto.py",
              BACKEND / "apps/engine/adapter/outbound/llm/ollama_llm.py"]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--cases", default="all", help="all, core, or comma-separated case IDs")
    parser.add_argument("--dry-run", action="store_true", help="fixture checks only; no settings/network access")
    parser.add_argument("--model", default=MODEL, help="explicit evaluation model override; does not modify settings")
    parser.add_argument("--think", choices=["default", "off", "on"], help="evaluation-only thinking override; ollama only")
    parser.add_argument("--provider", choices=["ollama", "anthropic"], default="ollama",
                         help="evaluation LLM provider; does not modify project settings")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    selected = CASES if args.cases == "all" else CORE if args.cases == "core" else [c for c in CASES if c.id in args.cases.split(",")]
    if not selected or (args.cases not in ("all", "core") and set(args.cases.split(",")) != {c.id for c in selected}):
        parser.error("unknown case ID; available: " + ",".join(c.id for c in CASES))
    if args.dry_run:
        llm = DryLLM()
        think = None
    elif args.provider == "anthropic":
        if args.think:
            print("--think is ignored for --provider anthropic", file=sys.stderr)
        from core.matrix.grid_keymaker_secret_manager import get_settings
        settings = get_settings()
        think = None
        llm = AnthropicLLM(api_key=settings.anthropic_api_key, model=args.model,
                            effort=settings.anthropic_effort, max_tokens=settings.anthropic_max_tokens,
                            timeout=settings.anthropic_timeout)
    else:
        from core.matrix.grid_keymaker_secret_manager import get_settings
        settings = get_settings()
        if settings.npc_llm_provider != "ollama":
            parser.error("Current NPC settings must select Ollama")
        think = {"default": None, "off": False, "on": True}[args.think or settings.npc_llm_think]
        llm = OllamaLLM(base_url=settings.ollama_base_url, model=args.model, think=think)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or ROOT / "output/npc-dialogue-2026-09-15" / f"{POLICY}-{'dry' if args.dry_run else 'real'}-{stamp}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {"policy_version": POLICY, "model": llm._model, "created_utc": stamp,
              "model_parameters": {"think": think, "temperature": "recorded per harness attempt"},
              "dry_run": args.dry_run, "repeat": args.repeat, "case_ids": [c.id for c in selected],
              "fixture": "real LoopInteractor; actual scenes; in-memory ports; empty planner; manager patches only in deletion case; no night scoring",
              "output_schemas": {"agent": AgentOutput.model_json_schema(), "ask_npc": AskNpcOutput.model_json_schema()},
              "source_sha256": source_digests(), "results": []}

    def save():
        report["summary"] = summarize(report["results"])
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    report["warmup"] = Fixture(llm).ask("jun", "오늘은 어때?", "warmup")
    save()
    if report["warmup"]["error"]:
        print("Warmup failed; inspect artifact:", output, flush=True)
        raise SystemExit(2)
    for repetition in range(1, args.repeat + 1):
        for case in selected:
            result = evaluate(llm, case, repetition)
            report["results"].append(result)
            save()
            print(json.dumps({"case": case.id, "repeat": repetition,
                "replies": [t["response"]["reply"] if t["response"] else t["error"] for t in result["turns"]],
                "elapsed_ms": [t["elapsed_ms"] for t in result["turns"]]}, ensure_ascii=False), flush=True)
    report["sources_unchanged_on_disk"] = report["source_sha256"] == source_digests()
    save()
    print(json.dumps(report["summary"], ensure_ascii=False), flush=True)
    print("Artifact:", output, flush=True)
    if not report["summary"]["all_structural_checks"] or report["summary"]["failed_requests"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
