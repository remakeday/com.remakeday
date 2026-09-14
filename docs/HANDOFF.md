# 작업 이어하기 — 2026-09-14

> 이 문서 하나만 읽어도 이어서 작업할 수 있게 쓴다.
> 이전 인계(테스터2 착수 시점)는 `HANDOFF-2026-09-09.md`에 보존했다.

## 한 줄 상황

**E7 Stage 0~3 완료. evaluator 통제를 실플레이로 교체하자 우열이 역전됐고(A.8), 동시성은 두 후보 모두 통과(A.9). 남은 것은 Stage 4(루프 완주)와 결정 항목 D1~D3 — 모델 교체는 아직 결정하지 않았다.**

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

### 3. Stage 4 — 루프 스모크 ← **다음 할 일. 여기부터.**

최종 후보로 게임 1회차를 완주시킨다. **이게 통과하기 전에는 "대체 가능"이라고 쓰지 않는다.** 프로브 통과가 실제 루프 통과와 같지 않다. `--stage loop` 미구현 — 구현부터.

착수 순서:

1. **실행 방식 결정 (착수 시 첫 결정)** — 프로덕션 `.env`는 못 건드린다(Core는 Gemini). 두 가지 중 하나:
   - **(a) 별도 환경으로 백엔드 기동**: `pigfarm_test` DB(2026-09-10 검증에서 쓴 그 DB) + 환경변수 오버라이드(`CORE_LLM_PROVIDER=ollama`, `CORE_LLM_MODEL=<후보>`)로 포트 따로 띄운다. 실제 API 경로를 그대로 타는 게 장점
   - **(b) 러너가 엔진 직접 조립**: 서버 없이 인터랙터를 직접 호출. 기존 `selfplay` 러너(metrics.yml에 2026-09-06 이력, 당시 gemma3:12b로 1게임 완주)가 어느 방식인지 먼저 확인하고 재사용한다 — **새로 만들기 전에 이것부터 확인**
2. **완주 주체** — 사람 없이 돌리려면 selfplay 페르소나를 붙인다. 판정 기준은 점수가 아니라 **크래시 0 · 폴백 폭주 없음 · 1회차(6비트+밤) 완주**다 (§4.1 차단 조건)
3. **두 후보 각각 1회씩** — `gemma4:12b-N`, `gemma4:e4b-N`. NPC는 exaone 그대로(Stage 3에서 공존 확인됨)
4. **테스터 판 DB에 흔적을 남기지 않는다** — 테스트 attempt는 별도 DB이거나, 같은 DB라면 생성한 attempt를 기록·구분한다 (2026-09-10 검증은 "기존 플레이 DB에 테스트 판을 만들지 않았다"를 지켰다)
5. 결과는 부록 A.10 + `metrics.yml` (`stage: loop`)

### 4. 결정이 필요한 항목

| # | 결정 | 배경 |
|---|---|---|
| D1 | **Gemini 페이싱 값** | 10 RPM 때문에 품질 1위 모델이 C11·C13에 탈락했다. 쿼터 제약이 실제로 얼마인지 확인하고 올릴 수 있는지 판단. 올릴 수 있으면 판정이 뒤집힌다 |
| D2 | **현행 운영 Gemini를 thinking OFF로 바꿀지** | ON/OFF 품질이 동일한데 p50이 5.3배 차이다(9,138 → 1,720ms). `gemini_llm.py`에 `thinking_config(thinking_budget=0)` 한 줄. **품질 손실 없는 속도 개선** |
| D3 | **`teamprofile.md`의 장민석·신채연 분담** | v2.0에 "확정 필요 — 제안"으로 표시돼 있다. 실제와 다르면 §2·§3만 교체 |

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

- **프로덕션 엔진 코드를 바꾸지 않는다.** thinking 제어는 러너 안 서브클래스(`ThinkingOllamaLLM`·`ThinkingGeminiLLM`)에만 있다. `ollama_llm.py`·`gemini_llm.py`는 오늘 한 줄도 안 바꿨다
- **모델별 프롬프트 튜닝 금지.** "이 모델은 프롬프트를 조금 고치면 통과한다"는 발견은 기록만 하고 결과에 반영하지 않는다
- **폴백을 성공으로 집계하지 않는다**
- **단일 종합 점수를 만들지 않는다.** Pareto와 역할별 지표로 본다
- **Stage 0·1은 `metrics.yml`에 적립하지 않는다.** Stage 2부터
- **금지 표현** — §0.2 표 참조. "A가 B보다 낫다", "작은 모델도 충분하다" 같은 문장은 쓰지 않는다

---

## 재현 방법

```bash
cd /home/kimchungsik/projects/demo.pigfarm/backend

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
| `backend/scripts/run_core_selection.py` | E7 러너. `--stage protocol\|smoke\|formal\|concurrency` · `--roles` 필터. `loop`만 미구현 |
| `backend/scripts/core_probes.py` | 코퍼스 + 4역할 프로브. 공개 관찰 11 · 질문 12 · 통제 10 · **eval 실플레이 통제 14** |
| `docs/review-verification/2026-09-14-eval-cases/CONFIRMED-eval-cases.md` | eval 통제 14건의 사전 등록(기대 판정 고정) 확정본 |
| `docs/review-verification/2026-09-09-connected-implementation/real-model-artifacts/` | 2026-09-09 원문. 코퍼스 출처 |
| `docs/teamprofile.md` | 팀 역할 정본 v2.0 |
| `docs/jekyll.md` | 작업 로그. 최신 날짜가 위 |

---

## 배경 — 오늘 정정한 과거 판단

이걸 모르면 같은 오해를 반복한다.

- **"gemma3:12b가 심각해서 Gemini로 바꿨다"는 부정확하다.** 2026-09-09 원문 10회분을 시간순으로 세어 보면 `advisor_answer` 12/12 폴백은 **첫 판 한 번뿐**이고, 19분 뒤 근거 인용 계약(`retry_feedback=True`, `intervention_interactor.py:267`)을 고치자 같은 모델이 0/12로 돌아왔다. Core를 Gemini로 전환한 것은 그로부터 약 4시간 뒤다
- **2026-09-08의 "Planner 81/81 전량 폴백"도 모델 문제가 아니었다.** 어휘 사전 불일치였고(`'혼자 있다'` vs 사전의 `"혼자 있는다"`), 지금은 `planner_output()`이 enum으로 막는다. 오늘 4모델 × 9콜 전부 LAR 1.0
- **RM1은 닫힌 적이 없다.** 설계 문서에 "adapter 전환 성공은 RM1 해결의 증거가 아니다"라고 적혀 있고 Gemini 전환 후 확인 기록도 없다. 오늘 기준선을 재니 PC3·SPC2가 그대로 실패한다

---

## E6 (Phase 2, NPC 슬롯) — 미착수

E7이 끝난 뒤 진행한다. 상세는 `docs/model_evaluation.md` §8. 착수 전 해결할 것 4건:

1. **양자화 혼재** — `qwen3.5:0.8b`·`2b`는 Q8_0, `4b`·`9b`는 Q4_K_M. E6 §2.1은 통일을 요구한다
2. **thinking 미제어** — Anchor인 `exaone3.5`는 thinking이 없어, 고치지 않으면 Anchor만 정상 조건인 비대칭 비교가 된다
3. **Anchor가 n=2** — `metrics.yml`의 유일한 age7 줄이 `gate_pass: false`. 재측정 선행
4. **judge 일치율 러너 부재** — E6 D3(≥90%)를 잴 러너가 없다

---

## 하지 말 것

- 실행 중인 프로덕션 `.env`를 실험 때문에 바꾸지 말 것. 현재 Core는 `gemini:gemini-3-flash-preview`다
- Stage 3·4 통과 전에 모델을 교체하지 말 것
- ~~`EVAL_CASES` 교체 전에 `evaluator_verdict` 역할의 우열을 결론짓지 말 것~~ → 교체·재측정 완료 (A.8)
- 테스터 판 데이터·DB를 재채점하거나 리셋하지 말 것
