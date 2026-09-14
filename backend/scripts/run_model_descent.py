"""run_model_descent.py — E6 NPC Slot Descent (부록 E6 v0.1 §6).

Anchor(exaone3.5:7.8b) 대비 qwen3.5 사다리(9b→4b→2b→0.8b)의 7세 정책 비열등을 잰다.
engine은 import만, 결과는 metrics.yml append + 원문 JSON.

셀 절차: Stage 0(스키마 1콜) → age7 5항목 × n (judge 3회 다수결 + 일치율 D3)
        → 누설 프로브 5 × leak_n (하네스 ON) → 지연 p50/p95 · Peak VRAM.

thinking 제어: capabilities에 thinking이 있는 모델은 러너 서브클래스(ThinkingOllamaLLM,
think=False)로 강제한다 — E6 §2.1. Anchor(exaone)는 thinking이 없어 그대로.

    .venv/bin/python scripts/run_model_descent.py --n 5 --tier formal
"""

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
import runner_common as rc  # noqa: E402
from run_age7_check import _FORGET_FACTS, ITEMS  # noqa: E402
from run_core_selection import ThinkingOllamaLLM, ps_snapshot, unload_model  # noqa: E402
from run_leak_test import PROBES  # noqa: E402

from apps.engine.app.dtos.llm_output_dto import AgentOutput  # noqa: E402
from apps.engine.app.use_cases.game_support import (  # noqa: E402
    applicable_ban_words,
    build_agent_messages,
    pick_fallback_line,
)
from apps.engine.app.use_cases.harness import forbidden_word_check, run_with_harness  # noqa: E402
from apps.scenarios.scenario_a.adapter import build as build_scenario  # noqa: E402

DEFAULT_MODELS = "exaone3.5:7.8b,qwen3.5:9b,qwen3.5:4b,qwen3.5:2b-q4_K_M,qwen3.5:0.8b"
ANCHOR = "exaone3.5:7.8b"
DEFAULT_OUT_DIR = "docs/review-verification/2026-09-14-npc-descent"
ITEM_KEYS = [it["key"] for it in ITEMS]  # 순서 고정 (§6.1 item_scores)
JUDGE_VOTES = 3          # D3 — 같은 응답을 3회 판정
ITEM_THRESHOLD = 0.7
VERDICT_ITEMS = ["1_사실대로", "2_왜=몰라", "4_유도수용", "5_문자그대로"]  # 항목 3은 관측만 (§3.1)


def model_info(base_url: str, model: str) -> tuple[str, list[str]]:
    res = httpx.post(f"{base_url.rstrip('/')}/api/show", json={"model": model}, timeout=10.0)
    d = res.json()
    return d.get("details", {}).get("quantization_level", "?"), d.get("capabilities", [])


def build_npc_llm(model: str, caps: list[str], base_url: str, timeout: float):
    if "thinking" in caps:
        return ThinkingOllamaLLM(base_url=base_url, model=model, think=False, timeout=timeout)
    llm = rc.make_llm(model, base_url)
    llm._timeout = timeout  # noqa: SLF001
    return llm


def first_attempt_schema_ok(report) -> bool:
    if not report.call_records:
        return False
    r0 = report.call_records[0]
    if r0.get("error") is not None:
        return False
    return not any(str(c).startswith("schema:") for c in r0.get("checks", []))


def call_elapsed_ms(report) -> int:
    return sum(int(r.get("elapsed_ms") or 0) for r in report.call_records)


def thinking_chars(llm) -> int:
    return int(getattr(llm, "last", {}).get("thinking_chars") or 0)


def run_cell(model, caps, quant, base_url, judge_llm, bundle, char, *,
             age7_on, n, leak_n, timeout, verbose) -> dict:
    cell: dict = {"model": model, "quant": quant, "policy": "on" if age7_on else "off",
                  "thinking_forced_off": "thinking" in caps}
    npc = build_npc_llm(model, caps, base_url, timeout)
    lat_ms: list[int] = []
    schema_ok = 0
    fallbacks = 0
    calls = 0
    think_total = 0

    # ── Stage 0 — 스키마 1콜 (직접 complete, 재시도 없음) ──────────────
    messages = build_agent_messages(bundle, char, suspicion=20, trust=50, opposite=False,
                                    rules_text="", memory=[], user_text="밥 먹었어?",
                                    loop_n=1, age7_on=age7_on)
    try:
        t0 = time.monotonic()
        raw = npc.complete(messages, AgentOutput.model_json_schema())
        AgentOutput.model_validate(raw)
        cell["stage0"] = {"pass": True, "ms": int((time.monotonic() - t0) * 1000)}
    except Exception as exc:  # noqa: BLE001
        cell["stage0"] = {"pass": False, "error": f"{type(exc).__name__}: {str(exc)[:200]}"}
        cell["collapse"] = "schema"
        return cell
    think_total += thinking_chars(npc)

    # ── age7 — 5항목 × n · judge 3회 다수결 · 일치율 ──────────────────
    rates: dict[str, float] = {}
    agree_hits = 0
    agree_total = 0
    transcripts = []
    for item in ITEMS:
        passed = 0
        for i in range(n):
            memory, rules_text, utterance = item["cases"][i % len(item["cases"])]
            messages = build_agent_messages(
                bundle, char, suspicion=20, trust=50, opposite=False,
                rules_text=rules_text, memory=memory or [],
                user_text=utterance, loop_n=1, age7_on=age7_on)
            out, report = run_with_harness(npc, messages, AgentOutput, role="agent")
            calls += 1
            lat_ms.append(call_elapsed_ms(report))
            schema_ok += first_attempt_schema_ok(report)
            fallbacks += report.fallback_used
            think_total += thinking_chars(npc)
            reply = out.reply if out else pick_fallback_line(char)
            tool = out.tool_call.model_dump() if (out and out.tool_call) else None

            judge_sys = item["judge"]
            if item["key"] == "3_3턴망각":
                judge_sys = judge_sys.replace("{fact}", _FORGET_FACTS[i % len(_FORGET_FACTS)])
            material = f"[질문] {utterance}\n[NPC의 답] {reply}\n[도구 호출] {tool or '없음'}"
            votes = [rc.judge_pass(judge_llm, judge_sys, material)[0] for _ in range(JUDGE_VOTES)]
            valid = [v for v in votes if v is not None]
            ok = sum(valid) > len(valid) / 2 if valid else False
            if len(valid) == JUDGE_VOTES:
                agree_total += 1
                agree_hits += len(set(valid)) == 1
            passed += ok
            transcripts.append({"item": item["key"], "i": i, "utterance": utterance,
                                "reply": reply, "tool": tool, "votes": votes,
                                "fallback": report.fallback_used, "ms": lat_ms[-1]})
            if verbose:
                print(f"    [{item['key']}] {'PASS' if ok else 'FAIL'} votes={votes} | "
                      f"{utterance} → {reply[:60]}", flush=True)
        rates[item["key"]] = passed / n if n else 0.0
    cell["item_rates"] = rates
    cell["item_scores"] = [round(rates[k], 4) for k in ITEM_KEYS]
    cell["items_passed"] = sum(1 for r in rates.values() if r >= ITEM_THRESHOLD)
    cell["judge_agreement"] = round(agree_hits / agree_total, 4) if agree_total else None
    cell["transcripts"] = transcripts

    # ── 누설 — 프로브 5 × leak_n · 하네스 ON ─────────────────────────
    chars_by_code = {c.code: c for c in bundle.characters}
    leak_total = leaks = caught = 0
    for code, probe in PROBES:
        pchar = chars_by_code[code]
        bans = applicable_ban_words(bundle, pchar.code, 1)
        checks = [forbidden_word_check(bans, fields=["reply"])]
        for _ in range(leak_n):
            messages = build_agent_messages(
                bundle, pchar, suspicion=40, trust=40, opposite=False,
                rules_text="", memory=[], user_text=probe, loop_n=1, age7_on=age7_on)
            out, report = run_with_harness(npc, messages, AgentOutput, role="agent",
                                           fact_checks=checks, harness_on=True)
            calls += 1
            lat_ms.append(call_elapsed_ms(report))
            schema_ok += first_attempt_schema_ok(report)
            fallbacks += report.fallback_used
            think_total += thinking_chars(npc)
            reply = out.reply if out else pick_fallback_line(pchar)
            leaked = any(w in reply for w in bans)
            leak_total += 1
            leaks += leaked
            caught += sum(1 for v in report.violations if v.startswith("forbidden_word"))
    cell["leak"] = {"total": leak_total, "leaks": leaks,
                    "rate": leaks / leak_total if leak_total else 0.0,
                    "harness_catches": caught}

    # ── 집계 ─────────────────────────────────────────────────────────
    lat_sorted = sorted(lat_ms)
    cell["calls"] = calls
    cell["schema_validity"] = round(schema_ok / calls, 4) if calls else None
    cell["fallback_rate"] = round(fallbacks / calls, 4) if calls else None
    cell["latency_p50_ms"] = lat_sorted[len(lat_sorted) // 2] if lat_sorted else None
    cell["latency_p95_ms"] = lat_sorted[min(len(lat_sorted) - 1, int(len(lat_sorted) * 0.95))] if lat_sorted else None
    cell["thinking_chars_total"] = think_total  # thinking 모델은 0이어야 한다 (§2.1 검증)
    ps = ps_snapshot(base_url)
    cell["peak_memory_gb"] = next((m["size_vram_gib"] for m in ps if m["model"] == model), None)

    # collapse 분류 (§3.1 · §6.1) — leak > schema > toddler > adult > none
    if cell["leak"]["rate"] > 0:
        cell["collapse"] = "leak"
    elif cell["schema_validity"] is not None and cell["schema_validity"] < 0.98:
        cell["collapse"] = "schema"
    elif rates.get("1_사실대로", 0.0) < ITEM_THRESHOLD:
        cell["collapse"] = "toddler"
    elif sum(1 for k in ("2_왜=몰라", "4_유도수용", "5_문자그대로")
             if rates.get(k, 0.0) < ITEM_THRESHOLD) >= 2:
        cell["collapse"] = "adult"
    else:
        cell["collapse"] = "none"
    return cell


def non_inferior(cell: dict, anchor: dict) -> bool | None:
    """§4 — 항목 단위(항목 3 제외) + 누설 0 + p95 ≤ Anchor. Anchor 셀 없으면 None."""
    if not anchor or "item_rates" not in anchor or "item_rates" not in cell:
        return None
    for k in VERDICT_ITEMS:
        if anchor["item_rates"].get(k, 0.0) >= ITEM_THRESHOLD \
                and cell["item_rates"].get(k, 0.0) < ITEM_THRESHOLD:
            return False
    if cell["leak"]["rate"] > 0:
        return False
    if cell["latency_p95_ms"] is None or anchor["latency_p95_ms"] is None:
        return None
    return cell["latency_p95_ms"] <= anchor["latency_p95_ms"]


def main() -> None:
    parser = argparse.ArgumentParser(description="E6 — NPC Slot Descent (부록 E6 §6)")
    parser.add_argument("--models", default=DEFAULT_MODELS)
    parser.add_argument("--policy", choices=["on", "off", "both"], default="on",
                        help="AGE7 정책 (판정은 on끼리 — §4. 기본 on)")
    parser.add_argument("--n", type=int, default=5, help="항목당 반복 (D4: ≥5)")
    parser.add_argument("--leak-n", type=int, default=2, help="누설 프로브당 반복 (기본 2)")
    parser.add_argument("--tier", choices=["screening", "formal"], default="formal")
    parser.add_argument("--runtime", default="ollama-cuda")
    parser.add_argument("--host", default="rtx5060ti-16g")
    parser.add_argument("--judge-model", default=rc.DEFAULT_JUDGE_MODEL)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--base-url", dest="ollama_url", default=None)
    parser.add_argument("--out", default=rc.DEFAULT_OUT)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    base_url = args.ollama_url or rc.ollama_base_url()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    rc.check_ollama(base_url, models + [args.judge_model])
    judge_llm = rc.make_llm(args.judge_model, base_url)

    bundle = build_scenario().bundle()
    char = next(c for c in bundle.characters if c.code == "jun")
    policies = {"on": [True], "off": [False], "both": [True, False]}[args.policy]

    out_dir = rc.PROJECT_ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    cells = []
    anchor_cell: dict = {}
    for model in models:
        quant, caps = model_info(base_url, model)
        for age7_on in policies:
            # 격리: 후보·judge 외 언로드
            for m in ps_snapshot(base_url):
                if m["model"] not in (model, args.judge_model):
                    unload_model(base_url, m["model"])
            label = "on" if age7_on else "off"
            print(f"\n### E6 · {model} ({quant}) · policy={label} · n={args.n} "
                  f"· judge={args.judge_model}×{JUDGE_VOTES}\n", flush=True)
            t0 = time.monotonic()
            cell = run_cell(model, caps, quant, base_url, judge_llm, bundle, char,
                            age7_on=age7_on, n=args.n, leak_n=args.leak_n,
                            timeout=args.timeout, verbose=args.verbose)
            cell["secs"] = round(time.monotonic() - t0, 1)
            if model == ANCHOR and age7_on:
                anchor_cell = cell
            cells.append(cell)
            if "item_rates" in cell:
                rc.print_table(["항목", "통과율"], [[k, cell["item_rates"][k]] for k in ITEM_KEYS])
                print(f"  items_passed {cell['items_passed']}/5 · leak {cell['leak']['rate']:.0%} "
                      f"· schema {cell['schema_validity']} · judge 일치 {cell['judge_agreement']} "
                      f"· p95 {cell['latency_p95_ms']}ms · VRAM {cell['peak_memory_gb']}GiB "
                      f"· collapse={cell['collapse']} · {cell['secs']}s", flush=True)
            else:
                print(f"  Stage 0 탈락: {cell['stage0']}", flush=True)

    # 비열등 판정 (on끼리, Anchor 존재 시)
    for cell in cells:
        if cell["policy"] == "on" and cell["model"] != ANCHOR:
            cell["non_inferior_to_anchor"] = non_inferior(cell, anchor_cell)

    raw_path = out_dir / f"e6-descent-{args.tier}-{stamp}.json"
    raw_path.write_text(json.dumps({
        "experiment": "E6", "tier": args.tier, "anchor": ANCHOR, "n": args.n,
        "leak_n": args.leak_n, "judge": args.judge_model, "judge_votes": JUDGE_VOTES,
        "item_threshold": ITEM_THRESHOLD, "verdict_items": VERDICT_ITEMS,
        "started_at": stamp, "host": args.host, "runtime": args.runtime,
        "cells": cells,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.tier != "formal":
        # §5 — metrics.yml 적립은 Formal 층뿐. Screening은 원문 JSON만 남긴다.
        print(f"\n원문 → {raw_path}\n(screening — metrics 적립 없음)")
        return

    for cell in cells:
        if "item_rates" not in cell:
            rc.append_metric(args.out, "model_descent", cell["model"],
                             policy=cell["policy"], tier=args.tier, runtime=args.runtime,
                             host=args.host, quant=cell["quant"], n=args.n,
                             stage0_pass=False, collapse=cell["collapse"])
            continue
        rc.append_metric(
            args.out, "model_descent", cell["model"],
            policy=cell["policy"], tier=args.tier, runtime=args.runtime, host=args.host,
            quant=cell["quant"], n=args.n,
            items_passed=cell["items_passed"], item_scores=cell["item_scores"],
            leak_rate_on=cell["leak"]["rate"], harness_catches=cell["leak"]["harness_catches"],
            schema_validity=cell["schema_validity"], fallback_rate=cell["fallback_rate"],
            latency_p50_ms=(None if args.tier == "screening" else cell["latency_p50_ms"]),
            latency_p95_ms=(None if args.tier == "screening" else cell["latency_p95_ms"]),
            peak_memory_gb=(None if args.tier == "screening" else cell["peak_memory_gb"]),
            judge_agreement=cell["judge_agreement"],
            thinking_chars_total=cell["thinking_chars_total"],
            non_inferior_to_anchor=cell.get("non_inferior_to_anchor"),
            collapse=cell["collapse"],
        )
    print(f"\n원문 → {raw_path}\nmetrics → {rc.resolve_out(args.out)}")


if __name__ == "__main__":
    main()
