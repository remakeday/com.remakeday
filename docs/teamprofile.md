# REMAKE DAY — 팀 역할 정의 v2.0

> 기준일: 2026-09-13
> 문서 지위: **팀 역할 정본.** 제출 폼·팀 소개·발표 크레딧·데브로그 작성자 표기에 동일하게 사용한다
> 프로젝트: **REMAKE DAY** — 시나리오 A (구역)
> 팀: BeyondFacade — 류준 · 장민석 · 신채연 · 이은상 · 김충식
> 일정: 2026-09-20 (예선) · 2026-10-17 데모데이 (본선)

> **표기 원칙** — 담당 표기는 해당 작업을 주도한 사람 기준이며, 인원이 적고 일정이 짧아 영역 구분 없이 교차 작업했다.

---

## Surface 경계

```text
Game Runtime          Next.js (App Router)
                      /play · /inspector/[attemptId] · /harness/[attemptId]

Backend               FastAPI — 모듈러 모놀리스 + 헥사고날
                      PostgreSQL (pigfarm-db) · alembic

LLM Runtime           NPC 슬롯 = ollama (로컬) / Core 슬롯 = 설정 스위치
                      provider는 .env 두 필드로만 바꾼다

작업 로그             docs/jekyll.md — 하루 단위, 최신 날짜가 위
```

- 게임 런타임과 문서·로그를 같은 것으로 취급하지 않는다.
- **배포 URL이 확정되기 전에는 문서에 임의 주소를 쓰지 않는다.** 현재 확정된 것은 로컬 기동 주소뿐이다.
- 모델·provider 전환은 코드가 아니라 `.env` 스위치로 한다. 문서에 "모델을 바꿨다"고 쓸 때는 어느 필드를 바꿨는지 함께 적는다.

---

## 0. 팀 구성 한눈에

| 이름 | 타이틀 | 한 줄 역할 |
|---|---|---|
| **류준** | Team Lead · Architect | 스코프와 기술 결정을 최종 확정하고 계층·계약·Port 구조를 소유한다. 발표자 |
| **장민석** | Backend · AI Agent Engineer | LLM 7역할 하네스와 평가 러너를 소유하고, 모델 선정에 숫자를 붙인다 |
| **신채연** | Backend · AI Agent Engineer | 게임 엔진(낮 루프·밤 채점·신의 개입)과 Game API·DB를 만든다 |
| **김충식** | Frontend Engineer | `/play` 게임 화면과 인스펙터를 만들고 장면·쿠키 이미지 에셋을 반입한다 |
| **이은상** | Frontend Engineer · Mobile | 반응형·모바일 대응과 보조 화면을 맡고 뷰포트·플레이 검증을 수행한다 |

> **확정 필요** — 장민석·신채연은 기존 표에서 둘 다 "백엔드 및 AI 에이전트"였다. 위 분담은 저장소의 실제 경계(평가·하네스 / 게임 루프·API)를 따라 나눈 **제안**이며, 실제 담당과 다르면 §1~§5를 그에 맞게 교체한다.

---

## 1. 류준 — Team Lead · Architect

### 역할 정의

팀장으로서 스코프와 기술 결정을 최종 확정한다. 백엔드의 계층 구조(모듈러 모놀리스 · 헥사고날 · Fractal 11-File Set)와 Port/Adapter 경계를 설계하고, 프론트–백엔드 API 계약을 소유한다. 아키텍처 결정을 문서로 남기고 발표를 맡는다.

### 업무 분류

| 대분류 | 중분류 | 소분류 |
|---|---|---|
| Software Architecture | 계층 설계 | `apps/` × `core/` 경계, Port/Adapter 구조, 의존 방향 강제 |
| | 계약 정의 | `docs/spec/api_contract.md`, DTO·스키마 경계, Boundary Gate(mapper·orm_mapper) |
| | 설계 원칙 | "하네스는 프롬프트가 아니라 코드"의 구조적 번역, LLM 제안 → 코드 확정 경계 |
| Scenario Port | 시나리오 교체 가능성 | `BaseScenario` 계약, `scenario_a` / `scenario_audit` / `scenario_example` 병존 |
| Team Lead | 의사결정 | 스코프 확정, 설계 문서 소유, 발표자 |

### 대표 산출물

- `backend/CLAUDE.md` — 아키텍처 규약 (Fractal · 헥사고날 · SOLID · DDD)
- `docs/spec/api_contract.md` — API 계약
- `docs/design/P0-skeleton.md` · `P1-day.md` · `P2-P5-mvp.md` — 단계별 설계
- `docs/define/REMAKE_DAY_기획서_확정본_v9.0` — 기획 정본
- 발표 (본선)

---

## 2. 장민석 — Backend · AI Agent Engineer

### 역할 정의

LLM이 말하는 7개 자리를 소유한다. 프롬프트·구조화 출력 스키마·시스템 하네스를 만들고, 모델이 실패했을 때 게임이 무너지지 않도록 재생성과 폴백 경로를 책임진다. "이 역할에 어떤 모델을 쓸 것인가"를 측정 가능한 실험으로 설계하고 러너를 실행한다.

### 업무 분류

| 대분류 | 중분류 | 소분류 |
|---|---|---|
| Agent Harness | 하네스 | `run_with_harness` — JSON 파싱 → 스키마 → 사실 층 → 재생성 2회 → 폴백 |
| | 사실 층 검사 | 금칙어, 소실 인물, 미지 인물, 한국어 전용, 행동 어휘, 근거 인용 |
| | 계측 | `HarnessReport` — attempts · violations · fallback_used · call_records |
| LLM Roles | 프롬프트 | `prompts.py` — agent · planner · manager · advisor · evaluator |
| | 구조화 출력 | `llm_output_dto.py` — 스키마 enum 제약(`Literal[tuple(vocab)]`) |
| | 7세 정책 | AGE7 정책 프롬프트, on/off ablation 스위치 |
| LLM Adapter | provider | `ollama_llm` · `gemini_llm` · `fake_llm`, RPM 페이싱 |
| Model Evaluation | 실험 설계 | **E7** Core 선정 · **E6** NPC descent, Funnel(Stage 0~4), 게이트 값 |
| | 러너 | `scripts/run_*.py`, `docs/metrics.yml` append, 비열등 판정 |
| | 배포 지표 | p50/p95 지연, Peak VRAM, 동시 상주 안전값 |

### 대표 산출물

- `backend/apps/engine/app/use_cases/harness.py` · `prompts.py`
- `backend/apps/engine/adapter/outbound/llm/` — provider 어댑터 3종
- `backend/scripts/run_*.py` — 평가 러너 (age7 · leak · judge · selfplay · calibration · paw)
- `docs/model_evaluation.md` — **모델 평가 정본** (E7 · E6)
- `docs/metrics.yml` — 실측 적립 (append-only)
- `docs/define/REMAKE_DAY_AI_Agent_Evaluation_PART1_정본_v1.0` + 부록 E6

---

## 3. 신채연 — Backend · AI Agent Engineer

### 역할 정의

세계가 굴러가는 규칙을 결정론 코드로 구현한다. 하루 6비트 낮 루프, 밤의 노트·주장·채점, 신의 개입(질문·규칙·원숭이손), 회차 간 세계 손상과 쿠키를 만든다. Game API와 PostgreSQL 스키마를 소유하고, LLM이 폴백이어도 규칙은 반드시 걸리도록 기계 보정 경로를 유지한다.

### 업무 분류

| 대분류 | 중분류 | 소분류 |
|---|---|---|
| Game Loop | 낮 | `loop_interactor` — 6비트 진행, 대화 예산, 의심·신뢰 게이지, 반대 모드 |
| | 규칙 강제 | `enforce_rules_on_plan` — Planner 출력·폴백과 무관하게 계획을 기계 보정 |
| Night Pipeline | 밤 | `night_interactor` — 노트 적립, 주장 분할, 정답 대조, 점수 산출 |
| | 채점 | 정답 명제 × 후보 판정(confirmed/partial/none), 인과 사슬 |
| Intervention | 신의 개입 | `intervention_interactor` — 질문 3회, 규칙 후보·직접 작성, 미리보기 |
| | 원숭이손 | `manager_interactor` — 제안 규칙 + 숨은 부작용, 수락/거절 |
| Game API | 엔드포인트 | `game_router.py` · `health_router.py`, 세션·회차·밤·개입 |
| Persistence | DB | PostgreSQL 스키마, alembic 마이그레이션, ORM/엔티티 매퍼 |
| Test | 회귀 | `backend/tests/pure` · `tests/engine`, `scripts/ci.sh` |

### 대표 산출물

- `backend/apps/engine/app/use_cases/` — loop · night · intervention · manager
- `backend/apps/engine/adapter/inbound/api/v1/` — Game API
- `backend/alembic/` — 스키마 마이그레이션
- `backend/tests/` — pure · engine 회귀 스위트
- `backend/apps/scenarios/scenario_a/` — 시나리오 어댑터

---

## 4. 김충식 — Frontend Engineer

### 역할 정의

플레이어가 실제로 만나는 화면을 만든다. `/play`의 아침–낮–밤 진행, 관찰·노트·증거 갤러리, 회고 화면을 구현하고, 개발자용 인스펙터와 하네스 뷰를 붙인다. 장면·인물·쿠키 이미지를 생성·반입하고 세계 손상 단계에 맞춰 연출한다.

### 업무 분류

| 대분류 | 중분류 | 소분류 |
|---|---|---|
| Game Frontend | 진행 화면 | `/play` — 아침·낮 대화·장면 이동·밤 전환, 대화 예산 표시 |
| | 밤 화면 | 노트 선택, 자유 서술, 주장 편집, 제출·결과 |
| | 컴포넌트 | `ObservationCard` · `EvidenceGallery` · `CellResults` · `Retrospective` · `GameplayGuide` |
| Inspector | 개발자 화면 | `/inspector/[attemptId]` · `/harness/[attemptId]` — 하네스 이벤트·판정 근거 |
| Asset | 이미지 | 장면·인물·쿠키 12종 생성, 손상 변형, 매니페스트 관리 |
| | 연출 | 손상 단계별 효과를 이미지에만 적용(글씨에 번지지 않게), 치지직은 코드로 |
| Docs | 콘텐츠 | 이미지 제작서, 데모 가이드 |

### 대표 산출물

- `frontend/app/play/page.tsx` · `frontend/app/inspector/` · `frontend/app/harness/`
- `frontend/components/` — 게임 화면 컴포넌트
- `frontend/public/assets/` — 장면·인물·쿠키 이미지
- `docs/REMAKE_DAY_이미지제작서_v1.md` · `docs/REMAKE_DAY_이미지제작서_쿠키12종.md`
- `docs/demo_guide.md` · `docs/first-play-guide.md`

---

## 5. 이은상 — Frontend Engineer · Mobile

### 역할 정의

화면이 어느 기기에서나 읽히는지 책임진다. 반응형·모바일 대응과 보조 화면을 만들고, 뷰포트 자동 검사와 플레이 검증으로 제출 가능 상태를 보증한다. 플레이테스트 피드백을 받아 결함으로 정리하고 재현 경로를 남긴다.

### 업무 분류

| 대분류 | 중분류 | 소분류 |
|---|---|---|
| Responsive UI | 뷰포트 | 390px · 1440px 기준 대응, 배경 비율(`object-contain`), 안전 영역 |
| | 가독성 | 안내 글씨와 대화 본문의 크기 분리, 상시 흐림 제거, 대비 확보 |
| Mobile | 플러터 | 모바일 클라이언트 검토 및 대응 |
| UI Support | 보조 화면 | 플레이 안내, 설정, 오류 토스트, 타이핑 인디케이터 |
| QA | 자동 검사 | `frontend/tests/*.cjs` — Playwright headless, `headless: true` 고정 |
| | 플레이 검증 | 테스터 회차 기록, 결함 로그, 재현 경로, 회귀 확인 |
| Release | 기동 검증 | `start_demo.sh` · `stop_demo.sh`, health 확인, 외부망 접속 확인 |

### 대표 산출물

- `frontend/tests/` — 뷰포트·플로우 자동 검사 (`five-loop-flow` · `gameplay-clarity` · `scene-illustrations` · `connected-investigation`)
- `frontend/components/ErrorToast.tsx` · `TypingIndicator.tsx` · `GameplayGuide.tsx`
- `docs/review-verification/` — 날짜별 검증 기록·결함 로그
- `start_demo.sh` · `stop_demo.sh`

---

## 6. 발표 · Q&A 분담

| 구간 | 담당 |
|---|---|
| 발표 전체 | 류준 |
| 모델 평가 · 하네스 구간 | 장민석 |
| 시연 조작 | 신채연 |
| 아키텍처 · 계약 질문 | 류준 |
| 숫자 · 게이트 · 모델 선정 질문 | 장민석 |
| 게임 규칙 · 채점 · 재현성 질문 | 신채연 |
| 화면 · 연출 · 에셋 질문 | 김충식 |
| 모바일 · 검증 · 배포 질문 | 이은상 |

---

## 7. 문서 지도

| 문서 | 지위 |
|---|---|
| 본 문서 | **팀 역할 정본** |
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

`docs/jekyll.md`는 **하루 단위로, 최신 날짜가 위로** 오도록 작성한다. 한 사람이 여러 영역을 건드린 날은 영역별로 나눠 적되, 담당 표기는 그 작업을 주도한 사람 기준으로 한다.

---

## 9. 변경 이력

| 버전 | 날짜 | 내용 |
|---|---|---|
| v2.0 | 2026-09-13 | 역할 정의를 업무 분류·대표 산출물 수준으로 확장. Surface 경계·발표 분담·문서 지도 추가. 장민석·신채연의 백엔드 분담은 제안 상태 |
| v1.0 | 2026-09-01 | 최초 작성 — 이름과 한 줄 역할만 |
