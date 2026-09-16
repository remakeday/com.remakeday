# 작업 이어하기 — 2026-09-15

> 이 문서 하나만 읽어도 이어서 작업할 수 있게 쓴다.
> 이전 인계(테스터2 착수 시점)는 `HANDOFF-2026-09-09.md`에 보존했다.

## 제출 모델 구성 — 확정 (2026-09-17)

**Core `anthropic:claude-sonnet-5` + NPC `anthropic:claude-haiku-4-5`.** 근거는 `docs/model_evaluation.md` 부록 A.19(Core PCA 0.97·극성 O·eval 0.71, NPC 41문답 실패 0·p50 1.9s, 7세 정책 4/5). 이 조합으로 self-play 5회차 1판을 돌려 이상 없음을 확인했다: 11.7→11.7→16.0→24.8→29.8, 261.5s, 폴백 0, planner 재생성 1(복구), NPC 메타 누설 0, 오류 0(`305d77a6`).

사용자 지시: 이 구성으로 `.env`를 고정한다. 단 **키는 지금 `.env`에서 제거해 두고**(과금 방지), 그 사이 개발·테스트는 로컬 ollama(Core gemma4:12b · NPC kanana1.5:8b, think off)로 한다. 제출(2026-09-20) 때 아래 순서로 전환한다.

1. `backend/.env`(배포 서버의 `.env`도 동일)에서 아래 다섯 줄을 맞춘다 — 키 값은 문서에 적지 않는다.
   ```
   ANTHROPIC_API_KEY=<Anthropic 콘솔 키, sk-ant-로 시작>
   CORE_LLM_PROVIDER=anthropic
   CORE_LLM_MODEL=claude-sonnet-5
   NPC_LLM_PROVIDER=anthropic
   NPC_LLM_MODEL=claude-haiku-4-5
   ```
   `*_LLM_THINK`는 ollama 전용이라 남아 있어도 무시된다. `ANTHROPIC_EFFORT`는 기본 `low`.
2. 백엔드 재기동(설정은 `get_settings()` lru_cache라 재기동해야 반영) → `curl localhost:8500/health`의 `models`가 `anthropic:claude-sonnet-5`/`anthropic:claude-haiku-4-5`인지 확인.
3. 확인 1판: `cd backend && PYTHONPATH=. .venv/bin/python scripts/run_selfplay.py --dev-login --loops 5 --n 1 -v`(계정 하루 5판 한도에 포함). 크래시·폴백 0이면 끝.
4. Anthropic 콘솔 지출 한도 설정 확인(판당 약 $0.8 추정: Core Sonnet ~$0.7 + NPC Haiku ~$0.1, `docs/apiscenario.md` §1.3b).
5. 롤백은 provider 두 줄을 `ollama`, 모델을 `gemma4:12b`/`kanana1.5:8b-q4km`로 되돌리고 재기동.

운영 관찰 항목(A.19 판정): advisor p95 5~7s 흔들림(C11 경계) · planner `beats` 상한 6이 Anthropic 구조화 출력에서 강제되지 않아 가끔 재생성(프롬프트 쪽 상한 명시나 후처리 자르기 검토) · 3턴 망각은 모든 NPC 모델 공통 약점.

## 현재 상태 — NPC 대화 개선

NPC 정책 `npc-dialogue-2`를 적용했다. ‘7세’는 쉬운 말투의 기준으로 두고 강제 회피·3줄 망각을 제거했다. 인물별 성격·기본 지식과 실제 당일 경험을 분리했다. **사용자 지시로 장면당 캐릭터 1회 제한을 복구했다.** 다른 캐릭터에게는 말할 수 있고, 다음 장면에서 같은 캐릭터와 다시 대화할 수 있다. 하루 예산 8/7/6/5/4는 유지한다. 발화별 UUID와 루프 잠금으로 중복 요청·저장 실패 때 대화 예산과 기록이 어긋나지 않게 했다. 같은 성공 요청의 재전송은 제한에 걸리지 않고 저장된 답변을 반환한다.

네 NPC 모두 새 루프에서 당일 기억을 초기화하며 신뢰 5%만 남는다. 민석만 과거 대화를 기억하는 예외는 없다. 관리자 삭제는 지정 출처와 연관 문답을 가리고, 실제로 다시 본 경험으로 재학습할 수 있다. 기존 문자열 기억은 읽기 호환하며 DB 마이그레이션은 없다. 구버전이 이미 잘라 버린 기억은 복구할 수 없으므로 새 판에서 확인한다.

**현재 로컬 구성: NPC·Core `ollama:gemma4:12b`, 둘 다 think off, embedding gemini.** NPC는 실제 행동·출처 설명의 부분 개선을 근거로 변경했다. 최종 Gemma 41문답에서 서비스 실패·재생성 0, 중간값 2.599초·p95 3.053초다. 인물 부재 추측과 현재 전언 회피가 남아 최초 의미 품질 목표에는 미달한다. 반복되는 기억·전언 문제를 모두 해결했다고 간주하지 않는다.

백엔드 **460개 통과**, TypeScript 검사 및 헤드리스 UI **4종 통과**. 자세한 변경·실행 상태는 [검증 기록](review-verification/2026-09-15-npc-dialogue/README.md), 모델 판단과 남은 문제는 [평가 정본](model_evaluation.md)의 맨 위에 있다. 기존 미커밋 작업과 플레이 기록은 유지했으며 커밋·푸시하지 않았다.

추가 복구 검증: 백엔드 460개, TypeScript, 헤드리스 `npc-followup`·`gameplay-clarity`·`connected-investigation`이 통과했다. 마지막 검사는 첫 실행의 이미지 로딩 타이밍 실패를 조사한 뒤 원본 재실행이 통과했다. 평가 러너도 다음 장면에서 후속 질문하도록 맞췄고, 마지막 장면은 후속 질문 생략을 기록한다. 모델 호출 없는 dry-run은 40문답·구조 검사 294개를 통과했다. BGM은 진입 자동재생 시도와 차단 시 첫 조작 재시도, 기존 켜기·끄기 버튼을 유지한다. 백엔드 8500·프런트엔드 3500을 재가동했다.

다음 플레이에서는 장면당 캐릭터 1회 제한과 다음 장면에서의 재개, 오늘 경험과 지난 루프의 구분, 현재 전달한 말에 대한 반응, 네 인물의 관심사 차이를 관찰한다. 사람이 참여한 블라인드 페르소나 평가와 새 참가자의 5회차 플레이는 아직 하지 않았다.

## 이전 상태 — 2026-09-14 기록

**모델 선정 전부 완료(2026-09-14) — 운영 구성: Core `ollama:gemma4:12b`(think off) · NPC `ollama:kanana1.5:8b-q4km`(Apache 2.0) · embedding gemini.** Core는 §5.3 채택 선언(테스트 393 passed·실서버 검증), NPC는 라이선스 조사(A.17 — EXAONE 3.5 연구 전용 확정)와 상업 후보 실측을 거쳐 kanana로 교체(교체 전 루프 스모크 A.18 통과: 완주·폴백 0/16·회피 0/21·혼입 0). **어댑터 패턴 보장 — 롤백은 `.env` `NPC_LLM_MODEL=exaone3.5:7.8b` 한 줄**(exaone 7.8b는 롤백용 로컬 유지, 평가용 임시 모델·GGUF ~9GB 정리). 운영 관찰 항목: 사실 질문 회피·질문 관련성·단답 경향(스모크 11.4자). D2는 Gemini 이탈로 소멸. 커밋·푸시(09c3f23)·start_demo 실기동 완료, 첫 실플레이(판 da38de28) 피드백 6건 접수 → **개선 배치 진행 중: 1/3 채점 신뢰 3종 완료**(temp 0 회귀 고정·단조 잠금 ratchet·덩어리 칸 해소 — 실판 오프라인 검산으로 요동 케이스 차단 확인) · **2/3 개입·NPC 완료**(신의 질문=단서 해금 10리드+디렉션, dormant 탐사 행동 5종+어휘 4종, 직접쓰기 대안 3후보, AGE7 v2+메모리 창 절단 — 419 passed, 재측정 7세 4/5·망각 1.00·누설 0). · **3/3 진실 연출·회고 UX 완료** — 진실 단계 공개(서버 필터 `truth_reveal`·`ending_lines_by_cell` 셀 ≥80 게이팅, 못 맞춘 칸 "?"+재도전 카피), 신규 `GET /attempts/{id}/journey`(5밤 후 공개), 회고를 "추리 여정"으로 재작성(개발 데이터는 접힘 강등), 질문 답변 해금 단서 강조 카드. backend **425 passed** · build 통과 · **UI 테스트 4종 통과**(신규 UX 반영 갱신) · 스모크(pigfarm_test)에서 해금 노트 적립·journey 게이트 실동작 확인. **개선 배치 3/3 전부 완료 — 서버 재기동됨(health npc kanana·core gemma4:12b·/play 200), 테스터 재플레이 대기.** 재플레이 관찰 포인트: ①몰라 비율(이전 24%) ②동일 제출 점수 요동(ratchet) ③질문당 새 단서 1개 체감 ④직접 규칙의 어휘 다양성(설명한다 수렴 해소) ⑤결말 "?" 잠금 체감 ⑥회고 여정 가독성.

---

## 지금 바로 할 일 (우선순위 순)

### 1. `evaluator_verdict` 통제를 실플레이 제출문으로 교체 — ✅ **완료 (2026-09-14)**

자작 3건 → 실플레이 14건으로 교체하고(기대 판정 사전 등록: `docs/review-verification/2026-09-14-eval-cases/CONFIRMED-eval-cases.md`) `--roles evaluator`로 재측정했다. 결과는 **부록 A.8** (`docs/model_evaluation.md`).

- **우열이 역전됐다**: 기준선 1.00 → **0.36**(4셀 중 최하), `gemma4:12b-N` 0.67 → **0.57**(최상). "기준선이 통과한 역할을 떨어뜨렸다"는 A.7의 비열등 차단 전제가 소멸했다
- "`gemma4`가 엄격한 방향으로 틀린다"는 우려도 뒤집혔다 — 기준선이 근거 없는 partial을 내는 **관대한 방향** 오답(A1·A5·B2·D1)이었다
- 새로 발견된 두 결함은 모델 교체로 안 닫힌다: **partial 정의는 4셀 공통 실패**(15회 중 0회), **덩어리 칸(`source_claims` 8칸 초과 몰아넣기)은 4셀 공통 취약**. 각각 `review.md` 5순위·별도 파이프라인 수정 사안
- §5.3 비열등 최종 선언은 보류 — VRAM(7.51 vs 7.49)·evl 지연(2,179 vs 997ms)의 문자적 비교가 남아 있다

### 2. Stage 3 — 동시성 — ✅ **완료 (2026-09-14)**

`--stage concurrency`를 러너에 구현해 실행했다. 결과는 **부록 A.9**. 두 후보 모두 NPC(`exaone3.5:7.8b`, 실측 4.83 GiB)와 교대 구간 무축출 공존 — **통과**.

```
gemma4:12b-N  pair peak 12.34 GiB · GPU 13,326/16,311 MiB (여유 ~2.9 GiB)
gemma4:e4b-N  pair peak  7.89 GiB · GPU  9,520/16,311 MiB
```

관측 1건: `e4b` 초기 로드 때 NPC 1회성 축출(다음 콜에서 1초 재로드 후 안정). A.9에 기록.

### 3. Stage 4 — 루프 스모크 — ✅ **완료 (2026-09-14)**

`--stage loop`를 구현해 실행했다. 결과는 **부록 A.10**, `metrics.yml` 2줄(`stage: loop`).

- **방식 (a) 채택** — 기존 `run_selfplay.py`가 HTTP 방식임을 확인하고 재사용. `scripts/loop_app.py` 래퍼가 컴포지션 루트의 `get_core_llm`만 러너의 `ThinkingOllamaLLM(think=False)`로 교체 — **프로덕션 엔진 코드·`.env` 무변경**, `pigfarm_test` DB(테스터 판 무접촉), 포트 8600
- **두 후보 모두 통과** — 1회차(낮 발화→비트→밤 제출→개입) 완주, 크래시 0, 폴백 0/17, thinking 0자(C9 검증). `12b` 61.1s / `e4b` 35.6s. `e4b`만 하네스 재시도 2회(재생성 해소, 폴백 아님)
- 플레이어 모델은 상주 NPC(exaone) 재사용 — 제3 모델 로드 시 12b 셀에서 축출 나기 때문
- 1차 실행은 계측 결함(5밤 게이트에 잠긴 인스펙터 조회)으로 `gate_pass=false` 오기록 — DB 직접 집계로 교체 후 재실행이 정본. 경위는 A.10

### 4. 결정이 필요한 항목 ← **다음 할 일. 여기부터.**

| # | 결정 | 배경 |
|---|---|---|
| ~~D1~~ | ~~**Gemini 페이싱 값**~~ → **해소 (2026-09-14, A.11)** | 실측: 유료 키 40콜/55.4s(약 43 RPM) 429 0건. **사용자 결정: 판단 기준은 무료 티어(10 RPM)로 고정 + 실제로 키를 무료로 교체.** 무료 키 재프로브(A.11 추록): 초소형 콜 20~28s·503 발생·실효 2.7 RPM — **쿼터 이전에 지연이 먼저 무너진다. 무료 기준에서 Gemini raw는 C11을 10배 초과, 온라인 대안 성립 안 함.** 단 시점 한정 측정(수요 스파이크) |
| ~~D2~~ | ~~**현행 운영 Gemini를 thinking OFF로 바꿀지**~~ → **대상 소멸 (2026-09-14)** | Core가 `gemma4:12b-N`(ollama)로 전환돼 운영에서 Gemini가 빠졌다. thinking 제어는 ollama 쪽에 프로덕션 반영됨(`CORE_LLM_THINK=off`). Gemini로 복귀할 일이 생기면 그때 재론 |
| ~~D3~~ | ~~**`teamprofile.md`의 장민석·신채연 분담**~~ → **해소 (2026-09-14)** | v2.0 제안이 사용자가 준 원본(`Masterless_Company_Team_Roles_v1.1`)을 반영하지 않았던 것으로 확인. **v3.0으로 전면 개정** — Masterless와 동일 분담: 류준=TL·AI Agent(하네스), 민석=AI Evaluation(러너·모델 선정), 채연=Full-stack(엔진+게임 프론트·시연), 은상=QA·Release, 충식=Scenario Director. beyondbob `_data/team.yml`도 동기화 |

---

## E7 현재 결과 요약

정본은 `docs/model_evaluation.md`. 부록 A.5·A.6·A.7·A.8·A.9가 Stage 0·1·2·2보강·3이다. 아래는 판단에 필요한 최소치다.

### Stage 2 공식 수치 (A.7 + eval은 A.8 실플레이 통제로 갱신)

| 셀 | PCA | 극성쌍 | adv p95 | eval 기대 *(A.8)* | VRAM | 게이트 |
|---|---|---|---|---|---|---|
| `gemma3:12b` *(기준선)* | 0.70 | **X** | 4,473 | 0.36 | 7.49 | C11·C12·C13 통과 |
| **`gemma4:12b-N`** | **0.90** | **O** | 4,215 | **0.57** | 7.51 | 전부 통과 |
| `gemma4:e4b-N` | 0.70 | X | **2,491** | 0.48 | **3.06** | 전부 통과 |
| `gemini-3-flash-N` | **1.00** | **O** | 2,238 *(raw)* | 0.50 | — | **C11·C13 탈락** |

- **`gemma4:12b-N`에서 RM1이 닫힌다.** 기준선이 못 넘던 PC3·PC8·SPC2를 n=3 전부 통과. 로컬에서 유일
- **A.8에서 eval 우열 역전.** 자작 통제의 1.00(기준선) 대 0.67은 실플레이 통제에서 0.36 대 0.57이 됐다. A.7의 "비열등 아님" 근거는 소멸 — 다만 §5.3 비열등 **선언**은 VRAM(7.51 vs 7.49)·evl 지연의 문자적 비교가 남아 보류 중
- **모델 교체로 안 닫히는 결함 2건(A.8)** — partial 정의는 4셀 공통 실패(15회 중 0회), 덩어리 칸(`source_claims` 8칸 초과 몰아넣기)은 4셀 공통 취약. 채점 프롬프트·파이프라인 수정 사안으로 E7 밖
- **Gemini는 모델이 아니라 페이싱 때문에 탈락.** raw는 가장 빠르고 품질 전 지표 1위
- **`gemma4:e4b-N`은 효율 축의 답.** 기준선과 같은 품질에 속도 1.5~2배, VRAM 41%
- 전 셀 폴백 0.00 · 오류 0 · planner LAR 1.0

### thinking에 대한 답 (RQ-C2)

**Core 역할에서 thinking ON은 비용만 늘린다.** Stage 1에서 `-T` 셀이 C11에 전부 탈락했다(최악 194,589ms, 38배). 품질 이득도 없다 — Gemini는 ON/OFF 동일, `gemma4:12b`는 ON에서 오히려 무너지고(폴백 0.32), `gemma4:e4b`만 소폭 올랐다. **효과가 모델마다 반대 방향이라 일률적으로 말할 수 없다.**

---

## 이 실험에서 지켜야 할 규칙

`docs/model_evaluation.md` §2.3에 전부 있다. 어기면 새 실험이다.

- **실험 중에는 프로덕션 엔진 코드를 바꾸지 않는다.** thinking 제어는 러너 안 서브클래스(`ThinkingOllamaLLM`·`ThinkingGeminiLLM`)로만 실험했다. ~~한 줄도 안 바꿨다~~ → **채택 확정 후(2026-09-14) 승인된 반영 1건**: `ollama_llm.py` think 인자 + `Settings`/`llm_factory` 배선 (§5.3 채택 선언 참조, 테스트 동반). `gemini_llm.py`는 무변경
- **모델별 프롬프트 튜닝 금지.** "이 모델은 프롬프트를 조금 고치면 통과한다"는 발견은 기록만 하고 결과에 반영하지 않는다
- **폴백을 성공으로 집계하지 않는다**
- **단일 종합 점수를 만들지 않는다.** Pareto와 역할별 지표로 본다
- **Stage 0·1은 `metrics.yml`에 적립하지 않는다.** Stage 2부터
- **금지 표현** — §0.2 표 참조. "A가 B보다 낫다", "작은 모델도 충분하다" 같은 문장은 쓰지 않는다

---

## 재현 방법

```bash
cd /home/kimchungsik/projects/com.remakeday/backend

# 환경 확인
curl -s http://localhost:11434/api/tags | python3 -m json.tool | grep '"name"'
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader

# Stage 0 — 프로토콜 호환 (13셀, 몇 분)
.venv/bin/python scripts/run_core_selection.py --stage protocol

# Stage 1 — smoke · advisor 전용 (8셀 × 22문항, 약 45분)
.venv/bin/python scripts/run_core_selection.py --stage smoke --timeout 120

# Stage 2 — formal · 4역할 (4셀 × n=3, 약 20분)
.venv/bin/python scripts/run_core_selection.py --stage formal --n 3 --timeout 120

# Stage 2 보강 — evaluator만 재측정 (실플레이 통제 14건, 약 10분)
.venv/bin/python scripts/run_core_selection.py --stage formal --n 3 --timeout 120 --roles evaluator

# Stage 3 — concurrency · 후보 2 + NPC (셀당 1~2분)
.venv/bin/python scripts/run_core_selection.py --stage concurrency --timeout 120

# Stage 4 — loop · 후보 2 각 1회차 완주 (셀당 1분 내외, pigfarm_test DB·포트 8600 자동)
.venv/bin/python scripts/run_core_selection.py --stage loop --timeout 120
```

모델 5종은 이미 로컬에 있다. 양자화는 전부 Q4_K_M이다.

```
gemma3:12b 7.49 · gemma4:12b 7.51 · gemma4:e4b 3.06 · qwen3.5:9b 5.25 (실측 VRAM GiB)
exaone3.5:7.8b 4.83 (2026-09-14 실측, 종전 표기 4.14)  ← NPC 슬롯. 건드리지 않는다
```

---

## 파일 지도

| 파일 | 내용 |
|---|---|
| `docs/model_evaluation.md` | **모델 평가 정본.** E7 설계 + Stage 0~2 실측 (816줄) |
| `docs/review-verification/2026-09-13-core-selection/` | 원문 JSON — stage0 / stage1 / stage2 |
| `backend/scripts/run_core_selection.py` | E7 러너. `--stage protocol\|smoke\|formal\|concurrency\|loop` · `--roles` 필터. 전 스테이지 구현 완료 |
| `backend/scripts/loop_app.py` | Stage 4 전용 서버 래퍼 — 프로덕션 무수정 thinking 주입 + `/loop-debug` |
| `backend/scripts/core_probes.py` | 코퍼스 + 4역할 프로브. 공개 관찰 11 · 질문 12 · 통제 10 · **eval 실플레이 통제 14** |
| `docs/review-verification/2026-09-14-eval-cases/CONFIRMED-eval-cases.md` | eval 통제 14건의 사전 등록(기대 판정 고정) 확정본 |
| `docs/review-verification/2026-09-09-connected-implementation/real-model-artifacts/` | 2026-09-09 원문. 코퍼스 출처 |
| `docs/teamprofile.md` | 팀 역할 정본 v3.0 (Masterless v1.1 구조와 동일 분담) |
| `docs/jekyll.md` | 작업 로그. 최신 날짜가 위 |

---

## 배경 — 오늘 정정한 과거 판단

이걸 모르면 같은 오해를 반복한다.

- **"gemma3:12b가 심각해서 Gemini로 바꿨다"는 부정확하다.** 2026-09-09 원문 10회분을 시간순으로 세어 보면 `advisor_answer` 12/12 폴백은 **첫 판 한 번뿐**이고, 19분 뒤 근거 인용 계약(`retry_feedback=True`, `intervention_interactor.py:267`)을 고치자 같은 모델이 0/12로 돌아왔다. Core를 Gemini로 전환한 것은 그로부터 약 4시간 뒤다
- **2026-09-08의 "Planner 81/81 전량 폴백"도 모델 문제가 아니었다.** 어휘 사전 불일치였고(`'혼자 있다'` vs 사전의 `"혼자 있는다"`), 지금은 `planner_output()`이 enum으로 막는다. 오늘 4모델 × 9콜 전부 LAR 1.0
- **RM1은 닫힌 적이 없다.** 설계 문서에 "adapter 전환 성공은 RM1 해결의 증거가 아니다"라고 적혀 있고 Gemini 전환 후 확인 기록도 없다. 오늘 기준선을 재니 PC3·SPC2가 그대로 실패한다

---

## E6 (Phase 2, NPC 슬롯) — ✅ **Formal 완료 (2026-09-14, A.12·A.13)**

블로커 4건 전부 해소(§8.2), `scripts/run_model_descent.py` 구현, ON/OFF 10셀 × n=5 실행.

- **자연 7세(정책 OFF) 크기는 없다** — 전 셀 collapse ≠ none. qwen은 전 크기 3세화 방향(사실 응답 0.2~0.6), exaone은 어른화(이유 생성·의도 추론)
- **정책 ON에서 7세 구간은 `qwen3.5:4b` 하나** — 5항목 전부 ≥0.7·누설 0·스키마 1.0·D3 1.0·p95 2,290ms·2.98 GiB. 2B 이하는 정책을 줘도 3세화, 7.8B(Anchor)·9B는 어른화 신호 잔존. 정책 효과(ON−OFF)는 4B에서 최대(+2)
- **후속 검증 통과** — 4b+`gemma4:12b` pair 10.49 GiB·교대 무축출(여유 ~4.1 GiB, exaone 조합 대비 +1.2), 루프 스모크(NPC 4b·Core 12b 동시 think OFF) 1회차 완주·폴백 0/17
- 주의: Anchor가 이번 judge 규칙(3표 다수결)에서 1/5라 §4 비열등 판정은 형해화 — 절대 축(collapse) 기준으로 후보는 4b 하나. 4b **한자 혼입 2/25** 관측(korean_only가 영문만 검사 — CJK 검사 추가는 후속 과제)
- **발화 품질 A/B (A.14, E6과 별개 축)** — exaone vs 4b 쌍대 블라인드(25쌍·3표·스왑 2회): exaone 우세 3항목(자연스러움 18:3·관련성 18:3·페르소나 14:2), 4b 우세는 7세 말투 15:7뿐(9.1자 단답 기인, judge 편향 방향이라 단독 근거 배제). **NPC 결정 = 정책 축(4b) vs 품질 축(exaone) 트레이드오프 — 사용자 결정 대기**
- 남은 확장(선택): OFF 축 심화(Chart 9 완성), Screening Farm, `run_selfplay` 장기 루프, `korean_only`에 CJK 검사 추가(4b 채택 시 사실상 필수)

---

## 하지 말 것

- 실행 중인 프로덕션 `.env`를 실험 때문에 바꾸지 말 것. ~~현재 Core는 `gemini:gemini-3-flash-preview`다~~ → **현재 Core는 `ollama:gemma4:12b`(think off)다 (2026-09-14 채택 반영, §5.3).** NPC는 `ollama:exaone3.5:7.8b` 유지
- ~~Stage 3·4 통과 전에 모델을 교체하지 말 것~~ → Core는 Funnel 0~4 통과 후 사용자 결정으로 교체 완료. **NPC 교체는 아직 결정 전** — A.12(정책)·A.14(품질) 트레이드오프에서 사용자가 정한다
- ~~`EVAL_CASES` 교체 전에 `evaluator_verdict` 역할의 우열을 결론짓지 말 것~~ → 교체·재측정 완료 (A.8)
- 테스터 판 데이터·DB를 재채점하거나 리셋하지 말 것
