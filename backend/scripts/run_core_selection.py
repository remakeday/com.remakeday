"""run_core_selection.py — E7 Core 슬롯 모델 선정 (docs/model_evaluation.md).

모델 × thinking(off/on/default) 셀마다 Core 역할 프로브를 돌린다.
engine은 import만 하고, thinking 제어는 어댑터 서브클래싱으로 주입한다 — 프로덕션 코드 무변경.

    .venv/bin/python scripts/run_core_selection.py --stage protocol
"""

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import core_probes as cp  # noqa: E402
import httpx  # noqa: E402
import runner_common as rc  # noqa: E402

from apps.engine.adapter.outbound.llm.ollama_llm import OllamaLLM  # noqa: E402
from apps.engine.app.dtos.llm_output_dto import evaluator_verdict_output  # noqa: E402
from apps.engine.app.ports.output.llm_port import LLMParseError  # noqa: E402
from apps.engine.app.use_cases import prompts  # noqa: E402
from apps.engine.app.use_cases.game_support import system_msg  # noqa: E402
from apps.engine.app.use_cases.harness import run_with_harness  # noqa: E402

GEMINI_PREFIX = "gemini"
DEFAULT_MODELS = "gemma3:12b,gemma4:12b,gemma4:e4b,qwen3.5:9b,gemini-3-flash-preview"
DEFAULT_OUT_DIR = "docs/review-verification/2026-09-13-core-selection"


# ── thinking 제어 어댑터 ──────────────────────────────────────────────
# 프로덕션 어댑터는 think 필드를 보내지 않는다. 러너 안에서만 주입한다.
# 마지막 호출의 thinking 사용량을 인스턴스에 남겨 셀 라벨을 검증한다(게이트 C9).


class ThinkingOllamaLLM(OllamaLLM):
    def __init__(self, base_url: str, model: str, think: bool | None, timeout: float = 300.0) -> None:
        super().__init__(base_url=base_url, model=model, timeout=timeout)
        self._think = think
        self.last: dict = {}

    def complete(self, messages, json_schema, *, temperature=None) -> dict:
        body = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "keep_alive": "2h",
            "options": {"temperature": 0.7 if temperature is None else temperature},
        }
        if json_schema:
            body["format"] = json_schema
        if self._think is not None:
            body["think"] = self._think
        res = httpx.post(f"{self._base_url}/api/chat", json=body, timeout=self._timeout)
        res.raise_for_status()
        payload = res.json()
        msg = payload.get("message", {})
        self.last = {
            "thinking_chars": len(msg.get("thinking") or ""),
            "output_tokens": payload.get("eval_count"),
            "prompt_tokens": payload.get("prompt_eval_count"),
            "raw_content": msg.get("content", ""),
        }
        try:
            return json.loads(msg.get("content", ""))
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMParseError(f"JSON 파싱 실패: {str(msg.get('content'))[:200]}") from exc


class ThinkingGeminiLLM:
    """GeminiLLM과 같은 LLMPort 계약. thinking_config만 추가로 주입한다."""

    def __init__(self, api_key: str, model: str, think: bool | None, timeout: float = 300.0) -> None:
        from google import genai
        from google.genai import types

        self._types = types
        self._client = genai.Client(
            api_key=api_key, http_options=types.HttpOptions(timeout=int(timeout * 1000))
        )
        self._model = model
        self._think = think
        self.last: dict = {}

    def complete(self, messages, json_schema, *, temperature=None) -> dict:
        types = self._types
        instructions = [m.content for m in messages if m.role == "system"]
        contents = [
            types.Content(role="model" if m.role == "assistant" else "user",
                          parts=[types.Part.from_text(text=m.content)])
            for m in messages if m.role != "system"
        ]
        if not contents:
            contents = [types.Content(role="user", parts=[types.Part.from_text(
                text="위 지시에 따라 JSON으로 응답하라.")])]
        kwargs = dict(
            system_instruction="\n\n".join(instructions) or None,
            temperature=0.7 if temperature is None else temperature,
            response_mime_type="application/json",
            response_json_schema=json_schema or None,
        )
        if self._think is False:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        elif self._think is True:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=-1, include_thoughts=True)
        response = self._client.models.generate_content(
            model=self._model, contents=contents, config=types.GenerateContentConfig(**kwargs),
        )
        usage = response.usage_metadata
        self.last = {
            "thinking_tokens": getattr(usage, "thoughts_token_count", None),
            "output_tokens": getattr(usage, "candidates_token_count", None),
            "prompt_tokens": getattr(usage, "prompt_token_count", None),
            "raw_content": response.text or "",
        }
        try:
            return json.loads(response.text)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMParseError(f"JSON 파싱 실패: {str(response.text)[:200]}") from exc


def build_cell_llm(model: str, think: bool | None, base_url: str):
    if model.startswith(GEMINI_PREFIX):
        key = rc.load_env().get("GEMINI_API_KEY", "")
        if not key.strip():
            raise SystemExit("[에러] GEMINI_API_KEY가 없다. backend/.env를 확인하라.")
        return ThinkingGeminiLLM(api_key=key, model=model, think=think)
    return ThinkingOllamaLLM(base_url=base_url, model=model, think=think)


# ── Stage 0 프로브 ───────────────────────────────────────────────────
# evaluator_verdict — 실프롬프트, 한국어, enum 제약 필드 2개, temperature 0.0

PROBE_CLAIMS = [
    "여기는 대피소가 아니라 가축을 기르는 곳 같다",
    "검진은 아픈 사람을 골라내려고 한다",
    "트럭에 실려 가면 돌아오지 못한다",
    "관리자는 사람이 아니다",
]
PROBE_TRUTH = "이송은 출하를 뜻한다"
# 사전등록 기대: 후보 2(트럭에 실려 가면 돌아오지 못한다)가 정답과 같은 일을 가리킨다
PROBE_EXPECT = {"confirmed", "partial"}


def probe_system() -> str:
    return prompts.EVALUATOR_VERDICT_SYSTEM.format(
        truth_claim=PROBE_TRUTH,
        user_claims="\n".join(f"{i}. {c}" for i, c in enumerate(PROBE_CLAIMS)),
    )


def peak_vram_gib(base_url: str, model: str) -> float | None:
    try:
        res = httpx.get(f"{base_url.rstrip('/')}/api/ps", timeout=5.0)
        for m in res.json().get("models", []):
            if m.get("name") == model or m.get("model") == model:
                return round(m.get("size_vram", 0) / 2**30, 2)
    except Exception:  # noqa: BLE001
        return None
    return None


def run_cell(model: str, think: bool | None, base_url: str) -> dict:
    label = {None: "default", False: "off", True: "on"}[think]
    cell = {"model": model, "think": label}
    try:
        llm = build_cell_llm(model, think, base_url)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001
        return {**cell, "ok": False, "error": f"build: {type(exc).__name__}: {exc}"}

    started = time.perf_counter()
    try:
        out, report = run_with_harness(
            llm, [system_msg(probe_system())],
            evaluator_verdict_output(len(PROBE_CLAIMS)),
            role="evaluator_verdict", temperature=0.0,
        )
    except Exception as exc:  # noqa: BLE001
        return {**cell, "ok": False, "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "error": f"{type(exc).__name__}: {exc}"}
    elapsed = round((time.perf_counter() - started) * 1000)

    last = getattr(llm, "last", {})
    cell.update({
        "ok": out is not None,
        "elapsed_ms": elapsed,
        "attempts": report.attempts,
        "fallback_used": report.fallback_used,
        "violations": report.violations,
        "verdict": out.verdict if out else None,
        "matched_index": out.matched_index if out else None,
        "why": (out.why[:120] if out else None),
        "expected_hit": (out.verdict in PROBE_EXPECT) if out else False,
        "thinking_chars": last.get("thinking_chars"),
        "thinking_tokens": last.get("thinking_tokens"),
        "output_tokens": last.get("output_tokens"),
        "peak_vram_gib": None if model.startswith(GEMINI_PREFIX) else peak_vram_gib(base_url, model),
    })
    if not cell["ok"]:
        cell["raw_head"] = str(last.get("raw_content", ""))[:160]
    return cell


def thinking_used(cell: dict) -> int:
    return (cell.get("thinking_chars") or 0) + (cell.get("thinking_tokens") or 0)



# ── Stage 1 — smoke · advisor_answer ─────────────────────────────────

def pct(n: int, d: int) -> float:
    return round(n / d, 4) if d else 0.0


def run_advisor_cell(model: str, think: bool | None, base_url: str, timeout: float) -> dict:
    label = {None: "default", False: "off", True: "on"}[think]
    llm = build_cell_llm(model, think, base_url)
    if hasattr(llm, "_timeout"):
        llm._timeout = timeout

    items, lat, thinking_total = [], [], 0
    for loop_n, q in cp.QUESTIONS:
        items.append(one_item(llm, loop_n, q, kind="question"))
    for cid, loop_n, q, expect, ev_ids, ov in cp.CONTROLS:
        items.append(one_item(llm, loop_n, q, kind="control", control_id=cid,
                              expected=expect, expected_evidence=ev_ids, overrides=ov))
    for it in items:
        lat.append(it["elapsed_ms"])
        thinking_total += it.get("thinking", 0) or 0

    qs = [i for i in items if i["kind"] == "question"]
    cs = [i for i in items if i["kind"] == "control"]
    by_id = {i["control_id"]: i for i in cs}
    viol: dict[str, int] = {}
    for i in items:
        for v in i["violations"]:
            viol[v.split(":")[0].strip()] = viol.get(v.split(":")[0].strip(), 0) + 1

    lat_sorted = sorted(lat)
    pairs_ok = all(by_id.get(a, {}).get("expected_hit") and by_id.get(b, {}).get("expected_hit")
                   for a, b in cp.CONTROL_PAIRS)
    return {
        "model": model, "think": label, "calls": len(items),
        "fallback_rate": pct(sum(1 for i in items if i["fallback"]), len(items)),
        "violations": viol,
        "detail_rate": pct(sum(1 for i in qs if i["has_detail"]), len(qs)),
        "evidence_rate": pct(sum(1 for i in qs if i["has_evidence"]), len(qs)),
        "egr": pct(sum(1 for i in qs if i["has_detail"] and i["has_evidence"]), len(qs)),
        "pca": pct(sum(1 for i in cs if i["expected_hit"]), len(cs)),
        "pc_evidence_rate": pct(sum(1 for i in cs if i["evidence_hit"]), len(cs)),
        "polarity_pairs_ok": pairs_ok,
        "control_detail": {i["control_id"]: {"got": i["status"], "want": i["expected"],
                                             "hit": i["expected_hit"]} for i in cs},
        "errors": sum(1 for i in items if i.get("error")),
        "latency_p50_ms": lat_sorted[len(lat_sorted) // 2],
        "latency_p95_ms": lat_sorted[min(len(lat_sorted) - 1, int(len(lat_sorted) * 0.95))],
        "thinking_total": thinking_total,
        "peak_vram_gib": None if model.startswith(GEMINI_PREFIX) else peak_vram_gib(base_url, model),
        "items": items,
    }


def one_item(llm, loop_n, question, *, kind, control_id=None, expected=None,
             expected_evidence=None, overrides=None) -> dict:
    started = time.perf_counter()
    err = None
    try:
        probe = cp.ask_probe(loop_n, question, llm, overrides=overrides)
        result, harness = probe["result"], probe["harness"]
    except Exception as exc:  # noqa: BLE001
        result, harness = {}, []
        err = f"{type(exc).__name__}: {exc}"[:180]
    elapsed = round((time.perf_counter() - started) * 1000)
    last = getattr(llm, "last", {})
    ev = result.get("evidence_ids") or []
    status = result.get("status")
    return {
        "kind": kind, "control_id": control_id, "loop_n": loop_n, "question": question,
        "status": status, "answer": result.get("answer"),
        "detail": (result.get("detail") or "")[:200] or None,
        "evidence_ids": ev,
        "has_detail": bool(result.get("detail")), "has_evidence": bool(ev),
        "expected": expected,
        "expected_hit": (status == expected) if expected else None,
        "evidence_hit": (set(expected_evidence or []) <= set(ev)) if expected_evidence else None,
        "fallback": any(h.get("fallback_used") for h in harness),
        "violations": [v for h in harness for v in (h.get("violations") or [])],
        "attempts": max((h.get("attempts", 0) for h in harness), default=0),
        "thinking": (last.get("thinking_chars") or 0) + (last.get("thinking_tokens") or 0),
        "elapsed_ms": elapsed, "error": err,
    }


def stage_smoke(models, base_url, caps, timeout, dropped):
    plan = []
    for m in models:
        can_think = m.startswith(GEMINI_PREFIX) or ("thinking" in caps.get(m, []))
        plan.extend([(m, False), (m, True)] if can_think else [(m, None)])
    plan = [c for c in plan if (c[0], {None: "default", False: "off", True: "on"}[c[1]]) not in dropped]

    print(f"\n### E7 Stage 1 — smoke · advisor_answer · {len(plan)}셀 × 22문항\n", flush=True)
    cells = []
    for model, think in plan:
        label = {None: "default", False: "off", True: "on"}[think]
        print(f"  … {model} / think={label}", flush=True)
        c = run_advisor_cell(model, think, base_url, timeout)
        cells.append(c)
        print(f"     폴백 {c['fallback_rate']:.2f} · EGR {c['egr']:.2f} · PCA {c['pca']:.2f} "
              f"· 극성쌍 {'O' if c['polarity_pairs_ok'] else 'X'} · p50 {c['latency_p50_ms']}ms", flush=True)
    return cells



# ── Stage 2 — formal · 4역할 × n ─────────────────────────────────────

PACING_RPM = 10  # gemini_llm.py 기본값. effective 유도에 쓴다


def p_at(values, q):
    v = sorted(values)
    return v[min(len(v) - 1, int(len(v) * q))] if v else 0


def role_stats(items):
    lat = [i["elapsed_ms"] for i in items]
    return {"calls": len(items),
            "fallback_rate": pct(sum(1 for i in items if i["fallback"]), len(items)),
            "latency_p50_ms": p_at(lat, 0.5), "latency_p95_ms": p_at(lat, 0.95)}


def run_formal_cell(model, think, base_url, timeout, n, roles):
    from apps.scenarios.scenario_a.adapter import build as build_sc
    llm = build_cell_llm(model, think, base_url)
    if hasattr(llm, "_timeout"):
        llm._timeout = timeout
    scenario = build_sc()
    bundle = scenario.bundle()
    adv, pln, mgr, evl = [], [], [], []

    for rep in range(n):
        if "advisor" in roles:
            for loop_n, q in cp.QUESTIONS:
                adv.append({**one_item(llm, loop_n, q, kind="question"), "rep": rep})
            for cid, loop_n, q, expect, ev_ids, ov in cp.CONTROLS:
                adv.append({**one_item(llm, loop_n, q, kind="control", control_id=cid,
                                       expected=expect, expected_evidence=ev_ids, overrides=ov), "rep": rep})
        if "planner" in roles:
            for dmg, rules in cp.PLANNER_CASES:
                pln.append(timed(lambda: cp.planner_probe(llm, bundle, damage_level=dmg, rules=rules),
                                 llm, extra={"damage_level": dmg, "rep": rep}))
        if "manager" in roles:
            for case in cp.MANAGER_CASES:
                mgr.append(timed(lambda c=case: cp.manager_probe(llm, scenario, c) + ({},),
                                 llm, extra={"rep": rep}))
        if "evaluator" in roles:
            for case in cp.EVAL_CASES:
                evl.append(timed(lambda c=case: cp.evaluator_probe(llm, c), llm,
                                 extra={"truth": case[0], "rep": rep}))

    is_gem = model.startswith(GEMINI_PREFIX)
    pace_ms = 60000 // PACING_RPM
    cell = {"model": model, "think": {None: "default", False: "off", True: "on"}[think], "n": n,
            "roles": sorted(roles)}
    gates = {}

    if adv:
        qs = [i for i in adv if i["kind"] == "question"]
        cs = [i for i in adv if i["kind"] == "control"]
        # 통제는 rep마다 반복되므로 id별 전체 통과율로 본다
        by_id = {}
        for i in cs:
            by_id.setdefault(i["control_id"], []).append(bool(i["expected_hit"]))
        pairs_ok = all(all(by_id.get(a, [False])) and all(by_id.get(b, [False]))
                       for a, b in cp.CONTROL_PAIRS)
        cell["advisor"] = {**role_stats(adv),
                           "egr": pct(sum(1 for i in qs if i["has_detail"] and i["has_evidence"]), len(qs)),
                           "pca": pct(sum(1 for i in cs if i["expected_hit"]), len(cs)),
                           "pc_evidence_rate": pct(sum(1 for i in cs if i["evidence_hit"]), len(cs)),
                           "polarity_pairs_ok": pairs_ok,
                           "control_pass_rate": {k: pct(sum(v), len(v)) for k, v in sorted(by_id.items())}}
        adv_p95 = p_at([i["elapsed_ms"] for i in adv], 0.95)
        gates["C11_advisor_p95_le_5s"] = {
            "raw": adv_p95, "effective": max(adv_p95, pace_ms) if is_gem else adv_p95,
            "pass": (max(adv_p95, pace_ms) if is_gem else adv_p95) <= 5000}

    if pln:
        lar_vals = [x["meta"].get("lar") for x in pln if x["ok"] and x["meta"].get("lar") is not None]
        cell["planner"] = {**role_stats_x(pln),
                           "lar": round(sum(lar_vals) / len(lar_vals), 4) if lar_vals else None}
        pln_p95 = p_at([x["elapsed_ms"] for x in pln], 0.95)
        gates["C12_planner_p95_le_15s"] = {
            "raw": pln_p95, "effective": max(pln_p95, pace_ms) if is_gem else pln_p95,
            "pass": (max(pln_p95, pace_ms) if is_gem else pln_p95) <= 15000}

    if mgr:
        cell["manager_check"] = role_stats_x(mgr)

    if evl:
        ev_hits = sum(1 for x in evl if x["meta"].get("hit"))
        cell["evaluator_verdict"] = {**role_stats_x(evl), "expected_hit_rate": pct(ev_hits, len(evl))}
        evl_p50 = p_at([x["elapsed_ms"] for x in evl], 0.5)
        gates["C13_night_scoring_le_30s"] = {
            "per_call_p50": evl_p50, "claims_assumed": 10,
            "total": (max(evl_p50, pace_ms) if is_gem else evl_p50) * 10,
            "pass": ((max(evl_p50, pace_ms) if is_gem else evl_p50) * 10) <= 30000}

    cell.update({
        "gates": gates,
        "pacing_note": "gemini는 effective = max(raw, 6000ms) 유도값. 측정값 아님" if is_gem else None,
        "peak_vram_gib": None if is_gem else peak_vram_gib(base_url, model),
        "items": {k: v for k, v in
                  [("advisor", adv), ("planner", pln), ("manager_check", mgr), ("evaluator_verdict", evl)] if v},
    })
    return cell


def role_stats_x(rows):
    lat = [r["elapsed_ms"] for r in rows]
    return {"calls": len(rows),
            "fallback_rate": pct(sum(1 for r in rows if r["fallback"]), len(rows)),
            "error_count": sum(1 for r in rows if r.get("error")),
            "latency_p50_ms": p_at(lat, 0.5), "latency_p95_ms": p_at(lat, 0.95)}


def timed(fn, llm, *, extra=None):
    started = time.perf_counter()
    err, out, report, meta = None, None, None, {}
    try:
        out, report, meta = fn()
    except Exception as exc:  # noqa: BLE001
        err = f"{type(exc).__name__}: {exc}"[:180]
    last = getattr(llm, "last", {})
    return {**(extra or {}), "ok": out is not None, "error": err,
            "fallback": bool(report.fallback_used) if report else True,
            "violations": list(report.violations) if report else [],
            "attempts": report.attempts if report else 0,
            "thinking": (last.get("thinking_chars") or 0) + (last.get("thinking_tokens") or 0),
            "elapsed_ms": round((time.perf_counter() - started) * 1000), "meta": meta or {}}


NPC_MODEL = "exaone3.5:7.8b"


def ps_snapshot(base_url):
    res = httpx.get(f"{base_url.rstrip('/')}/api/ps", timeout=5.0).json()
    return [{"model": m.get("name") or m.get("model"),
             "size_vram_gib": round(m.get("size_vram", 0) / 2**30, 2),
             "size_gib": round(m.get("size", 0) / 2**30, 2)}
            for m in res.get("models", [])]


def gpu_used_mib():
    import subprocess
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader,nounits"], text=True)
        used, total = out.strip().splitlines()[0].split(",")
        return int(used), int(total)
    except Exception:  # noqa: BLE001
        return None, None


def unload_model(base_url, model):
    try:
        httpx.post(f"{base_url.rstrip('/')}/api/generate",
                   json={"model": model, "prompt": "", "keep_alive": 0}, timeout=30.0)
    except Exception:  # noqa: BLE001
        pass


def npc_call(base_url, timeout):
    t0 = time.monotonic()
    httpx.post(f"{base_url.rstrip('/')}/api/chat", json={
        "model": NPC_MODEL, "stream": False,
        "messages": [{"role": "system", "content": "너는 격리 구역의 준이다. 한 문장으로만 답한다."},
                     {"role": "user", "content": "트럭 소리 들었어?"}]}, timeout=timeout)
    return int((time.monotonic() - t0) * 1000)


def stage_concurrency(spec, base_url, timeout, rounds):
    """Stage 3 — 후보 + NPC 동시 상주. NPC 콜과 Core 콜을 교대로 날리며
    매 콜 뒤 /api/ps로 상주를 확인한다. 축출·부분 오프로드 발생 시 후보 탈락."""
    from apps.scenarios.scenario_a.adapter import build as build_sc
    scenario = build_sc()
    bundle = scenario.bundle()
    print(f"\n### E7 Stage 3 — concurrency · 후보 {len(spec)} + NPC {NPC_MODEL} · rounds={rounds}\n", flush=True)
    out = []
    for model, think in spec:
        # 격리: 후보·NPC 외 상주 모델 언로드
        for m in ps_snapshot(base_url):
            if m["model"] not in (model, NPC_MODEL):
                unload_model(base_url, m["model"])
        print(f"  … {model} + {NPC_MODEL}", flush=True)
        llm = build_cell_llm(model, think, base_url)
        if hasattr(llm, "_timeout"):
            llm._timeout = timeout

        snaps, npc_ms, core_ms, evictions, offloads = [], [], [], [], []

        def snap(tag):
            resident = ps_snapshot(base_url)
            used, total = gpu_used_mib()
            names = {r["model"] for r in resident}
            entry = {"after": tag, "resident": resident, "gpu_used_mib": used, "gpu_total_mib": total}
            snaps.append(entry)
            return names, resident

        # 1) NPC 먼저 상주 (프로덕션 상태), 2) 후보 로드
        npc_ms.append(npc_call(base_url, timeout))
        snap("npc_warm")
        t0 = time.monotonic()
        cp.evaluator_probe(llm, cp.EVAL_CASES[13])  # D4 — 짧고 결정적
        core_ms.append(int((time.monotonic() - t0) * 1000))
        names, resident = snap("core_warm")

        # 3) 교대 콜 — 매 스냅샷에서 둘 다 상주해야 한다
        for r in range(rounds):
            npc_ms.append(npc_call(base_url, timeout))
            names, resident = snap(f"round{r+1}_npc")
            missing = {model, NPC_MODEL} - names
            if missing:
                evictions.append({"after": f"round{r+1}_npc", "missing": sorted(missing)})
            t0 = time.monotonic()
            if r == 1:
                cp.planner_probe(llm, bundle)  # 가장 무거운 Core 콜 1회 포함
            else:
                cp.evaluator_probe(llm, cp.EVAL_CASES[13])
            core_ms.append(int((time.monotonic() - t0) * 1000))
            names, resident = snap(f"round{r+1}_core")
            missing = {model, NPC_MODEL} - names
            if missing:
                evictions.append({"after": f"round{r+1}_core", "missing": sorted(missing)})
            for rmod in resident:
                if rmod["model"] in (model, NPC_MODEL) and rmod["size_vram_gib"] < rmod["size_gib"]:
                    offloads.append({"after": f"round{r+1}", **rmod})

        both = [s for s in snaps if {model, NPC_MODEL} <= {r["model"] for r in s["resident"]}]
        peak_pair = max((sum(r["size_vram_gib"] for r in s["resident"]
                             if r["model"] in (model, NPC_MODEL)) for s in both), default=None)
        peak_gpu = max((s["gpu_used_mib"] for s in snaps if s["gpu_used_mib"]), default=None)
        cell = {
            "candidate": model, "think": {None: "default", False: "off", True: "on"}[think],
            "npc": NPC_MODEL, "rounds": rounds,
            "pair_peak_vram_gib": peak_pair, "gpu_peak_used_mib": peak_gpu,
            "gpu_total_mib": snaps[0]["gpu_total_mib"],
            "npc_latency_ms": npc_ms, "core_latency_ms": core_ms,
            "evictions": evictions, "partial_offloads": offloads,
            "gate_no_eviction": {"pass": not evictions and not offloads},
            "snapshots": snaps,
        }
        out.append(cell)
        print(f"     pair peak {peak_pair} GiB · GPU {peak_gpu}/{snaps[0]['gpu_total_mib']} MiB"
              f" · 축출 {len(evictions)} · 오프로드 {len(offloads)}"
              f" → {'통과' if cell['gate_no_eviction']['pass'] else '탈락'}", flush=True)
        unload_model(base_url, model)  # 다음 셀 격리. NPC는 프로덕션 상태라 유지
    return out


# ── Stage 4 — loop ───────────────────────────────────────────────────

LOOP_DB_URL = "postgresql+psycopg://pigfarm:pigfarm-dev@localhost:5435/pigfarm_test"
LOOP_PORT = 8600
LOOP_PLAYER_MODEL = NPC_MODEL  # 상주 NPC 재사용 — 제3 모델 로드로 인한 축출 회피


def _loop_harness_stats(attempt_id):
    """서버 쪽 하네스 이벤트를 DB에서 직접 센다.

    /attempts/{id}/harness 인스펙터는 다섯 번째 밤 종료 후에만 열리므로(AccessDenied)
    1회차 스모크에서는 쓸 수 없다. events 테이블 읽기 전용 SELECT만 한다."""
    from sqlalchemy import create_engine, text
    eng = create_engine(LOOP_DB_URL)
    try:
        with eng.connect() as conn:
            rows = conn.execute(text(
                "SELECT payload->>'role' AS role, count(*) AS calls, "
                "sum(CASE WHEN (payload->>'fallback_used')::bool THEN 1 ELSE 0 END) AS fallbacks, "
                "sum((payload->>'attempts')::int) AS attempts "
                "FROM events WHERE session_id = :sid AND type = 'harness_event' "
                "GROUP BY 1 ORDER BY 1"), {"sid": attempt_id}).mappings().all()
    finally:
        eng.dispose()
    per_role = {r["role"]: {"calls": int(r["calls"]), "fallbacks": int(r["fallbacks"] or 0),
                            "attempts": int(r["attempts"] or 0)} for r in rows}
    return {
        "model_calls": sum(v["calls"] for v in per_role.values()),
        "model_attempts": sum(v["attempts"] for v in per_role.values()),
        "fallbacks": sum(v["fallbacks"] for v in per_role.values()),
        "per_role": per_role,
    }


def _wait_health(client, secs):
    deadline = time.monotonic() + secs
    last = None
    while time.monotonic() < deadline:
        try:
            res = client.get("/health")
            if res.status_code == 200:
                return res.json()
        except Exception as exc:  # noqa: BLE001
            last = exc
        time.sleep(1.0)
    raise RuntimeError(f"서버 health 대기 초과: {last}")


def stage_loop(spec, base_url, timeout, out_dir):
    """Stage 4 — 루프 스모크 (§4.1). 후보별로 별도 환경 서버(scripts.loop_app,
    포트 8600, pigfarm_test DB)를 띄우고 selfplay(성실)로 1회차(낮 발화→비트→밤 제출)를
    완주시킨다. 판정은 점수가 아니라 크래시 0·폴백 폭주 없음·완주다."""
    import os
    import random
    import subprocess

    import run_selfplay as sp

    player_llm = rc.make_llm(LOOP_PLAYER_MODEL, base_url)
    print(f"\n### E7 Stage 4 — loop · 후보 {len(spec)} · persona=성실 · loops=1 "
          f"· player={LOOP_PLAYER_MODEL} · db=pigfarm_test\n", flush=True)
    cells = []
    for model, _think in spec:
        # 격리: 후보·NPC 외 상주 모델 언로드
        for m in ps_snapshot(base_url):
            if m["model"] not in (model, NPC_MODEL):
                unload_model(base_url, m["model"])
        row = {"model": model, "think": "off", "persona": "성실", "loops": 1}
        env = dict(os.environ)
        env.update({"DATABASE_URL": LOOP_DB_URL, "CORE_LLM_PROVIDER": "ollama",
                    "CORE_LLM_MODEL": model, "LOOP_CORE_TIMEOUT": str(timeout)})
        slug = model.replace(":", "_").replace("/", "_")
        log_path = out_dir / f"stage4-server-{slug}.log"
        print(f"  … {model} — 서버 기동 (:{LOOP_PORT}, 로그 {log_path.name})", flush=True)
        log_f = log_path.open("w", encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "scripts.loop_app:app",
             "--port", str(LOOP_PORT)],
            cwd=rc.BACKEND_ROOT, env=env, stdout=log_f, stderr=subprocess.STDOUT)
        client = httpx.Client(base_url=f"http://localhost:{LOOP_PORT}", timeout=timeout * 3)
        t0 = time.monotonic()
        try:
            health = _wait_health(client, 60)
            row["health_core"] = health["models"]["core"]
            if health["models"]["core"] != f"ollama:{model}":
                raise RuntimeError(f"core 라벨 불일치: {health['models']['core']}")
            result = sp.play_game(client, player_llm, "성실", max_loops=1,
                                  rng=random.Random(42), verbose=True)
            row["attempt_id"] = result["attempt_id"]
            row["scores"] = result["scores"]
            row["completed"] = len(result["scores"]) == 1
            dbg = client.get("/loop-debug").json()
            row["core_calls"] = dbg["core_calls"]
            row["thinking_chars_total"] = dbg["thinking_chars_total"]
            row["think_off_verified"] = dbg["thinking_chars_total"] == 0  # 게이트 C9
            stats = _loop_harness_stats(result["attempt_id"])
            row["fallbacks"] = stats["fallbacks"]
            row["model_calls"] = stats["model_calls"]
            row["model_attempts"] = stats["model_attempts"]
            row["per_role"] = stats["per_role"]
            row["pair_ps"] = ps_snapshot(base_url)
            row["crash"] = False
        except Exception as exc:  # noqa: BLE001
            row["crash"] = True
            row["error"] = f"{type(exc).__name__}: {exc}"
            row.setdefault("completed", False)
        finally:
            row["secs"] = round(time.monotonic() - t0, 1)
            row["server_alive_at_end"] = proc.poll() is None
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            log_f.close()
            client.close()
        row["gate_pass"] = bool(row.get("completed")) and not row["crash"] \
            and row.get("server_alive_at_end", False)
        cells.append(row)
        status = "완주" if row.get("completed") else "미완주"
        print(f"  {model}: {status} · 점수 {row.get('scores')} · 폴백 {row.get('fallbacks')} "
              f"· core 콜 {row.get('core_calls')} · thinking {row.get('thinking_chars_total')}자 "
              f"· {row['secs']}s · gate_pass={row['gate_pass']}", flush=True)
    return cells


def stage_formal(cells_spec, base_url, timeout, n, roles):
    print(f"\n### E7 Stage 2 — formal · {len(cells_spec)}셀 × 역할 {sorted(roles)} × n={n}\n", flush=True)
    out = []
    for model, think in cells_spec:
        label = {None: "default", False: "off", True: "on"}[think]
        print(f"  … {model} / think={label}", flush=True)
        c = run_formal_cell(model, think, base_url, timeout, n, roles)
        out.append(c)
        g = c["gates"]
        parts = []
        if "advisor" in roles:
            parts.append(f"advisor PCA {c['advisor']['pca']:.2f} 극성쌍 {'O' if c['advisor']['polarity_pairs_ok'] else 'X'}")
        if "planner" in roles:
            parts.append(f"planner LAR {c['planner']['lar']}")
        if "evaluator" in roles:
            parts.append(f"eval 기대 {c['evaluator_verdict']['expected_hit_rate']:.2f}")
        for key, name in [("C11_advisor_p95_le_5s", "C11"), ("C12_planner_p95_le_15s", "C12"),
                          ("C13_night_scoring_le_30s", "C13")]:
            if key in g:
                parts.append(f"{name} {'O' if g[key]['pass'] else 'X'}")
        print("     " + " · ".join(parts), flush=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="E7 Core 슬롯 모델 선정")
    parser.add_argument("--stage", default="protocol",
                        choices=["protocol", "smoke", "formal", "concurrency", "loop"])
    parser.add_argument("--roles", default=None,
                        help="formal 역할 필터 (advisor,planner,manager,evaluator 콤마 목록 · 기본 전부). smoke는 advisor 고정")
    parser.add_argument("--timeout", type=float, default=120.0, help="콜당 타임아웃 초 (기본 120)")
    parser.add_argument("--n", type=int, default=3, help="formal 반복 수 (기본 3)")
    parser.add_argument("--rounds", type=int, default=3, help="concurrency 교대 콜 라운드 수 (기본 3)")
    parser.add_argument("--models", default=DEFAULT_MODELS)
    parser.add_argument("--base-url", dest="ollama_url", default=None)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    base_url = args.ollama_url or rc.ollama_base_url()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    local = [m for m in models if not m.startswith(GEMINI_PREFIX)]
    rc.check_ollama(base_url, local)

    # thinking capability 조회 — 없는 모델은 default만 잰다
    caps: dict[str, list[str]] = {}
    for m in local:
        res = httpx.post(f"{base_url.rstrip('/')}/api/show", json={"model": m}, timeout=10.0)
        caps[m] = res.json().get("capabilities", [])

    if args.stage == "loop":
        # Stage 3 통과 후보 (docs/model_evaluation.md 부록 A.9)
        spec = [("gemma4:12b", False), ("gemma4:e4b", False)]
        spec = [c for c in spec if c[0] in models]
        rc.check_ollama(base_url, [NPC_MODEL])
        out_dir = rc.PROJECT_ROOT / args.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        cells = stage_loop(spec, base_url, args.timeout, out_dir)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = out_dir / f"stage4-loop-{stamp}.json"
        path.write_text(json.dumps({
            "experiment": "E7", "stage": "loop", "npc": NPC_MODEL,
            "player_model": LOOP_PLAYER_MODEL, "persona": "성실", "loops": 1,
            "db": "pigfarm_test", "port": LOOP_PORT,
            "started_at": stamp, "host": "rtx5060ti-16g", "runtime": "ollama-cuda",
            "cells": cells,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        for row in cells:
            rc.append_metric(
                "docs/metrics.yml", "core_selection", row["model"],
                think="off", stage="loop", persona="성실", loops=1,
                completed=row.get("completed"), crash=row["crash"],
                fallbacks=row.get("fallbacks"), core_calls=row.get("core_calls"),
                model_calls=row.get("model_calls"), model_attempts=row.get("model_attempts"),
                score=(row.get("scores") or [None])[0],
                thinking_chars_total=row.get("thinking_chars_total"),
                secs=row.get("secs"), attempt_id=row.get("attempt_id"),
                npc=NPC_MODEL, player_model=LOOP_PLAYER_MODEL, db="pigfarm_test",
                gate_pass=row["gate_pass"],
                host="rtx5060ti-16g", runtime="ollama-cuda", quant="Q4_K_M")
        print(f"\n원문 → {path}\nmetrics → docs/metrics.yml")
        return

    if args.stage == "concurrency":
        # Stage 2 통과 후보 (docs/model_evaluation.md 부록 A.7·A.8)
        spec = [("gemma4:12b", False), ("gemma4:e4b", False)]
        spec = [c for c in spec if c[0] in models]
        rc.check_ollama(base_url, [NPC_MODEL])
        cells = stage_concurrency(spec, base_url, args.timeout, args.rounds)
        out_dir = rc.PROJECT_ROOT / args.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = out_dir / f"stage3-concurrency-{stamp}.json"
        path.write_text(json.dumps({
            "experiment": "E7", "stage": "concurrency", "npc": NPC_MODEL,
            "started_at": stamp, "host": "rtx5060ti-16g", "runtime": "ollama-cuda",
            "cells": cells,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n원문 → {path}")
        return

    if args.stage == "formal":
        roles = set((args.roles or "advisor,planner,manager,evaluator").split(","))
        bad = roles - {"advisor", "planner", "manager", "evaluator"}
        if bad:
            raise SystemExit(f"--roles 알 수 없는 역할: {sorted(bad)}")
        # Stage 1 통과 셀 (docs/model_evaluation.md 부록 A.6)
        spec = [("gemma3:12b", None), ("gemma4:12b", False),
                ("gemma4:e4b", False), ("gemini-3-flash-preview", False)]
        spec = [c for c in spec if c[0] in models]
        cells = stage_formal(spec, base_url, args.timeout, args.n, roles)
        out_dir = rc.PROJECT_ROOT / args.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = out_dir / f"stage2-formal-{stamp}.json"
        path.write_text(json.dumps({
            "experiment": "E7", "stage": "formal", "n": args.n,
            "roles": sorted({"advisor": "advisor_answer", "planner": "planner",
                             "manager": "manager_check", "evaluator": "evaluator_verdict"}[r] for r in roles),
            "started_at": stamp, "host": "rtx5060ti-16g", "runtime": "ollama-cuda",
            "pacing_rpm": PACING_RPM, "cells": cells,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n원문 → {path}")
        return

    if args.stage == "smoke":
        # Stage 0에서 탈락한 셀은 제외한다 (docs/model_evaluation.md 부록 A.5)
        dropped = {("qwen3.5:9b", "on")}
        cells = stage_smoke(models, base_url, caps, args.timeout, dropped)

        rows = [[c["model"], c["think"], c["calls"], f'{c["fallback_rate"]:.2f}',
                 f'{c["egr"]:.2f}', f'{c["pca"]:.2f}', f'{c["pc_evidence_rate"]:.2f}',
                 "O" if c["polarity_pairs_ok"] else "X",
                 c["latency_p50_ms"], c["latency_p95_ms"], c["thinking_total"],
                 c["peak_vram_gib"] if c["peak_vram_gib"] is not None else "-"]
                for c in cells]
        print()
        rc.print_table(["model", "think", "colls", "폴백", "EGR", "PCA", "PC근거",
                        "극성쌍", "p50", "p95", "thinking", "VRAM"], rows)

        print("\n통제별 판정 (want → got):")
        ids = [c[0] for c in cp.CONTROLS]
        print("  " + " ".join(f"{i:>5}" for i in ["cell"] + ids))
        for c in cells:
            marks = [("O" if c["control_detail"][i]["hit"] else "X") for i in ids]
            print(f'  {c["model"][:12]}/{c["think"][:3]:<4} ' + " ".join(f"{m:>5}" for m in marks))

        print("\nStage 1 게이트 (smoke 차단: 폴백 > 0.5 또는 오류 다수):")
        for c in cells:
            bad = c["fallback_rate"] > 0.5
            print(f'  {c["model"]:24} {c["think"]:<8} 폴백 {c["fallback_rate"]:.2f} '
                  f'오류 {c["errors"]:2d} → {"탈락" if bad else "생존"}')

        out_dir = rc.PROJECT_ROOT / args.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = out_dir / f"stage1-smoke-advisor-{stamp}.json"
        path.write_text(json.dumps({
            "experiment": "E7", "stage": "smoke", "roles": ["advisor_answer"],
            "started_at": stamp, "host": "rtx5060ti-16g", "runtime": "ollama-cuda",
            "corpus": {"questions": len(cp.QUESTIONS), "controls": len(cp.CONTROLS),
                       "public_observations": len(cp.PUBLIC)},
            "dropped_by_stage0": sorted(f"{m}/{t}" for m, t in dropped),
            "cells": cells,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n원문 → {path}")
        return

    plan: list[tuple[str, bool | None]] = []
    for m in models:
        can_think = m.startswith(GEMINI_PREFIX) or ("thinking" in caps.get(m, []))
        plan.extend([(m, None), (m, False), (m, True)] if can_think else [(m, None)])

    print(f"\n### E7 Stage 0 — protocol · {len(plan)}셀\n")
    results = []
    for model, think in plan:
        label = {None: "default", False: "off", True: "on"}[think]
        print(f"  … {model} / think={label}", flush=True)
        cell = run_cell(model, think, base_url)
        results.append(cell)

    rows = []
    for c in results:
        thinking = thinking_used(c)
        rows.append([
            c["model"], c["think"],
            "O" if c.get("ok") else "X",
            c.get("verdict") or (c.get("error", "")[:28] if not c.get("ok") else "-"),
            "O" if c.get("expected_hit") else "X",
            c.get("elapsed_ms", "-"),
            thinking if thinking else 0,
            c.get("peak_vram_gib") if c.get("peak_vram_gib") is not None else "-",
        ])
    print()
    rc.print_table(["model", "think", "ok", "verdict", "기대일치", "ms", "thinking", "VRAM GiB"], rows)

    # 게이트 C9 — thinking off 셀에서 thinking 사용량이 0인가
    print("\n게이트 C9 (think=off 셀의 thinking 사용량 = 0):")
    bad = [c for c in results if c["think"] == "off" and thinking_used(c) > 0]
    for c in results:
        if c["think"] == "off":
            used = thinking_used(c)
            print(f"  {c['model']:24} {used:>7}  {'통과' if used == 0 else '미달 — 라벨 신뢰 불가'}")
    print(f"  → {'전부 통과' if not bad else str(len(bad)) + '셀 미달'}")

    # provider 기본값이 어느 셀인가 (§7 제약 2)
    print("\nprovider 기본값 판정:")
    by_model: dict[str, dict[str, dict]] = {}
    for c in results:
        by_model.setdefault(c["model"], {})[c["think"]] = c
    for model, cells in by_model.items():
        d = cells.get("default")
        if d is None:
            continue
        used = thinking_used(d)
        if len(cells) == 1:
            verdict = "thinking 없음 — default = off"
        else:
            verdict = "default = ON" if used > 0 else "default = OFF"
        print(f"  {model:24} thinking {used:>7} → {verdict}")

    out_dir = rc.PROJECT_ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"stage0-protocol-{stamp}.json"
    path.write_text(json.dumps({
        "experiment": "E7", "stage": "protocol",
        "started_at": stamp, "host": "rtx5060ti-16g", "runtime": "ollama-cuda",
        "probe": {"role": "evaluator_verdict", "truth_claim": PROBE_TRUTH,
                  "claims": PROBE_CLAIMS, "expected_verdict": sorted(PROBE_EXPECT)},
        "capabilities": caps,
        "cells": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n원문 → {path}")
    print("Stage 0은 metrics.yml에 적립하지 않는다 (model_evaluation.md §4.1).")


if __name__ == "__main__":
    main()
