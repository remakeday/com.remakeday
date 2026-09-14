# REMAKE DAY — 팀 역할 정의 v3.1

> 기준일: 2026-09-14
> 문서 지위: **팀 역할 정본.** 제출 폼·팀 소개·발표 크레딧·데브로그 작성자 표기에 동일하게 사용한다
> 프로젝트: **REMAKE DAY** — 시나리오 A (구역)
> Jekyll: `beyondbob.remakeday.com` — BeyondFacade 개발 허브
> 팀: BeyondFacade — 류준 · 장민석 · 신채연 · 이은상 · 김충식
> 일정: 2026-09-20 (예선) · 2026-10-17 데모데이 (본선)
> 역할 구조 원본: `Masterless_Company_Team_Roles_v1.1_2026-09-10.md` — 동일 팀·동일 분담을 이 프로젝트에 맞게 번역했다

> **표기 원칙** — 담당 표기는 해당 작업을 주도한 사람 기준이며, 인원이 적고 일정이 짧아 영역 구분 없이 교차 작업했다.

---

## Web Surface / Frontend Boundary

현재 확정된 Surface는 다음과 같이 구분한다.

```text
beyondbob.remakeday.com
→ BeyondFacade Jekyll 개발 허브 — 기획·칸반·일정·데브로그

Game Runtime Frontend
→ Next.js (App Router)
→ /play · /inspector/[attemptId] · /harness/[attemptId]
→ 배포 URL은 별도 확정 전까지 문서에서 임의 생성하지 않는다

Backend
→ FastAPI — 모듈러 모놀리스 + 헥사고날
→ PostgreSQL (pigfarm-db) · alembic

LLM Runtime
→ NPC 슬롯 = ollama (로컬) / Core 슬롯 = 설정 스위치
→ provider는 .env 두 필드로만 바꾼다

작업 로그
→ docs/jekyll.md — 하루 단위, 최신 날짜가 위. 매일 23:45 자동 기록 후
   beyondbob _posts/로 포스트 변환 복사
```

- Jekyll 허브와 게임 런타임을 같은 것으로 취급하지 않는다.
- **배포 URL이 확정되기 전에는 문서에 임의 주소를 쓰지 않는다.** 현재 확정된 것은 로컬 기동 주소뿐이다.
- 모델·provider 전환은 코드가 아니라 `.env` 스위치로 한다. 문서에 "모델을 바꿨다"고 쓸 때는 어느 필드를 바꿨는지 함께 적는다.

---

## 0. 팀 구성 한눈에

| 이름 | 타이틀 | 한 줄 역할 |
|---|---|---|
| **류준** | Team Lead · AI Agent Engineer | 소프트웨어 아키텍처와 Agent Harness·LLM 역할 프롬프트를 소유하고 팀의 기술 결정을 내린다. 발표자 |
| **장민석** | AI Evaluation Engineer | 평가 설계·러너·모델 선정(E7·E6)으로 "이 슬롯에 어떤 모델을 쓸 것인가"에 숫자를 붙인다. Inspector 소유 |
| **신채연** | Full-stack Engineer · Game Frontend | 게임 엔진(낮 루프·밤 채점·신의 개입)·Game API·DB와 Next.js `/play` 게임 화면을 연결한다. 시연 조작 |
| **이은상** | QA · UI Support · Release Engineer | 규칙·재현성·반응형 UI를 검증하고 보조 화면·그림/사운드 반입·기동/배포 검증을 책임진다 |
| **김충식** | Scenario Director · Content | 시나리오 A의 세계·인물·진실 명제·쿠키 콘텐츠와 그림(장면·인물·쿠키)·사운드(배경 BGM·음성 대사)를 만들고 Jekyll 허브 콘텐츠를 관리한다 |

---

## 1. 류준 — Team Lead · AI Agent Engineer

### 역할 정의

팀장으로서 스코프와 기술 결정을 최종 확정한다. 백엔드의 계층 구조(모듈러 모놀리스 · 헥사고날 · Fractal 11-File Set)와 Port/Adapter 경계를 설계하고, 프론트–백엔드 API 계약을 소유한다. LLM이 말하는 7개 자리의 프롬프트·구조화 출력 스키마·시스템 하네스를 구현하고, 모델이 실패했을 때 게임이 무너지지 않도록 재생성과 폴백 경로를 책임진다. 아키텍처 결정을 문서로 남기고 발표를 맡는다.

### 업무 분류

| 대분류 | 중분류 | 소분류 |
|---|---|---|
| Software Architecture | 계층 설계 | `apps/` × `core/` 경계, Port/Adapter 구조, 의존 방향 강제 |
| | 계약 정의 | `docs/spec/api_contract.md`, DTO·스키마 경계, Boundary Gate(mapper·orm_mapper) |
| | 설계 원칙 | "하네스는 프롬프트가 아니라 코드"의 구조적 번역, LLM 제안 → 코드 확정 경계 |
| Agent Harness | 하네스 | `run_with_harness` — JSON 파싱 → 스키마 → 사실 층 → 재생성 2회 → 폴백 |
| | 사실 층 검사 | 금칙어, 소실 인물, 미지 인물, 한국어 전용, 행동 어휘, 근거 인용 |
| LLM Roles | 프롬프트 | `prompts.py` — agent · planner · manager · advisor · evaluator |
| | 구조화 출력 | `llm_output_dto.py` — 스키마 enum 제약(`Literal[tuple(vocab)]`) |
| | 7세 정책 | AGE7 정책 프롬프트, on/off ablation 스위치 |
| Scenario Port | 시나리오 교체 가능성 | `BaseScenario` 계약, `scenario_a` / `scenario_audit` / `scenario_example` 병존 |
| Team Lead | 의사결정 | 스코프 확정, 설계 문서 소유, 발표자 |

### 대표 산출물

- `backend/CLAUDE.md` — 아키텍처 규약 (Fractal · 헥사고날 · SOLID · DDD)
- `backend/apps/engine/app/use_cases/harness.py` · `prompts.py`
- `docs/spec/api_contract.md` — API 계약
- `docs/design/P0-skeleton.md` · `P1-day.md` · `P2-P5-mvp.md` — 단계별 설계
- `docs/define/REMAKE_DAY_기획서_확정본_v9.0` — 기획 정본
- 발표 (본선)

---

## 2. 장민석 — AI Evaluation Engineer

### 역할 정의

"이 슬롯에 어떤 모델을 쓸 것인가"라는 질문을 측정 가능한 실험으로 설계하고 실행한다. 평가 러너·프로브 코퍼스·게이트를 소유하고, Core 슬롯 선정(E7)과 NPC 슬롯 descent(E6)에 숫자를 붙인다. 하네스의 계측(HarnessReport)을 집계하고, provider 어댑터와 판단 근거를 시각화하는 Inspector·Harness 뷰를 만든다. 발표의 모델 평가 구간을 맡는다.

### 업무 분류

| 대분류 | 중분류 | 소분류 |
|---|---|---|
| Evaluation Design | 실험 설계 | **E7** Core 선정 · **E6** NPC descent, Funnel(Stage 0~4), 게이트 값, 통제 사전 등록 |
| | 실패 분류 | 폴백/위반 분류, 금지 표현 규칙(단일 종합 점수 금지 · 폴백은 성공이 아니다) |
| Harness Instrumentation | 계측 집계 | `HarnessReport` — attempts · violations · fallback_used · call_records |
| Eval Runner | 러너 | `scripts/run_*.py`, `docs/metrics.yml` append, 비열등 판정 |
| Model Descent | 모델 사다리 | 후보 인벤토리, thinking 제어(러너 서브클래스), Screening/Formal 분리 |
| | provider 어댑터 | `ollama_llm` · `gemini_llm` · `fake_llm`, RPM 페이싱 |
| Deployment Metrics | 배포 지표 | p50/p95 지연, Peak VRAM, 동시 상주 안전값 |
| Inspector | 판정 시각화 | `/inspector/[attemptId]` · `/harness/[attemptId]` — 하네스 이벤트·판정 근거, 발표 구간 |

### 대표 산출물

- `backend/scripts/run_*.py` — 평가 러너 (core_selection · age7 · leak · judge · selfplay · paw)
- `docs/model_evaluation.md` — **모델 평가 정본** (E7 · E6)
- `docs/metrics.yml` — 실측 적립 (append-only)
- `backend/apps/engine/adapter/outbound/llm/` — provider 어댑터 3종
- `frontend/app/inspector/` · `frontend/app/harness/` — Inspector 화면
- `docs/define/REMAKE_DAY_AI_Agent_Evaluation_PART1_정본_v1.0` + 부록 E6

---

## 3. 신채연 — Full-stack Engineer · Game Frontend

### 역할 정의

세계가 굴러가는 규칙을 결정론 코드로 구현한다. 하루 6비트 낮 루프, 밤의 노트·주장·채점, 신의 개입(질문·규칙·원숭이손), 회차 간 세계 손상과 쿠키를 만들고, Game API와 PostgreSQL 스키마를 소유한다. LLM이 폴백이어도 규칙은 반드시 걸리도록 기계 보정 경로를 유지한다. Next.js 기반 `/play` 게임 화면(아침–낮–밤 진행·노트·제출·회고)을 연결·구현하고 프로덕션 빌드·기동을 주도한다. 시연 조작을 맡는다.

### 업무 분류

| 대분류 | 중분류 | 소분류 |
|---|---|---|
| Game Engine | 낮 | `loop_interactor` — 6비트 진행, 대화 예산, 의심·신뢰 게이지, 반대 모드 |
| | 규칙 강제 | `enforce_rules_on_plan` — Planner 출력·폴백과 무관하게 계획을 기계 보정 |
| | 밤 | `night_interactor` — 노트 적립, 주장 분할, 정답 대조, 점수 산출 |
| | 신의 개입 | `intervention_interactor` · `manager_interactor` — 질문 3회, 규칙, 원숭이손 |
| Game API | 엔드포인트 | `game_router.py` · `health_router.py`, 세션·회차·밤·개입 |
| Persistence | DB | PostgreSQL 스키마, alembic 마이그레이션, ORM/엔티티 매퍼 |
| Game Frontend | 진행 화면 | `/play` — 아침·낮 대화·장면 이동·밤 전환, 대화 예산 표시 |
| | 밤 화면 | 노트 선택, 자유 서술, 주장 편집, 제출·결과, 회고 |
| Frontend Release | Runtime 기동 | Next.js production build, 포트 3500 기동, 백엔드 연결 검증 |

### 대표 산출물

- `backend/apps/engine/app/use_cases/` — loop · night · intervention · manager
- `backend/apps/engine/adapter/inbound/api/v1/` — Game API
- `backend/alembic/` — 스키마 마이그레이션
- `frontend/app/play/page.tsx` · `frontend/components/` — 게임 화면
- 시연 조작 (본선)

---

## 4. 이은상 — QA · UI Support · Release Engineer

### 역할 정의

규칙·재현성·화면을 검증하고 결함을 기록한다. 뷰포트 자동 검사와 플레이 검증으로 제출 가능 상태를 보증하고, 보조 화면과 그림·사운드 반입을 지원한다. 통합 리허설과 백엔드/프론트 외부망 검증, 기동 스크립트를 책임진다. Jekyll 허브와 게임 런타임의 링크·뷰포트·정적 파일 경로도 검증한다.

### 업무 분류

| 대분류 | 중분류 | 소분류 |
|---|---|---|
| Game QA | 검증 | 백엔드 회귀 스위트(`tests/pure` · `tests/engine`) 실행·감시, 채점 재현성 확인 |
| | 플레이 검증 | 테스터 회차 기록, 결함 로그, 재현 경로, 회귀 확인 |
| Visual QA | 뷰포트 | `frontend/tests/*.cjs` — Playwright headless(`headless: true` 고정), 390px · 1440px |
| | 가독성 | 안내 글씨와 대화 본문 분리, 상시 흐림 제거, 대비 확보 |
| UI Support | 보조 화면 | 플레이 안내, 설정, 오류 토스트, 타이핑 인디케이터 |
| | 그림·사운드 반입 지원 | 이미지·오디오 매니페스트 검증, 정적 경로 확인, 재생·음량 동작 확인 |
| Release | 기동·리허설 | `start_demo.sh` · `stop_demo.sh`, health 확인, 외부망 접속 확인, 통합 리허설 |

### 대표 산출물

- `frontend/tests/` — 뷰포트·플로우 자동 검사 (`five-loop-flow` · `gameplay-clarity` · `scene-illustrations` · `connected-investigation`)
- `frontend/components/ErrorToast.tsx` · `TypingIndicator.tsx` · `GameplayGuide.tsx`
- `docs/review-verification/` — 날짜별 검증 기록·결함 로그
- `start_demo.sh` · `stop_demo.sh`

---

## 5. 김충식 — Scenario Director · Content

### 역할 정의

REMAKE DAY가 살아가는 세계를 쓴다. 시나리오 A(구역)의 인물·비트·공개 관찰·진실 명제·쿠키 콘텐츠 데이터와 장면·인물·쿠키 **그림**·스타일 가이드를 만든다. **사운드도 소유한다** — 배경 BGM과 음성 대사(팀원 각자 자기 배역 목소리를 녹음)를 기획·수집·반입한다. beyondbob Jekyll 허브의 문서 콘텐츠(데브로그·가이드)를 관리하고, 세계관과 콘텐츠에 관한 질문을 받는다.

### 업무 분류

| 대분류 | 중분류 | 소분류 |
|---|---|---|
| Scenario | 세계·인물 | 시나리오 A — 구역 설정, 인물 6명, 관계·동기, hidden truth |
| | 콘텐츠 데이터 | 비트·공개 관찰·질문 응답·진실 명제·쿠키 12종, 대사·서술 |
| 그림 | 이미지 | 장면·인물·쿠키 그림 생성(승인 이미지 A안 — 고정 초상·사건 장면·밤 갤러리), 손상 변형, 매니페스트 |
| | 연출 원칙 | 손상 단계별 효과를 그림에만 적용(글씨에 번지지 않게), 치지직은 코드로 |
| 사운드 | 배경 BGM | 장면·국면(아침·낮·밤·개입)별 BGM 선정, 루프 편집, 볼륨·전환 규칙 |
| | 음성 대사 | 대사 스크립트 발췌, **팀원 각자 자기 배역 녹음** 수집, 파일 규격·반입, 재생 지점 정의 |
| Docs | 콘텐츠 | 이미지 제작서, 데모 가이드, 플레이 가이드 |
| Jekyll Hub | 허브 콘텐츠 | beyondbob 데브로그·문서 콘텐츠 관리 (개발은 com.remakeday, 지킬은 beyondbob 원칙) |

### 대표 산출물

- `backend/apps/scenarios/scenario_a/` — 시나리오 콘텐츠 데이터
- `frontend/public/assets/` — 장면·인물·쿠키 그림 (디렉터리명은 코드 경로라 유지)
- 배경 BGM · 음성 대사 녹음 파일 (반입 규격 포함)
- `docs/REMAKE_DAY_이미지제작서_v1.md` · `docs/REMAKE_DAY_이미지제작서_쿠키12종.md`
- `docs/demo_guide.md` · `docs/first-play-guide.md`
- `beyondbob.remakeday.com` Jekyll 데브로그 콘텐츠, 시연 영상

---

## 6. 발표 · Q&A 분담

| 구간 | 담당 |
|---|---|
| 발표 전체 | 류준 |
| 모델 평가(E7·E6) 구간 | 장민석 |
| 시연 조작 | 신채연 |
| 아키텍처 · 하네스 · 계약 질문 | 류준 |
| 숫자 · 게이트 · 모델 선정 질문 | 장민석 |
| 게임 규칙 · 채점 · 화면 질문 | 신채연 |
| 세계관 · 콘텐츠 · 그림/사운드 질문 | 김충식 |
| QA · 배포 질문 | 이은상 |

---

## 7. 문서 지도

| 문서 | 지위 |
|---|---|
| 본 문서 | **팀 역할 정본** |
| `docs/Masterless_Company_Team_Roles_v1.1_2026-09-10.md` | 역할 구조 원본 (참조용) |
| `docs/define/REMAKE_DAY_기획서_확정본_v9.0_2026-09-10.md` | 기획 정본 |
| `docs/define/REMAKE_DAY_통합시나리오_v1.0_2026-09-10.md` | 시나리오 정본 |
| `docs/define/REMAKE_DAY_AI_Agent_Evaluation_PART1_정본_v1.0_2026-09-10.md` | 평가 정본 |
| `docs/model_evaluation.md` | **모델 평가 정본** (E7 · E6) |
| `docs/REMAKE_DAY_모델구성_정책프롬프트_v1.md` | 모델 구성·정책 프롬프트 |
| `docs/spec/api_contract.md` | API 계약 |
| `docs/jekyll.md` | 작업 로그 (하루 단위) |
| `docs/HANDOFF.md` | 세션 인계 |
| `docs/review-verification/` | 날짜별 검증 원문 |

---

## 8. 데브로그 작성 규칙

데브로그와 작업 로그를 쓸 때도 위 역할을 그대로 따른다. 각 글의 작성자·담당 영역은 §0의 표를 기준으로 기재한다.

`docs/jekyll.md`는 **하루 단위로, 최신 날짜가 위로** 오도록 작성한다. 한 사람이 여러 영역을 건드린 날은 영역별로 나눠 적되, 담당 표기는 그 작업을 주도한 사람 기준으로 한다. 매일 23:45 자동 기록이 돌고, 당일 섹션은 beyondbob `_posts/`로 포스트 변환 복사된다.

---

## 9. 변경 이력

| 버전 | 날짜 | 내용 |
|---|---|---|
| v3.1 | 2026-09-14 | "에셋" 용어 제거 — 우리 것은 **그림**이다(사용자 확정). 사운드 신설: 배경 BGM + 음성 대사(팀원 각자 자기 배역 목소리 녹음) — 김충식 소유, 은상은 반입 검증 지원. 충식 타이틀 Content/Asset → Content |
| v3.0 | 2026-09-14 | **`Masterless_Company_Team_Roles_v1.1` 구조로 전면 개정** (사용자 지시 — 다른 프로젝트와 동일 분담). 류준 = Team Lead · AI Agent(하네스·프롬프트), 장민석 = AI Evaluation(러너·모델 선정·Inspector), 신채연 = Full-stack(게임 엔진·API·게임 프론트·시연), 이은상 = QA·UI Support·Release, 김충식 = Scenario Director·Content/Asset. v2.0의 "확정 필요" 각주 해소 (E7 결정 항목 D3) |
| v2.0 | 2026-09-13 | 역할 정의를 업무 분류·대표 산출물 수준으로 확장. Surface 경계·발표 분담·문서 지도 추가. 장민석·신채연의 백엔드 분담은 제안 상태 |
| v1.0 | 2026-09-01 | 최초 작성 — 이름과 한 줄 역할만 |
