"""run_selfplay.py — LLM 에이전트가 HTTP로 실제 게임을 플레이한다 (작업지시서 §P6).

페르소나 3종: 성실(파편 기반 서술) / 산탄총(아무 주장 8개) / 침묵(발화 0, 빈 서술).
플레이어 행동(발화 1~3회, 밤 서술)은 gemma3:12b가 생성한다.
백엔드 서버가 8500에 떠 있어야 한다.

    .venv/bin/python scripts/run_selfplay.py --n 1 --loops 1 --persona 성실
"""

import argparse
import random
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
import runner_common as rc  # noqa: E402
from pydantic import BaseModel, ConfigDict, Field  # noqa: E402

from apps.engine.app.use_cases.harness import run_with_harness  # noqa: E402

PERSONAS = ["성실", "산탄총", "침묵"]


class UtteranceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target: str
    text: str


class PlayerUtterances(BaseModel):
    model_config = ConfigDict(extra="forbid")
    utterances: list[UtteranceSpec] = Field(min_length=1, max_length=3)


class NightNarration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    free_text: str


class ShotgunClaims(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claims: list[str] = Field(min_length=8, max_length=8)


UTTER_SYSTEM = {
    "성실": (
        "너는 텍스트 게임의 플레이어다. 세계가 이상하다 — 오늘이 지나면 멸망한다. "
        "왜인지 알아내야 한다.\n[오늘 아침]\n{morning}\n[네 노트]\n{notes}\n"
        "[말 걸 수 있는 인물(code: 이름)]\n{npcs}\n"
        "노트와 아침 장면의 이상한 점을 캐묻는 짧은 발화를 {k}개 만든다. "
        "target은 반드시 code로 쓴다.\n출력: JSON만."
    ),
    "산탄총": (
        "너는 텍스트 게임의 플레이어다. 전략 없이 아무 말이나 던진다.\n"
        "[오늘 아침]\n{morning}\n[말 걸 수 있는 인물(code: 이름)]\n{npcs}\n"
        "인물들에게 던질 짧은 발화 {k}개. 뜬금없어도 된다. target은 반드시 code로 쓴다.\n"
        "출력: JSON만."
    ),
}

NIGHT_SYSTEM_DILIGENT = (
    "너는 텍스트 게임의 플레이어다. 오늘 무슨 상황이었는지 서술해 점수를 받는다.\n"
    "[네 노트(파편·확인된 것)]\n{notes}\n[오늘 오간 대화]\n{talks}\n"
    "노트의 파편을 근거로 오늘 상황을 3~5문장으로 서술한다. 노트와 대화에 있는 것만 쓴다.\n"
    "출력: JSON만."
)

NIGHT_SYSTEM_SHOTGUN = (
    "너는 텍스트 게임의 플레이어다. 세계의 진실을 마구 찍어서 점수를 노린다.\n"
    "[오늘 아침]\n{morning}\n"
    "이 세계에 대한 과감한 주장 8개를 한 문장씩 만든다. 근거는 필요 없다. 서로 달라야 한다.\n"
    "출력: JSON만."
)


def gen(llm, output_model, system: str):
    out, _ = run_with_harness(
        llm, [rc.sys_msg(system), rc.usr_msg("만들어라.")], output_model, role="player"
    )
    return out


def play_game(client: httpx.Client, player_llm, persona: str, *, max_loops: int,
              rng: random.Random, verbose: bool) -> dict:
    t0 = time.monotonic()
    res = client.post("/sessions", json={})
    res.raise_for_status()
    attempt_id = res.json()["attempt_id"]

    scores: list[float] = []
    reach50: int | None = None
    finished = None
    for _ in range(max_loops):
        loop = client.post(f"/sessions/{attempt_id}/loops").json()
        loop_id, loop_n = loop["loop_id"], loop["loop_n"]
        morning = loop.get("morning_text", "")
        npcs = client.get(f"/loops/{loop_id}/npcs").json()["npcs"]
        npc_codes = {n["code"] for n in npcs}
        npc_list = "\n".join(f"{n['code']}: {n['name']}" for n in npcs)
        notes = client.get(f"/loops/{loop_id}/notes").json()["notes"]
        notes_text = "\n".join(f"- {n['text']}" for n in notes) or "(없음)"
        talks: list[str] = []

        # 낮 — 발화
        if persona != "침묵":
            k = rng.randint(1, 3)
            plan = gen(player_llm, PlayerUtterances, UTTER_SYSTEM[persona].format(
                morning=morning, notes=notes_text, npcs=npc_list, k=k))
            for u in (plan.utterances[:k] if plan else []):
                target = u.target if u.target in npc_codes else rng.choice(sorted(npc_codes))
                r = client.post(f"/loops/{loop_id}/utterances",
                                json={"target": target, "text": u.text})
                if r.status_code == 200:
                    reply = r.json()["reply"]
                    talks.append(f"나→{target}: {u.text} / {r.json()['npc']['name']}: {reply}")
                    if verbose:
                        print(f"    [{loop_n}회차] 나→{target}: {u.text} → {reply}")

        # 비트 진행 (원숭이손 제안은 50% 확률 수락)
        for _ in range(10):
            b = client.post(f"/loops/{loop_id}/beats/next").json()
            offer = b.get("paw_offer")
            if offer:
                accept = rng.random() < 0.5
                client.post(f"/loops/{loop_id}/paw/respond",
                            json={"offer_id": offer["offer_id"], "accept": accept})
                if verbose:
                    print(f"    [{loop_n}회차] 원숭이손 '{offer['rule_label']}' → "
                          f"{'수락' if accept else '거부'}")
            if b.get("day_done"):
                break

        # 밤 — 서술
        notes = client.get(f"/loops/{loop_id}/notes").json()["notes"]
        notes_text = "\n".join(f"- {n['text']}" for n in notes) or "(없음)"
        if persona == "성실":
            nn = gen(player_llm, NightNarration, NIGHT_SYSTEM_DILIGENT.format(
                notes=notes_text, talks="\n".join(talks) or "(없음)"))
            free_text = nn.free_text if nn else notes_text
            tapped = [n["id"] for n in notes][:4]
        elif persona == "산탄총":
            sc = gen(player_llm, ShotgunClaims, NIGHT_SYSTEM_SHOTGUN.format(morning=morning))
            free_text = " ".join(sc.claims) if sc else "전부 이상하다."
            tapped = []
        else:  # 침묵
            free_text, tapped = "", []

        draft = client.post(f"/loops/{loop_id}/night/draft",
                            json={"tapped_note_ids": tapped, "free_text": free_text}).json()
        night_id = draft["night_id"]
        sub = client.post(f"/nights/{night_id}/submit").json()
        total = float(sub.get("total") or 0)
        scores.append(total)
        if sub.get("passed") and reach50 is None:
            reach50 = loop_n
        if verbose:
            print(f"    [{loop_n}회차] 점수 {total} passed={sub.get('passed')} "
                  f"is_final={sub.get('is_final')}")
        if sub.get("is_final"):
            finished = sub.get("closed_by")
            break
        if sub.get("intervention_available"):
            client.post(f"/nights/{night_id}/questions", json={"text": "오늘 무슨 일이 있었나?"})
            client.get(f"/nights/{night_id}/options")
            r = client.post(f"/nights/{night_id}/rule", json={"choice": "1"})
            if r.status_code != 200 or not r.json().get("ok"):
                client.post(f"/nights/{night_id}/rule",
                            json={"choice": "custom", "custom_text": "아무도 배급을 남기지 않는다"})
        else:
            break

    return {
        "attempt_id": attempt_id,
        "scores": scores,
        "reach50_loop": reach50,
        "closed_by": finished,
        "secs": round(time.monotonic() - t0, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="자기대전 — LLM 플레이어가 HTTP로 게임을 플레이")
    parser.add_argument("--model", default=rc.DEFAULT_JUDGE_MODEL,
                        help=f"플레이어 모델 (기본 {rc.DEFAULT_JUDGE_MODEL})")
    parser.add_argument("--n", type=int, default=1, help="판 수 (기본 1)")
    parser.add_argument("--out", default=rc.DEFAULT_OUT,
                        help="metrics 파일 (프로젝트 루트 기준, 기본 docs/metrics.yml)")
    parser.add_argument("--base-url", dest="server_url", default="http://localhost:8500",
                        help="백엔드 서버 (기본 http://localhost:8500)")
    parser.add_argument("--ollama-url", dest="ollama_url", default=None,
                        help="ollama base url (기본 .env OLLAMA_BASE_URL)")
    parser.add_argument("--persona", choices=PERSONAS + ["all"], default="성실")
    parser.add_argument("--loops", type=int, default=5, help="판당 최대 회차 (기본 5)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    client = httpx.Client(base_url=args.server_url.rstrip("/"), timeout=300.0)
    try:
        health = client.get("/health")
        health.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            f"[에러] 백엔드 서버가 응답하지 않는다: {args.server_url} ({exc})\n"
            "       backend에서 서버를 먼저 띄워라 (포트 8500)."
        ) from exc

    ollama_url = args.ollama_url or rc.ollama_base_url()
    rc.check_ollama(ollama_url, [args.model])
    player_llm = rc.make_llm(args.model, ollama_url)
    rng = random.Random(args.seed)

    personas = PERSONAS if args.persona == "all" else [args.persona]
    all_rows = []
    for persona in personas:
        print(f"\n### 자기대전 · persona={persona} · {args.n}판 × ≤{args.loops}회차 "
              f"· player={args.model}\n")
        games = []
        for g in range(args.n):
            print(f"  판 {g + 1} 시작…")
            result = play_game(client, player_llm, persona,
                               max_loops=args.loops, rng=rng, verbose=args.verbose)
            games.append(result)
            with rc.SELFPLAY_ATTEMPTS_LOG.open("a", encoding="utf-8") as f:
                f.write(f"{result['attempt_id']}\t{persona}\t{date.today().isoformat()}\n")
            print(f"  판 {g + 1}: 점수 {result['scores']} · 50%도달 "
                  f"{result['reach50_loop'] or '-'}회차 · {result['secs']}s "
                  f"({result['closed_by'] or '미종결'})")

        rows = [[i + 1, g["scores"], g["reach50_loop"] or "-", g["closed_by"] or "-", g["secs"]]
                for i, g in enumerate(games)]
        print()
        rc.print_table(["판", "회차별 점수", "50% 도달", "종결", "소요(s)"], rows)
        all_rows.append((persona, games))

        path = rc.append_metric(
            args.out, "selfplay", args.model,
            persona=persona, games=args.n, max_loops=args.loops,
            scores=[g["scores"] for g in games],
            reach50_loops=[g["reach50_loop"] for g in games],
            avg_secs=sum(g["secs"] for g in games) / len(games) if games else 0,
            attempt_ids=[g["attempt_id"] for g in games],
        )
    print(f"\nmetrics → {path}\nattempt 로그 → {rc.SELFPLAY_ATTEMPTS_LOG}")


if __name__ == "__main__":
    main()
