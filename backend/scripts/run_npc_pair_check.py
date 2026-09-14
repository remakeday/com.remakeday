"""E6 후속 — NPC 후보 + Core `gemma4:12b` 동시 상주 체크 (stage_concurrency 패턴).

NPC 선상주 → Core 로드 → NPC/Core 교대 3라운드, 매 콜 뒤 /api/ps + nvidia-smi.
축출·부분 오프로드(size_vram < size)를 센다. NPC가 thinking 모델이면 think=False.

    .venv/bin/python scripts/run_npc_pair_check.py --npc qwen3.5:4b --core gemma4:12b
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
from run_core_selection import (  # noqa: E402
    ThinkingOllamaLLM,
    gpu_used_mib,
    ps_snapshot,
    unload_model,
)


def has_thinking(base_url, model):
    res = httpx.post(f"{base_url.rstrip('/')}/api/show", json={"model": model}, timeout=10.0)
    return "thinking" in res.json().get("capabilities", [])


def make(base_url, model, timeout):
    if has_thinking(base_url, model):
        return ThinkingOllamaLLM(base_url=base_url, model=model, think=False, timeout=timeout)
    llm = rc.make_llm(model, base_url)
    llm._timeout = timeout  # noqa: SLF001
    return llm


def chat_ms(llm, sys_text, usr_text):
    t0 = time.monotonic()
    llm.complete([rc.sys_msg(sys_text), rc.usr_msg(usr_text)],
                 {"type": "object", "properties": {"reply": {"type": "string"}},
                  "required": ["reply"]})
    return int((time.monotonic() - t0) * 1000)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--npc", required=True)
    p.add_argument("--core", default="gemma4:12b")
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--base-url", dest="ollama_url", default=None)
    p.add_argument("--out-dir", default="docs/review-verification/2026-09-14-npc-descent")
    args = p.parse_args()

    base_url = args.ollama_url or rc.ollama_base_url()
    rc.check_ollama(base_url, [args.npc, args.core])
    for m in ps_snapshot(base_url):
        if m["model"] not in (args.npc, args.core):
            unload_model(base_url, m["model"])

    npc = make(base_url, args.npc, args.timeout)
    core = make(base_url, args.core, args.timeout)

    snaps, evictions, offloads = [], [], []
    peak_pair = 0.0
    peak_gpu = 0

    def snap(tag):
        nonlocal peak_pair, peak_gpu
        ps = ps_snapshot(base_url)
        used, total = gpu_used_mib()
        pair = sum(m["size_vram_gib"] for m in ps if m["model"] in (args.npc, args.core))
        peak_pair = max(peak_pair, pair)
        peak_gpu = max(peak_gpu, used or 0)
        resident = {m["model"] for m in ps}
        for name in (args.npc, args.core):
            if name not in resident:
                evictions.append({"tag": tag, "missing": name})
        for m in ps:
            if m["model"] in (args.npc, args.core) and m["size_vram_gib"] < m["size_gib"] - 0.05:
                offloads.append({"tag": tag, "model": m["model"]})
        snaps.append({"tag": tag, "ps": ps, "gpu_used_mib": used, "gpu_total_mib": total})
        print(f"  [{tag}] pair {pair:.2f} GiB · GPU {used}/{total} MiB · resident={sorted(resident)}",
              flush=True)

    print(f"\n### pair check · NPC {args.npc} (think off if capable) + Core {args.core}\n", flush=True)
    ms = chat_ms(npc, "너는 격리 구역의 준이다. 한 문장으로만 답한다.", "트럭 소리 들었어?")
    snap(f"npc_warm({ms}ms)")
    ms = chat_ms(core, "당신은 게임의 코어다. JSON으로만 답한다.", "오늘 아침 장면을 한 문장으로.")
    snap(f"core_warm({ms}ms)")
    for r in range(args.rounds):
        ms = chat_ms(npc, "너는 격리 구역의 준이다. 한 문장으로만 답한다.", "배급 몇 시야?")
        snap(f"r{r+1}_npc({ms}ms)")
        ms = chat_ms(core, "당신은 게임의 코어다. JSON으로만 답한다.", "밤 채점 한 줄 요약.")
        snap(f"r{r+1}_core({ms}ms)")

    result = {
        "npc": args.npc, "core": args.core, "rounds": args.rounds,
        "pair_peak_vram_gib": round(peak_pair, 2), "gpu_peak_used_mib": peak_gpu,
        "gpu_total_mib": snaps[-1]["gpu_total_mib"],
        "evictions": evictions, "partial_offloads": offloads, "snapshots": snaps,
        "npc_thinking_chars_last": getattr(npc, "last", {}).get("thinking_chars"),
    }
    out_dir = rc.PROJECT_ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"e6-pair-{args.npc.replace(':', '_')}-{args.core.replace(':', '_')}-{stamp}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\npair peak {result['pair_peak_vram_gib']} GiB · GPU peak {peak_gpu} MiB "
          f"· 교대 축출 {len(evictions)} · 오프로드 {len(offloads)}\n원문 → {path}")


if __name__ == "__main__":
    main()
