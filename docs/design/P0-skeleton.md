# P0 설계서 — 뼈대 (Skeleton)

> 범위: 작업지시서 §P0. 명세: 기획서 v8.1 §8, §9, §11.4, 부록 B·C
> 상태: **승인됨 (2026-09-06, 이벤트 저장 = 옵션 A) → 구현 완료.** 실측값은 docs/devlog.md
> 이 문서에는 시나리오 고유 명사를 쓰지 않는다. 시나리오 데이터는 "부록 A 시드"로만 지칭

---

## 0. 범위 / 비범위

**P0에서 만드는 것**

1. 헥사고날 스캐폴딩 (`apps/engine` + `apps/scenarios`)
2. 포트 인터페이스 6종 + `fake` 어댑터 전 역할
3. LLM 포트 팩토리 (`.env` 스위치)
4. 이벤트 로그 저장소 (부록 C 17종) + 기록/조회 유스케이스
5. `ScenarioPort` 인터페이스 + `scenario_example` 더미 + `scenario_a` 시드(부록 A, 매 기동 upsert)
6. `GET /health`
7. CI 체크 4종: pytest · import-linter · 코어 금칙어 grep · scenario_a 누락 시 example 폴백 기동

**P0에서 만들지 않는 것** — 상태 머신, 에이전트 유스케이스 6종, 하네스 파이프라인, 게임 API(P1~), ollama/gemini 실어댑터 구현(인터페이스와 팩토리 등록만; 실구현은 P1/P6). 다른 단계 코드를 미리 쓰지 않는다.

---

## 1. 디렉토리 구조

기존 `apps/dummy` 뼈대 규약(adapter / app / domain / dependencies)을 그대로 따른다.
`dummy`는 P0 완료 후 삭제한다 (참조용 템플릿 역할 종료).

```
backend/
  core/                              공용 인프라만. apps를 import하지 않는다 (기존 규약)
    matrix/                          DB 엔진·세션 팩토리 (기존 그대로)
  apps/
    engine/                          ← "코어" = 금칙어 grep 범위. 시나리오를 모른다
      domain/
        entities/                    (P0: 비움. P1부터)
        value_objects/               event 타입 enum 등
      app/
        ports/
          input/                     HealthUseCase, EventLogUseCase
          output/                    llm_port.py, embedding_port.py, scenario_port.py,
                                     tool_port.py, event_log_port.py, clock_port.py
        use_cases/                   health_interactor.py, event_log_interactor.py
        dtos/                        이벤트 스키마 17종 (부록 C)
      adapter/
        inbound/api/
          v1/                        health_router.py
          schemas/  mappers/
        outbound/
          llm/                       fake_llm.py  (ollama·gemini는 P1/P6에서 파일 추가)
          embedding/                 fake_embedding.py
          repositories/ orms/ orm_mappers/   event_log SQLAlchemy 구현
          clock/                     system_clock.py
      dependencies/                  컴포지션 루트. .env는 여기(설정 모듈)서만 읽는다
    scenarios/
      scenario_example/              공개 더미: 인물 A·B·C, 비트 6, 정답 주장 3, 쿠키 3, 금칙어 1
      scenario_a/                    부록 A 시드. git init 시 .gitignore 등록
  main.py                            FastAPI 앱 조립 + 기동 시 시나리오 시드 upsert
  requirements.txt
docker-compose.yml                   Postgres + pgvector
```

**의존성 규칙 (import-linter로 고정)**

```
scenarios  →  engine.app.ports (ScenarioPort 구현)          허용
engine     →  scenarios                                      금지
engine.domain / engine.app  →  adapter, FastAPI, SQLAlchemy  금지
apps  →  core                                                허용 (역방향 금지, 기존 규약)
```

---

## 2. 포트 인터페이스 6종

시그니처는 방향을 고정하기 위한 것. 파라미터 세부는 구현에서 다듬되 **역할 무관 단일 인터페이스** 원칙은 바꾸지 않는다.

### 2.1 LLMPort

```python
class LLMPort(Protocol):
    def complete(self, messages: list[Message], json_schema: dict) -> dict: ...
```

- 역할(NPC/Advisor/…) 차이는 포트가 아니라 **컴포지션 루트에서 프롬프트 빌더 + provider 조합**으로 만든다 (기획서 8.2 "정책이 다른 같은 인터페이스")
- 출력 스키마 검증·재시도는 포트 밖(P1 하네스)의 일. 포트는 1회 호출만 책임
- `FakeLLM`: 생성자에 `responses: list[dict]` 큐를 받아 순서대로 반환. 테스트가 시나리오를 완전히 통제

### 2.2 EmbeddingPort

```python
class EmbeddingPort(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:   # 1,536차원
```

- `FakeEmbedding`: 텍스트 해시 기반 결정론 벡터 (같은 입력 → 같은 벡터)

### 2.3 ScenarioPort

작업지시서 P0 요구 그대로 — 인물·비트·정답 주장·쿠키 문장·금칙어·프롬프트 조각.

```python
class ScenarioPort(Protocol):
    def name(self) -> str: ...
    def characters(self) -> list[Character]: ...          # 인물 (이름·역할·초기 상태)
    def beats(self) -> list[Beat]: ...                    # 비트 6개 (서술문 포함)
    def truth_claims(self) -> list[TruthClaim]: ...       # 정답 주장 (칸 태그 포함)
    def cookie_texts(self) -> list[CookieText]: ...       # 쿠키 12종 (칸×강도)
    def forbidden_words(self) -> list[str]: ...           # 하네스 금칙어
    def prompt_fragment(self, role: str) -> str: ...      # 역할별 프롬프트 조각
```

- 반환 타입은 `engine/app/dtos`의 시나리오 DTO. **시나리오 고유 명사는 값으로만 흐르고 코드·식별자에는 없다**
- 7세 정책 프롬프트 조각은 ScenarioPort가 아니라 engine에 둔다 — P1 범위

### 2.4 ToolPort

```python
class ToolPort(Protocol):
    def dispatch(self, call: ToolCall) -> ToolResult: ...   # ask_npc, search_notes
```

- P0는 인터페이스 + `FakeTool`(고정 결과 반환)만. 실구현·부작용은 P1(ask_npc)·P2(search_notes)

### 2.5 EventLogPort

```python
class EventLogPort(Protocol):
    def record(self, event: GameEvent) -> None: ...
    def query(self, session_id, *, type=None, loop_n=None) -> list[GameEvent]: ...
```

### 2.6 ClockPort

```python
class ClockPort(Protocol):
    def now(self) -> datetime: ...
```

- 도메인·유스케이스가 시계를 직접 부르지 않게. 테스트는 `FakeClock`

---

## 3. 이벤트 로그 — 저장 방식 ★결정 필요★

### 옵션 A — 단일 `events` 테이블 + Pydantic 스키마 17종 (추천)

```
events
  id            bigserial PK
  session_id    uuid          (인덱스)
  attempt_n     int
  loop_n        int | null
  type          varchar(32)   (인덱스: session_id + type)
  payload       jsonb         부록 C 필드 전부
  created_at    timestamptz
```

- 필드 검증은 이벤트별 Pydantic DTO 17종이 담당. `record()`는 DTO만 받으므로 **필드 하나도 빠질 수 없다** (지시서 요구)
- B 지표 추출(파악 곡선·수락률·수정률…)은 `type` 인덱스 + JSONB 경로 쿼리로 충분
- Alembic 마이그레이션 1개. 이벤트 필드가 진화해도 스키마 변경 없음
- 단점: payload에 DB 레벨 제약이 없다 → 완화책: DTO 검증 + 이벤트별 기록·조회 왕복 테스트 17종

### 옵션 B — 이벤트별 물리 테이블 17개

- 장점: 컬럼 제약·타입이 DB에 박힘, 이벤트별 조회가 SQL로 자명
- 단점: 마이그레이션 17벌, 필드 진화 때마다 Alembic, 조인 없는 순수 append 로그에 과한 구조

**추천: A.** 지시서의 "로그 테이블 전부"는 "17종 이벤트가 전부 기록·조회 가능해야 한다"로 해석하고, 그 보장을 DTO 17종 + 테스트 17종으로 옮긴다. 승인 시 A/B 중 선택해 달라.

---

## 4. DB / docker-compose

- **Postgres 16 + pgvector** 단일 컨테이너. 임베딩 1,536차원(gemini-embedding 스키마 그대로), 노트 검색과 채점 RAG가 같은 인덱스를 쓰므로(기획서 8.5) 1일차부터 벡터 확장이 필요
- SQLAlchemy 2.0 + Alembic. 엔진·세션은 기존 `core/matrix` 그대로 사용 (`DATABASE_URL` 환경변수)
- **호스트 포트 5435** (확정): 다른 프로젝트 규칙 — 127.0.0.1 바인딩, 프로젝트별 순차 포트(5432 foodrm · 5433 lifetutorial · 5434 beyondfacade), `{프로젝트}-db` 컨테이너명, 네임드 볼륨, pgvector/pgvector:pg17 — 을 따라 `pigfarm-db`로 작성 완료 (docker-compose.yml)
- P0 테이블: `events`(§3) + 시나리오 시드 테이블(`scenario_characters`, `scenario_beats`, `scenario_truth_claims`, `scenario_cookies`) + `truth_claim_embeddings`(vector(1536), 실제 채움은 P2)

**시드 정책** (지시서 "하지 말 것" 반영)

- `ensure_seeded` early-return 금지. **매 기동 시 자연키(시나리오명+항목 코드) upsert** → 시드 파일이 바뀌면 재기동만으로 DB 반영
- `SCENARIO=a`인데 `scenario_a/` 디렉토리가 없으면 경고 로그 후 `scenario_example`로 기동 (CI·공개 리포 대비)

---

## 5. `.env` 스위치와 컴포지션 루트

작업지시서 §2 그대로. P0에서 전부 정의하고, P0 시점 유효 값은 `fake`뿐.

```
DATABASE_URL=postgresql+psycopg://pigfarm:***@localhost:5435/pigfarm
GEMINI_API_KEY=...                       온라인 provider용. fake만 쓰는 동안은 비어도 기동
SCENARIO=a|example                       기본 a, 없으면 example 폴백
NPC_LLM_PROVIDER=ollama|gemini|fake      NPC_LLM_MODEL=gemma3:4b
ADVISOR_LLM_PROVIDER=gemini|fake         (Normalizer 동일 값)
MANAGER_LLM_PROVIDER=gemini|fake         (Evaluator 동일 값)
EMBEDDING_PROVIDER=gemini|fake
SYSTEM_HARNESS=on|off                    기본 on
COOKIE_AB=on|off        PAW_REASON_AB=on|off
```

- 설정·시크릿 로딩은 backend/CLAUDE.md 규약대로 `core/matrix/grid_keymaker_secret_manager.py`(전역 인프라 매니저)에 두고, `dependencies/`는 그것만 참조한다. 코드 다른 곳에 `os.environ` 금지 (시크릿 원칙 §1-7의 집행 지점)
- `backend/.env`는 작성 완료 — P0 시점 값 전부 `fake`, `GEMINI_API_KEY`는 사용자가 채운다
- `dependencies/`의 팩토리가 (역할 → provider 어댑터) 매핑을 조립. 미지의 provider 값이면 기동 실패 (fail-fast)

---

## 6. GET /health

```json
{
  "scenario": "example",
  "harness": "on",
  "models": { "npc": "fake", "advisor": "fake", "manager": "fake", "embedding": "fake" },
  "db": "ok"
}
```

지시서 완료 조건("활성 모델 3종·시나리오 이름·하네스 on/off") + DB 연결 체크.

---

## 7. CI

git 저장소가 아직 없으므로 P0에서는 **로컬 스크립트로 동일 체크를 만들고**, git init 후 GitHub Actions로 그대로 옮긴다.

| 체크 | 도구 | 내용 |
|---|---|---|
| 테스트 | pytest | `backend/tests/` 전체 |
| 의존성 방향 | import-linter | §1의 4개 계약 |
| 코어 금칙어 | grep 스크립트 | `apps/engine/` 전체에서 시나리오 금칙어 목록 검출 시 실패. 금칙어 목록 파일은 `scenarios/scenario_a/` 안에 둔다 (코어가 모르는 상태 유지) |
| 폴백 기동 | pytest | `scenario_a` 경로를 숨긴 채 앱 기동 → health가 `example` 반환 |

실행 진입점: `backend/scripts/ci.sh` (pytest + lint + grep 순차, 하나라도 실패 시 비-0 종료).

---

## 8. 테스트 목록 (P0)

1. **이벤트 17종 각각**: DTO로 기록 → 조회 → 필드 왕복 일치 (파라미터라이즈 17케이스)
2. 필수 필드 누락 DTO → 검증 실패
3. `FakeLLM` 큐 순서 반환 / `FakeEmbedding` 결정론(같은 입력 → 같은 벡터, 차원 1536)
4. ScenarioPort 계약 테스트: `scenario_example`·`scenario_a` 둘 다 같은 계약 스위트 통과 (인물 수·비트 6·정답 주장·쿠키·금칙어 비어있지 않음)
5. 시드 upsert: 기동 2회 → 중복 없음 / 시드 값 변경 후 재기동 → DB 반영
6. 폴백 기동 (§7)
7. `GET /health` 응답 스키마
8. import-linter 계약 위반 샘플이 실제로 잡히는지 (계약 자체의 스모크)

---

## 9. 완료 조건 (지시서 §P0 그대로)

- [ ] `GET /health`가 활성 모델 3종·시나리오 이름·하네스 on/off 반환
- [ ] 17개 이벤트 각각 기록·조회 테스트 통과 — devlog에 **통과 테스트 수** 기록
- [ ] CI(로컬 ci.sh) 초록. `apps/engine` 금칙어 0건 — devlog에 grep 대상 파일 수 기록

---

## 10. 승인 시 함께 결정해 달라

1. **이벤트 저장 방식**: 옵션 A(단일 테이블+DTO 17종, 추천) vs B(물리 테이블 17개)
   - 참고: backend/CLAUDE.md의 "1 ERD 테이블 = 1 Fractal 11-File Set" 규약 기준으로도 옵션 A가 `event_log` 프랙탈 1세트로 떨어져 정합적
2. `apps/dummy` 삭제 시점: P0 완료 시 삭제 제안
3. (미결 유지 가능) `scenario_a` 비공개 방식은 git init 때 — .gitignore 제안

(해결됨) DB 호스트 포트: 다른 프로젝트 순차 규칙에 따라 **5435** 확정, docker-compose.yml 작성 완료
