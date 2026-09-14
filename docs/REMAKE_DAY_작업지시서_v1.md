# REMAKE DAY — 작업지시서 v1 (Claude Code용)

> 명세: 기획서 v8.1 · 이미지 제작서 v1 + 부록 N · 목업 HTML
> 순서: **백엔드 P0→P7 → 프론트 F0→F3.** 프론트는 백엔드 P2가 돌기 전엔 시작하지 않는다
> 이 문서는 Claude Code에게 **한 번에 한 단계씩** 준다. 전체를 한 세션에 주지 않는다

---

## 0. Claude Code에게 일을 시키는 방법

Life Tutorial에서 검증된 순서 그대로. 단계마다 네 박자.

```
① 설계서   Claude Code가 그 단계의 설계 문서를 먼저 쓴다 (docs/design/{P번호}-{이름}.md)
           → 사람이 읽고 승인. 승인 전엔 코드 없음
② 테스트   실패하는 테스트를 먼저 쓴다. 도메인 규칙은 전부 여기서 고정
③ 구현     테스트가 통과할 때까지. 스키마·포트·어댑터 순서
④ 기록     실측값과 결정을 docs/devlog.md에 그날 날짜로. "고쳤다"가 아니라 "몇에서 몇으로"
```

**세션 시작 프롬프트 형식**

```
너는 REMAKE DAY 백엔드를 만든다. 명세는 docs/spec/기획서_v8.1.md이고, 이 세션의 범위는
작업지시서 §P{번호}만이다. 다른 단계의 코드를 미리 쓰지 않는다.
먼저 docs/design/P{번호}-*.md에 설계서를 쓰고 멈춘다. 내가 승인하면 테스트부터 시작한다.
§1의 원칙을 위반하는 순간 멈추고 나에게 묻는다.
```

**하지 말 것**

- 기획서에 없는 기능을 "있으면 좋을 것 같아서" 넣지 않는다. 범위는 줄이기만 가능
- 코어(`engine/`)에 시나리오 고유 명사를 쓰지 않는다. 채연·민석·대피소·돼지 전부. CI가 막지만, CI가 막기 전에 안 쓴다
- LLM이 숫자를 계산하게 하지 않는다. 의심도·신뢰도·점수·예산은 코드
- 조언자(Advisor)·정리자(Normalizer) 프롬프트에 스토리보드나 정답 주장을 넣지 않는다. 절대
- 시드 데이터를 `ensure_seeded` early-return 패턴으로 만들지 않는다. 시드가 바뀌면 재기동으로 DB에 반영돼야 한다 (Life Tutorial 8/29 결함)
- 프론트에서 외부 CDN을 참조하지 않는다. 폰트 셀프호스트

---

## 1. 원칙 (전 단계 공통)

| # | 원칙 | 검증 |
|---|---|---|
| 1 | 헥사고날 + DDD. 도메인 → 애플리케이션 → 어댑터. 의존은 안쪽으로만 | import-linter, CI |
| 2 | 포트는 셋: `LLMPort`, `ToolPort`, `ScenarioPort`. 시나리오는 어댑터 인스턴스 | 코어 diff 0줄 (P7) |
| 3 | 계산은 코드, 판단은 LLM (기획서 8.8) | 도메인 계층 LLM import 0 |
| 4 | 모든 LLM 출력은 JSON 스키마 + 검증 + 재시도. 실패 시 폴백 명시 | 통과율 계측 |
| 5 | 로그 먼저. 부록 C 이벤트가 없으면 기능이 아니다 | 이벤트별 테스트 |
| 6 | 코어에 금칙어 0건: 인물명 5개, 대피소, 돼지, 돈사, 축산, 살처분 | CI grep |
| 7 | 시크릿은 `.env`만. 코드·ini·문서에 없음 | grep |
| 8 | 버전 태그 `BE vX.Y.Z` / `FE vX.Y.Z`, 커밋 메시지에 명시 | — |
| 9 | 측정하지 않은 것은 주장하지 않는다. devlog에 숫자 없는 "개선" 금지 | 리뷰 |

---

## 2. 모델 구성 — 몇 개 쓰나

**운영 LLM 2개 + 임베딩 1개. 벤치마크용 하위 후보 3개.**

| 계층 | 역할 | 모델 | 위치 | 이유 |
|---|---|---|---|---|
| 하위 | Agent (NPC 4인) | **로컬 소형 1개** — 후보 3종 중 벤치마크로 확정 | 홈서버 GPU | 7세 체크리스트(기획서 5.2)를 4/5 넘으면서 가장 싼 것. "NPC가 일곱 살 같은 건 모델 선택" |
| 중위 | Advisor, Normalizer | **상위와 같은 모델, 프롬프트만 다름** | 온라인 | 로그만 읽고 사실을 답하는 일. 별도 모델 둘 이유 없음. 격리는 프롬프트·입력으로 |
| 상위 | Manager, Evaluator | **Gemini flash-lite 1개** | 온라인 | 긴 로그·다단계 판단·채점 일관성. Life Tutorial에서 분류 100%·날조 0 실적 |
| 임베딩 | 정답 주장 검색, 노트 검색 | **gemini-embedding 1개** | 온라인 | 이미 쓰던 것. 1,536차원 스키마 그대로. VRAM은 NPC 모델에 몰아준다 |

**하위 후보 3종** (P6 벤치마크에서 하나로)

| 후보 | 크기 | 예상 |
|---|---|---|
| exaone3.5:2.4b | ~2GB | 한국어 강함. 7세보다 똑똑할 수 있음 → 체크리스트 2·3번 실패 위험 |
| gemma3:4b | ~3.3GB | 균형. 1순위 예상 |
| qwen3:1.7b 또는 llama3.2:3b | ~1.5~2GB | 3세처럼 나올 위험. 하한 확인용 |

**폴백**: 하위 후보 셋이 다 체크리스트 4/5를 못 넘으면 → 하위도 Gemini flash-lite에 "7세 정책" 시스템 프롬프트. 그 경우 devlog에 "폴백을 썼다"고 적고 발표에서도 말한다.

**VRAM**: 16GB 한 장. NPC 모델 하나만 상주(≤4GB). Manager·Evaluator가 온라인이라 Life Tutorial의 "두 모델 공존" 문제가 없다. `OLLAMA_NUM_PARALLEL`은 NPC 4인 동시 판단이 있으니 **4**로 시작하고 P6에서 실측.

**`.env` 스위치**

```
NPC_LLM_PROVIDER=ollama|gemini|fake        NPC_LLM_MODEL=gemma3:4b
ADVISOR_LLM_PROVIDER=gemini|fake            (Normalizer도 같은 값 사용)
MANAGER_LLM_PROVIDER=gemini|fake            (Evaluator도 같은 값 사용)
EMBEDDING_PROVIDER=gemini|fake
SYSTEM_HARNESS=on|off                       ← ablation용. 기본 on
COOKIE_AB=on|off                            ← A/B 배정 (세션 해시로 50:50)
PAW_REASON_AB=on|off
```

`fake`는 전 역할에 있어야 한다. 백엔드 테스트와 프론트 개발은 전부 `fake`로 돈다.

---

## 3. 리포 구조

```
remake-day/
  backend/
    engine/                     ← BeyondBob Engine. 시나리오 모름
      domain/                   순수 함수. 의심·신뢰·예산·이상자·소문·점수·충돌·쿠키선택·원숭이손조건
      application/              오케스트레이션. Planner/Agent/Manager/Advisor/Normalizer/Evaluator 유스케이스
      ports/                    LLMPort, ToolPort, ScenarioPort, RepoPort, ClockPort
    adapters/
      llm/                      ollama, gemini, fake
      embedding/
      persistence/              SQLAlchemy 2.0 + Alembic (Life Tutorial 그대로)
      http/                     FastAPI 라우터
      scenario_a/               ← 대피소. 인물·비트·정답 주장·쿠키 문장·프롬프트·금칙어
      scenario_audit/           ← P7. 감사 대응
    tests/
      domain/  application/  adapters/  contract/  eval/
    scripts/
      run_selfplay.py  run_age7_check.py  run_judge_consistency.py  run_leak_test.py  warmup.sh
  frontend/                     ← F단계
  docs/
    spec/  design/  adr/  devlog.md  metrics.yml
```

`scenario_a/`는 **private 서브모듈 또는 `.gitignore`**. 공개 리포에는 `scenario_example/`(인물명 A·B·C, 정답 주장 3개짜리 더미)만 둔다. 개발 일지도 공개 전 금칙어 grep.

---

## 4. 백엔드 단계

각 단계의 **완료 조건**이 다음 단계의 시작 조건이다. 완료 조건에 숫자가 있으면 devlog에 그 숫자를 적는다.

### P0 · 뼈대 (1일)

**만드는 것**
- 헥사고날 스캐폴딩, 포트 3개 인터페이스, `fake` 어댑터 전 역할
- LLM 포트 팩토리 (`.env` 스위치 §2)
- **로그 테이블 전부** (부록 C 17개 이벤트) + 기록 유스케이스. 필드 하나도 빼지 않는다
- `ScenarioPort` 인터페이스: 인물·비트·정답 주장·쿠키 문장·금칙어·프롬프트 조각을 내려주는 메서드
- `scenario_a` 어댑터에 부록 A 시드. 시드 동기화는 매 기동 시 upsert
- CI: pytest, import-linter, 코어 금칙어 grep, `scenario_a` 누락 시 `scenario_example`로 기동

**완료 조건**
- `GET /health`가 활성 모델 3종·시나리오 이름·하네스 on/off를 반환
- 17개 이벤트 각각 기록·조회 테스트 통과
- CI 초록. 코어에 금칙어 0건

### P1 · 하루 (2일) — 방어선 ①

**만드는 것**
- 세션·판·회차 상태 머신: `attempt → loop(1..5) → beat(1..6) → night`. 도메인 순수 함수
- 발화 예산 8→4, 비트 넘기기 무료
- `Agent` 유스케이스: NPC 개별 판단. 입력 = Planner 방침 + 상태 + 발화 + 적용 규칙. 출력 스키마 `{reply, suspicion_delta, trust_delta, tool_call?, plan_change?}`
- `Planner`: 회차 시작 시 NPC별 비트 계획
- **시스템 하네스**: 스키마 검증 + 금칙어 검출(ScenarioPort에서 받음) + 소실 인물 언급 검출 → 거부·재생성(최대 2회) → 폴백 대사
- 의심도·신뢰도 도메인 함수 (임계 60, 신뢰는 비용 행동에서만, 5% 잔류)
- `ask_npc` 도구: NPC↔NPC 확인, 호출 시 대상 의심도 +, 예산 회차당 2
- **7세 정책 프롬프트 조각** (ScenarioPort가 아니라 engine에: "직접 질문엔 사실대로 / 왜엔 몰라 / 3턴 기억 / 문자 그대로")

**API**
```
POST /sessions                      → attempt 시작 (진입 화면 뒤)
POST /sessions/{id}/loops           → 회차 시작, 아침 텍스트·손상 단계 반환
POST /loops/{id}/utterances         {target, text} → NPC 응답, 남은 예산, 비트
POST /loops/{id}/beats/next         → 다음 비트, 서술문, (원숭이손 오퍼?)
GET  /loops/{id}/notes              → 노트 (파편·확인 사실·규칙)
```

**완료 조건**
- `fake`로 한 회차 6비트 완주 E2E 테스트
- 하네스 ON: 금칙어 발화 0건 / OFF: 주입된 금칙 프롬프트에서 누설 재현 (ablation 테스트 2건)
- 의심 임계 돌파 시 반대 행동 테스트
- `ask_npc` 불일치 발각 → 대상 의심도 상승 테스트

### P2 · 밤 (2일) — 방어선 ②의 절반

**만드는 것**
- `Normalizer`: 서술 + 탭한 노트 → 주장 ≤8. 스키마 `{claims: [str]}`. **덧붙임 검사**: 주장의 명사·숫자 토큰이 입력에 없으면 삭제 (Life Tutorial `value_fabrication` 이식)
- 확인 1회: `PATCH /nights/{id}/claims` 1번만 허용
- 정답 주장 임베딩 (시드 시 1회) + 그 회차 부작용 주장 생성(Evaluator, 규칙 로그에서)
- 주장별 RAG top 3 → `Evaluator` 판정 `{truth_claim_id, verdict: confirmed|partial|none, matched_user_claim}`
- 칸별 점수: 확인 비율, **80% 이상 만점**, 미만 비례. 1회차는 부작용 칸 제외. 도메인 순수 함수
- 총점 → 50% 판정 → `death` 또는 `clear` 이벤트. 멸망 방식(트럭/조용히/폐쇄)은 이상자 수·소문 지수로
- 오답 주장 로그 (감점 없음)

**API**
```
POST /loops/{id}/night/draft        {tapped_note_ids, free_text} → claims
PATCH /nights/{id}/claims           {claims} (1회)
POST /nights/{id}/submit            → {total, passed, world_outcome}   ← 칸별 점수는 반환하지 않음
```

**완료 조건**
- 소설 통과 테스트: 세계 접촉 없는 서술 10종 → 전부 50% 미만
- 두루뭉술 테스트: "병이 도는 것 같아" → 0
- 정답 서술 → 100% (부작용 제외 3칸)
- 덧붙임 테스트: 입력에 없는 인물·숫자가 주장에 나오면 실패
- 판정 일관성: 같은 주장 세트 10회 → verdict 일치율 ≥ 95%

### P3 · 신의개입 (1.5일) — 방어선 ②의 나머지

**만드는 것**
- `Advisor` 입력 = 그 회차 Evaluator 원인 체인 **만**. 스토리보드 접근 경로가 코드상 존재하지 않아야 한다 (테스트로 고정)
- 질문 3회, 답 형식 4종 고정 `{answer: 맞다|틀리다|그런 일은 없었다|그건 알 수 없다, detail?}`. "맞다"는 노트에 `confirmed` 저장
- 규칙 후보 3개 (부록 B 스키마) + 직접 쓰기 → 스키마 매핑, 실패 시 거부 사유 반환
- 규칙 누적, 충돌 감지(도메인), 손상 +1
- Advisor 메모리 소거: 회차마다 새 컨텍스트

**API**
```
POST /nights/{id}/questions         {text} → {answer, detail, remaining}
GET  /nights/{id}/options           → 3 options
POST /nights/{id}/rule              {choice: 1|2|3|custom, custom_text?} → rule, conflicts
```

**완료 조건**
- Advisor 프롬프트 빌더에 ScenarioPort 의존 없음 (import 테스트)
- 4형식 외 답 0건 (스키마 테스트)
- 규칙 충돌 감지 테스트 (같은 target·beat에 suppress/enforce)
- 직접 쓰기 "아무도 안 아프다" → 거부

### P4 · Manager (1.5일) — 방어선 ③

**만드는 것**
- 비트 경계 점검: 입력 = 전체 NPC 상태 + 규칙 + 손상 + 전날 점수. 출력 = 패치 `{npc, memory_delete|plan_patch, reason}` 예산 2/회차
- 원숭이손: 1회차 무조건, 이후 전날 ≥40% 시 1회, 판당 최대 2. `{rule, shown_reason|null, hidden_side_effect}`. `PAW_REASON_AB`로 reason 표시 50:50
- 밤의 결정: 이상자 수·소문 지수 → 트럭/조용히/폐쇄/무사. 도메인 함수, Manager는 사유만
- Manager 메모리 유지 (회차 간, 판 간 전날 점수)
- Evaluator 원인 체인 생성 (하루 종료 시)

**완료 조건**
- 보정 예산 초과 불가 테스트
- 원숭이손 출현 조건 테스트 (1회차 100% / 39% 다음날 0 / 40% 다음날 1 / 3번째 없음)
- 원숭이손 `hidden_side_effect`가 API 응답에 노출되지 않음 (인스펙터 엔드포인트에만)
- 원인 체인이 Advisor 입력으로 연결되는 E2E

### P5 · 판 종료·쿠키·재도전 (1일) — 방어선 ④

**만드는 것**
- 5회차 밤 종료 처리: 50%↑ 클리어 / 50%↓ 멸망 종료, 신의개입 없음
- 100% → `understood`, "돼지" 확인 시 `understood_all` (정체 칸 확인 목록에 pig 주장 포함 여부)
- **쿠키 선택** (도메인 순수 함수): 50%↑만 / 가장 낮은 칸(동점 시 원인→동기→부작용→정체) / 강도 = 점수 구간 기본 + 이미 본 칸이면 +1, 상한 3 / 12개 다 봤으면 없음. 부작용 쿠키는 템플릿 채움
- `COOKIE_AB` 배정 (세션 해시)
- 재도전: 새 attempt, 노트·규칙 비움, `prior_cell_results`·`cookies_seen` 유지
- 하네스 공개 엔드포인트 (100%만), 인스펙터 엔드포인트 (전 이벤트 + Manager 패치 + 원숭이손 출처 + 채점 근거)

**API**
```
POST /nights/{id}/submit            → 5회차면 {closed_by, cells, cookie?}
POST /sessions                      {prior_attempt_id?} → 재도전
GET  /attempts/{id}/harness         (100%만 200, 아니면 403)
GET  /attempts/{id}/inspector       (개발자 토큰)
```

**완료 조건**
- 쿠키 선택 함수 테스트 12케이스 (칸×강도) + 중복 회피 + 12개 소진
- 정체 쿠키가 다른 세 칸 미달 상태에서 나오지 않음
- 하네스 엔드포인트 99%에서 403

### P6 · 검증 러너 (1일) — 1주차 게이트의 도구

**만드는 것**
- `run_age7_check.py`: 후보 모델 × 5항목 × 20발화 → 통과율 마크다운
- `run_selfplay.py`: LLM 에이전트가 플레이어. 5회차 × N판 → 파악 곡선, 50% 도달 회차 분포, 100% 도달 판 수. 페르소나 3종(성실·산탄총·침묵)
- `run_leak_test.py`: 하네스 ON/OFF × 회차 → 정체 누설률
- `run_judge_consistency.py`: 같은 주장 반복 → 일치율; 소설 10종 → 통과율
- `run_paw_eval.py`: 원숭이손 수락 후/거부 후 점수 변화 (자기대전 기반)
- 전부 `docs/metrics.yml`에 한 줄 append하는 형식 (Life Tutorial 대시보드 그대로)

**완료 조건 = 1주차 게이트 (기획서 12.4)**
- 하위 후보 중 하나가 7세 체크리스트 4/5 이상 → 그 모델로 확정. 없으면 폴백 결정 기록
- 자기대전 4회차 50% 근처, 재도전 2~3판 내 100% 등장. 아니면 임계 80% 조정 → 재실행
- 하네스 OFF 누설률이 ON 대비 유의미하게 높음 (아니면 ablation 데모 불가 → 금칙어 주입 방식 재검토)
- 판정 일치율 ≥ 95%, 소설 통과 0/10

### P7 · 전이 어댑터 (0.5일) — 방어선 ⑤

**만드는 것**
- `scenario_audit/`: 감사 대응. 인물 3+2, 비트 6, 정답 주장 4칸, 쿠키 12, 금칙어, 프롬프트 조각
- `.env` `SCENARIO=a|audit` 스위치

**완료 조건**
- `git diff --stat engine/` = 0줄
- 감사 시나리오로 P1~P5 E2E 통과
- 인스펙터가 같은 형식으로 열림

**여기까지 백엔드 총 10.5일.** 2주차 수요일에 끝난다. 프론트는 P2 완료 시점(1주차 목)부터 병행 시작.

---

## 5. 프론트 단계

명세는 목업 HTML(`REMAKE_DAY_목업.html`)이다. 화면·흐름·톤을 그대로 옮긴다. 새로 디자인하지 않는다.

### F0 · 계약·스캐폴딩 (0.5일)

- Next.js + TS strict + Tailwind (Life Tutorial 구성 그대로). 포트 3100
- API 계약 파일 (`contracts/api.ts`) — §4의 엔드포인트 전부. 백엔드 `fake`와 MSW 둘 다 계약 통과 (`npm run check:contract`)
- 폰트 셀프호스트: Noto Serif KR 서브셋. **외부 CDN 0건**
- 디자인 토큰: `--ink #1C2340 --paper #EDE8DC --orange #C8722E --void #000`. 목업 CSS를 토큰으로 승격
- 이미지 매핑 테이블: `(beat, damage_level) → C/D 파일`, `(npc, state) → E 파일`, `(cell, level) → N 파일`. **LLM 출력은 이미지 선택에 관여하지 않는다**

### F1 · 한 판 흐름 (2일)

목업의 화면을 순서대로 실제 API에 연결. 각 화면은 목업의 해당 섹션이 스펙.

| 화면 | 목업 id | API |
|---|---|---|
| 진입 (3줄) | `#entry` | `POST /sessions` |
| 아침 (손상 3단계 판 밀림은 CSS transform) | `#morning` | `POST /loops` |
| 대화 (헤더 이미지·비트 6·NPC 4·눈금) | `#chat` | `/utterances`, `/beats/next`, `/notes` |
| 관리자 방송 팝업 | `#mgr` | beat 응답의 `broadcast` |
| 원숭이손 팝업 (reason 표시는 서버가 결정) | `#paw` | beat 응답의 `paw_offer` |
| 밤 — 노트 탭 + 서술 | `#night` | `/night/draft` |
| 정리 확인 (1회 수정) | `#normal` | `PATCH /claims` |
| 점수 (총점만) | `#score` | `/submit` |
| 멸망 전환 3종 | `#doom` | `world_outcome` |
| 신의개입 질문·선택지 | `#god` | `/questions`, `/options`, `/rule` |
| 클리어 + **치지직 쿠키** | `#clear` + 신규 | `/submit` 5회차 응답의 `cookie` |
| 멸망 종료 | `#doomend` | |
| 하네스 공개 | 신규 (M01) | `/harness` |

- 치지직: 이미지 제작서 부록 N.3 타임라인 그대로. `prefers-reduced-motion` 대응
- 한글 IME Enter 가드 (Life Tutorial 해결책 이식)
- 재도전: 새 세션, 이전 칸별 결과 표시

### F2 · 노트·인스펙터 (1일)

- 노트 패널: 파편·확인 사실·규칙과 관찰. 밤에 탭해서 답안 삽입
- 인스펙터 (`/inspector/{attempt}`, 개발자 토큰): 이벤트 타임라인, Manager 패치, 원숭이손 출처, 채점 근거 인용. 기획서 8.9 형식
- 커리어·감사 어댑터 진입 링크 (같은 랜딩)

### F3 · 배포·시연 (0.5일)

- Vercel 프론트 + Cloudflare 터널 백엔드 (Life Tutorial B안 그대로). 밤 채점 파이프라인이 100초 안에 끝나는지 실측
- 소개 문구 = 진입 3줄. 스크린샷·메타 태그에 금칙어 0
- 빈 전송 시연 스크립트 (발화·질문·서술 예시 문장)
- `/licenses`: 폰트 OFL, 생성 이미지 출처

**프론트 총 4일.** 백엔드와 겹쳐 2주차 금요일에 끝난다. 3주차는 검증·발표.

---

## 6. 일정 요약

| 주 | 월 | 화 | 수 | 목 | 금 |
|---|---|---|---|---|---|
| 1 | P0 | P1 | P1 | P2 · **F0 시작** | P2 · **게이트 준비(P6 러너 일부)** |
| 2 | P3 · F1 | P3/P4 · F1 | P4 · F2 | P5 · F2 | P6 게이트 실행 · P7 · F3 |
| 3 | 실사용 로그 수집 · 벤치마크 | 이미지 D군 후처리 · 튜닝 | 발표 자료 | 리허설 | 버퍼 |

**1주차 금요일 게이트가 P6에 걸려 있으므로 P6의 `run_age7_check.py`는 P1 직후 먼저 만든다.** 순서상 P6이지만 착수는 1주차 화요일.

---

## 7. 단계별 Claude Code 프롬프트 예시

**P1 시작**
```
범위: 작업지시서 §P1. 명세: 기획서 v8.1 §4.1, §5.1~5.4, §8.2 Planner/Agent, §8.6 시스템 하네스.
먼저 docs/design/P1-day.md를 쓴다. 포함: 상태 머신 다이어그램, Agent 출력 스키마, 하네스 거부→재생성→폴백 흐름,
의심·신뢰 계산식과 임계, 테스트 목록. 코드는 쓰지 않는다. 승인을 기다린다.
```

**P2 시작**
```
범위: §P2. 명세: 기획서 v8.1 §7.1~7.3, §8.2 Normalizer/Evaluator.
Normalizer 프롬프트 빌더는 ScenarioPort를 import하지 않는다 — 이것을 테스트로 먼저 고정한다.
덧붙임 검사는 Life Tutorial insight BC의 value_fabrication 로직을 이식한다 (경로: ...).
칸 만점 임계 80%는 도메인 상수 CELL_FULL_THRESHOLD로 두고 .env로 덮어쓸 수 있게 한다.
```

**게이트 실행**
```
범위: §P6 실행. 후보 모델 3종에 run_age7_check.py, 확정 모델로 run_selfplay.py 30판.
결과를 docs/metrics.yml에 append하고 docs/devlog.md에 "무엇을 재서 어느 모델을 골랐는지"를 숫자로 쓴다.
기획서 12.4의 통과 조건 넷을 각각 PASS/FAIL로 적고, FAIL이면 어떤 손잡이(임계·모델·회차)를 먼저 돌릴지 제안만 한다. 돌리지는 않는다.
```

---

## 8. 완료 정의 (제출 가능 상태)

- 방어선 ①~⑤ 전부 초록 (P1~P5, P7)
- 게이트 4항목 PASS 또는 폴백 결정 기록
- `docs/metrics.yml`에 A 실험 8종 이상 실측값
- 공개 리포에 금칙어 0, `scenario_a` 비공개
- 프론트 실도메인에서 한 판 15분 완주, 콘솔 에러 0
- devlog에 P0~F3 각 단계 날짜·숫자·되돌린 결정
