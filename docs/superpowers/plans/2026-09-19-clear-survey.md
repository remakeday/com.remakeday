# 클리어 화면 플레이 평가 수집 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 5회차를 마친 플레이어에게 다섯 항목 별점을 받아 `survey_votes` 테이블에 쌓는다. 건너뛰기도 기록한다.

**Architecture:** 새 테이블 하나(`survey_votes`)가 판과 1:0..1로 붙는다. 기존 `owned` 라우터에 엔드포인트 하나를 더해 판 소유자만 투표할 수 있게 하고, 판당 한 표는 DB 유니크 제약이 보장한다. 클리어 화면은 결말 → 설문 → 회고·다시 시작 3단계가 된다.

**Tech Stack:** FastAPI, SQLAlchemy 2.0(Mapped/mapped_column), alembic, PostgreSQL, Next.js App Router, Tailwind, Playwright(헤드리스)

**Spec:** `docs/superpowers/specs/2026-09-19-clear-survey-design.md`

## Global Constraints

- **등급 A** — DB 스키마 변경 + 공개 API 추가. task마다 구현+검토, 마지막에 전체 리뷰.
- **제출 선언 전에 끝나야 한다.** 선언 뒤에는 앱 코드를 고칠 수 없다.
- **프론트엔드(`frontend/`)는 Codex astra가 맡는다** (`codex exec -m gpt-6-astra -s workspace-write`). 백엔드·문서는 Claude 서브에이전트.
- **Codex 샌드박스는 Chrome을 띄우지 못한다.** 헤드리스 실행은 컨트롤러가 한다(`NODE_PATH=<스크래치>/pw/node_modules`).
- **전체 pytest는 테스트 DB를 공유한다.** 서브에이전트는 해당 파일만 돌리고, 전체는 컨트롤러가 마지막에 한 번.
- **외래키는 걸지 않는다.** 이 저장소 관행(`attempts.user_id`도 인덱스만).
- 점수 항목 다섯 개의 컬럼명은 `fun`·`novelty`·`ai_agency`·`polish`·`recommend`로 고정한다. 화면 문구는 재미·몰입도 / 참신성 / AI 활용 체감 / 완성도 / 추천 의향.
- 서버 재기동은 포트로 끊고(`fuser -k 8500/tcp`) 시작은 **별도 명령**으로. 같은 줄에 두면 셸이 죽는다.

---

### Task 1: 테이블 · ORM · 리포지토리

**Files:**
- Create: `backend/alembic/versions/2026_09_19_0900-a1b2c3d4e5f6_survey_votes.py`
- Modify: `backend/apps/engine/adapter/outbound/orms/game_state_orm.py` (import 줄, 파일 끝에 클래스 추가)
- Modify: `backend/apps/engine/adapter/outbound/repositories/game_repository.py` (파일 끝에 클래스 추가)
- Test: `backend/tests/engine/test_survey_votes.py`

**Interfaces:**
- Consumes: `Base`(`core.matrix.grid_oracle_database_manager`), `save_game_changes`(같은 리포지토리 모듈)
- Produces:
  - `SurveyVoteOrm` — 테이블 `survey_votes`
  - `SurveyVoteRepository(session)` with `record(attempt_id: uuid.UUID, user_id: uuid.UUID | None, *, skipped: bool, scores: dict[str, int | None]) -> bool` — 첫 표면 True, 이미 있으면 False

- [ ] **Step 1: 실패하는 테스트를 쓴다**

```python
"""클리어 화면 플레이 평가 — 판당 한 표, 부분 응답, 건너뛰기 기록."""

import uuid

import pytest
from sqlalchemy import text

from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    SurveyVoteRepository,
)

FULL = {"fun": 5, "novelty": 4, "ai_agency": 5, "polish": 3, "recommend": 4}
EMPTY = {"fun": None, "novelty": None, "ai_agency": None, "polish": None, "recommend": None}


def _attempt(db_session, user_id=None):
    return AttemptRepository(db_session).create(None, user_id=user_id)


def test_first_vote_is_recorded(db_session):
    user_id = uuid.uuid4()
    attempt = _attempt(db_session, user_id)
    repo = SurveyVoteRepository(db_session)
    assert repo.record(attempt.id, user_id, skipped=False, scores=FULL) is True
    row = db_session.execute(
        text("select fun, recommend, skipped, user_id from survey_votes where attempt_id = :a"),
        {"a": attempt.id},
    ).one()
    assert (row.fun, row.recommend, row.skipped, row.user_id) == (5, 4, False, user_id)


def test_second_vote_on_same_attempt_is_ignored(db_session):
    attempt = _attempt(db_session)
    repo = SurveyVoteRepository(db_session)
    assert repo.record(attempt.id, None, skipped=False, scores=FULL) is True
    assert repo.record(attempt.id, None, skipped=False, scores={**FULL, "fun": 1}) is False
    kept = db_session.execute(
        text("select fun from survey_votes where attempt_id = :a"), {"a": attempt.id}
    ).scalar_one()
    assert kept == 5  # 첫 표가 유효하다


def test_partial_answer_keeps_blanks_as_null(db_session):
    attempt = _attempt(db_session)
    partial = {**EMPTY, "fun": 4, "recommend": 2}
    assert SurveyVoteRepository(db_session).record(attempt.id, None, skipped=False, scores=partial) is True
    row = db_session.execute(
        text("select fun, novelty, recommend from survey_votes where attempt_id = :a"),
        {"a": attempt.id},
    ).one()
    assert (row.fun, row.novelty, row.recommend) == (4, None, 2)


def test_skip_is_recorded_as_its_own_row(db_session):
    attempt = _attempt(db_session)
    assert SurveyVoteRepository(db_session).record(attempt.id, None, skipped=True, scores=EMPTY) is True
    row = db_session.execute(
        text("select skipped, fun from survey_votes where attempt_id = :a"), {"a": attempt.id}
    ).one()
    assert (row.skipped, row.fun) == (True, None)


@pytest.mark.parametrize("bad", [0, 6, -1])
def test_score_outside_one_to_five_is_rejected_by_the_database(db_session, bad):
    attempt = _attempt(db_session)
    with pytest.raises(Exception):
        SurveyVoteRepository(db_session).record(
            attempt.id, None, skipped=False, scores={**EMPTY, "fun": bad}
        )
    db_session.rollback()


def test_skipped_row_may_not_carry_scores(db_session):
    attempt = _attempt(db_session)
    with pytest.raises(Exception):
        SurveyVoteRepository(db_session).record(
            attempt.id, None, skipped=True, scores={**EMPTY, "fun": 3}
        )
    db_session.rollback()


def test_unskipped_row_needs_at_least_one_score(db_session):
    attempt = _attempt(db_session)
    with pytest.raises(Exception):
        SurveyVoteRepository(db_session).record(attempt.id, None, skipped=False, scores=EMPTY)
    db_session.rollback()
```

- [ ] **Step 2: 실패를 확인한다**

Run: `cd backend && .venv/bin/python -m pytest tests/engine/test_survey_votes.py -q`
Expected: FAIL — `ImportError: cannot import name 'SurveyVoteRepository'`

- [ ] **Step 3: 마이그레이션을 만든다**

`backend/alembic/versions/2026_09_19_0900-a1b2c3d4e5f6_survey_votes.py`:

```python
"""survey_votes

클리어 화면 플레이 평가 — 판당 한 표(유니크), 항목별 1~5점 부분 응답 허용,
건너뛰기도 행으로 남긴다. 기존 테이블은 건드리지 않는다.

Revision ID: a1b2c3d4e5f6
Revises: fbec9419f894
Create Date: 2026-09-19 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fbec9419f894'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SCORES = ("fun", "novelty", "ai_agency", "polish", "recommend")
_FILLED = "num_nonnulls(" + ", ".join(_SCORES) + ")"


def upgrade() -> None:
    op.create_table(
        "survey_votes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("skipped", sa.Boolean(), nullable=False, server_default=sa.false()),
        *(sa.Column(name, sa.SmallInteger(), nullable=True) for name in _SCORES),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("attempt_id", name="uq_survey_votes_attempt"),
        *(
            sa.CheckConstraint(
                f"{name} IS NULL OR ({name} BETWEEN 1 AND 5)", name=f"ck_survey_votes_{name}"
            )
            for name in _SCORES
        ),
        sa.CheckConstraint(
            f"(skipped AND {_FILLED} = 0) OR (NOT skipped AND {_FILLED} > 0)",
            name="ck_survey_votes_skip_consistency",
        ),
    )
    op.create_index("ix_survey_votes_user_id", "survey_votes", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_survey_votes_user_id", table_name="survey_votes")
    op.drop_table("survey_votes")
```

- [ ] **Step 4: ORM을 더한다**

`game_state_orm.py`의 import에 `CheckConstraint`와 `SmallInteger`를 넣는다(알파벳 순서 유지: `Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint, Uuid, func`). 파일 끝에 추가:

```python
_SURVEY_SCORES = ("fun", "novelty", "ai_agency", "polish", "recommend")
_SURVEY_FILLED = "num_nonnulls(" + ", ".join(_SURVEY_SCORES) + ")"


class SurveyVoteOrm(Base):
    """클리어 화면 플레이 평가 — 판당 한 표. 건너뛰기도 행으로 남겨 참가율을 잰다."""

    __tablename__ = "survey_votes"
    __table_args__ = (
        UniqueConstraint("attempt_id", name="uq_survey_votes_attempt"),
        *(
            CheckConstraint(f"{name} IS NULL OR ({name} BETWEEN 1 AND 5)", name=f"ck_survey_votes_{name}")
            for name in _SURVEY_SCORES
        ),
        CheckConstraint(
            f"(skipped AND {_SURVEY_FILLED} = 0) OR (NOT skipped AND {_SURVEY_FILLED} > 0)",
            name="ck_survey_votes_skip_consistency",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    skipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fun: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    novelty: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    ai_agency: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    polish: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    recommend: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 5: 리포지토리를 더한다**

`game_repository.py` 맨 위 import에 `SurveyVoteOrm`을 추가하고(`game_state_orm`에서 가져오는 기존 줄에 붙인다), `from sqlalchemy.dialects.postgresql import insert as pg_insert`를 더한 뒤 파일 끝에 추가:

```python
SURVEY_SCORE_FIELDS = ("fun", "novelty", "ai_agency", "polish", "recommend")


class SurveyVoteRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def record(
        self,
        attempt_id: uuid.UUID,
        user_id: uuid.UUID | None,
        *,
        skipped: bool,
        scores: dict[str, int | None],
    ) -> bool:
        """첫 표만 남긴다 — 이미 표가 있으면 아무것도 바꾸지 않고 False.

        새로고침·더블클릭으로 같은 표가 두 번 와도 오류를 내지 않는다.
        """
        stmt = (
            pg_insert(SurveyVoteOrm)
            .values(
                id=uuid.uuid4(),
                attempt_id=attempt_id,
                user_id=user_id,
                skipped=skipped,
                **{name: scores.get(name) for name in SURVEY_SCORE_FIELDS},
            )
            .on_conflict_do_nothing(index_elements=["attempt_id"])
        )
        inserted = self._s.execute(stmt).rowcount
        save_game_changes(self._s)
        return inserted > 0
```

- [ ] **Step 6: 테스트가 통과하는지 확인한다**

Run: `cd backend && .venv/bin/python -m pytest tests/engine/test_survey_votes.py -q`
Expected: PASS (7 passed)

테스트 DB가 마이그레이션이 아니라 메타데이터로 만들어지면 ORM만으로 통과한다. 그렇더라도 마이그레이션은 실서버용으로 반드시 있어야 한다.

- [ ] **Step 7: 마이그레이션을 실제 DB에 적용해 본다**

Run: `cd backend && .venv/bin/alembic upgrade head && .venv/bin/alembic current`
Expected: `a1b2c3d4e5f6 (head)`

Run: `docker exec pigfarm-db psql -U pigfarm -d pigfarm -Atc "\d survey_votes"`
Expected: 컬럼 10개, `uq_survey_votes_attempt` 유니크, `ix_survey_votes_user_id` 인덱스

- [ ] **Step 8: 커밋**

```bash
git add backend/alembic/versions backend/apps/engine/adapter/outbound backend/tests/engine/test_survey_votes.py
git commit -m "feat(survey): survey_votes 테이블·ORM·리포지토리 — 판당 한 표, 부분 응답, 건너뛰기 기록"
```

---

### Task 2: 인터랙터 · 엔드포인트 · 계약

**Files:**
- Create: `backend/apps/engine/app/use_cases/survey_interactor.py`
- Modify: `backend/apps/engine/dependencies/engine_dependency.py` (파일 끝에 `get_survey_interactor`)
- Modify: `backend/apps/engine/adapter/inbound/api/v1/game_router.py` (요청 모델 + `owned` 엔드포인트)
- Modify: `docs/spec/api_contract.md`
- Modify: `frontend/contracts/api.ts` (타입 + 클라이언트 한 줄)
- Test: `backend/tests/engine/test_survey_endpoint.py`

**Interfaces:**
- Consumes: Task 1의 `SurveyVoteRepository.record(...) -> bool`, `AttemptRepository.get(attempt_id) -> AttemptOrm | None`
- Produces:
  - `SurveyInteractor(attempts, votes)` with `record(attempt_id: uuid.UUID, *, skipped: bool, scores: dict[str, int | None]) -> dict` → `{"recorded": bool}`
  - `POST /attempts/{attempt_id}/survey`
  - 프론트: `api.sendSurvey(attemptId, req)`, 타입 `SurveyReq`·`SurveyRes`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

```python
"""플레이 평가 엔드포인트 — 소유자만, 판당 한 번, 범위 밖 점수는 422."""

import uuid

from fastapi.testclient import TestClient

FULL = {"skipped": False, "fun": 5, "novelty": 4, "ai_agency": 5, "polish": 3, "recommend": 4}


def _own_attempt(c) -> str:
    return c.post("/sessions", json={}).json()["attempt_id"]


def test_owner_can_vote_once(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        attempt_id = _own_attempt(c)
        first = c.post(f"/attempts/{attempt_id}/survey", json=FULL)
        assert first.status_code == 200 and first.json() == {"recorded": True}
        again = c.post(f"/attempts/{attempt_id}/survey", json={**FULL, "fun": 1})
        assert again.status_code == 200 and again.json() == {"recorded": False}


def test_skip_is_accepted_without_scores(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        attempt_id = _own_attempt(c)
        r = c.post(f"/attempts/{attempt_id}/survey", json={"skipped": True})
        assert r.status_code == 200 and r.json() == {"recorded": True}


def test_partial_answer_is_accepted(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        attempt_id = _own_attempt(c)
        r = c.post(f"/attempts/{attempt_id}/survey", json={"skipped": False, "fun": 4})
        assert r.status_code == 200 and r.json() == {"recorded": True}


def test_no_score_without_skip_is_treated_as_skip(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        attempt_id = _own_attempt(c)
        r = c.post(f"/attempts/{attempt_id}/survey", json={"skipped": False})
        assert r.status_code == 200 and r.json() == {"recorded": True}


def test_score_outside_range_is_422(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        attempt_id = _own_attempt(c)
        assert c.post(f"/attempts/{attempt_id}/survey", json={**FULL, "fun": 6}).status_code == 422
        assert c.post(f"/attempts/{attempt_id}/survey", json={**FULL, "fun": 0}).status_code == 422


def test_stranger_attempt_is_404(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        assert c.post(f"/attempts/{uuid.uuid4()}/survey", json=FULL).status_code == 404
```

- [ ] **Step 2: 실패를 확인한다**

Run: `cd backend && .venv/bin/python -m pytest tests/engine/test_survey_endpoint.py -q`
Expected: FAIL — 404 (경로가 없다)

- [ ] **Step 3: 인터랙터를 만든다**

`backend/apps/engine/app/use_cases/survey_interactor.py`:

```python
"""클리어 화면 플레이 평가 기록.

소유권은 라우터의 require_attempt_owner가 이미 확인했다. 여기서는 판에 붙은
user_id를 그대로 표에 옮겨, 나중에 사람 판만 집계할 수 있게 한다.
"""

import uuid

SCORE_FIELDS = ("fun", "novelty", "ai_agency", "polish", "recommend")


class SurveyInteractor:
    def __init__(self, attempts, votes) -> None:
        self._attempts, self._votes = attempts, votes

    def record(self, attempt_id: uuid.UUID, *, skipped: bool, scores: dict[str, int | None]) -> dict:
        attempt = self._attempts.get(attempt_id)
        given = {name: scores.get(name) for name in SCORE_FIELDS}
        # 별점을 하나도 안 매기고 보낸 것은 건너뛴 것과 같다 — 빈 표를 만들지 않는다.
        if not any(v is not None for v in given.values()):
            skipped, given = True, dict.fromkeys(SCORE_FIELDS)
        recorded = self._votes.record(
            attempt_id,
            attempt.user_id if attempt else None,
            skipped=skipped,
            scores=given,
        )
        return {"recorded": recorded}
```

- [ ] **Step 4: 의존성을 배선한다**

`engine_dependency.py` 파일 끝에 추가한다. `SurveyVoteRepository`를 `game_repository` import 줄에 더하고, `SurveyInteractor`를 import한다:

```python
def get_survey_interactor(session: Session = Depends(get_session)):
    return SurveyInteractor(
        attempts=AttemptRepository(session),
        votes=SurveyVoteRepository(session),
    )
```

- [ ] **Step 5: 엔드포인트를 더한다**

`game_router.py`의 요청 모델 구역(`class RulePreviewReq` 아래)에 추가한다:

```python
Score = Annotated[int, Field(ge=1, le=5)]


class SurveyReq(BaseModel):
    """다섯 항목 1~5점. 빈 항목은 보내지 않아도 된다(부분 응답)."""

    skipped: bool = False
    fun: Score | None = None
    novelty: Score | None = None
    ai_agency: Score | None = None
    polish: Score | None = None
    recommend: Score | None = None
```

`owned` 라우터의 `/attempts/{attempt_id}/harness` 아래에 추가한다:

```python
@owned.post("/attempts/{attempt_id}/survey")
def survey(attempt_id: uuid.UUID, req: SurveyReq, uc=Depends(get_survey_interactor)):
    scores = req.model_dump(exclude={"skipped"})
    return _run(uc.record, attempt_id, skipped=req.skipped, scores=scores)
```

`get_survey_interactor`를 `engine_dependency` import 줄에 더한다.

- [ ] **Step 6: 테스트가 통과하는지 확인한다**

Run: `cd backend && .venv/bin/python -m pytest tests/engine/test_survey_endpoint.py tests/engine/test_survey_votes.py -q`
Expected: PASS (13 passed)

- [ ] **Step 7: 계약 문서와 프론트 타입을 맞춘다**

`docs/spec/api_contract.md`의 판 하위 경로 절에 추가한다:

```markdown
### POST /attempts/{attempt_id}/survey — 플레이 평가

req: `{skipped: boolean, fun?: 1..5|null, novelty?, ai_agency?, polish?, recommend?}`
res: `{recorded: boolean}`
- 판 소유자만. 남의 판·없는 판은 404.
- 판당 한 표. 이미 표가 있으면 `recorded: false`(오류가 아니다, 첫 표가 유효).
- 별점을 하나도 안 보내면 건너뛴 것으로 기록한다.
- 점수가 1~5 밖이면 422.
```

같은 문서의 422 상한 목록에 `POST /attempts/{attempt_id}/survey`의 점수 1~5를 한 구절로 덧붙인다.

`frontend/contracts/api.ts`의 타입 구역에 추가한다:

```typescript
export interface SurveyReq {
  skipped: boolean;
  fun?: number | null;
  novelty?: number | null;
  ai_agency?: number | null;
  polish?: number | null;
  recommend?: number | null;
}
export interface SurveyRes {
  recorded: boolean;
}
```

`export const api = {` 안 `// 밤` 구역 아래에 추가한다:

```typescript
  // 플레이 평가
  sendSurvey: (attemptId: string, req: SurveyReq) =>
    request<SurveyRes>("POST", `/attempts/${attemptId}/survey`, req),
```

- [ ] **Step 8: 타입 검사와 커밋**

Run: `cd frontend && npx tsc --noEmit`
Expected: 오류 없음

```bash
git add backend/apps/engine docs/spec/api_contract.md frontend/contracts/api.ts backend/tests/engine/test_survey_endpoint.py
git commit -m "feat(survey): 판 소유자용 평가 엔드포인트와 계약 — 판당 한 표, 부분 응답, 건너뛰기"
```

---

### Task 3: 클리어 화면 설문 블록 (Codex astra)

**Files:**
- Create: `frontend/components/SurveyBlock.tsx`
- Modify: `frontend/components/screens/ClearScreen.tsx`
- Test: Task 4에서 헤드리스로

**Interfaces:**
- Consumes: Task 2의 `api.sendSurvey(attemptId, req)`, 타입 `SurveyReq`
- Produces: `<SurveyBlock attemptId={...} onDone={() => void} />` — 보내기·건너뛰기 어느 쪽이든 `onDone`을 부른다

- [ ] **Step 1: Codex astra에 맡긴다**

지시문에 담을 내용:

- `ClearScreen.tsx`는 지금 2단계다. 결말(점수·진실·엔딩 문장 + "이 세계의 바깥으로") → 회고(`Retrospective`) + "다시 시작". 여기에 중간 단계를 하나 넣어 **결말 → 설문 → 회고·다시 시작** 3단계로 만든다.
- `SurveyBlock.tsx` 신규. 제목 "이 게임은 어땠나", 다섯 줄:

  | 라벨 | 필드 | 아래 작은 글씨 |
  |---|---|---|
  | 재미·몰입도 | `fun` | 게임 플레이가 재미있고 몰입감 있었다. |
  | 참신성 | `novelty` | 기존 AI 서비스나 게임과 다른 새로운 경험이었다. |
  | AI 활용 체감 | `ai_agency` | AI가 단순한 대사 생성이 아니라 게임의 판단과 진행에 실제로 관여한다고 느꼈다. |
  | 완성도 | `polish` | 게임의 진행 방식과 인터페이스가 자연스럽고 안정적이었다. |
  | 추천 의향 | `recommend` | 다른 사람에게 이 게임을 플레이해보라고 추천하고 싶다. |

- 별은 항목마다 5개. 누르면 그 점수까지 채워지고 다시 누르면 해제된다. **일부만 매겨도 보낼 수 있다.**
- 버튼 두 개는 **같은 크기·같은 줄**: "평가 보내기", "건너뛰기". 건너뛰기를 작게 만들거나 숨기지 않는다.
- 보내기 → `api.sendSurvey(attemptId, {skipped: false, ...점수})`. 건너뛰기 → `{skipped: true}`.
- 어느 쪽이든 끝나면 `onDone()`을 불러 회고·다시 시작이 나타난다. **요청이 실패해도 `onDone()`을 부른다** — 평가 때문에 게임이 막히면 안 된다.
- 보내는 동안 두 버튼을 잠그고 `aria-busy`를 준다(기존 화면들과 같은 방식).
- 접근성: 항목마다 `role="radiogroup"` + `aria-label="재미·몰입도"`, 별 버튼 이름은 "재미·몰입도 3점". 키보드로 조작된다.
- 화면 톤은 `ClearScreen`의 어두운 배경(`text-paper`, `border-paper/60`)에 맞춘다.
- 테스트가 잡을 수 있게 설문 블록 바깥에 `data-survey="block"`을 둔다.

- [ ] **Step 2: 타입 검사**

Run: `cd frontend && npx tsc --noEmit`
Expected: 오류 없음

- [ ] **Step 3: 컨트롤러가 diff를 확인하고 커밋**

```bash
git add frontend/components/SurveyBlock.tsx frontend/components/screens/ClearScreen.tsx
git commit -m "feat(ui): 클리어 화면 플레이 평가 별점과 건너뛰기 (Codex astra)"
```

---

### Task 4: 헤드리스 시나리오

**Files:**
- Create: `frontend/tests/clear-survey.cjs`
- Test: 자기 자신

**Interfaces:**
- Consumes: Task 3의 `data-survey="block"`, 버튼 이름 "평가 보내기"·"건너뛰기"·"다시 시작", 별 버튼 이름 "재미·몰입도 3점" 형식

- [ ] **Step 1: Codex astra에 맡긴다**

`frontend/tests/day-screen-vn.cjs`의 가짜 API 방식을 그대로 따른다(`page.route`로 모든 요청을 가로채고, 없는 경로는 "Unexpected API"로 던진다). 1440px 한 가지면 된다.

확인할 것 네 가지:

1. 결말 화면에서 "이 세계의 바깥으로"를 누르면 설문 블록이 보이고, **"다시 시작"은 아직 없다.**
2. 별점을 두 항목만 매기고 "평가 보내기"를 누르면 `POST /attempts/{id}/survey`가 `{skipped:false, fun:…, recommend:…}` 꼴로 한 번 나가고, 그 뒤 "다시 시작"이 나타난다.
3. 다시 처음부터 시작해 "건너뛰기"를 누르면 `{skipped:true}`가 나가고, 역시 "다시 시작"이 나타난다.
4. 평가 요청이 500으로 실패해도 "다시 시작"이 나타난다.

- [ ] **Step 2: 컨트롤러가 실행한다**

Run: `cd frontend && NODE_PATH=<스크래치>/pw/node_modules node tests/clear-survey.cjs`
Expected: PASS

- [ ] **Step 3: 커밋**

```bash
git add frontend/tests/clear-survey.cjs
git commit -m "test(headless): 클리어 화면 평가 전송·건너뛰기·실패 시 진행"
```

---

### Task 5: 전체 검증과 배포

**Files:** 없음(실행과 기록만)
- Modify: `docs/jekyll.md`, `docs/superpowers/plans/2026-09-19-clear-survey.md`(결과 절)

- [ ] **Step 1: 백엔드 전체와 계약**

Run: `cd backend && .venv/bin/python -m pytest -q && .venv/bin/lint-imports`
Expected: 1041 + 신규 13건 내외 통과, `Contracts: 4 kept, 0 broken`

- [ ] **Step 2: 프론트 전체**

Run: `cd frontend && npx tsc --noEmit`, 이어서 헤드리스 전종을 **한 번에 하나씩**.
Expected: `dev-login`만 실패(개발 로그인을 꺼 둔 상태라 의도된 실패), 나머지 전부 통과

- [ ] **Step 3: 서버 재기동과 마이그레이션**

```bash
cd backend && .venv/bin/alembic upgrade head
fuser -k 8500/tcp
```
그다음 **별도 명령으로** uvicorn을 절대경로로 시작하고 `/health` 200(로컬·터널)과 설정을 확인한다. 설정은 그대로여야 한다: `anthropic claude-sonnet-5 | anthropic claude-haiku-4-5`, 한도 3/200, `trust_proxy True`, `dev_login off`.

- [ ] **Step 4: 실서버에 표가 실제로 쌓이는지**

개발 로그인이 꺼져 있어 컨트롤러는 API로 판을 만들 수 없다. 대신 확인한다:
- `docker exec pigfarm-db psql -U pigfarm -d pigfarm -Atc "\d survey_votes"`로 실 DB에 테이블이 있는지
- 사용자가 구글 계정으로 한 판 끝내고 투표한 뒤 `select * from survey_votes` 한 줄로 확인

- [ ] **Step 5: 전체 리뷰(A등급)**

sonnet 서브에이전트에게 변경 전체를 검토시킨다. 초점: 유니크 제약과 `on_conflict_do_nothing`의 경쟁 조건, 판에 user_id가 없는 경우, 라우터 소유권 확인이 새 경로에도 걸리는지, 화면이 요청 실패에 막히지 않는지, 테스트가 형식적으로만 통과하지 않는지.

- [ ] **Step 6: 기록과 커밋**

`docs/jekyll.md` 오늘 항목에 무엇을 왜 넣었는지, 검증 수치, 남은 것(리서치 페이지)을 적는다.

- [ ] **Step 7: 배포 (사용자 지시 2026-09-19 "완성되면 자동 배포까지 진행해")**

```bash
git push origin feat/coherence-chain
git push origin feat/coherence-chain:main
```
그다음 Vercel 배포 상태가 success인지 확인하고, 공개 사이트가 새 커밋인지 확인한다. `main` 푸시가 권한에 막히면 멈추고 사용자에게 그 한 줄을 요청한다.

---

## 실행 메모

- **DB는 되돌릴 수 있다.** 문제가 생기면 `alembic downgrade -1`로 테이블만 지우면 된다. 기존 데이터는 건드리지 않는다.
- **프론트가 늦어도 백엔드는 안전하다.** 엔드포인트만 있고 화면이 없으면 표가 안 쌓일 뿐 게임은 그대로다.
- **표가 하나도 없어도 게임은 정상이다.** 설문은 게임 흐름을 막지 않는다.
