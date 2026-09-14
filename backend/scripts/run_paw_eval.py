"""run_paw_eval.py — 원숭이손 수락/거부 후 다음 회차 점수 변화 (작업지시서 §P6).

run_selfplay가 남긴 attempt(scripts/.selfplay_attempts.log)를 inspector API
(GET /attempts/{id}/inspector?token=INSPECTOR_TOKEN)로 읽어,
monkey_paw_offer 이벤트(수락 여부, loop_n)와 answer_scored(loop_n, total)를 대조해
수락/거부 각각의 다음 회차 점수 변화(Δ)를 계산한다. 데이터 없으면 "데이터 없음" 후 정상 종료.

    .venv/bin/python scripts/run_paw_eval.py
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
import runner_common as rc  # noqa: E402


def collect_attempt_ids(args) -> list[str]:
    ids = list(args.attempt_id or [])
    log = Path(args.attempts_file)
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            parts = line.split("\t")
            if parts and parts[0].strip():
                ids.append(parts[0].strip())
    # 순서 유지 중복 제거
    return list(dict.fromkeys(ids))


def eval_attempt(client: httpx.Client, attempt_id: str, token: str) -> list[dict]:
    """수락/거부 이벤트별 (loop_n, accepted, delta) 목록. 접근 실패는 건너뛴다."""
    res = client.get(f"/attempts/{attempt_id}/inspector", params={"token": token})
    if res.status_code != 200:
        print(f"  [skip] {attempt_id}: HTTP {res.status_code}")
        return []
    events = res.json().get("events", [])
    scores = {e["loop_n"]: float(e["total"]) for e in events if e.get("type") == "answer_scored"}
    out = []
    for e in events:
        if e.get("type") != "monkey_paw_offer":
            continue
        ln = e["loop_n"]
        before, after = scores.get(ln), scores.get(ln + 1)
        out.append({
            "attempt_id": attempt_id,
            "loop_n": ln,
            "accepted": bool(e.get("accepted")),
            "delta": (after - before) if (before is not None and after is not None) else None,
        })
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="원숭이손 수락/거부 후 점수 변화 (selfplay 로그 기반)")
    parser.add_argument("--model", default="-", help="기록용 모델 라벨 (계산에는 안 쓴다)")
    parser.add_argument("--n", type=int, default=0, help="(미사용 — 데이터는 selfplay 로그가 결정)")
    parser.add_argument("--out", default=rc.DEFAULT_OUT,
                        help="metrics 파일 (프로젝트 루트 기준, 기본 docs/metrics.yml)")
    parser.add_argument("--base-url", dest="server_url", default="http://localhost:8500",
                        help="백엔드 서버 (기본 http://localhost:8500)")
    parser.add_argument("--attempts-file", default=str(rc.SELFPLAY_ATTEMPTS_LOG),
                        help="selfplay가 남긴 attempt 로그")
    parser.add_argument("--attempt-id", action="append", help="attempt id 직접 지정 (반복 가능)")
    args = parser.parse_args()

    token = rc.load_env().get("INSPECTOR_TOKEN", "")
    if not token:
        raise SystemExit("[에러] .env에 INSPECTOR_TOKEN이 없다.")

    ids = collect_attempt_ids(args)
    if not ids:
        print("데이터 없음 — run_selfplay.py를 먼저 돌려 attempt를 만들어라.")
        return

    client = httpx.Client(base_url=args.server_url.rstrip("/"), timeout=30.0)
    try:
        client.get("/health").raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            f"[에러] 백엔드 서버가 응답하지 않는다: {args.server_url} ({exc})"
        ) from exc

    records = []
    for aid in ids:
        records.extend(eval_attempt(client, aid, token))
    if not records:
        print("데이터 없음 — 원숭이손 이벤트가 기록된 attempt가 없다.")
        return

    def stats(accepted: bool):
        deltas = [r["delta"] for r in records if r["accepted"] == accepted and r["delta"] is not None]
        n_all = sum(1 for r in records if r["accepted"] == accepted)
        avg = sum(deltas) / len(deltas) if deltas else None
        return n_all, len(deltas), avg

    acc_n, acc_m, acc_avg = stats(True)
    rej_n, rej_m, rej_avg = stats(False)

    print(f"\n### 원숭이손 평가 · attempt {len(ids)}개 · 이벤트 {len(records)}건\n")
    rc.print_table(
        ["응답", "제안 수", "Δ 계산 가능", "다음 회차 평균 Δ"],
        [
            ["수락", acc_n, acc_m, f"{acc_avg:+.1f}" if acc_avg is not None else "-"],
            ["거부", rej_n, rej_m, f"{rej_avg:+.1f}" if rej_avg is not None else "-"],
        ],
    )

    path = rc.append_metric(
        args.out, "paw_eval", args.model,
        attempts=len(ids), offers=len(records),
        accepted=acc_n, rejected=rej_n,
        avg_delta_accept=acc_avg, avg_delta_reject=rej_avg,
    )
    print(f"\nmetrics → {path}")


if __name__ == "__main__":
    main()
