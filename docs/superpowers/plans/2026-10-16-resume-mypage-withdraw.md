# 이어하기·마이페이지·회원탈퇴 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 진행 중인 판을 다시 열거나(이어하기) 포기하고 새로 시작할 수 있게 하고, 이어하기·회원탈퇴만 담은 마이페이지와 회원탈퇴 API를 만든다.

**Architecture:** 백엔드는 새 유스케이스 `ResumeInteractor` 하나가 "진행 중인 판"을 찾고 최신 회차 상태로 단계를 고른다. 화면 데이터는 기존 인터랙터에 붙인 읽기 메서드(`LoopInteractor.resume_shell`·`resume_day`, `NightInteractor.resume_view`)가 만들고, 단계→조립기는 표(dict)로 고른다. 회원탈퇴는 `UserRepository.delete_with_data`가 자식 테이블부터 한 트랜잭션에서 지운다. 프론트는 `/play` 진입 때 진행 중인 판을 먼저 묻고, 선택 화면·`?resume=1`·단계별 state 채우기를 더한다. `/mypage`는 새 라우트다.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, PostgreSQL(테스트 DB `pigfarm_test`), pytest, Next.js App Router(React 19), Tailwind, Playwright(헤드리스 Chrome)

**Spec:** `docs/superpowers/specs/2026-10-16-resume-mypage-withdraw-design.md`

## Global Constraints

- **검토 등급** — Task 4(회원탈퇴 API)·Task 7(마이페이지·탈퇴 화면) **A**, 나머지 **B**. A task는 구현+검토(sonnet), 최종 전체 리뷰는 A가 섞였으므로 opus 1회 + 수정 1회 + 범위 재검토. B task 검토는 sonnet/haiku, 계약 타입만 바꾸는 Task 5는 개별 검토 생략.
- **담당** — 백엔드·문서(Task 1~4)는 Claude 서브에이전트. `frontend/`(Task 5~8)는 Codex CLI `codex exec -m gpt-6-astra -s workspace-write`. Codex 결과의 diff·`npx tsc --noEmit`·헤드리스 실행은 컨트롤러가 한다.
- **Codex 샌드박스는 Chrome을 띄우지 못한다.** 헤드리스는 컨트롤러가 `NODE_PATH=/home/kimchungsik/projects/cloud.localhostdaegu/frontend/node_modules`, `executablePath: '/usr/bin/google-chrome'`, `headless: true`로 돌린다.
- **브라우저 규칙(CLAUDE.md)** — 보이는 브라우저를 열지 않는다. 서버 기동 명령에 `open`·`xdg-open`·AppleScript를 붙이지 않는다. 준비 확인은 `curl`로만. 헤드리스 스크립트는 한 번에 하나씩, 앞 프로세스가 끝난 뒤 다음. `/play`를 새로고침해서 느린 응답을 복구하지 않는다. 이 작업이 띄운 프로세스만 끈다.
- **전체 pytest는 테스트 DB를 공유한다.** 서브에이전트는 자기 task의 테스트 파일과 지정한 기존 파일만 돌리고, 전체는 컨트롤러가 Task 9에서 한 번.
- **마이그레이션 없음.** `attempts.status`는 `String(16)`이라 `abandoned`를 그대로 넣는다.
- **FK에 `ON DELETE CASCADE`가 없다.** 삭제는 자식부터: `nights` → `npc_states` → `loops` → `notes`·`rules` → `survey_votes` → `events` → `attempts` → `users`.
- **경로 고정** — `GET /api/v1/me/attempts/active`, `POST /api/v1/me/attempts/active/abandon`(204), `DELETE /api/v1/auth/me`(204 + `rd_session` 쿠키 삭제). 기존 게임 라우트(`/sessions` 등)는 접두 없이 그대로.
- **화면 문구 고정** — "이어하기", "다시 시작하기", "오늘 남은 판 {today_remaining}/{daily_limit} · 다시 시작하면 1회가 차감됩니다", "오늘은 더 시작할 수 없습니다", "마이페이지", "회원탈퇴", "모든 플레이 기록이 즉시 삭제되며 되돌릴 수 없습니다", "탈퇴", "취소". 브라우저 `confirm()` 금지.
- **커밋 정책(사용자 결정 2026-10-16).** 작업 트리가 더럽다. `git add -A`·`git add .`·`git commit -a`·`git add -p`·`git apply --cached` 금지. **이 작업이 새로 만든 파일과, 작업 시작 전 미커밋 변경이 없던 파일만 커밋한다.** 미커밋 변경이 섞인 파일은 수정만 하고 커밋하지 않는다. 각 task 시작 전에 컨트롤러가 그 task 파일들의 `git status --short <파일>`을 장부에 적어 두고, 그때 이미 `M`이던 파일은 커밋 명령에서 뺀다. 지금(2026-10-16) 알려진 해당 파일: `frontend/app/page.tsx`, `frontend/tests/` 6개(`connected-investigation`·`day-screen-vn-shots`·`day-screen-vn`·`five-loop-flow`·`scene-illustrations`·`voice-transitions`), `docs/jekyll.md`. `frontend/app/privacy/page.tsx`도 미커밋 수정이 있지만 이 계획은 건드리지 않는다. 그 수정은 지우지 말고 보존한다. 각 task 끝에 **"커밋하지 않고 남긴 파일"** 목록을 적고, 최종 보고에 모아서 올린다.
- **배포·서버 재기동 없음.** 프로젝트는 2026-10-12 종료됐고 서비스 복구 금지다. 헤드리스용 프론트 dev 서버(3500)만 Task 9에서 잠시 띄우고 끈다.
- `<스크래치>` = 컨트롤러 세션의 스크래치 디렉터리(시스템 프롬프트가 알려 주는 절대 경로). Codex 지시문 파일만 거기에 둔다.
- 백엔드 명령은 전부 `cd /home/kimchungsik/projects/com.remakeday/backend && .venv/bin/python -m pytest ...` 형식. 테스트 DB 컨테이너는 `pigfarm-db`(2026-10-16 확인 시 기동 중).
- CLAUDE.md §5: 상태·종류로 갈라지는 분기는 표(dict)·전략으로 둔다. 이 계획의 단계 매핑(`PHASE_BY_STATE`, 단계→조립기, 프론트 `RESUME_SCREEN`)이 그 예다.

## Review Focus

1. **낮 3비트에서 설명 규칙이 이미 실행된 뒤 새로고침** — 재실행은 기록을 더하지 않지만 그 규칙의 설명·부작용 줄을 다시 만들지 않는다. 이어하기 화면에도 그 줄이 그대로 보여야 한다. → Task 2 `test_resume_day_keeps_rule_explanation_lines`
2. **"다시 시작하기"를 두 번 빠르게 누름** — 포기는 한 번만, 새 판도 하나만 생겨야 한다(두 번째 포기가 방금 만든 새 판을 포기하면 안 된다). → Task 8 `restartOnceOnDoubleClick`
3. **조회 API가 없는 구 백엔드(404) 또는 일시 오류** — `/play`가 막히지 않고 예전처럼 새 판을 만든다. 허들(401·403·503·429)만 GuardScreen. → Task 8 `fallsBackWhenActiveLookupFails`
4. **응답 저장(2026-09-18) 전에 제출한 밤에서 멈춘 판** — 저장된 제출 응답이 없어도 개입 화면이 빈 화면이 되지 않는다. → Task 2 `test_submitted_night_without_stored_response_still_resumes`
5. **탈퇴하는 사용자와 같은 events 테이블을 쓰는 다른 사용자** — 다른 사용자의 guard 이벤트(user_sub)·평가·판 이벤트는 한 줄도 줄지 않는다. 중간에 실패하면 아무것도 지워지지 않는다. → Task 4 `test_delete_with_data_removes_every_row_of_one_user_only`·`test_delete_with_data_is_all_or_nothing`·`test_withdraw_deletes_only_that_users_rows`

추가로 사용자 결정(2026-10-16)으로 묶은 두 경우: **최신 판을 포기·완료한 뒤 오래된 active 판이 남아 있음** → `attempt: null`(Task 2 `test_latest_active_is_the_newest_attempt_only_while_it_is_active`, Task 3 `test_abandoning_latest_does_not_resurface_older_active`). **탈퇴 뒤 남은 세션 쿠키로 새 판 요청** → 401이고 users 행이 다시 생기지 않음(Task 4 `test_withdrawn_session_cookie_cannot_recreate_user`).

---

### Task 1: 장면 재실행 멱등성 전제 확인 (B)

스펙 §4 첫 항목. 이 task가 통과해야 Task 2의 낮 복원이 성립한다.

**Files:**
- Create: `backend/tests/pure/test_scene_rerun_idempotency.py`

**Interfaces:**
- Consumes: `execute_scene(event_log, loop, bundle, rules, on_action=None)`(`apps/engine/app/use_cases/scene_execution.py`), 테스트 도우미 `Events`·`loop_at`(`tests/pure/test_review_failure_boundaries.py`), `wish_rules(key)`(`tests/pure/test_paw_scene_execution.py`)
- Produces: 없음(전제 확인). Task 2는 "재실행은 statement·paw_effect 줄만 빠뜨린다"를 근거로 그 줄을 되살린다.

- [ ] **Step 1: 테스트를 쓴다**

`backend/tests/pure/test_scene_rerun_idempotency.py`:

```python
"""이어하기 전제 — 같은 비트에 execute_scene을 다시 불러도 기록·관찰·세계 효과가 늘지 않는다 (설계 2026-10-16 §2.2·§4).

이 전제가 깨지면 이어하기는 낮 장면을 execute_scene으로 다시 그릴 수 없다 — 쓰기 없는 읽기 전용 경로가 따로 필요하다.
"""

import pytest

from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION, SOURCE_ACTION, execute_scene
from apps.engine.domain.entities.rule_rules import Rule
from apps.scenarios.scenario_a.adapter import build
from tests.pure.test_paw_scene_execution import wish_rules
from tests.pure.test_review_failure_boundaries import Events, loop_at

BUNDLE = build().bundle()
ACTORS = sorted({a.actor for a in BUNDLE.scene_actions})


def _rule_sets() -> dict[str, list[Rule]]:
    """규칙 없음 · 원숭이손 소원 네 가지 · 모든 인물 설명 · 모든 인물 출처 — 규칙 실행·부작용 문장 경로를 전부 지난다."""
    sets = {"규칙 없음": []}
    sets.update({f"소원 {w.key}": wish_rules(w.key)[1] for w in BUNDLE.paw_wishes})
    sets["모두 설명"] = [Rule(f"R{i}", "user_choice", a, None, "enforce", EXPLAIN_ACTION, 1)
                       for i, a in enumerate(ACTORS, 1)]
    sets["모두 출처"] = [Rule(f"R{i}", "user_choice", a, None, "enforce", SOURCE_ACTION, 1)
                       for i, a in enumerate(ACTORS, 1)]
    return sets


RULE_SETS = _rule_sets()


@pytest.mark.parametrize("damage", [0, 3])
@pytest.mark.parametrize("loop_n", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("name", list(RULE_SETS))
def test_rerunning_the_current_beat_records_nothing_new(name, loop_n, damage):
    events, loop = Events(), loop_at(1)
    loop.loop_n, loop.damage_level = loop_n, damage
    rules = RULE_SETS[name]
    for beat in range(1, 7):
        loop.beat = beat
        effects = []
        execute_scene(events, loop, BUNDLE, rules, on_action=effects.append)
        rows, fired = len(events.rows), len(effects)
        execute_scene(events, loop, BUNDLE, rules, on_action=effects.append)  # 이어하기의 재실행
        assert len(events.rows) == rows, f"{beat}비트 재실행이 기록(관찰·규칙 실행)을 더했다"
        assert len(effects) == fired, f"{beat}비트 재실행이 세계 효과(on_action)를 다시 불렀다"


@pytest.mark.parametrize("key", [w.key for w in BUNDLE.paw_wishes])
def test_rerun_after_paw_accepted_mid_beat_records_nothing_new(key):
    """원숭이손은 2비트 장면 뒤에 받는다. 받은 즉시 재실행(_replay_wish_scene)한 뒤 이어하기가 또 그려도 새 기록이 없다."""
    events, loop = Events(), loop_at(2)
    loop.loop_n = 1
    rules = wish_rules(key)[1]
    execute_scene(events, loop, BUNDLE, [])      # 2비트 첫 장면 — 제안은 이 장면과 함께 뜬다
    execute_scene(events, loop, BUNDLE, rules)   # 수락 즉시 재실행과 같은 호출
    rows = len(events.rows)
    execute_scene(events, loop, BUNDLE, rules)   # 이어하기
    assert len(events.rows) == rows


def test_rerun_drops_only_rule_statement_and_paw_effect_lines():
    """이어하기가 되살리는 줄의 근거 — 재실행은 이미 실행한 규칙의 설명(statement)·부작용(paw_effect) 줄만 빠뜨린다."""
    dropped = set()
    for rules in RULE_SETS.values():
        events, loop = Events(), loop_at(1)
        loop.loop_n = 1
        for beat in range(1, 7):
            loop.beat = beat
            first = execute_scene(events, loop, BUNDLE, rules)
            again = execute_scene(events, loop, BUNDLE, rules)
            kept = {line.observation_id for line in again.lines}
            dropped |= {line.kind for line in first.lines if line.observation_id not in kept}
    assert dropped <= {"statement", "paw_effect"}
    assert dropped  # 이 시나리오에 설명·소원 규칙 줄이 실제로 있다 — 비어 있으면 위 단언이 아무것도 확인하지 않는다
```

- [ ] **Step 2: 실행한다**

Run: `cd /home/kimchungsik/projects/com.remakeday/backend && .venv/bin/python -m pytest tests/pure/test_scene_rerun_idempotency.py -q`
Expected: PASS (75 passed). 계획 작성 때(2026-10-16) 같은 조합을 스크래치 스크립트로 돌려 기록 증가 0건, 빠지는 줄은 `statement`·`paw_effect`뿐임을 확인했다.

**하나라도 FAIL이면 여기서 멈춘다.** 구현으로 고치지 말고, 실패한 매개변수(규칙 묶음·회차·피해 단계·비트)와 늘어난 이벤트 종류를 컨트롤러에 보고한다. 스펙 §2.2에 따라 낮 복원을 쓰기 없는 읽기 전용 경로로 바꿀지는 컨트롤러가 사용자와 정한다. Task 2 이후는 시작하지 않는다.

- [ ] **Step 3: 커밋**

```bash
cd /home/kimchungsik/projects/com.remakeday
git add backend/tests/pure/test_scene_rerun_idempotency.py
git commit -m "test(resume): 같은 비트 장면 재실행이 기록·세계 효과를 더하지 않는다는 이어하기 전제"
```

커밋하지 않고 남긴 파일: 없음(새 파일만).

---

### Task 2: 이어하기 화면 데이터 조립기 — 낮 장면·회차 껍데기·밤 데이터 (B)

**Files:**
- Modify: `backend/apps/engine/adapter/outbound/orms/game_state_orm.py:35` (status 주석)
- Modify: `backend/apps/engine/adapter/outbound/repositories/game_repository.py` (`AttemptRepository`에 `latest_active`)
- Modify: `backend/apps/engine/app/use_cases/loop_interactor.py` (모듈 함수 `_recorded_rule_lines`, `_start_loop`의 아침 문장·규칙 문구를 메서드로 추출, `resume_shell`·`resume_day`)
- Modify: `backend/apps/engine/app/use_cases/night_interactor.py` (`resume_view`·`_resumed_submit`)
- Test: `backend/tests/engine/test_resume_views.py`

**Interfaces:**
- Consumes: Task 1의 전제(재실행은 쓰기 없음, statement·paw_effect 줄만 빠짐)
- Produces:
  - `AttemptRepository.latest_active(user_id: uuid.UUID) -> AttemptOrm | None` — 그 사용자의 판 중 `created_at`이 가장 늦은 판이 `status='active'`일 때만 그 판, 아니면 `None`. 최신 판이 닫혔거나(closed) 포기됐으면(abandoned) 그보다 오래된 active 판은 다시 잡지 않는다(사용자 결정 2026-10-16)
  - `LoopInteractor.resume_shell(loop: LoopOrm) -> dict` — `start_loop` 응답과 **같은 16개 키**(`loop_id, loop_n, morning_text, damage_level, budget_left, beat, beat_title, narration, broadcast, illustrations, aftermath, observations, note_found, ambient, lines, active_rules`). 장면 필드는 비어 있다(`beat_title=""`, `narration=""`, `broadcast=None`, `illustrations=[]`, `observations=[]`, `lines=[]`), `aftermath`·`note_found`·`ambient`는 `None`
  - `LoopInteractor.resume_day(loop: LoopOrm) -> dict` — 같은 키, 현재 비트 장면을 채운다. 새 기록을 남기지 않는다
  - `NightInteractor.resume_view(loop: LoopOrm) -> dict` — 아래 표의 5개 키. 쓰기·모델 호출 없음

| 키 | 타입 | 뜻 |
|---|---|---|
| `night_id` | `str \| None` | 정리 전(`night_pending`)이면 `None` → 밤 글쓰기 화면. 있으면 확인 화면부터 |
| `claims` | `list[str]` | 정리된 주장(확인 화면 `initialClaims`, 개입 화면 `hypothesis`) |
| `is_question` | `list[bool]` | 확인 화면 `initialIsQuestion` |
| `questions_left` | `int` | 개입 화면 남은 질문(새 밤은 3) |
| `submit` | `dict \| None` | 제출한 밤만. `answer_scored` 이벤트에 저장된 제출 응답(`SubmitRes`) + 지금 기록으로 다시 만든 `suggested_questions`(이미 한 질문 제외). 저장 응답이 없는 구 제출은 `nights` 행으로 최소 응답을 만든다 |

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`backend/tests/engine/test_resume_views.py`:

```python
"""이어하기 화면 데이터 — 낮 장면 다시 그리기·회차 껍데기·밤 단계 데이터 (설계 2026-10-16 §2.2)."""

import json
import uuid

from sqlalchemy import func, select

from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
from apps.engine.adapter.outbound.orms.game_state_orm import NightOrm, RuleOrm
from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    LoopRepository,
    NightRepository,
    RuleRepository,
)
from apps.engine.adapter.outbound.repositories.user_repository import UserRepository
from apps.engine.app.dtos.auth_dto import GoogleProfileDTO
from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION
from apps.engine.dependencies.engine_dependency import get_loop_interactor, get_night_interactor


def _event_count(db_session) -> int:
    db_session.expire_all()
    return db_session.scalar(select(func.count()).select_from(EventLogOrm))


def _scene(lines: list[dict]) -> list[tuple]:
    """대사창 줄 비교용 — 되살리지 않는 지나가는 말(npc)·기록 알림(system)은 뺀다. 되살린 줄은 순서가 달라질 수 있어 정렬한다."""
    return sorted((l["kind"], l["text"], l["observation_id"] or "") for l in lines if l["kind"] not in ("npc", "system"))


def _started(db_session, rules=()):
    loops = get_loop_interactor(db_session)
    attempt = AttemptRepository(db_session).create(None)
    for rule in rules:
        RuleRepository(db_session).add(rule(attempt.id))
    started = loops.start_loop(attempt.id)
    return loops, started, uuid.UUID(started["loop_id"])


def _night_ready(db_session):
    loops, _, loop_id = _started(db_session)
    for _ in range(6):
        loops.advance_beat(loop_id)
    return get_night_interactor(db_session), LoopRepository(db_session).get(loop_id)


# ── 진행 중인 판 ──────────────────────────────────────────────


def test_latest_active_is_the_newest_attempt_only_while_it_is_active(db_session):
    """진행 중인 판 = 가장 최근 판이 active일 때만. 최신 판이 끝나거나 포기되면 오래된 active 판을 다시 잡지 않는다."""
    users, attempts = UserRepository(db_session), AttemptRepository(db_session)
    alice = users.upsert_from_google(GoogleProfileDTO(sub="alice", email="", name="a"))
    bob = users.upsert_from_google(GoogleProfileDTO(sub="bob", email="", name="b"))
    attempts.create(None, user_id=alice.id)  # 이 기능 전에 닫히지 않고 남은 오래된 active 판
    newer = attempts.create(None, user_id=alice.id)
    attempts.create(None, user_id=bob.id)  # 남의 판이 더 최근이어도 alice의 답은 그대로
    assert attempts.latest_active(alice.id).id == newer.id

    for status in ("closed", "abandoned"):
        newest = attempts.create(None, user_id=alice.id)
        newest.status = status
        attempts.save()
        assert attempts.latest_active(alice.id) is None, f"최신 판이 {status}인데 오래된 active 판이 다시 잡혔다"
    assert attempts.latest_active(uuid.uuid4()) is None


# ── 낮 ────────────────────────────────────────────────────────


def test_resume_shell_matches_start_loop_shape_without_scene(db_session):
    loops, started, loop_id = _started(db_session)
    shell = loops.resume_shell(LoopRepository(db_session).get(loop_id))
    assert set(shell) == set(started)
    assert (shell["loop_id"], shell["loop_n"], shell["morning_text"], shell["budget_left"], shell["active_rules"]) == (
        started["loop_id"], 1, started["morning_text"], started["budget_left"], started["active_rules"])
    assert (shell["lines"], shell["observations"], shell["illustrations"]) == ([], [], [])
    assert (shell["ambient"], shell["aftermath"], shell["note_found"], shell["broadcast"]) == (None, None, None, None)


def test_resume_day_redraws_first_scene_without_new_records(db_session):
    loops, started, loop_id = _started(db_session)
    before = _event_count(db_session)
    resumed = loops.resume_day(LoopRepository(db_session).get(loop_id))
    again = loops.resume_day(LoopRepository(db_session).get(loop_id))
    assert _event_count(db_session) == before
    assert resumed == again
    assert _scene(resumed["lines"]) == _scene(started["lines"])
    assert (resumed["beat"], resumed["beat_title"], resumed["budget_left"]) == (1, started["beat_title"], started["budget_left"])
    assert resumed["observations"] == started["observations"]
    assert (resumed["ambient"], resumed["aftermath"], resumed["note_found"]) == (None, None, None)


def test_resume_day_keeps_rule_explanation_lines(db_session):
    """Review Focus 1 — 3비트 설명 규칙이 실행된 뒤 다시 그려도 설명 줄이 남고 기록은 늘지 않는다."""
    explain = lambda attempt_id: RuleOrm(  # noqa: E731
        attempt_id=attempt_id, rule_id="R1", source="user_choice", target="민석", when_beat=3,
        effect="enforce", action=EXPLAIN_ACTION, created_loop=1)
    loops, _, loop_id = _started(db_session, rules=[explain])
    loops.advance_beat(loop_id)
    advanced = loops.advance_beat(loop_id)  # 3비트
    told = [l for l in advanced["lines"] if l["kind"] == "statement" and l["observation_id"].endswith(":rule-3-R1")]
    assert told, "R1 설명이 3비트에 나오지 않았다 — 시나리오 전제(민석 3비트 기회)를 확인한다"
    before = _event_count(db_session)
    resumed = loops.resume_day(LoopRepository(db_session).get(loop_id))
    assert _event_count(db_session) == before
    assert _scene(resumed["lines"]) == _scene(advanced["lines"])
    assert resumed["beat"] == 3


# ── 밤·채점·개입 ──────────────────────────────────────────────


def test_night_resume_view_follows_the_night(db_session):
    nights, loop = _night_ready(db_session)
    assert nights.resume_view(loop) == {
        "night_id": None, "claims": [], "is_question": [], "questions_left": 3, "submit": None}

    draft = nights.draft(loop.id, [], "채연이 밥을 남겼다. 왜 남겼을까?")
    view = nights.resume_view(loop)
    assert (view["night_id"], view["claims"], view["is_question"], view["submit"]) == (
        draft["night_id"], draft["claims"], draft["is_question"], None)

    submitted = nights.submit(uuid.UUID(draft["night_id"]))
    before = _event_count(db_session)
    view = nights.resume_view(loop)
    assert _event_count(db_session) == before  # 저장 응답을 읽기만 한다 — 채점·기록 없음
    assert json.loads(json.dumps(view["submit"])) == json.loads(json.dumps(submitted))

    night = NightRepository(db_session).get(uuid.UUID(draft["night_id"]))
    night.questions_left, night.questions = 1, ["채연이 밥 남겼어?", "누가 방송실에 갔어?"]
    NightRepository(db_session).save()
    view = nights.resume_view(loop)
    assert view["questions_left"] == 1
    assert not set(view["submit"]["suggested_questions"]) & set(night.questions)


def test_submitted_night_without_stored_response_still_resumes(db_session):
    """Review Focus 4 — 응답 저장(2026-09-18) 전 제출: answer_scored 응답이 없어도 개입 화면이 쓸 점수가 있다."""
    nights, loop = _night_ready(db_session)
    NightRepository(db_session).create(NightOrm(loop_id=loop.id, claims=["채연이 밥을 남겼다."],
                                                submitted=True, total=42.0, passed=False))
    loop.state = "intervention"
    LoopRepository(db_session).save()
    submit = nights.resume_view(loop)["submit"]
    assert (submit["total"], submit["loop_n"], submit["is_final"], submit["intervention_available"]) == (42.0, 1, False, True)
    assert isinstance(submit["suggested_questions"], list)
```

- [ ] **Step 2: 실패를 확인한다**

Run: `cd /home/kimchungsik/projects/com.remakeday/backend && .venv/bin/python -m pytest tests/engine/test_resume_views.py -q`
Expected: FAIL — `AttributeError: 'AttemptRepository' object has no attribute 'latest_active'`, `'LoopInteractor' object has no attribute 'resume_shell'` 등

- [ ] **Step 3: 판 상태 주석과 진행 중인 판 조회를 더한다**

`game_state_orm.py`의 `AttemptOrm.status` 줄을 바꾼다:

```python
    status: Mapped[str] = mapped_column(String(16), default="active")  # active|closed|abandoned
```

`game_repository.py`의 `AttemptRepository`에서 `get_owned` 바로 아래에 추가한다:

```python
    def latest_active(self, user_id: uuid.UUID) -> AttemptOrm | None:
        """진행 중인 판 — 그 사용자의 가장 최근 판이 active일 때만 그 판(설계 2026-10-16 §1).
        최신 판이 closed·abandoned면 None — 그보다 오래된 active 판은 다시 잡지도, 닫지도 않는다."""
        latest = self._s.scalars(
            select(AttemptOrm)
            .where(AttemptOrm.user_id == user_id)
            .order_by(AttemptOrm.created_at.desc())
        ).first()
        return latest if latest is not None and latest.status == "active" else None
```

- [ ] **Step 4: LoopInteractor에 이어하기 조립기를 더한다**

`loop_interactor.py` — `_WORLD_EFFECTS = {...}` 줄 아래에 모듈 함수를 추가한다:

```python
# 이어하기 재실행 때 execute_scene이 다시 만들지 않는 규칙 줄 — 공개 기록 키 접두 → 대사창 줄 종류.
# 키는 scene_execution의 disclose 키(rule-{비트}-{규칙}, paw-effect-{비트}-{규칙})와 같다.
_RECORDED_RULE_LINES = {"rule": "statement", "paw-effect": "paw_effect"}


def _recorded_rule_lines(loop, lines, observations) -> list[LineDTO]:
    """이미 실행된 규칙의 설명·부작용 줄은 재실행이 건너뛴다(tests/pure/test_scene_rerun_idempotency.py). 공개 기록에서 되살린다."""
    shown = {line.observation_id for line in lines}
    restored = []
    for o in observations:
        if o["observation_id"] in shown:
            continue
        key = o["observation_id"].removeprefix(f"{loop.id}:")
        kind = next((k for prefix, k in _RECORDED_RULE_LINES.items() if key.startswith(f"{prefix}-{loop.beat}-")), None)
        if kind is not None:
            restored.append(LineDTO(kind=kind, speaker=o["actor"], text=o["text"], observation_id=o["observation_id"]))
    return restored
```

`_start_loop` 안에서 아침 문장과 규칙 문구를 메서드로 옮긴다. 이 줄을 지운다:

```python
        first = MORNING_SHIFTED if shifted else MORNING_FIRST
```

반환 dict의 두 항목을 바꾼다. 이것을:

```python
            "morning_text": f"{first} {self._scenario.morning_line(damage)}".strip(),
```

이렇게:

```python
            "morning_text": self._morning_text(loop),
```

이것을:

```python
            "active_rules": [
                r.shown_reason
                or f"{r.target}: {r.action} {'금지' if r.effect == 'suppress' else '강제'}"
                for r in player_visible(rule_rows)  # 숨은 규칙은 보이지 않는다
            ],
```

이렇게:

```python
            "active_rules": self._active_rule_labels(rule_rows),
```

`# ── 조회 ───` 구역 바로 위에 이어하기 구역을 추가한다:

```python
    # ── 이어하기 ──────────────────────────────────────────────

    def resume_shell(self, loop) -> dict:
        """이어하기 — start_loop 응답과 같은 모양의 회차 정보. 장면은 비워 둔다(낮이 아닌 단계용).
        ambient·aftermath·note_found는 되살리지 않는다(설계 2026-10-16 §2.2)."""
        return {
            "loop_id": str(loop.id), "loop_n": loop.loop_n, "morning_text": self._morning_text(loop),
            "damage_level": loop.damage_level, "budget_left": loop.budget_left, "beat": loop.beat,
            "beat_title": "", "narration": "", "broadcast": None, "illustrations": [],
            "aftermath": None, "observations": [], "note_found": None, "ambient": None, "lines": [],
            "active_rules": self._active_rule_labels(self._rules.list(loop.attempt_id)),
        }

    def resume_day(self, loop) -> dict:
        """이어하기 — 낮 현재 비트 장면을 다시 그린다. 재실행은 이미 기록된 규칙 실행·관찰을 건너뛰어
        새 기록·세계 효과를 남기지 않는다. 건너뛴 설명·부작용 줄은 공개 기록에서 되살린다."""
        bundle = self._scenario.bundle()
        beat = execute_scene(self._events, loop, bundle, self._rules.list(loop.attempt_id),
                             on_action=self._world_effect(loop))
        observations = [o.model_dump() for o in public_observations(self._events, loop.attempt_id)
                        if o.loop_id == str(loop.id) and o.beat == loop.beat]
        beat = beat.model_copy(update={"lines": [*beat.lines, *_recorded_rule_lines(loop, beat.lines, observations)]})
        return {
            **self.resume_shell(loop),
            "beat_title": beat.title, "narration": beat.narration, "broadcast": beat.broadcast,
            "illustrations": [i.model_dump() for i in beat.illustrations],
            "observations": observations,
            "lines": self._scene_lines(loop, beat, observations, None, None),
        }
```

`# ── 내부 ───` 구역의 `_loop_state` 위에 추가한다:

```python
    def _morning_text(self, loop) -> str:
        first = MORNING_SHIFTED if loop.morning_shifted else MORNING_FIRST
        return f"{first} {self._scenario.morning_line(loop.damage_level)}".strip()

    @staticmethod
    def _active_rule_labels(rule_rows) -> list[str]:
        """오늘 세계에 걸린 규칙의 유저용 문구 — 숨은 규칙은 보이지 않는다."""
        return [r.shown_reason or f"{r.target}: {r.action} {'금지' if r.effect == 'suppress' else '강제'}"
                for r in player_visible(rule_rows)]
```

- [ ] **Step 5: NightInteractor에 밤 데이터 조립기를 더한다**

`night_interactor.py`의 game_constants import를 바꾼다:

```python
from apps.engine.domain.value_objects.game_constants import CELLS, LOOPS_PER_ATTEMPT, MAX_CLAIMS, QUESTIONS_PER_NIGHT
```

`# ── 내부 ───` 구역 바로 위에 추가한다:

```python
    # ── 이어하기 ──────────────────────────────────────────────

    def resume_view(self, loop) -> dict:
        """이어하기 — 밤·채점·개입 화면이 처음 받는 데이터. 쓰기·모델 호출 없음 (설계 2026-10-16 §2.2).
        night_id가 없으면 아직 정리 전(밤 글쓰기), 있으면 확인 화면부터. 제출한 밤은 저장된 제출 응답을 쓴다."""
        night = self._nights.for_loop(loop.id)
        if night is None:
            return {"night_id": None, "claims": [], "is_question": [],
                    "questions_left": QUESTIONS_PER_NIGHT, "submit": None}
        return {
            "night_id": str(night.id), "claims": list(night.claims),
            "is_question": _question_flags(night.claims),
            "questions_left": night.questions_left,
            "submit": self._resumed_submit(loop, night) if night.submitted else None,
        }

    def _resumed_submit(self, loop, night) -> dict:
        stored = [e.response for e in self._events.query(loop.attempt_id, type=EventType.ANSWER_SCORED, loop_n=loop.loop_n)
                  if e.response]
        # 응답 저장(2026-09-18) 전에 제출한 밤 — 개입 화면이 쓰는 점수만 밤 행에서 되살린다.
        response = stored[-1] if stored else {
            "total": night.total or 0.0, "passed": bool(night.passed), "loop_n": loop.loop_n,
            "world_outcome": loop.world_outcome, "is_final": False, "closed_by": None, "cells": None,
            "cookie": None, "intervention_available": True, "ending_lines": None, "truth_reveal": None,
            "cell_feedback": None, "wrong_claim_count": 0, "accepted_claims": [], "empty_cells": [],
            "night_clue": None,
        }
        observations = public_observations(self._events, loop.attempt_id, through_loop=loop.loop_n)
        return {**response, "suggested_questions": suggest_questions(
            observations, loop_n=loop.loop_n, asked=list(night.questions or []))}
```

- [ ] **Step 6: 테스트와 주변 회귀를 돌린다**

Run: `cd /home/kimchungsik/projects/com.remakeday/backend && .venv/bin/python -m pytest tests/engine/test_resume_views.py tests/engine/test_usecase_day.py tests/engine/test_usecase_night.py tests/engine/test_e2e_flow.py -q && .venv/bin/lint-imports`
Expected: PASS(신규 6건 + 기존 전부), `Contracts: 4 kept, 0 broken`

`test_resume_day_keeps_rule_explanation_lines`가 "R1 설명이 3비트에 나오지 않았다"로 실패하면 시나리오 전제 문제다 — 대상 인물을 `tests/pure/test_review_failure_boundaries.py::test_authored_explanation_is_speech_not_independently_verified_truth`가 쓰는 조합과 맞춰 보고, 그래도 안 나오면 멈추고 보고한다. 테스트를 약하게 고치지 않는다.

- [ ] **Step 7: 커밋**

```bash
cd /home/kimchungsik/projects/com.remakeday
git add backend/apps/engine/adapter/outbound/orms/game_state_orm.py backend/apps/engine/adapter/outbound/repositories/game_repository.py backend/apps/engine/app/use_cases/loop_interactor.py backend/apps/engine/app/use_cases/night_interactor.py backend/tests/engine/test_resume_views.py
git commit -m "feat(resume): 이어하기 화면 데이터 — 낮 현재 비트 다시 그리기(규칙 줄 복원)·회차 껍데기·밤 단계 데이터"
```

커밋하지 않고 남긴 파일: 없음(백엔드 파일은 2026-10-16 기준 미커밋 변경이 없다 — 시작 전 `git status --short`로 다시 확인).

---

### Task 3: 진행 중인 판 API — 조회·단계 매핑·포기 (B)

**Files:**
- Create: `backend/apps/engine/app/use_cases/resume_interactor.py`
- Create: `backend/apps/engine/adapter/inbound/api/v1/me_router.py`
- Modify: `backend/apps/engine/dependencies/engine_dependency.py` (import + 파일 끝 `get_resume_interactor`)
- Modify: `backend/main.py` (라우터 등록)
- Modify: `backend/tests/engine/test_attempt_ownership.py` (`PUBLIC_ROUTES`)
- Modify: `docs/spec/api_contract.md`
- Test: `backend/tests/engine/test_resume_api.py`

**Interfaces:**
- Consumes: Task 2의 `AttemptRepository.latest_active`, `LoopInteractor.resume_shell`·`resume_day`, `NightInteractor.resume_view`; 기존 `AttemptRepository.count_today(user_id, now)`, `LoopRepository.latest_for(attempt_id)`, `UserRepository.get_by_sub(sub)`, `ScenarioPort.entry_lines()`
- Produces:
  - `ResumeInteractor(*, attempts, loops, users, scenario, day_view, night_view, user_daily_attempts: int)` with `active(user: SessionUserDTO) -> dict`, `abandon(user: SessionUserDTO) -> None`
  - `PHASE_BY_STATE: dict[str, str]`(모듈 상수)
  - `GET /api/v1/me/attempts/active` 응답 — 키는 항상 6개:

```
{
  "attempt": {attempt_id, attempt_n, entry_lines, prior_cell_results} | null,
  "resume_phase": "entry" | "day" | "night" | "score" | "god" | null,   // attempt가 null이면 null
  "loop": StartLoopRes 모양 | null,       // 회차가 없을 때만 null. 낮은 장면 포함, 그 밖은 resume_shell
  "night": Task 2 표의 5개 키 | null,     // night·score·god 단계만
  "today_remaining": int,                 // max(0, 하루 한도 - 오늘 만든 판 수), 포기한 판 포함
  "daily_limit": int                      // USER_DAILY_ATTEMPTS
}
```
  - `POST /api/v1/me/attempts/active/abandon` → 204, 본문 없음
  - `get_resume_interactor(session)` (`engine_dependency`)

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`backend/tests/engine/test_resume_api.py`:

```python
"""이어하기 API — 진행 중인 판 찾기·단계 매핑·포기 (설계 2026-10-16 §2.1~2.3, §4)."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
from apps.engine.adapter.outbound.orms.game_state_orm import AttemptOrm
from apps.engine.adapter.outbound.repositories.game_repository import AttemptRepository, LoopRepository
from apps.engine.adapter.outbound.repositories.user_repository import UserRepository
from apps.engine.app.dtos.auth_dto import GoogleProfileDTO

ACTIVE = "/api/v1/me/attempts/active"
ABANDON = "/api/v1/me/attempts/active/abandon"


def _limit() -> int:
    from core.matrix import grid_keymaker_secret_manager as cfg
    return cfg.get_settings().user_daily_attempts


def _play_until(client, state: str) -> dict:
    """새 판 하나를 state까지 실제 API로 진행한다(가짜 모델). none = 판만 있고 회차 없음."""
    ids: dict = {}

    def new_session():
        ids["attempt_id"] = client.post("/sessions", json={}).json()["attempt_id"]

    def start_day():
        ids["loop_id"] = client.post(f"/sessions/{ids['attempt_id']}/loops").json()["loop_id"]

    def end_day():
        for _ in range(6):
            client.post(f"/loops/{ids['loop_id']}/beats/next")

    def draft():
        ids["night_id"] = client.post(f"/loops/{ids['loop_id']}/night/draft",
                                      json={"tapped_note_ids": [], "free_text": "채연이 밥을 남겼다."}).json()["night_id"]

    def submit():
        assert client.post(f"/nights/{ids['night_id']}/submit").status_code == 200

    def choose_rule():
        client.get(f"/nights/{ids['night_id']}/options")
        assert client.post(f"/nights/{ids['night_id']}/rule", json={"choice": "1"}).json()["ok"]

    steps = [("none", new_session), ("day", start_day), ("night_pending", end_day),
             ("night_draft", draft), ("intervention", submit), ("closed", choose_rule)]
    for name, step in steps:
        step()
        if name == state:
            return ids
    raise AssertionError(f"모르는 상태: {state}")


@pytest.mark.parametrize("state,phase", [
    ("none", "entry"), ("day", "day"), ("night_pending", "night"), ("night_draft", "night"),
    ("scored", "score"), ("intervention", "god"), ("closed", "entry"),
])
def test_resume_phase_follows_latest_loop_state(db_session, logged_in, state, phase):
    from main import app
    with TestClient(app) as client:
        ids = _play_until(client, "intervention" if state == "scored" else state)
        if state == "scored":  # 지금 엔진은 scored를 거치지 않는다(제출 뒤 곧바로 intervention) — 표의 행을 직접 만든다
            loop = LoopRepository(db_session).latest_for(uuid.UUID(ids["attempt_id"]))
            loop.state = "scored"
            db_session.commit()
        res = client.get(ACTIVE)
    assert res.status_code == 200
    body = res.json()
    assert body["attempt"]["attempt_id"] == ids["attempt_id"]
    assert len(body["attempt"]["entry_lines"]) == 3
    assert body["resume_phase"] == phase
    assert (body["loop"] is None) == (state == "none")  # 회차 없음만 loop가 없다 — 프론트가 선택 화면 없이 그대로 쓰는 기준
    assert (body["night"] is None) == (phase in ("entry", "day"))
    assert body["daily_limit"] == _limit()


def test_day_resume_returns_current_scene_and_writes_nothing(db_session, logged_in):
    from main import app
    with TestClient(app) as client:
        ids = _play_until(client, "day")
        client.post(f"/loops/{ids['loop_id']}/beats/next")
        db_session.expire_all()
        before = db_session.scalar(select(func.count()).select_from(EventLogOrm))
        first, second = client.get(ACTIVE).json(), client.get(ACTIVE).json()
        db_session.expire_all()
        after = db_session.scalar(select(func.count()).select_from(EventLogOrm))
    assert after == before
    assert first == second
    loop = first["loop"]
    assert (loop["loop_id"], loop["beat"]) == (ids["loop_id"], 2)
    assert loop["lines"] and loop["lines"][0]["kind"] == "scene"
    assert (loop["ambient"], loop["aftermath"]) == (None, None)


def test_draft_and_god_resume_carry_night_data(db_session, logged_in):
    from main import app
    with TestClient(app) as client:
        ids = _play_until(client, "night_draft")
        drafted = client.get(ACTIVE).json()["night"]
        client.post(f"/nights/{ids['night_id']}/submit")
        god = client.get(ACTIVE).json()["night"]
    assert (drafted["night_id"], drafted["claims"], drafted["submit"]) == (ids["night_id"], ["채연이 밥을 남겼다."], None)
    assert (god["night_id"], god["questions_left"]) == (ids["night_id"], 3)
    assert god["submit"]["loop_n"] == 1 and god["submit"]["intervention_available"] is True
    assert isinstance(god["submit"]["suggested_questions"], list)


def test_abandoned_attempt_is_not_active_but_still_counts_today(db_session, logged_in):
    from main import app
    with TestClient(app) as client:
        ids = _play_until(client, "none")
        assert client.get(ACTIVE).json()["today_remaining"] == _limit() - 1
        res = client.post(ABANDON)
        assert res.status_code == 204 and res.content == b""
        body = client.get(ACTIVE).json()
        assert (body["attempt"], body["resume_phase"], body["loop"], body["night"]) == (None, None, None, None)
        assert body["today_remaining"] == _limit() - 1  # 포기한 판도 그날 판 수에 남는다 — "1회 차감"의 실체
        assert client.post(f"/sessions/{ids['attempt_id']}/loops").status_code == 409  # 포기한 판은 다시 열 수 없다
    db_session.expire_all()
    assert db_session.get(AttemptOrm, uuid.UUID(ids["attempt_id"])).status == "abandoned"


def test_abandon_without_active_attempt_is_a_noop(db_session, logged_in):
    from main import app
    with TestClient(app) as client:
        assert client.post(ABANDON).status_code == 204
        assert client.get(ACTIVE).json() == {
            "attempt": None, "resume_phase": None, "loop": None, "night": None,
            "today_remaining": _limit(), "daily_limit": _limit()}


def test_other_users_attempt_is_never_active(db_session, logged_in):
    from main import app
    alice = UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub="alice", email="", name="alice"))
    AttemptRepository(db_session).create(None, user_id=alice.id)
    with TestClient(app) as client:
        assert client.get(ACTIVE).json()["attempt"] is None
        assert client.post(ABANDON).status_code == 204
    db_session.expire_all()
    assert db_session.scalars(select(AttemptOrm.status)).all() == ["active"]  # 남의 판은 포기되지 않는다


def test_abandoning_latest_does_not_resurface_older_active(db_session, logged_in):
    """사용자 결정 2026-10-16 — 진행 중인 판은 최신 판이 active일 때만. 최신 판을 포기하면 오래된 active 판이 있어도 attempt=null."""
    from main import app
    with TestClient(app) as client:
        old = _play_until(client, "none")["attempt_id"]
        new = _play_until(client, "none")["attempt_id"]
        assert client.get(ACTIVE).json()["attempt"]["attempt_id"] == new
        assert client.post(ABANDON).status_code == 204
        body = client.get(ACTIVE).json()
        assert (body["attempt"], body["resume_phase"]) == (None, None)
        assert client.post(ABANDON).status_code == 204  # 두 번째 포기는 아무것도 하지 않는다 — 오래된 판을 포기하지 않는다
    db_session.expire_all()
    assert db_session.get(AttemptOrm, uuid.UUID(old)).status == "active"  # 오래된 판은 건드리지 않는다
    assert db_session.get(AttemptOrm, uuid.UUID(new)).status == "abandoned"


@pytest.mark.parametrize("method,path", [("GET", ACTIVE), ("POST", ABANDON)])
def test_me_routes_require_login(db_session, monkeypatch, method, path):
    from main import app
    from apps.engine.adapter.inbound.api.v1 import guards
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "guard_auth", "on")
    guards._BUCKETS.clear()
    with TestClient(app) as client:
        assert client.request(method, path).status_code == 401
```

- [ ] **Step 2: 실패를 확인한다**

Run: `cd /home/kimchungsik/projects/com.remakeday/backend && .venv/bin/python -m pytest tests/engine/test_resume_api.py -q`
Expected: FAIL — 경로가 없어 404 (`assert 404 == 200` 등)

- [ ] **Step 3: 유스케이스를 만든다**

`backend/apps/engine/app/use_cases/resume_interactor.py`:

```python
"""이어하기 — 로그인 사용자의 진행 중인 판을 찾고, 그 판을 다시 여는 화면 데이터를 고른다 (설계 2026-10-16 §2.1~2.3).

진행 중인 판 = 그 사용자의 가장 최근 판이 status='active'일 때만 그 판. 단계는 최신 회차 상태가 정한다.
낮 장면은 LoopInteractor, 밤·채점·개입 데이터는 NightInteractor가 만든다 — 여기서는 단계에 맞는 조립기를 고르기만 한다.
쓰기는 abandon 하나뿐이다.
"""

from datetime import datetime, timezone

from apps.engine.app.dtos.auth_dto import SessionUserDTO

# 최신 회차 상태 → 프론트가 여는 단계. scored는 지금 엔진이 거치지 않지만(제출 뒤 곧바로 intervention) 스펙 표대로 둔다.
PHASE_BY_STATE = {
    "day": "day",
    "night_pending": "night",
    "night_draft": "night",
    "scored": "score",
    "intervention": "god",
    "closed": "entry",
}
NO_LOOP_PHASE = "entry"


def _no_night(loop) -> None:
    return None


class ResumeInteractor:
    def __init__(self, *, attempts, loops, users, scenario, day_view, night_view, user_daily_attempts: int) -> None:
        self._attempts = attempts
        self._loops = loops
        self._users = users
        self._scenario = scenario
        self._limit = user_daily_attempts
        # 단계 → (회차 데이터, 밤 데이터) 조립기. 낮만 장면을 다시 그리고, 나머지는 장면이 빈 회차 정보를 준다.
        self._builders = {
            "entry": (day_view.resume_shell, _no_night),
            "day": (day_view.resume_day, _no_night),
            "night": (day_view.resume_shell, night_view.resume_view),
            "score": (day_view.resume_shell, night_view.resume_view),
            "god": (day_view.resume_shell, night_view.resume_view),
        }

    def active(self, user: SessionUserDTO) -> dict:
        owner = self._users.get_by_sub(user.sub)
        attempt = self._attempts.latest_active(owner.id) if owner else None
        snapshot = {"attempt": None, "resume_phase": None, "loop": None, "night": None,
                    "today_remaining": self._remaining(owner), "daily_limit": self._limit}
        if attempt is None:
            return snapshot
        loop = self._loops.latest_for(attempt.id)
        phase = PHASE_BY_STATE[loop.state] if loop else NO_LOOP_PHASE
        build_loop, build_night = self._builders[phase]
        return {
            **snapshot,
            "attempt": {
                "attempt_id": str(attempt.id), "attempt_n": attempt.attempt_n,
                "entry_lines": self._scenario.entry_lines(), "prior_cell_results": attempt.prior_cell_results,
            },
            "resume_phase": phase,
            "loop": build_loop(loop) if loop else None,
            "night": build_night(loop) if loop else None,
        }

    def abandon(self, user: SessionUserDTO) -> None:
        """진행 중인 판을 abandoned로 닫는다. 없으면 아무 일도 하지 않는다. 포기한 판은 그날 판 수에 남는다."""
        owner = self._users.get_by_sub(user.sub)
        attempt = self._attempts.latest_active(owner.id) if owner else None
        if attempt is None:
            return
        attempt.status = "abandoned"
        self._attempts.save()

    def _remaining(self, owner) -> int:
        if owner is None:
            return self._limit
        return max(0, self._limit - self._attempts.count_today(owner.id, datetime.now(timezone.utc)))
```

- [ ] **Step 4: 의존성과 라우터를 배선한다**

`engine_dependency.py` — `from apps.engine.app.use_cases.night_interactor import NightInteractor` 아래에 import를 더한다:

```python
from apps.engine.app.use_cases.resume_interactor import ResumeInteractor
```

파일 끝에 추가한다:

```python
def get_resume_interactor(session: Session = Depends(get_session)):
    return ResumeInteractor(
        attempts=AttemptRepository(session),
        loops=LoopRepository(session),
        users=UserRepository(session),
        scenario=_scenario(),
        day_view=get_loop_interactor(session),
        night_view=get_night_interactor(session),
        user_daily_attempts=get_settings().user_daily_attempts,
    )
```

`backend/apps/engine/adapter/inbound/api/v1/me_router.py`:

```python
"""이어하기 라우터 — 로그인 사용자 자신의 진행 중인 판 (설계 2026-10-16 §2.2·§2.3).

경로에 판 ID가 없으므로 판 주인 확인(require_attempt_owner) 대신 로그인(require_user)만 건다.
대상 판은 세션 사용자의 판 중에서만 고른다 — 남의 판은 애초에 후보가 아니다.
"""

from fastapi import APIRouter, Depends, Response

from apps.engine.adapter.inbound.api.v1.guards import require_user
from apps.engine.dependencies.engine_dependency import get_resume_interactor

router = APIRouter(prefix="/api/v1/me", tags=["me"])


@router.get("/attempts/active")
def active_attempt(user=Depends(require_user), uc=Depends(get_resume_interactor)):
    return uc.active(user)


@router.post("/attempts/active/abandon", status_code=204)
def abandon_active_attempt(user=Depends(require_user), uc=Depends(get_resume_interactor)) -> Response:
    uc.abandon(user)
    return Response(status_code=204)
```

`backend/main.py` — game_router import 아래에 추가:

```python
from apps.engine.adapter.inbound.api.v1.me_router import router as me_router
```

파일 끝 `app.include_router(auth_router)` 아래에 추가:

```python
app.include_router(me_router)
```

- [ ] **Step 5: 라우트 인벤토리에 올린다**

`backend/tests/engine/test_attempt_ownership.py`의 `PUBLIC_ROUTES`에서 `("POST", "/api/v1/auth/logout"),` 아래에 추가한다:

```python
    # 로그인만 — 판 ID 없이 세션 사용자 자신의 진행 중인 판을 다룬다(이어하기, 2026-10-16). 비로그인 401은 test_resume_api.py
    ("GET", "/api/v1/me/attempts/active"),
    ("POST", "/api/v1/me/attempts/active/abandon"),
```

- [ ] **Step 6: 테스트를 돌린다**

Run: `cd /home/kimchungsik/projects/com.remakeday/backend && .venv/bin/python -m pytest tests/engine/test_resume_api.py tests/engine/test_attempt_ownership.py tests/engine/test_resume_views.py -q && .venv/bin/lint-imports`
Expected: PASS(신규 15건 + 기존), `Contracts: 4 kept, 0 broken`

- [ ] **Step 7: 계약 문서를 맞춘다**

`docs/spec/api_contract.md`의 `## 판 종료 후 (P5)` 절 바로 위에 새 절을 추가한다:

```markdown
## 이어하기 (2026-10-16)

### GET /api/v1/me/attempts/active — 진행 중인 판

로그인 필요(`require_user`, 비로그인 401). 판 ID가 경로에 없어 판 주인 확인 대신 세션 사용자의 판 중에서만 찾는다.
진행 중인 판 = 그 사용자의 가장 최근 판이 `status='active'`일 때만 그 판. 최신 판이 `closed`·`abandoned`면 `attempt: null`이고, 그보다 오래된 active 판은 다시 잡지도 닫지도 않는다.

res(키는 항상 6개):
`{attempt: CreateSessionRes|null, resume_phase: "entry"|"day"|"night"|"score"|"god"|null, loop: StartLoopRes|null, night: ResumeNight|null, today_remaining: number, daily_limit: number}`

- `resume_phase`는 최신 회차 상태로 정한다: 회차 없음·`closed` → `entry`, `day` → `day`, `night_pending`·`night_draft` → `night`, `scored` → `score`, `intervention` → `god`.
- `loop`는 회차가 없을 때만 `null`. `day`면 현재 비트 장면(다시 실행해도 기록·세계 효과가 늘지 않는다, 이미 실행된 규칙의 설명·부작용 줄은 공개 기록에서 되살린다). 그 밖의 단계는 장면 필드가 빈 회차 정보. `ambient`·`aftermath`·`note_found`는 항상 `null`.
- `ResumeNight` = `{night_id: string|null, claims: string[], is_question: boolean[], questions_left: number, submit: SubmitRes|null}`. `night_id`가 없으면 정리 전(밤 글쓰기), 있으면 확인 화면부터. `submit`은 제출한 밤만 — 저장된 제출 응답 + 이미 한 질문을 뺀 `suggested_questions`.
- `today_remaining` = `max(0, USER_DAILY_ATTEMPTS - 오늘 만든 판 수)`. 포기한 판도 센다.

### POST /api/v1/me/attempts/active/abandon — 진행 중인 판 포기

로그인 필요. 진행 중인 판을 `abandoned`로 바꾸고 **204**(본문 없음). 진행 중인 판이 없어도 204. 포기한 판은 다시 이어할 수 없고(`POST /sessions/{id}/loops` 409), 그날 판 수에는 남는다. 새 판은 이어서 `POST /sessions`로 만든다(한도면 기존 403 `daily_attempt_limit`).
```

같은 문서 `### 라우트별 가드 매트릭스` 표의 `POST /sessions` 행 아래에 두 행을 추가한다:

```markdown
| `GET /api/v1/me/attempts/active` | 필요 | — (세션 사용자의 판만 후보) | — |
| `POST /api/v1/me/attempts/active/abandon` | 필요 | — (세션 사용자의 판만 후보) | — |
```

- [ ] **Step 8: 커밋**

```bash
cd /home/kimchungsik/projects/com.remakeday
git add backend/apps/engine/app/use_cases/resume_interactor.py backend/apps/engine/adapter/inbound/api/v1/me_router.py backend/apps/engine/dependencies/engine_dependency.py backend/main.py backend/tests/engine/test_resume_api.py backend/tests/engine/test_attempt_ownership.py docs/spec/api_contract.md
git commit -m "feat(resume): 진행 중인 판 조회·단계 매핑·포기 API (/api/v1/me/attempts/active)"
```

커밋하지 않고 남긴 파일: 없음(시작 전 `git status --short`로 `docs/spec/api_contract.md`·`backend/` 파일이 깨끗한지 다시 확인한다. 그새 `M`이 됐으면 그 파일은 빼고 여기에 적는다).

---

### Task 4: 회원탈퇴 API — 한 트랜잭션 삭제 (A)

**Files:**
- Modify: `backend/apps/engine/app/use_cases/session_interactor.py` (`UnknownUser`, `_resolve_user_id` — users 행이 없으면 다시 만들지 않는다)
- Modify: `backend/apps/engine/adapter/inbound/api/v1/game_router.py` (`_run`이 `UnknownUser`를 401로)
- Modify: `backend/tests/engine/conftest.py` (`logged_in`이 users 행을 만든다)
- Modify: `backend/apps/engine/adapter/outbound/repositories/user_repository.py` (`delete_with_data`)
- Modify: `backend/apps/engine/app/ports/output/user_repository_port.py` (`get_by_sub`·`delete_with_data`)
- Modify: `backend/apps/engine/app/ports/input/auth_use_case.py` (`withdraw`)
- Modify: `backend/apps/engine/app/use_cases/auth_interactor.py` (`withdraw`)
- Modify: `backend/apps/engine/adapter/inbound/api/v1/auth_router.py` (`DELETE /me`)
- Modify: `backend/tests/engine/test_attempt_ownership.py` (`PUBLIC_ROUTES`)
- Modify: `docs/spec/api_contract.md`
- Test: `backend/tests/engine/test_withdraw.py`

**Interfaces:**
- Consumes: ORM 전부(`AttemptOrm, LoopOrm, NpcStateOrm, NightOrm, NoteOrm, RuleOrm, SurveyVoteOrm`, `EventLogOrm`, `UserOrm`), `SESSION_COOKIE = "rd_session"`, `AuthUseCase.current_user(token)`
- Produces:
  - `UserRepository.delete_with_data(user_id: uuid.UUID, sub: str) -> None` — 한 번의 commit, 실패하면 rollback 후 예외를 다시 던진다
  - `AuthInteractor.withdraw(user: SessionUserDTO) -> None` — users 행이 없으면 아무 일도 하지 않는다
  - `DELETE /api/v1/auth/me` → 204 + `rd_session` 쿠키 삭제, 비로그인 401
  - `UnknownUser(Exception)`(`session_interactor`) — 세션은 유효한데 users 행이 없을 때. `POST /sessions`가 401 `{"detail": "로그인이 필요하다"}`로 돌려준다(프론트는 기존 GuardScreen "login")
  - Task 7이 쓰는 경로·상태 코드는 위와 같다

**탈퇴 뒤 남은 쿠키(사용자 결정 2026-10-16).** 세션 토큰은 서명형이라 탈퇴 뒤에도 TTL 동안 검증을 통과한다. 지금 `SessionInteractor._resolve_user_id`는 users 행이 없으면 upsert하므로, 남은 쿠키로 `POST /sessions`를 부르면 계정이 되살아난다. 이 task에서 그 upsert를 없앤다. 근거 확인: Google 로그인 콜백(`AuthInteractor.complete_login`, `auth_interactor.py:42`)과 개발 계정 로그인(`dev_login`, 같은 파일 70행)은 로그인할 때 users 행을 만든다. 그래서 정상 로그인 사용자는 `/sessions` 전에 이미 행이 있다. 예외는 `GUARD_AUTH=off`의 sub `"dev"` 하나다. 이 사용자에게는 로그인 단계가 없으므로 지금처럼 첫 판에서 행을 만든다. 이 변경으로 깨지는 기존 테스트는 users 행 없이 `POST /sessions`를 부르던 테스트다. `logged_in` 픽스처(`test_e2e_flow`·`test_guards`·`test_survey_endpoint`와 Task 3의 `test_resume_api`가 씀), `test_attempt_ownership`의 `test_foreign_prior_attempt_is_ignored_like_missing`(bob)·`test_dev_account_game_continues_from_another_session`(google-carol), 이 task의 `_client`가 여기에 해당한다. 아래 단계에서 함께 고친다.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`backend/tests/engine/test_withdraw.py`:

```python
"""회원탈퇴 — 탈퇴한 사용자의 행은 모든 테이블에서 0, 다른 사용자의 행은 그대로, 세션 쿠키 삭제 (설계 2026-10-16 §2.4)."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
from apps.engine.adapter.outbound.orms.game_state_orm import (
    AttemptOrm,
    LoopOrm,
    NightOrm,
    NoteOrm,
    NpcStateOrm,
    RuleOrm,
    SurveyVoteOrm,
)
from apps.engine.adapter.outbound.orms.user_orm import UserOrm
from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    LoopRepository,
    NightRepository,
    NoteRepository,
    RuleRepository,
    SurveyVoteRepository,
)
from apps.engine.adapter.outbound.repositories.user_repository import UserRepository
from apps.engine.adapter.outbound.security.session_token_signer import SessionTokenSigner
from apps.engine.app.dtos.auth_dto import GoogleProfileDTO, SessionUserDTO
from apps.engine.app.dtos.event_log_dto import GuardEvent, SessionStartEvent
from apps.engine.domain.value_objects.game_constants import SURVEY_SCORE_FIELDS

SECRET = "test-secret-withdraw"


def _footprint(db_session, user_id, attempt_ids, sub) -> dict[str, int]:
    """한 사용자가 남긴 행 수 — 탈퇴 전에 잡아 둔 user_id·attempt_ids로 센다(탈퇴 뒤에는 users 행으로 찾을 수 없다)."""
    db_session.expire_all()
    loop_ids = select(LoopOrm.id).where(LoopOrm.attempt_id.in_(attempt_ids))

    def count(model, *where) -> int:
        return db_session.scalar(select(func.count()).select_from(model).where(*where))

    return {
        "users": count(UserOrm, UserOrm.id == user_id),
        "attempts": count(AttemptOrm, AttemptOrm.id.in_(attempt_ids)),
        "loops": count(LoopOrm, LoopOrm.attempt_id.in_(attempt_ids)),
        "npc_states": count(NpcStateOrm, NpcStateOrm.loop_id.in_(loop_ids)),
        "nights": count(NightOrm, NightOrm.loop_id.in_(loop_ids)),
        "notes": count(NoteOrm, NoteOrm.attempt_id.in_(attempt_ids)),
        "rules": count(RuleOrm, RuleOrm.attempt_id.in_(attempt_ids)),
        "survey_votes": count(SurveyVoteOrm, SurveyVoteOrm.user_id == user_id),
        "events": count(EventLogOrm, EventLogOrm.session_id.in_(attempt_ids)),
        "guard_events": count(EventLogOrm, EventLogOrm.type == "guard",
                              EventLogOrm.payload["user_sub"].astext == sub),
    }


def _seed(db_session, sub: str):
    """sub 사용자의 판 하나 — 탈퇴가 지워야 할 모든 테이블에 한 줄 이상."""
    user = UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub=sub, email=f"{sub}@x", name=sub))
    attempt = AttemptRepository(db_session).create(None, user_id=user.id)
    loop = LoopRepository(db_session).create(LoopOrm(attempt_id=attempt.id, loop_n=1, budget_left=8),
                                             [NpcStateOrm(code="chaeyeon", name="채연")])
    NightRepository(db_session).create(NightOrm(loop_id=loop.id))
    NoteRepository(db_session).upsert(attempt.id, kind="fragment", text="트럭 소리.", loop_n=1,
                                      source_key=f"{loop.id}:scene-1")
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="user_choice", target="채연",
                                           when_beat=None, effect="enforce", action="쉰다", created_loop=1))
    SurveyVoteRepository(db_session).record(attempt.id, user.id, skipped=True,
                                            scores=dict.fromkeys(SURVEY_SCORE_FIELDS))
    events = EventLogRepository(db_session)
    events.record(attempt.id, SessionStartEvent(session=str(attempt.id), attempt_n=1, prior_cell_results=None))
    events.record(uuid.uuid4(), GuardEvent(layer="user_daily", reason="오늘은 여기까지", ip_hash="x", user_sub=sub))
    return user.id, [attempt.id]


# ── 저장소 ────────────────────────────────────────────────────


def test_delete_with_data_removes_every_row_of_one_user_only(db_session):
    """Review Focus 5 — 같은 테이블을 쓰는 다른 사용자의 판·평가·guard 이벤트는 그대로."""
    alice, bob = _seed(db_session, "alice"), _seed(db_session, "bob")
    alice_before, bob_before = _footprint(db_session, *alice, "alice"), _footprint(db_session, *bob, "bob")
    assert all(alice_before.values()), alice_before  # 지울 행이 모든 테이블에 있었다
    UserRepository(db_session).delete_with_data(alice[0], "alice")
    assert _footprint(db_session, *alice, "alice") == dict.fromkeys(alice_before, 0)
    assert _footprint(db_session, *bob, "bob") == bob_before


def test_delete_with_data_is_all_or_nothing(db_session, monkeypatch):
    """Review Focus 5 — 커밋이 실패하면 하나도 지워지지 않는다(한 트랜잭션)."""
    alice = _seed(db_session, "alice")
    before = _footprint(db_session, *alice, "alice")

    def failing_commit():
        raise RuntimeError("commit failed")

    monkeypatch.setattr(db_session, "commit", failing_commit)
    with pytest.raises(RuntimeError):
        UserRepository(db_session).delete_with_data(alice[0], "alice")
    monkeypatch.undo()
    assert _footprint(db_session, *alice, "alice") == before


# ── HTTP (실제 세션 쿠키) ─────────────────────────────────────


@pytest.fixture
def cookie_auth(db_session, monkeypatch):
    """실제 세션 쿠키 경로 — GUARD_AUTH=on. 속도 제한은 풀고 판 수 한도는 넉넉히 둔다."""
    from apps.engine.adapter.inbound.api.v1 import guards
    from core.matrix import grid_keymaker_secret_manager as cfg
    s = cfg.get_settings()
    for key, value in {"guard_auth": "on", "session_secret": SECRET, "ip_sessions_per_minute": 1000,
                       "ip_actions_per_minute": 1000, "user_daily_attempts": 10,
                       "frontend_base_url": "http://localhost:3500"}.items():
        monkeypatch.setattr(s, key, value)
    guards._BUCKETS.clear()
    yield s
    guards._BUCKETS.clear()


def _token(sub: str) -> str:
    return SessionTokenSigner(SECRET).issue(SessionUserDTO(sub=sub, email=f"{sub}@x", name=sub), 3600)


def _client(app, sub: str, db_session=None) -> TestClient:
    """세션 쿠키를 든 클라이언트. db_session을 주면 Google 로그인 콜백처럼 users 행을 먼저 만든다."""
    if db_session is not None:
        UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub=sub, email=f"{sub}@x", name=sub))
    client = TestClient(app)
    client.cookies.set("rd_session", _token(sub))
    return client


def _play_one_night(client) -> None:
    """실제 게임 한 밤 — 회차·NPC 상태·노트·밤·규칙·평가·이벤트가 실제 경로로 생긴다(빠뜨린 테이블을 잡는다)."""
    attempt_id = client.post("/sessions", json={}).json()["attempt_id"]
    loop_id = client.post(f"/sessions/{attempt_id}/loops").json()["loop_id"]
    for _ in range(6):
        client.post(f"/loops/{loop_id}/beats/next")
    night_id = client.post(f"/loops/{loop_id}/night/draft",
                           json={"tapped_note_ids": [], "free_text": "채연이 밥을 남겼다."}).json()["night_id"]
    assert client.post(f"/nights/{night_id}/submit").status_code == 200
    client.get(f"/nights/{night_id}/options")
    assert client.post(f"/nights/{night_id}/rule", json={"choice": "1"}).json()["ok"]
    assert client.post(f"/attempts/{attempt_id}/survey", json={"skipped": True}).status_code == 200


def _ids(db_session, sub: str):
    db_session.expire_all()
    user = db_session.scalar(select(UserOrm).where(UserOrm.google_sub == sub))
    return user.id, list(db_session.scalars(select(AttemptOrm.id).where(AttemptOrm.user_id == user.id)))


def test_withdraw_deletes_only_that_users_rows(cookie_auth, db_session, monkeypatch):
    from main import app
    with TestClient(app):  # lifespan(시드) 1회
        alice, bob = _client(app, "google-alice", db_session), _client(app, "google-bob", db_session)
        _play_one_night(alice)
        _play_one_night(bob)
        monkeypatch.setattr(cookie_auth, "user_daily_attempts", 1)
        assert alice.post("/sessions", json={}).status_code == 403  # guard 이벤트(user_sub) 한 줄씩
        assert bob.post("/sessions", json={}).status_code == 403
        alice_ids, bob_ids = _ids(db_session, "google-alice"), _ids(db_session, "google-bob")
        alice_before = _footprint(db_session, *alice_ids, "google-alice")
        bob_before = _footprint(db_session, *bob_ids, "google-bob")
        assert all(alice_before.values()), alice_before

        res = alice.delete("/api/v1/auth/me")

    assert res.status_code == 204
    set_cookie = res.headers["set-cookie"]
    assert 'rd_session=""' in set_cookie and "Max-Age=0" in set_cookie
    assert _footprint(db_session, *alice_ids, "google-alice") == dict.fromkeys(alice_before, 0)
    assert _footprint(db_session, *bob_ids, "google-bob") == bob_before


def test_withdraw_of_user_without_row_is_204(cookie_auth, db_session):
    from main import app
    with TestClient(app):
        res = _client(app, "google-ghost").delete("/api/v1/auth/me")
    assert res.status_code == 204
    assert 'rd_session=""' in res.headers["set-cookie"]


def test_withdraw_requires_login(cookie_auth):
    from main import app
    with TestClient(app) as client:
        assert client.delete("/api/v1/auth/me").status_code == 401


def test_withdrawn_session_cookie_cannot_recreate_user(cookie_auth, db_session):
    """사용자 결정 2026-10-16 — 탈퇴 뒤 남은(아직 서명이 유효한) 쿠키로 새 판을 요청해도 401이고 users 행이 다시 생기지 않는다."""
    from main import app
    with TestClient(app):
        alice = _client(app, "google-alice", db_session)
        assert alice.post("/sessions", json={}).status_code == 200
        assert alice.delete("/api/v1/auth/me").status_code == 204
        leftover = TestClient(app)  # 브라우저가 쿠키를 지우지 않았거나 누가 복사해 둔 경우
        leftover.cookies.set("rd_session", _token("google-alice"))
        res = leftover.post("/sessions", json={})
        active = leftover.get("/api/v1/me/attempts/active")
    assert res.status_code == 401 and res.json() == {"detail": "로그인이 필요하다"}
    assert active.status_code == 200 and active.json()["attempt"] is None  # 조회는 읽기만 — 행을 만들지 않는다
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(UserOrm).where(UserOrm.google_sub == "google-alice")) == 0
    assert db_session.scalar(select(func.count()).select_from(AttemptOrm)) == 0


def test_session_start_without_users_row_is_rejected_without_upsert():
    """유스케이스 단위 — users 행이 없으면 UnknownUser, upsert하지 않는다(판 수 조회 전에 멈춘다)."""
    from types import SimpleNamespace

    from apps.engine.app.use_cases.session_interactor import SessionInteractor, UnknownUser

    class Users:
        def __init__(self):
            self.upserts = []

        def get_by_sub(self, sub):
            return None

        def upsert_from_google(self, profile):
            self.upserts.append(profile.sub)
            return SimpleNamespace(id=uuid.uuid4())

    users = Users()
    uc = SessionInteractor(attempts=None, event_log=None, scenario=None, users=users,
                           user_daily_attempts=3, daily_attempt_cap=200)
    with pytest.raises(UnknownUser):
        uc.start(None, SessionUserDTO(sub="google-gone", email="", name=""), "iphash")
    assert users.upserts == []
```

`GUARD_AUTH=off`의 sub `"dev"`가 지금처럼 첫 판에서 행을 만드는지는 기존 `test_attempt_ownership.py::test_guard_auth_off_uses_dev_identity_for_ownership`이 확인한다. 이 task의 회귀 실행에 넣는다.

- [ ] **Step 2: 실패를 확인한다**

Run: `cd /home/kimchungsik/projects/com.remakeday/backend && .venv/bin/python -m pytest tests/engine/test_withdraw.py -q`
Expected: FAIL — `AttributeError: 'UserRepository' object has no attribute 'delete_with_data'`, HTTP 테스트는 405(`DELETE /api/v1/auth/me` 없음), `test_session_start_without_users_row_is_rejected_without_upsert`는 `ImportError: cannot import name 'UnknownUser'`

- [ ] **Step 3: 삭제 저장소를 만든다**

`user_repository.py`의 import 구역을 바꾼다:

```python
from __future__ import annotations

import uuid

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
from apps.engine.adapter.outbound.orms.game_state_orm import (
    AttemptOrm,
    LoopOrm,
    NightOrm,
    NoteOrm,
    NpcStateOrm,
    RuleOrm,
    SurveyVoteOrm,
)
from apps.engine.adapter.outbound.orms.user_orm import UserOrm
from apps.engine.app.dtos.auth_dto import GoogleProfileDTO
from apps.engine.domain.entities.user_entity import User
```

`UserRepository` 끝에 추가한다:

```python
    def delete_with_data(self, user_id: uuid.UUID, sub: str) -> None:
        """회원탈퇴 — 이 사용자의 판과 하위 행, 기록, 계정을 한 트랜잭션에서 지운다(설계 2026-10-16 §2.4).

        FK에 ON DELETE CASCADE가 없어 자식부터 지운다. 중간에 실패하면 전부 되돌리고 예외를 다시 던진다.
        평가는 user_id와 판 ID 어느 쪽으로든 이 사용자 것이면 지운다(구판 표의 user_id가 비어 있어도 남지 않게).
        """
        attempt_ids = select(AttemptOrm.id).where(AttemptOrm.user_id == user_id)
        loop_ids = select(LoopOrm.id).where(LoopOrm.attempt_id.in_(attempt_ids))
        statements = (
            delete(NightOrm).where(NightOrm.loop_id.in_(loop_ids)),
            delete(NpcStateOrm).where(NpcStateOrm.loop_id.in_(loop_ids)),
            delete(LoopOrm).where(LoopOrm.attempt_id.in_(attempt_ids)),
            delete(NoteOrm).where(NoteOrm.attempt_id.in_(attempt_ids)),
            delete(RuleOrm).where(RuleOrm.attempt_id.in_(attempt_ids)),
            delete(SurveyVoteOrm).where(or_(SurveyVoteOrm.user_id == user_id,
                                            SurveyVoteOrm.attempt_id.in_(attempt_ids))),
            delete(EventLogOrm).where(EventLogOrm.session_id.in_(attempt_ids)),
            delete(EventLogOrm).where(EventLogOrm.type == "guard", EventLogOrm.payload["user_sub"].astext == sub),
            delete(AttemptOrm).where(AttemptOrm.user_id == user_id),
            delete(UserOrm).where(UserOrm.id == user_id),
        )
        try:
            for statement in statements:
                self._s.execute(statement)
            self._s.commit()
        except Exception:
            self._s.rollback()
            raise
```

- [ ] **Step 4: 포트와 유스케이스를 넓힌다**

`user_repository_port.py` 전체:

```python
"""Driven Port — User 애그리거트 저장소."""

from __future__ import annotations

import uuid
from typing import Protocol

from apps.engine.app.dtos.auth_dto import GoogleProfileDTO
from apps.engine.domain.entities.user_entity import User


class UserRepositoryPort(Protocol):
    def upsert_from_google(self, profile: GoogleProfileDTO) -> User:
        """google_sub 기준으로 사용자를 만들거나 갱신하고, 저장된 엔티티를 돌려준다."""
        ...

    def get_by_sub(self, sub: str) -> User | None:
        """google_sub로 사용자를 찾는다. 없으면 None."""
        ...

    def delete_with_data(self, user_id: uuid.UUID, sub: str) -> None:
        """회원탈퇴 — 그 사용자의 판·기록·계정을 한 트랜잭션에서 지운다."""
        ...
```

`auth_use_case.py`의 `AuthUseCase`에 추가한다:

```python
    def withdraw(self, user: SessionUserDTO) -> None:
        """회원탈퇴 — 세션 사용자의 모든 데이터를 지운다. 이미 없는 사용자면 아무 일도 하지 않는다."""
        ...
```

`auth_interactor.py`의 `AuthInteractor`에서 `current_user` 아래에 추가한다:

```python
    def withdraw(self, user: SessionUserDTO) -> None:
        stored = self._users.get_by_sub(user.sub)
        if stored is None:
            return
        self._users.delete_with_data(stored.id, user.sub)
```

- [ ] **Step 5: 엔드포인트를 더한다**

`auth_router.py`의 import를 바꾼다:

```python
from fastapi.responses import JSONResponse, RedirectResponse, Response
```

`logout` 아래에 추가한다:

```python
@router.delete("/me", status_code=204)
def withdraw_me(request: Request, use_case: AuthUseCase = Depends(get_auth_use_case)) -> Response:
    """회원탈퇴 — 세션 쿠키의 사용자 데이터를 전부 지우고 쿠키를 삭제한다. 이미 지워진 사용자도 204."""
    user = use_case.current_user(request.cookies.get(SESSION_COOKIE))
    if user is None:
        raise HTTPException(status_code=401, detail="로그인되어 있지 않습니다")
    use_case.withdraw(user)
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response
```

`test_attempt_ownership.py`의 `PUBLIC_ROUTES`에서 Task 3이 넣은 두 줄 아래에 추가한다:

```python
    ("DELETE", "/api/v1/auth/me"),  # 회원탈퇴 — 세션 쿠키 사용자 자신(비로그인 401은 test_withdraw.py)
```

- [ ] **Step 6: 남은 쿠키로 users 행이 되살아나지 않게 한다**

`session_interactor.py` — `DailyCapReached` 클래스 아래에 추가한다:

```python
class UnknownUser(Exception):
    """세션은 유효한데 users 행이 없다(탈퇴한 계정에 남은 쿠키) — 행을 다시 만들지 않는다. 라우터가 401로 매핑한다."""
```

`_resolve_user_id`를 바꾼다:

```python
    def _resolve_user_id(self, user: SessionUserDTO) -> UUID:
        """users 행은 로그인할 때 만들어진다(Google 콜백·개발 계정 로그인). 여기서는 찾기만 한다.
        예외는 GUARD_AUTH=off의 sub "dev" — 로그인 단계가 없어 첫 판에서 행을 만든다."""
        existing = self._users.get_by_sub(user.sub)
        if existing is not None:
            return existing.id
        if user.sub != "dev":
            raise UnknownUser()
        return self._users.upsert_from_google(GoogleProfileDTO(sub="dev", email="dev@local", name="dev")).id
```

`game_router.py` — import 줄을 바꾼다:

```python
from apps.engine.app.use_cases.session_interactor import DailyCapReached, UnknownUser, UserDailyLimit
```

`_run`의 `except DailyCapReached:` 갈래 아래에 추가한다:

```python
    except UnknownUser as e:  # 탈퇴한 계정에 남은 쿠키 — 로그인 화면으로 돌려보낸다
        raise HTTPException(status_code=401, detail="로그인이 필요하다") from e
```

users 행 없이 `POST /sessions`를 부르던 테스트를 고친다. 제품 코드를 되돌려 맞추지 않는다.

`backend/tests/engine/conftest.py`의 `logged_in` 전체를 바꾼다(Google 로그인 콜백이 하는 일을 대신한다):

```python
@pytest.fixture
def logged_in(request, db_session):
    """`guards.require_user`를 로그인된 사용자로 오버라이드 — 로그인 때처럼 users 행도 만든다. 실패해도 finally에서 정리."""
    from main import app
    from apps.engine.adapter.inbound.api.v1 import guards
    from apps.engine.adapter.outbound.repositories.user_repository import UserRepository
    from apps.engine.app.dtos.auth_dto import GoogleProfileDTO, SessionUserDTO

    sub = getattr(request, "param", "tester")
    UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub=sub, email="t@x", name="t"))
    app.dependency_overrides[guards.require_user] = lambda: SessionUserDTO(sub=sub, email="t@x", name="t")
    guards._BUCKETS.clear()
    try:
        yield
    finally:
        app.dependency_overrides.pop(guards.require_user, None)
        guards._BUCKETS.clear()
```

`backend/tests/engine/test_attempt_ownership.py` 두 곳:
- `test_foreign_prior_attempt_is_ignored_like_missing` — `ids = _seed_game(db_session, "alice")` 바로 아래에 `UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub="bob", email="", name="bob"))  # bob도 로그인한 사용자다`를 넣는다.
- `test_dev_account_game_continues_from_another_session` — 시그니처를 `(real_auth, db_session)`으로 바꾸고, `google = TestClient(app)` 바로 위에 `UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub="google-carol", email="c@x", name="c"))  # Google 콜백이 만드는 행`을 넣는다.

- [ ] **Step 7: 테스트를 돌린다**

Run: `cd /home/kimchungsik/projects/com.remakeday/backend && .venv/bin/python -m pytest tests/engine/test_withdraw.py tests/engine/test_attempt_ownership.py tests/engine/test_dev_login.py tests/engine/test_guards.py tests/engine/test_e2e_flow.py tests/engine/test_survey_endpoint.py tests/engine/test_resume_api.py tests/pure/test_session_interactor_toctou.py -q && .venv/bin/lint-imports`
Expected: PASS(신규 7건 + 기존 — `test_guard_auth_off_uses_dev_identity_for_ownership` 포함), `Contracts: 4 kept, 0 broken`

위 목록 밖에서 `POST /sessions`가 401로 실패하는 테스트가 나오면, 그 테스트가 users 행 자동 생성에 기대고 있었는지 확인한다. 그렇다면 그 테스트에서 로그인 때처럼 행을 먼저 만들고, 고친 파일을 이 task의 커밋 목록에 더한다.

- [ ] **Step 8: 계약 문서를 맞춘다**

`docs/spec/api_contract.md`의 `### POST /api/v1/auth/dev/login` 절 바로 위에 추가한다:

```markdown
### DELETE /api/v1/auth/me — 회원탈퇴 (2026-10-16)

`rd_session` 쿠키의 사용자 한 명의 데이터를 **한 트랜잭션에서** 지우고 **204** + `rd_session` 쿠키 삭제. 쿠키가 없거나 무효면 401 `{"detail":"로그인되어 있지 않습니다"}`. 쿠키는 유효한데 users 행이 이미 없으면 그대로 204.

삭제 순서(FK에 CASCADE가 없다): `nights` → `npc_states` → `loops` → `notes`·`rules` → `survey_votes`(user_id 또는 판 ID) → `events`(session_id ∈ 그 사용자의 판 ID) → `events`(`type='guard'`, `payload.user_sub` = 그 사용자의 sub) → `attempts` → `users`. 중간에 실패하면 아무것도 지우지 않는다.

세션 토큰은 서명형이라 탈퇴 뒤에도 TTL 동안 검증을 통과한다. 하지만 users 행은 로그인할 때만 만들어지므로, 남은 쿠키로 `POST /sessions`를 부르면 **401** `{"detail":"로그인이 필요하다"}`이고 계정이 되살아나지 않는다(`GUARD_AUTH=off`의 sub `"dev"`만 첫 판에서 행을 만든다).
```

`### POST /sessions` 절 끝에 한 줄을 더한다:

```markdown
- 세션은 유효한데 users 행이 없으면(탈퇴한 계정의 남은 쿠키) 401 `{"detail":"로그인이 필요하다"}`. `GUARD_AUTH=off`의 sub `"dev"`는 첫 판에서 행을 만든다.
```

- [ ] **Step 9: 커밋**

```bash
cd /home/kimchungsik/projects/com.remakeday
git add backend/apps/engine/app/use_cases/session_interactor.py backend/apps/engine/adapter/inbound/api/v1/game_router.py backend/tests/engine/conftest.py backend/apps/engine/adapter/outbound/repositories/user_repository.py backend/apps/engine/app/ports/output/user_repository_port.py backend/apps/engine/app/ports/input/auth_use_case.py backend/apps/engine/app/use_cases/auth_interactor.py backend/apps/engine/adapter/inbound/api/v1/auth_router.py backend/tests/engine/test_withdraw.py backend/tests/engine/test_attempt_ownership.py docs/spec/api_contract.md
git commit -m "feat(auth): 회원탈퇴 DELETE /api/v1/auth/me — 한 트랜잭션 삭제·쿠키 삭제, 남은 쿠키로 계정이 되살아나지 않게"
```

커밋하지 않고 남긴 파일: 없음(시작 전 `git status --short`로 위 파일이 모두 깨끗한지 확인한다. `M`이던 파일이 있으면 커밋에서 빼고 여기에 적는다).

- [ ] **Step 10: A등급 task 검토**

sonnet 검토자에게 Task 4 diff를 맡긴다. 초점: 삭제 순서와 서브쿼리가 FK 위반 없이 한 트랜잭션인지, 다른 사용자 행을 건드릴 수 있는 조건(guard 이벤트 `user_sub` 비교, `user_id IS NULL` 구판)이 있는지, 비로그인·무효 쿠키·users 행 없음 세 경로, 테스트가 실제로 "모든 테이블"을 덮는지(`all(alice_before.values())`), `_resolve_user_id` 변경으로 로그인 직후 사용자가 401을 받는 경로가 있는지(Google 콜백·개발 계정 로그인이 행을 만든 뒤에만 `/sessions`가 불리는지), `GUARD_AUTH=off`의 `"dev"`가 그대로 동작하는지.

---

### Task 5: 프론트 계약 — 이어하기·탈퇴 타입과 클라이언트 (B, 개별 검토 생략)

**Files:**
- Modify: `frontend/contracts/api.ts`

**Interfaces:**
- Consumes: Task 3·4의 경로와 응답 모양
- Produces:
  - 타입 `ResumePhase`, `ResumeNight`, `ActiveAttemptRes`
  - `api.getActiveAttempt(): Promise<ActiveAttemptRes>`, `api.abandonActiveAttempt(): Promise<void>`, `api.withdraw(): Promise<void>`
  - `request()`가 `DELETE`를 받고, **204면 본문을 읽지 않고 `undefined`를 돌려준다**(지금은 `res.json()`이 빈 본문에서 던진다)

- [ ] **Step 1: Codex astra 지시문을 스크래치에 쓴다**

컨트롤러가 `<스크래치>/F1.prompt.md`에 아래를 그대로 쓴다(브라우저 규칙 포함):

````markdown
작업 디렉터리: /home/kimchungsik/projects/com.remakeday/frontend. 수정 파일은 contracts/api.ts 하나뿐이다.
브라우저·dev 서버를 띄우지 않는다. open·xdg-open 금지. 다른 파일의 미커밋 수정은 건드리지 않는다.

1) `// ── 판 종료 후 (P5) ───` 구역 바로 위에 추가:

```ts
// ── 이어하기 (2026-10-16) ─────────────────────────────

export type ResumePhase = "entry" | "day" | "night" | "score" | "god";

/** 이어하기 밤 데이터 — night_id가 없으면 정리 전(밤 글쓰기), 있으면 확인 화면부터. submit은 제출한 밤만 */
export interface ResumeNight {
  night_id: string | null;
  claims: string[];
  is_question: boolean[];
  /** 개입 화면 남은 신의 질문 — 새 밤은 3 */
  questions_left: number;
  submit: SubmitRes | null;
}

export interface ActiveAttemptRes {
  attempt: CreateSessionRes | null;
  resume_phase: ResumePhase | null;
  /** start_loop 응답과 같은 모양. 낮이면 현재 비트 장면, 그 밖의 단계는 장면이 빈 회차 정보. 회차가 없으면 null */
  loop: StartLoopRes | null;
  night: ResumeNight | null;
  /** 오늘 더 만들 수 있는 판 수 — 포기한 판도 센다 */
  today_remaining: number;
  daily_limit: number;
}
```

2) `request<T>`의 method 타입을 `"GET" | "POST" | "PATCH" | "DELETE"`로 바꾼다.

3) `request<T>`의 `if (!res.ok) { ... }` 블록 뒤, `return (await res.json()) as T;` 바로 앞에 추가:

```ts
  if (res.status === 204) return undefined as T; // 본문 없는 성공(포기·탈퇴)
```

4) `api` 객체의 `// 인증 — Google OAuth 세션` 구역 위에 추가:

```ts
  // 이어하기
  getActiveAttempt: () =>
    request<ActiveAttemptRes>("GET", "/api/v1/me/attempts/active"),
  abandonActiveAttempt: () =>
    request<void>("POST", "/api/v1/me/attempts/active/abandon"),
```

5) 같은 `// 인증` 구역의 `logout` 아래에 추가:

```ts
  withdraw: () => request<void>("DELETE", "/api/v1/auth/me"),
```
````

- [ ] **Step 2: Codex를 실행한다**

Run: `cd /home/kimchungsik/projects/com.remakeday/frontend && codex exec -m gpt-6-astra -s workspace-write "$(cat <스크래치>/F1.prompt.md)"`
Expected: `contracts/api.ts`만 바뀐다

- [ ] **Step 3: 컨트롤러가 확인한다**

Run: `cd /home/kimchungsik/projects/com.remakeday && git diff --stat -- frontend/contracts/api.ts && cd frontend && npx tsc --noEmit`
Expected: `api.ts` 한 파일, 타입 오류 없음

- [ ] **Step 4: 커밋**

```bash
cd /home/kimchungsik/projects/com.remakeday
git add frontend/contracts/api.ts
git commit -m "feat(contract): 이어하기·회원탈퇴 타입과 클라이언트, 204 응답 처리 (Codex astra)"
```

커밋하지 않고 남긴 파일: 없음(`frontend/contracts/api.ts`는 2026-10-16 기준 깨끗하다. 시작 전 다시 확인한다).

---

### Task 6: `/play` 진입 — 진행 중인 판 묻기·선택 화면·단계별 복원 (B)

**Files:**
- Create: `frontend/components/screens/ResumeChoiceScreen.tsx`
- Modify: `frontend/app/play/page.tsx`
- Modify: `frontend/components/screens/GodScreen.tsx` (선택 prop `initialRemaining`)
- Modify: `frontend/lib/useLeaveWarning.ts` (이탈 경고 문구를 이어하기에 맞게)
- Test: Task 8에서 헤드리스로(이탈 경고 문구 단언은 `tests/leave-warning.cjs`, Task 8에서 고친다)

**Interfaces:**
- Consumes: Task 5의 `api.getActiveAttempt`·`api.abandonActiveAttempt`, 타입 `ActiveAttemptRes`·`ResumePhase`
- Produces:
  - `<ResumeChoiceScreen todayRemaining dailyLimit busy onResume onRestart />`
  - `/play` 동작: 조회 → `attempt: null`이면 `createSession` / `resume_phase: "entry"`이고 `loop: null`이면 그 판을 그대로 쓰고 진입 화면 / `?resume=1`이면 바로 복원 / 그 밖은 선택 화면. 조회가 허들(401·403·503·429)이면 GuardScreen, 그 밖의 실패(404·네트워크·5xx)면 예전처럼 `createSession`
  - 복원 단계: `entry`→진입, `day`→낮(아침 화면 건너뜀), `night`→`night_id` 없으면 밤 글쓰기·있으면 확인 화면, `score`→점수, `god`→신의 개입
  - `GodScreen`의 `initialRemaining?: number`(기본 3)
  - Task 8이 쓰는 버튼 이름: "이어하기", "다시 시작하기"
  - 이탈 경고 `returnValue`: `"지금 나가도 다시 들어오면 이어서 할 수 있습니다. 쓰던 글과 오늘 대화 말풍선은 남지 않습니다."`

**이탈 경고는 남긴다(사용자 결정 3 검토, 2026-10-16).** 이어하기가 생겨 판 자체는 사라지지 않는다. 그래도 나가면 잃는 것이 있다. 밤 글쓰기 칸에 쓰던 글은 `night/draft`를 보내기 전까지 서버에 없다. 오늘 대화 말풍선과 열려 있던 원숭이손 제안 팝업도 회차 단위 이어하기로는 되살아나지 않는다(스펙 §5). 그래서 경고는 그대로 켜 두고, 판이 사라진다는 틀린 말만 고친다. 최신 브라우저는 `returnValue` 문구를 화면에 보이지 않고 기본 확인창만 띄운다. 문구는 그 기본 확인창을 띄우는 신호이자 코드상의 기록이다.

`frontend/app/play/page.tsx`·`GodScreen.tsx`·`lib/useLeaveWarning.ts`는 2026-10-16 기준 미커밋 수정이 없다. `EntryScreen.tsx`·`DayScreen.tsx` 등은 미커밋 수정이 있으므로 이 task는 건드리지 않는다.

- [ ] **Step 1: Codex astra 지시문을 스크래치에 쓴다**

컨트롤러가 `<스크래치>/F2.prompt.md`에 아래를 그대로 쓴다:

````markdown
작업 디렉터리: /home/kimchungsik/projects/com.remakeday/frontend.
수정 파일: app/play/page.tsx, components/screens/GodScreen.tsx, lib/useLeaveWarning.ts. 새 파일: components/screens/ResumeChoiceScreen.tsx.
브라우저·dev 서버를 띄우지 않는다. open·xdg-open 금지. 다른 파일(특히 미커밋 수정이 있는 EntryScreen.tsx·DayScreen.tsx)은 건드리지 않는다.
`?resume=1`은 useSearchParams가 아니라 효과 안에서 `window.location.search`로 읽는다(Suspense 경계가 필요 없게).

## 1. 새 파일 components/screens/ResumeChoiceScreen.tsx

```tsx
"use client";

import { ENTRY_IMAGE } from "@/lib/imageMap";

/**
 * 진행 중인 판이 있을 때 — 이어하기 / 다시 시작하기 (설계 2026-10-16 §3.1). 진입 화면과 같은 배경·버튼.
 * 다시 시작하기는 그날 판 수를 한 칸 쓴다(포기한 판도 센다). 남은 판이 없으면 끈다.
 */
export function ResumeChoiceScreen({
  todayRemaining,
  dailyLimit,
  busy,
  onResume,
  onRestart,
}: {
  todayRemaining: number;
  dailyLimit: number;
  busy: boolean;
  onResume: () => void;
  onRestart: () => void;
}) {
  const canRestart = todayRemaining > 0;
  return (
    <div className="relative flex min-h-dvh w-full flex-col items-center justify-center overflow-hidden bg-void py-6 text-paper sm:py-8">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={ENTRY_IMAGE}
        alt=""
        decoding="async"
        className="pointer-events-none fixed inset-0 h-full w-full scale-[1.35] object-cover object-center opacity-40"
      />
      <div className="relative z-10 w-full max-w-md px-4">
        <section aria-busy={busy} className="w-full border border-paper/40 bg-void/80 p-5 text-left">
          <p className="text-lg leading-relaxed">진행 중인 판이 있다.</p>
          <button
            type="button"
            onClick={onResume}
            disabled={busy}
            className="mt-5 w-full border border-paper px-6 py-2 text-lg hover:bg-paper hover:text-void disabled:opacity-40"
          >
            이어하기
          </button>
          <button
            type="button"
            onClick={onRestart}
            disabled={busy || !canRestart}
            className="mt-3 w-full border border-paper px-6 py-2 text-lg hover:bg-paper hover:text-void disabled:opacity-40"
          >
            다시 시작하기
          </button>
          <p className="mt-2 text-base opacity-70">
            {canRestart
              ? `오늘 남은 판 ${todayRemaining}/${dailyLimit} · 다시 시작하면 1회가 차감됩니다`
              : "오늘은 더 시작할 수 없습니다"}
          </p>
        </section>
      </div>
    </div>
  );
}
```

## 2. components/screens/GodScreen.tsx

props 구조 분해에서 `initialSuggestedQuestions,` 다음 줄에 `initialRemaining = 3,`를 넣고, props 타입의 `initialSuggestedQuestions: string[];` 다음에:

```ts
  /** 이어하기 — 이 밤에 남은 질문 수. 새 밤은 3 */
  initialRemaining?: number;
```

`const [remaining, setRemaining] = useState(3);`을 `const [remaining, setRemaining] = useState(initialRemaining);`로 바꾼다. 다른 곳은 바꾸지 않는다.

## 3. app/play/page.tsx

(a) import — 타입 import에 `ActiveAttemptRes`, `ResumePhase`를 알파벳 순서로 더하고, 화면 import 묶음에 추가:

```ts
import { ResumeChoiceScreen } from "@/components/screens/ResumeChoiceScreen";
```

(b) `runCreateSession` 함수를 아래 `runGuarded`로 바꾸고, 기존 호출 두 곳(진입 효과·`retry`)의 이름도 `runGuarded`로 바꾼다:

```ts
/**
 * API 호출 하나를 감싸 401/403/503/429 허들을 GuardScreen으로 돌린다 (판 생성·이어하기 조회 공용).
 * onOtherFailure가 있으면 허들이 아닌 실패(404·네트워크·5xx)에 토스트 대신 그것을 부른다.
 */
function runGuarded<T>(
  run: (
    fn: () => Promise<T>,
    onOk: (value: T) => void,
    onFail?: (status: number) => boolean,
  ) => Promise<boolean>,
  call: () => Promise<T>,
  onOk: (value: T) => void,
  setGuard: (guard: { kind: GuardKind; retryAfter?: number }) => void,
  onOtherFailure?: () => void,
) {
  let captured: ApiError | null = null;
  return run(
    () =>
      call().catch((e: unknown) => {
        captured = e instanceof ApiError ? e : null;
        throw e;
      }),
    onOk,
    () => {
      const kind = captured ? guardKindFor(captured) : null;
      if (!kind) {
        if (!onOtherFailure) return false;
        onOtherFailure();
        return true;
      }
      setGuard({ kind, retryAfter: captured?.retryAfter });
      return true; // 실패 배너 억제 — GuardScreen이 대신 보인다
    },
  );
}
```

(c) `guardKindFor` 함수 아래(모듈 수준)에 추가:

```ts
/** 이어하기 단계 → 여는 화면. night는 정리를 이미 시작했으면(night_id) 확인 화면부터 — 밤 글쓰기를 다시 보내면 409다. */
const RESUME_SCREEN: Record<ResumePhase, (res: ActiveAttemptRes) => Phase> = {
  entry: () => "entry",
  day: () => "day",
  night: (res) => (res.night?.night_id ? "confirm" : "night"),
  score: () => "score",
  god: () => "god",
};
```

(d) `night` state 타입에 선택 필드를 더한다:

```ts
  const [night, setNight] = useState<{
    nightId: string;
    claims: string[];
    isQuestion: boolean[];
    /** 이어하기로 연 개입 단계 — 이미 쓴 신의 질문을 뺀 남은 횟수 */
    questionsLeft?: number;
  } | null>(null);
```

(e) `guard` state 아래에 추가:

```ts
  const [resumeChoice, setResumeChoice] = useState<ActiveAttemptRes | null>(null);
  const restarting = useRef(false);
```

(f) `useLeaveWarning` 위 주석 `// 진입·회고(clear)를 제외한 진행 중 — 새로고침·탭 닫기 확인. 이어받기는 없다.`를
`// 진입·회고(clear)를 제외한 진행 중 — 새로고침·탭 닫기 확인. 다시 들어오면 이어하기로 그 회차부터 연다.`로 바꾼다.

(g) 기존 진입 효과(`// 진입 시 세션 생성 — entry_lines는 이 응답에서 온다` 주석부터 그 useEffect 끝까지)를 아래로 바꾼다:

```ts
  // 이어하기 — 응답의 판·회차·밤으로 state를 채우고 그 단계 화면으로 간다. 대화 말풍선은 되살리지 않는다(dayLog 빈 배열).
  const hydrate = (res: ActiveAttemptRes) => {
    if (!res.attempt || !res.resume_phase) return;
    observationsRequest.current += 1;
    setAttempt(res.attempt);
    setLoop(res.loop ?? null);
    setActiveRules(res.loop?.active_rules ?? []);
    setDayLog([]);
    const resumed = res.night;
    setNight(resumed?.night_id ? {
      nightId: resumed.night_id,
      claims: resumed.claims,
      isQuestion: resumed.is_question,
      questionsLeft: resumed.questions_left,
    } : null);
    setSubmitResult(resumed?.submit ?? null);
    setResumeChoice(null);
    setPhase(RESUME_SCREEN[res.resume_phase](res));
  };

  // 진입 — 진행 중인 판이 있으면 이어하기/다시 시작하기를 고르고, 없으면 새 판을 만든다 (설계 2026-10-16 §3.1).
  // 조회 API가 없거나(구 백엔드) 허들 아닌 이유로 실패하면 예전처럼 새 판을 만든다 — 허들만 GuardScreen.
  const booted = useRef(false);
  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    const autoResume = new URLSearchParams(window.location.search).get("resume") === "1";
    const createFresh = () => {
      void runGuarded(sessionAction.run, () => api.createSession({}), setAttempt, setGuard);
    };
    void runGuarded(
      sessionAction.run,
      () => api.getActiveAttempt(),
      (res) => {
        if (!res.attempt) createFresh();
        else if (res.resume_phase === "entry" && !res.loop) setAttempt(res.attempt); // 회차 없는 판은 묻지 않고 그대로
        else if (autoResume) hydrate(res);
        else setResumeChoice(res);
      },
      setGuard,
      createFresh,
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 다시 시작하기 — 진행 중인 판을 포기하고 1회차 새 판(prior 없음). 두 번 눌러도 포기는 한 번만.
  const restart = () => {
    if (restarting.current) return;
    restarting.current = true;
    void sessionAction.run(
      () => api.abandonActiveAttempt(),
      () => {
        setResumeChoice(null);
        void runGuarded(sessionAction.run, () => api.createSession({}), setAttempt, setGuard);
      },
      () => {
        restarting.current = false; // 포기 요청이 실패하면 다시 누를 수 있다 — 토스트는 그대로 뜬다
        return false;
      },
    );
  };
```

(h) 렌더 — 진입 화면 블록을 아래 두 블록으로 바꾼다(EntryScreen props는 그대로):

```tsx
      {phase === "entry" && resumeChoice && !guard && (
        <ResumeChoiceScreen
          todayRemaining={resumeChoice.today_remaining}
          dailyLimit={resumeChoice.daily_limit}
          busy={sessionAction.busy}
          onResume={() => hydrate(resumeChoice)}
          onRestart={restart}
        />
      )}

      {phase === "entry" && !resumeChoice && !guard && (
        <EntryScreen
          lines={attempt?.entry_lines ?? null}
          priorCells={attempt?.prior_cell_results ?? null}
          loopN={loop?.loop_n ?? 1}
          loading={loopAction.busy}
          onBegin={startLoop}
        />
      )}
```

(i) `<GodScreen` props에 `initialSuggestedQuestions={submitResult.suggested_questions}` 다음 줄로 추가:

```tsx
          initialRemaining={night.questionsLeft}
```

그 밖의 줄(startLoop·retry의 state 초기화, 다른 화면 블록)은 바꾸지 않는다.

## 4. lib/useLeaveWarning.ts

파일 위 주석 `/** 판 진행 중 새로고침·탭 닫기·사이트 이탈 시 브라우저 확인창. 이어받기는 없다. */`를 아래로 바꾼다:

```ts
/**
 * 판 진행 중 새로고침·탭 닫기·사이트 이탈 시 브라우저 확인창.
 * 판은 이어하기로 다시 열 수 있지만, 보내지 않은 밤 글·오늘 대화 말풍선·열린 팝업은 되살아나지 않아 경고는 남긴다.
 */
```

`event.returnValue = "나가면 이 판은 사라집니다";`를 아래로 바꾼다:

```ts
      event.returnValue = "지금 나가도 다시 들어오면 이어서 할 수 있습니다. 쓰던 글과 오늘 대화 말풍선은 남지 않습니다.";
```

그 밖의 줄은 바꾸지 않는다.
````

- [ ] **Step 2: Codex를 실행한다**

Run: `cd /home/kimchungsik/projects/com.remakeday/frontend && codex exec -m gpt-6-astra -s workspace-write "$(cat <스크래치>/F2.prompt.md)"`
Expected: 네 파일만 바뀐다

- [ ] **Step 3: 컨트롤러가 확인한다**

Run: `cd /home/kimchungsik/projects/com.remakeday && git status --short frontend/app/play frontend/components/screens/GodScreen.tsx frontend/components/screens/ResumeChoiceScreen.tsx frontend/lib/useLeaveWarning.ts && cd frontend && npx tsc --noEmit`
Expected: `M app/play/page.tsx`, `M GodScreen.tsx`, `M lib/useLeaveWarning.ts`, `?? ResumeChoiceScreen.tsx`, 타입 오류 없음. diff에서 `runCreateSession` 이름이 남지 않았는지, `retry`의 state 초기화가 그대로인지 본다.

- [ ] **Step 4: 커밋**

```bash
cd /home/kimchungsik/projects/com.remakeday
git add frontend/app/play/page.tsx frontend/components/screens/GodScreen.tsx frontend/components/screens/ResumeChoiceScreen.tsx frontend/lib/useLeaveWarning.ts
git commit -m "feat(ui): /play 진입 때 진행 중인 판 이어하기·다시 시작하기, 단계별 복원, 이탈 경고 문구 (Codex astra)"
```

커밋하지 않고 남긴 파일: 없음(시작 전 네 파일이 깨끗했는지 장부로 확인한다. 그새 `M`이던 파일은 빼고 여기에 적는다).

---

### Task 7: `/mypage`와 랜딩 마이페이지 버튼 (A — 회원탈퇴 화면)

**Files:**
- Create: `frontend/app/mypage/page.tsx`
- Modify: `frontend/app/page.tsx` (**미커밋 수정 있음 — 보존**)
- Test: Task 8에서 헤드리스로

**Interfaces:**
- Consumes: Task 5의 `api.getMe`(기존)·`api.getActiveAttempt`·`api.withdraw`, `ApiError`
- Produces:
  - `/mypage`: 진입 시 `getMe()` 401이면 `router.replace("/")`. 진행 중인 판이 있을 때만 링크 "이어하기"(`/play?resume=1`). 버튼 "회원탈퇴" → 같은 화면에 확인 단계("모든 플레이 기록이 즉시 삭제되며 되돌릴 수 없습니다" + "탈퇴"/"취소"). 탈퇴 성공 → `window.location.assign("/")`
  - 랜딩: 로그인 상태면 "로그아웃" 위에 링크 "마이페이지"(`/mypage`)

마이페이지의 "이어하기"는 Next `Link`라 클라이언트 이동이다. `/play`는 효과 안에서 `window.location.search`를 읽으므로 이동 뒤 URL이 이미 바뀌어 있어야 한다 — Task 8의 `mypage 이어하기 opens the resumed day`가 이것을 확인한다. 그 검사가 선택 화면에서 멈추면 링크를 `<a href="/play?resume=1">`(전체 이동)로 바꾼다.

`frontend/app/page.tsx`의 미커밋 수정(로그인↔로그아웃 버튼, `preloadImages`)이 이 task의 전제다. HEAD의 랜딩에는 `loggedIn` state가 없다. 그 수정을 되돌리거나 다시 쓰지 않는다.

- [ ] **Step 1: Codex astra 지시문을 스크래치에 쓴다**

컨트롤러가 `<스크래치>/F3.prompt.md`에 아래를 그대로 쓴다:

````markdown
작업 디렉터리: /home/kimchungsik/projects/com.remakeday/frontend.
새 파일: app/mypage/page.tsx. 수정 파일: app/page.tsx — 이 파일에는 커밋하지 않은 수정이 이미 있다. 그 수정을 지우거나 다시 쓰지 말고 아래 두 군데만 고친다.
브라우저·dev 서버를 띄우지 않는다. open·xdg-open 금지. 브라우저 confirm() 금지.

## 1. 새 파일 app/mypage/page.tsx

```tsx
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/contracts/api";
import { ENTRY_IMAGE } from "@/lib/imageMap";

const BUTTON = "w-full border border-paper px-6 py-2 text-center text-lg hover:bg-paper hover:text-void disabled:opacity-40";

/**
 * 마이페이지 — 진행 중인 판 이어하기와 회원탈퇴만 둔다 (설계 2026-10-16 §3.2).
 * 탈퇴 확인은 브라우저 confirm() 대신 같은 화면에 펼친다.
 */
export default function MyPage() {
  const router = useRouter();
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [hasActive, setHasActive] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [withdrawing, setWithdrawing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    void (async () => {
      try {
        await api.getMe();
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 401) {
          router.replace("/");
          return;
        }
        setLoadError("잠시 뒤 다시 시도해 주세요.");
        setLoaded(true);
        return;
      }
      const active = await api.getActiveAttempt().catch(() => null);
      if (!alive) return;
      setHasActive(Boolean(active?.attempt));
      setLoaded(true);
    })();
    return () => {
      alive = false;
    };
  }, [router]);

  const withdraw = async () => {
    if (withdrawing) return;
    setWithdrawing(true);
    setError(null);
    try {
      await api.withdraw();
      window.location.assign("/");
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "탈퇴하지 못했습니다. 잠시 뒤 다시 시도해 주세요.");
      setWithdrawing(false);
    }
  };

  return (
    <main className="relative flex min-h-dvh w-full flex-col items-center justify-center overflow-hidden bg-void px-4 py-10 text-paper">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={ENTRY_IMAGE}
        alt=""
        decoding="async"
        className="pointer-events-none fixed inset-0 h-full w-full scale-[1.35] object-cover object-center opacity-40"
      />
      <section className="relative z-10 flex w-full max-w-md flex-col gap-4 border border-paper/40 bg-void/80 p-5">
        <h1 className="text-2xl">마이페이지</h1>
        {!loaded && <p className="opacity-60">불러오는 중…</p>}
        {loadError && <p role="alert">{loadError}</p>}
        {loaded && !loadError && (
          <>
            {hasActive && (
              <Link href="/play?resume=1" className={BUTTON}>
                이어하기
              </Link>
            )}
            {!confirming ? (
              <button type="button" onClick={() => setConfirming(true)} className={BUTTON}>
                회원탈퇴
              </button>
            ) : (
              <div role="group" aria-label="회원탈퇴 확인" className="border border-paper/60 p-4">
                <p className="text-lg leading-relaxed">모든 플레이 기록이 즉시 삭제되며 되돌릴 수 없습니다</p>
                <div className="mt-4 flex gap-3">
                  <button type="button" onClick={() => void withdraw()} disabled={withdrawing} aria-busy={withdrawing} className={BUTTON}>
                    탈퇴
                  </button>
                  <button type="button" onClick={() => setConfirming(false)} disabled={withdrawing} className={BUTTON}>
                    취소
                  </button>
                </div>
              </div>
            )}
            {error && <p role="alert" className="text-orange">{error}</p>}
          </>
        )}
        <Link href="/" className="text-center text-base opacity-70 underline">
          처음 화면으로
        </Link>
      </section>
    </main>
  );
}
```

## 2. app/page.tsx — 두 군데만

(a) 로그인/로그아웃 `<button ref={loginRef} ...>` 바로 위(그 위 주석 `{/* 같은 버튼을 유지해야 ... */}`보다도 위)에 추가:

```tsx
        {loggedIn && (
          <Link
            href="/mypage"
            className="entry-line mt-10 w-36 border border-paper py-2 text-center text-lg hover:bg-paper hover:text-void"
            style={{ animationDelay: "3.8s" }}
          >
            마이페이지
          </Link>
        )}
```

(b) 그 로그인/로그아웃 버튼의 className에서 `mt-10`을 로그아웃 상태에서만 빼도록 바꾼다(위 여백은 첫 버튼이 갖는다). 즉

`className="entry-line mt-10 w-36 border border-paper py-2 text-center text-lg hover:bg-paper hover:text-void disabled:opacity-50"`

을

``className={`entry-line ${loggedIn ? "" : "mt-10 "}w-36 border border-paper py-2 text-center text-lg hover:bg-paper hover:text-void disabled:opacity-50`}``

으로. 버튼 요소·ref·onAnimationStart·animationDelay(4.2s)·문구는 그대로 둔다(같은 버튼을 유지해야 페이드인이 다시 돌지 않는다). 지연 순서는 마이페이지 3.8s → 로그아웃 4.2s → 시작 4.6s.
````

- [ ] **Step 2: Codex를 실행한다**

Run: `cd /home/kimchungsik/projects/com.remakeday/frontend && codex exec -m gpt-6-astra -s workspace-write "$(cat <스크래치>/F3.prompt.md)"`
Expected: `app/mypage/page.tsx` 생성, `app/page.tsx` 두 군데 수정

- [ ] **Step 3: 컨트롤러가 확인한다**

Run: `cd /home/kimchungsik/projects/com.remakeday && git diff frontend/app/page.tsx && cd frontend && npx tsc --noEmit`
Expected: 타입 오류 없음. `git diff`에 기존 미커밋 수정(로그인↔로그아웃 버튼, `preloadImages`, `decoding`·`fetchPriority`)이 그대로 남아 있고, 그 위에 마이페이지 링크와 className 한 줄만 더해졌다.

- [ ] **Step 4: 커밋 — 새 파일만**

새 파일만 커밋한다:

```bash
cd /home/kimchungsik/projects/com.remakeday
git add frontend/app/mypage/page.tsx
git commit -m "feat(ui): 마이페이지 — 이어하기와 회원탈퇴 확인 단계 (Codex astra)"
```

`frontend/app/page.tsx`는 커밋 정책(Global Constraints)대로 **수정만 하고 커밋하지 않는다.** 미커밋 수정이 이미 섞인 파일이기 때문이다. 게다가 마이페이지 링크가 쓰는 `loggedIn` state와 버튼은 그 미커밋 수정에만 있고, 그 수정은 추적되지 않는 `frontend/lib/preloadImages.ts`를 import한다.

커밋하지 않고 남긴 파일: `frontend/app/page.tsx`(랜딩 마이페이지 링크 + className 한 줄. 기존 미커밋 수정 위에 얹혔다).

- [ ] **Step 5: A등급 task 검토**

sonnet 검토자에게 Task 7 diff를 맡긴다. 초점: 확인 단계 없이 탈퇴가 나갈 수 있는 경로(키보드·두 번 누르기), 탈퇴 실패 시 버튼이 다시 살아나는지, 401 리다이렉트가 다른 오류와 섞이지 않는지, 랜딩 기존 미커밋 수정이 보존됐는지.

---

### Task 8: 헤드리스 시나리오 — 이어하기·마이페이지·탈퇴, 기존 스크립트에 조회 응답 추가 (B)

**Files:**
- Create: `frontend/tests/resume-mypage.cjs`
- Modify(가짜 API에 조회 응답 한 갈래 추가): `frontend/tests/guard.cjs`, `gameplay-clarity.cjs`, `leave-warning.cjs`, `npc-followup.cjs`, `voice-playback.cjs`, `clear-survey.cjs` — 미커밋 수정 없음 / `connected-investigation.cjs`, `day-screen-vn-shots.cjs`, `day-screen-vn.cjs`, `five-loop-flow.cjs`, `scene-illustrations.cjs`, `voice-transitions.cjs` — **미커밋 수정 있음, 보존**
- `frontend/tests/dev-login.cjs`는 실서버 대상이라 고치지 않는다

**Interfaces:**
- Consumes: Task 6의 화면 동작과 버튼 이름, Task 7의 `/mypage` 문구, `vn-helpers.cjs`의 `line`·`readAll`·`expectBudget`
- Produces: `node tests/resume-mypage.cjs` → `PASS resume-mypage`

이제 `/play`는 마운트되자마자 `GET /api/v1/me/attempts/active`를 부른다. 기존 가짜 API 스크립트는 모르는 경로를 오류로 기록하거나 끊으므로, 각 스크립트가 "진행 중인 판 없음"을 돌려줘야 지금처럼 `/sessions`로 이어진다.

- [ ] **Step 1: Codex astra 지시문을 스크래치에 쓴다**

컨트롤러가 `<스크래치>/F4.prompt.md`에 아래를 그대로 쓴다:

````markdown
작업 디렉터리: /home/kimchungsik/projects/com.remakeday/frontend. 테스트 스크립트만 고친다. 실행하지 않는다(샌드박스가 Chrome을 막는다 — 실행은 컨트롤러).
브라우저·dev 서버를 띄우지 않는다. open·xdg-open 금지. 아래 파일 중 일부에는 커밋하지 않은 수정이 있다 — 지우거나 다시 쓰지 말고 한 갈래만 더한다.

## 1. 기존 스크립트 12개에 조회 응답 한 갈래

대상: tests/guard.cjs, gameplay-clarity.cjs, leave-warning.cjs, npc-followup.cjs, voice-playback.cjs, clear-survey.cjs,
connected-investigation.cjs, day-screen-vn-shots.cjs, day-screen-vn.cjs, five-loop-flow.cjs, scene-illustrations.cjs, voice-transitions.cjs.
dev-login.cjs는 건드리지 않는다.

각 파일의 page.route 처리기에서 `/sessions` 갈래보다 앞에, 그 파일의 기존 응답 방식(같은 CORS 헤더·같은 body 변수)대로
`GET /api/v1/me/attempts/active` → 200 본문

```js
{ attempt: null, resume_phase: null, loop: null, night: null, today_remaining: 3, daily_limit: 3 }
```

을 돌려주는 갈래 하나를 더한다. 예 — guard.cjs의 CASES 처리기:

```js
        if (url.pathname === '/api/v1/me/attempts/active') {
          return route.fulfill({
            json: { attempt: null, resume_phase: null, loop: null, night: null, today_remaining: 3, daily_limit: 3 },
            headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' },
          });
        }
```

guard.cjs의 testRestartGuard처럼 `if (p === '/sessions') {...} else if ...` 사슬인 곳은 맨 앞에
`if (p === '/api/v1/me/attempts/active') body = { attempt: null, resume_phase: null, loop: null, night: null, today_remaining: 3, daily_limit: 3 };`
를 두고 기존 `if`를 `else if`로 잇는다. 한 파일에 page.route가 여러 개면 /play를 여는 처리기마다 넣는다. 그 밖의 줄은 바꾸지 않는다.

## 1-1. tests/leave-warning.cjs — 이탈 경고 문구 단언

Task 6이 경고 문구를 "지금 나가도 다시 들어오면 이어서 할 수 있습니다. 쓰던 글과 오늘 대화 말풍선은 남지 않습니다."로 바꿨다. 이 파일은 옛 문구를 단언한다. 두 군데를 고친다.
- 1행 주석 `// 판 진행 중 beforeunload 이탈 경고. 진입·회고에서는 없다. 이어받기는 없다.` → `// 판 진행 중 beforeunload 이탈 경고. 진입·회고에서는 없다. 판은 이어하기로 다시 열 수 있다.`
- `assert.match(String(listenersOnDay.value), /사라집니다/);` → `assert.match(String(listenersOnDay.value), /다시 들어오면 이어서 할 수 있습니다/);`

## 2. 새 파일 tests/resume-mypage.cjs

```js
// 이어하기·마이페이지·회원탈퇴 (설계 2026-10-16) — 가짜 API만 쓴다(백엔드 불필요).
// NODE_PATH=/home/kimchungsik/projects/cloud.localhostdaegu/frontend/node_modules node tests/resume-mypage.cjs
// 헤드리스 브라우저 하나를 이 스크립트가 띄우고 끝에 닫는다. 프론트 dev 서버(3500)는 컨트롤러가 미리 띄운다.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { line, readAll, expectBudget } = require('./vn-helpers.cjs');

const BASE = 'http://localhost:3500';
const CORS = { 'access-control-allow-origin': BASE, 'access-control-allow-credentials': 'true' };
const ATTEMPT = { attempt_id: 'resume', attempt_n: 1, entry_lines: ['세계가 이상하다.'], prior_cell_results: null };
const NPCS = [{ code: 'chaeyeon', name: '채연', mood: 'calm', uttered: false }];
const SUBMIT = {
  total: 40, passed: false, loop_n: 2, world_outcome: 'truck', is_final: false, closed_by: null, cells: null,
  cookie: null, intervention_available: true, ending_lines: null, truth_reveal: null, cell_feedback: null,
  wrong_claim_count: 0, accepted_claims: [], empty_cells: ['cause', 'motive'], night_clue: null, suggested_questions: [],
};
const NIGHT = { night_id: 'resume-night', claims: ['채연이 밥을 남겼다.'], is_question: [false], questions_left: 3, submit: null };

function loopShell(fields = {}) {
  return {
    loop_id: 'resume-loop', loop_n: 2, morning_text: '7시 12분. 눈을 뜬다.', damage_level: 1, budget_left: 4,
    beat: 3, beat_title: '', narration: '', broadcast: null, illustrations: [], aftermath: null,
    ambient: null, note_found: null, observations: [], active_rules: [], lines: [], ...fields,
  };
}

const DAY_LOOP = loopShell({
  beat_title: '정오 배급', narration: '쟁반이 돈다. 채연이 쟁반을 밀어낸다.',
  lines: [line('scene', '쟁반이 돈다.'), line('action', '채연이 쟁반을 밀어낸다.')],
});
const NONE = { attempt: null, resume_phase: null, loop: null, night: null, today_remaining: 3, daily_limit: 3 };

function snapshot(phase, fields = {}) {
  return { attempt: ATTEMPT, resume_phase: phase, loop: null, night: null, today_remaining: 2, daily_limit: 3, ...fields };
}

/** 페이지 하나와 가짜 API — calls에 "메서드 경로"가 순서대로 쌓인다. 끝나면 이 페이지만 닫는다. */
async function withPage(browser, { active, me = 200, failActive = false }, run) {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  page.setDefaultTimeout(15000);
  const calls = [];
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.route('**/*', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.port !== '8500') return route.continue();
    if (request.method() === 'OPTIONS') {
      return route.fulfill({ status: 204, headers: { ...CORS, 'access-control-allow-methods': 'GET,POST,PATCH,DELETE', 'access-control-allow-headers': 'content-type' } });
    }
    const key = `${request.method()} ${url.pathname}`;
    calls.push(key);
    const reply = (status, json) => (json === undefined
      ? route.fulfill({ status, body: '', headers: CORS })
      : route.fulfill({ status, json, headers: CORS }));
    if (key === 'GET /api/v1/me/attempts/active') return failActive ? reply(404, { detail: 'Not Found' }) : reply(200, active);
    if (key === 'POST /api/v1/me/attempts/active/abandon') return reply(204);
    if (key === 'POST /sessions') return reply(200, { ...ATTEMPT, attempt_id: 'fresh' });
    if (key === 'GET /api/v1/auth/me') {
      return me === 200 ? reply(200, { sub: 'g-1', email: 'a@x', name: 'a', picture: '' }) : reply(401, { detail: '로그인되어 있지 않습니다' });
    }
    if (key === 'DELETE /api/v1/auth/me') return reply(204);
    if (url.pathname.endsWith('/observations')) return reply(200, { observations: [] });
    if (url.pathname.endsWith('/npcs')) return reply(200, { npcs: NPCS });
    if (url.pathname.endsWith('/night/previous')) return reply(200, { previous_answer: null });
    if (url.pathname.endsWith('/notes')) return reply(200, { notes: [] });
    errors.push(`Unexpected API: ${key}`);
    return route.abort();
  });
  try {
    await run(page, calls);
    assert.deepEqual(errors, [], 'no page errors or unexpected API calls');
  } finally {
    await page.close();
  }
}

const CHECKS = [
  ['choice screen shows cost, 이어하기 opens the day', (browser) => withPage(browser, { active: snapshot('day', { loop: DAY_LOOP }) }, async (page, calls) => {
    await page.goto(`${BASE}/play`);
    await page.getByText('오늘 남은 판 2/3 · 다시 시작하면 1회가 차감됩니다', { exact: true }).waitFor();
    await page.getByRole('button', { name: '이어하기', exact: true }).click();
    await expectBudget(page, 4);
    await readAll(page);
    await page.getByText('쟁반이 돈다.', { exact: false }).first().waitFor();
    assert.ok(!calls.includes('POST /sessions'), '이어하기는 새 판을 만들지 않는다');
  })],
  ['no games left disables restart', (browser) => withPage(browser, { active: snapshot('day', { loop: DAY_LOOP, today_remaining: 0 }) }, async (page) => {
    await page.goto(`${BASE}/play`);
    await page.getByText('오늘은 더 시작할 수 없습니다', { exact: true }).waitFor();
    assert.equal(await page.getByRole('button', { name: '다시 시작하기', exact: true }).isDisabled(), true);
    assert.equal(await page.getByRole('button', { name: '이어하기', exact: true }).isDisabled(), false);
  })],
  ['restartOnceOnDoubleClick', (browser) => withPage(browser, { active: snapshot('day', { loop: DAY_LOOP }) }, async (page, calls) => {
    await page.goto(`${BASE}/play`);
    await page.getByRole('button', { name: '다시 시작하기', exact: true }).dblclick();
    await page.getByRole('button', { name: '시작', exact: true, disabled: false }).waitFor({ state: 'visible' });
    assert.deepEqual(calls.filter((c) => c.startsWith('POST ')), ['POST /api/v1/me/attempts/active/abandon', 'POST /sessions']);
  })],
  ['?resume=1 skips the choice screen', (browser) => withPage(browser, { active: snapshot('day', { loop: DAY_LOOP }) }, async (page) => {
    await page.goto(`${BASE}/play?resume=1`);
    await expectBudget(page, 4);
    assert.equal(await page.getByRole('button', { name: '다시 시작하기', exact: true }).count(), 0);
  })],
  ['attempt without loops is reused silently', (browser) => withPage(browser, { active: snapshot('entry') }, async (page, calls) => {
    await page.goto(`${BASE}/play`);
    await page.getByRole('button', { name: '시작', exact: true, disabled: false }).waitFor({ state: 'visible' });
    assert.equal(await page.getByRole('button', { name: '이어하기', exact: true }).count(), 0);
    assert.ok(!calls.includes('POST /sessions'), '회차 없는 판은 묻지 않고 그대로 쓴다');
  })],
  ['fallsBackWhenActiveLookupFails', (browser) => withPage(browser, { active: NONE, failActive: true }, async (page, calls) => {
    await page.goto(`${BASE}/play`);
    await page.getByRole('button', { name: '시작', exact: true, disabled: false }).waitFor({ state: 'visible' });
    assert.ok(calls.includes('POST /sessions'), '조회 API가 없으면 예전처럼 새 판');
  })],
  ['night draft resumes at the confirm screen', (browser) => withPage(browser, { active: snapshot('night', { loop: loopShell({ beat: 6 }), night: NIGHT }) }, async (page) => {
    await page.goto(`${BASE}/play?resume=1`);
    await page.getByRole('button', { name: '맞아, 제출한다', exact: true }).waitFor();
    await page.getByText('채연이 밥을 남겼다.', { exact: false }).first().waitFor();
  })],
  ['god resumes with remaining questions', (browser) => withPage(browser, { active: snapshot('god', { loop: loopShell({ beat: 6 }), night: { ...NIGHT, questions_left: 1, submit: SUBMIT } }) }, async (page) => {
    await page.goto(`${BASE}/play?resume=1`);
    await page.getByText('남은 질문 1', { exact: true }).waitFor();
  })],
  ['landing shows 마이페이지 when logged in', (browser) => withPage(browser, { active: NONE }, async (page) => {
    await page.goto(`${BASE}/`);
    const link = page.getByRole('link', { name: '마이페이지', exact: true });
    await link.waitFor();
    assert.equal(await link.getAttribute('href'), '/mypage');
  })],
  ['mypage 이어하기 opens the resumed day', (browser) => withPage(browser, { active: snapshot('day', { loop: DAY_LOOP }) }, async (page) => {
    await page.goto(`${BASE}/mypage`);
    const resume = page.getByRole('link', { name: '이어하기', exact: true });
    await resume.waitFor();
    assert.equal(await resume.getAttribute('href'), '/play?resume=1');
    await resume.click();
    await expectBudget(page, 4);
    assert.equal(await page.getByRole('button', { name: '다시 시작하기', exact: true }).count(), 0);
  })],
  ['mypage withdraw needs the inline confirm step', (browser) => withPage(browser, { active: NONE }, async (page, calls) => {
    await page.goto(`${BASE}/mypage`);
    await page.getByRole('button', { name: '회원탈퇴', exact: true }).click();
    await page.getByText('모든 플레이 기록이 즉시 삭제되며 되돌릴 수 없습니다', { exact: true }).waitFor();
    assert.equal(await page.getByRole('link', { name: '이어하기', exact: true }).count(), 0, '진행 중인 판이 없으면 이어하기가 없다');
    await page.getByRole('button', { name: '취소', exact: true }).click();
    assert.equal(await page.getByRole('button', { name: '탈퇴', exact: true }).count(), 0);
    assert.ok(!calls.includes('DELETE /api/v1/auth/me'), '취소하면 탈퇴 요청이 없다');
    await page.getByRole('button', { name: '회원탈퇴', exact: true }).click();
    await page.getByRole('button', { name: '탈퇴', exact: true }).click();
    await page.waitForURL(`${BASE}/`);
    assert.equal(calls.filter((c) => c === 'DELETE /api/v1/auth/me').length, 1);
  })],
  ['mypage without login goes back to landing', (browser) => withPage(browser, { active: NONE, me: 401 }, async (page) => {
    await page.goto(`${BASE}/mypage`);
    await page.waitForURL(`${BASE}/`);
  })],
];

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  try {
    for (const [name, check] of CHECKS) {
      await check(browser);
      console.log(`ok - ${name}`);
    }
    console.log('PASS resume-mypage');
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
```
````

- [ ] **Step 2: Codex를 실행한다**

Run: `cd /home/kimchungsik/projects/com.remakeday/frontend && codex exec -m gpt-6-astra -s workspace-write "$(cat <스크래치>/F4.prompt.md)"`
Expected: 새 파일 1개, 기존 스크립트 12개에 갈래 하나씩, `leave-warning.cjs` 단언 한 줄과 주석 한 줄

- [ ] **Step 3: 컨트롤러가 diff를 확인한다**

Run: `cd /home/kimchungsik/projects/com.remakeday && git diff --stat -- frontend/tests && git diff -- frontend/tests | grep -c "api/v1/me/attempts/active"`
Expected: 12개 파일 수정, 조회 갈래가 처리기 수만큼(12 이상). 미커밋 수정이 있던 6개 파일은 기존 hunk가 그대로다(`git diff` 줄 수가 늘기만 했는지 본다).

- [ ] **Step 4: 헤드리스 실행은 Task 9에서 컨트롤러가 한다**

- [ ] **Step 5: 커밋 — 새 파일과 깨끗했던 파일만**

새 스크립트와, 이 task 전에 미커밋 수정이 없던 6개만 올린다:

```bash
cd /home/kimchungsik/projects/com.remakeday
git add frontend/tests/resume-mypage.cjs frontend/tests/guard.cjs frontend/tests/gameplay-clarity.cjs frontend/tests/leave-warning.cjs frontend/tests/npc-followup.cjs frontend/tests/voice-playback.cjs frontend/tests/clear-survey.cjs
git commit -m "test(headless): 이어하기 선택 화면·단계 복원·마이페이지 탈퇴 확인, 기존 가짜 API에 진행 중인 판 없음 응답"
```

미커밋 수정이 있던 6개는 커밋 정책대로 수정만 하고 커밋하지 않는다. 부분 스테이징(`git add -p`·`git apply --cached`)도 하지 않는다.

커밋하지 않고 남긴 파일: `frontend/tests/connected-investigation.cjs`, `frontend/tests/day-screen-vn-shots.cjs`, `frontend/tests/day-screen-vn.cjs`, `frontend/tests/five-loop-flow.cjs`, `frontend/tests/scene-illustrations.cjs`, `frontend/tests/voice-transitions.cjs`(각각 조회 응답 갈래 하나. 기존 미커밋 수정 위에 얹혔다). 이 갈래들이 커밋되지 않았으므로, 커밋된 트리만으로는 이 6개 스크립트가 새 `/play`에서 실패한다는 점을 최종 보고에 적는다.

---

### Task 9: 전체 검증·리뷰·기록 (컨트롤러)

**Files:**
- Modify: `docs/jekyll.md` (**미커밋 수정 있음**), `docs/superpowers/plans/2026-10-16-resume-mypage-withdraw.md`(결과 절)

- [ ] **Step 1: 백엔드 전체와 계층 계약**

Run: `cd /home/kimchungsik/projects/com.remakeday/backend && .venv/bin/python -m pytest -q && .venv/bin/lint-imports`
Expected: 실패 0(신규 103건 포함 — Task 1의 75건, Task 2의 6건, Task 3의 15건, Task 4의 7건), `Contracts: 4 kept, 0 broken`

- [ ] **Step 2: 타입 검사**

Run: `cd /home/kimchungsik/projects/com.remakeday/frontend && npx tsc --noEmit`
Expected: 오류 없음

- [ ] **Step 3: 프론트 dev 서버(3500)를 브라우저 없이 준비한다**

먼저 `curl -s -o /dev/null -w '%{http_code}' http://localhost:3500/`로 이미 떠 있는지 본다. 200이면 그대로 쓰고 끄지 않는다(이 작업이 띄운 게 아니다). 응답이 없으면 백그라운드로 `cd /home/kimchungsik/projects/com.remakeday/frontend && npm run dev`를 띄우고(명령에 `open`·`xdg-open`을 붙이지 않는다), Monitor로 `curl`이 200을 줄 때까지 기다린다. 백엔드(8500)는 띄우지 않는다 — 헤드리스는 가짜 API다.

- [ ] **Step 4: 헤드리스를 한 번에 하나씩 돌린다**

각 스크립트를 앞 프로세스가 끝난 뒤 다음 것을 돌린다:

Run: `cd /home/kimchungsik/projects/com.remakeday/frontend && NODE_PATH=/home/kimchungsik/projects/cloud.localhostdaegu/frontend/node_modules node tests/resume-mypage.cjs`
Expected: `ok - ...` 12줄, `PASS resume-mypage`

이어서 같은 방식으로 `guard`, `gameplay-clarity`, `leave-warning`, `npc-followup`, `voice-playback`, `voice-transitions`, `clear-survey`, `connected-investigation`, `scene-illustrations`, `five-loop-flow`, `day-screen-vn`.
Expected: 전부 통과(`dev-login`은 실서버 대상이라 돌리지 않는다). 실패하면 이번 변경 전에도 실패하던 것인지(`git stash` 금지 — 대신 실패 메시지가 조회 API·선택 화면과 관련 있는지)로 가른다.

- [ ] **Step 5: 이 작업이 띄운 dev 서버만 끈다**

Step 3에서 띄웠을 때만, **별도 명령으로** `fuser -k 3500/tcp`. 시작 명령과 같은 줄에 두지 않는다.

- [ ] **Step 6: 최종 전체 리뷰 (A 포함 → opus 1회)**

opus 검토자에게 Task 1~8 전체 diff를 맡긴다. 초점:
- Review Focus 다섯 줄이 각 테스트로 실제로 묶였는지
- `GET /active`가 낮 단계에서 `execute_scene`을 부르는데 쓰기가 정말 없는지(동시 요청 중 첫 실행이 아직 커밋 전일 때 포함)
- 탈퇴가 다른 사용자 행을 건드릴 조건, 한 트랜잭션 보장
- 선택 화면·`?resume=1`·포기→새 판 흐름에서 판 수가 두 번 차감되거나 남의 판이 잡히는 경로
- 남은 위험(아래 "실행 메모")이 보고에 들어갔는지

Critical이면 수정 1회 + 범위 재검토. 결과를 장부에 적는다.

- [ ] **Step 7: 기록**

`docs/jekyll.md`에는 미커밋 수정이 이미 있다. 오늘(2026-10-16) 항목을 맨 위에 더하되 **커밋하지 않는다**(커밋 정책). 이 계획 파일 끝에 "결과" 절을 더해 커밋한다. 결과 절에는 통과 수치, 리뷰 결과, 그리고 Task 1~9에서 모은 "커밋하지 않고 남긴 파일" 전체 목록(`frontend/app/page.tsx`, 헤드리스 6개, `docs/jekyll.md`)을 적는다:

```bash
cd /home/kimchungsik/projects/com.remakeday
git add docs/superpowers/plans/2026-10-16-resume-mypage-withdraw.md
git commit -m "docs: 이어하기·마이페이지·회원탈퇴 검증 결과"
```

배포·서버 재기동은 하지 않는다(프로젝트 종료).

---

## 실행 메모

- **멱등성 확인 결과(계획 작성 때).** 소원 4종·모든 인물 설명·출처 규칙 × 1~5회차 × 피해 0·3 × 1~6비트를 스크래치로 돌려, 같은 비트 재실행이 기록·세계 효과를 하나도 더하지 않음을 봤다. 다만 재실행은 이미 실행한 규칙의 설명(statement)·부작용(paw_effect) 줄을 대사창에 다시 넣지 않는다 — Task 2가 공개 기록에서 되살린다.
- **`scored` 상태는 지금 엔진이 쓰지 않는다.** 제출하면 곧바로 `intervention`(1~4회차) 또는 판 종료(5회차)다. 그래서 점수 화면에서 나가도 다시 들어오면 신의 개입부터 열린다(점수·결말 전환은 건너뜀). 5회차 제출 뒤에는 판이 닫혀 이어할 것이 없다.
- **`night_draft`는 확인 화면부터 연다.** 스펙 표는 둘 다 "밤 답안 작성"이지만, 정리를 이미 시작한 밤에 밤 글쓰기를 다시 보내면 409라 확인 화면이 같은 단계의 다음 칸이다.
- **"/5" 대신 `daily_limit`.** 하루 한도는 설정값(`USER_DAILY_ATTEMPTS`, 코드 기본 3)이다. 응답에 `daily_limit`을 더해 화면이 `{남은}/{한도}`를 쓴다.
- **진행 중인 판은 "최신 판이 active일 때만"(사용자 결정 2026-10-16).** 최신 판을 포기하거나 끝내면 오래된 active 판(이 기능 전에 닫히지 않은 판)이 남아 있어도 `attempt: null`이다. 오래된 판은 DB에 active로 남지만 화면에는 다시 나오지 않는다. 일괄 정리는 범위 밖이다.
- **남는 위험(범위 밖, 보고 대상).** ① 다른 탭에 열려 있던 포기한 판은 회차 시작만 막히고 그 회차의 발화·비트·밤은 계속 받는다(그 경로들은 판 상태를 보지 않는다). ② 모델 호출 중 별도 연결로 쓰는 하네스 감사 이벤트는 탈퇴 직후에 들어와 남을 수 있다.
- **사용자 결정으로 해소한 것.** 탈퇴 뒤 남은 세션 쿠키로 users 행이 되살아나던 경로는 Task 4가 막는다(`_resolve_user_id`가 행을 만들지 않고 401). 남은 쿠키는 TTL 동안 서명 검증을 통과하지만, 판 생성은 401, 진행 중인 판 조회는 `attempt: null`이다. 이탈 경고 문구는 Task 6이 고치고 경고 자체는 남긴다(근거는 Task 6).
- **커밋되지 않는 변경.** 커밋 정책 때문에 `frontend/app/page.tsx`(랜딩 마이페이지 링크)와 헤드리스 6개의 조회 응답 갈래, `docs/jekyll.md` 기록은 작업 트리에만 남는다. 커밋된 트리만 보면 랜딩에 마이페이지 링크가 없고, 그 6개 스크립트는 새 `/play`에서 실패한다.
- **되돌리기.** DB 스키마 변경이 없다. 백엔드 커밋을 되돌리면 새 경로가 사라지고, 프론트는 조회 실패(404) 때 예전처럼 새 판을 만든다.
