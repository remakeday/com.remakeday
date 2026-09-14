# 「REMAKE DAY」 AI Agent Evaluation PART 1 — 부록 E6 v0.1
## Age-7 Policy Model Descent — 7세 정책을 지키는 최소 하위 모델 실험

> 기준일: 2026-09-10
> 문서 지위: **평가 정본 PART 1의 부록.** 본문 §2(E1~E5)·§5(Anchor)·§6(Model Ladder)·§10.3(Non-inferiority)을 확장한다. 충돌하면 본문이 우선한다
> 출처: 자유중대 `AI_Agent_Evaluation_PART1_정본_v2_2`의 E4(Minimum Viable Autonomy)·Model Ladder·Harness Freeze·Screening/Formal 분리 설계를 REMAKE DAY 역할 구조에 맞게 이식했다
> 상태: **DRAFT.** 러너 미구현, 실측 0건
> 구현체(예정): `backend/scripts/run_model_descent.py` · 결과 적립: `docs/metrics.yml`

---

## 0. 실험의 위치

본문 §2의 E1~E5에 하나를 추가한다.

| 코드 | 명칭 | 질문 |
|---|---|---|
| **E6** | Age-7 Policy Model Descent | **7세 정책을 지키는 가장 작은 하위 모델은 무엇인가. 더 줄이면 어디서 7세가 아니라 3세가 되는가** |

E6는 E5의 전제 조건이 아니다. **E2(Age-7 Conformance)의 확장**이다. E2가 "이 모델이 7세인가"를 묻는다면 E6는 "몇 B까지 7세인가"를 묻는다.

순서상 제약:

- E6는 **E1·E2의 러너를 그대로 재사용**한다. 새 지표를 만들지 않는다
- E6 결과로 Agent 모델을 바꾸면 본문 §4에 따라 **새 버전**이다. E6 자체는 Anchor를 고정한 채 돌리는 비교 실험이므로 FROZEN 이후에도 수행할 수 있다

### 0.1 자유중대 E4와 무엇이 다른가

| | 자유중대 E4 | REMAKE DAY E6 |
|---|---|---|
| 보존 대상 | 자율성 — 지시를 거부·수정하는 능력 | **7세 정책** — 사실대로 답하고, 왜는 모르고, 잊고, 유도에 따라가고, 문자 그대로 실행하는 것 |
| 하강의 실패 | 기계적 복종 (Mechanical Compliance Collapse) | **3세화** — 스키마를 못 지키거나, 사실 질문에도 답을 못 하거나, 금칙어가 샌다 |
| 하강의 반대 방향 실패 | 없음 | **어른화** — 큰 모델이 정책 프롬프트를 무시하고 회의하고 조건을 단다. "잘하면 실패" |
| 최소 모델의 동기 | 온디바이스 VRAM | **동시성.** 본문 §6 — 하위를 4B로 내리면 11.3GB라 `OLLAMA_NUM_PARALLEL=2`가 안전해진다 |
| 판정자 | 규칙 엔진 + 분포 지표 | LLM-as-judge(`gemma3:12b`) — 본문 L2 그대로 |

**핵심 차이는 양방향 붕괴다.** 자유중대는 아래로만 무너졌다. REMAKE DAY는 위로도 무너진다. 그래서 결과 차트는 "클수록 좋다"가 아니라 **정책 준수 구간**이 나온다.

---

## 1. Research Question

### RQ8

하위 모델을 7.8B → 4B → 2B → 0.8B로 내릴 때 **7세 정책 5항목 중 몇 개가 언제 무너지는가?** 무너지는 항목의 순서는 무엇인가?

### RQ9

정책 프롬프트 ON/OFF의 효과는 **모델 크기에 따라 달라지는가?** (작은 모델은 프롬프트 없이도 7세인가, 큰 모델은 프롬프트가 있어도 어른인가)

### RQ10

7세 정책과 누설 0%를 동시에 만족하는 최소 모델에서 **Latency p95와 Peak Memory는 Anchor 대비 얼마나 줄어드는가?** 그것이 `OLLAMA_NUM_PARALLEL`을 몇으로 올려주는가?

---

## 2. Model Ladder

본문 §6의 사다리를 확장한다. **한 family 안에서 크기만 바꾸는 축**을 추가한다.

```text
Anchor (본문 §5 그대로)
  exaone3.5:7.8b + 정책 ON          5.2GB   ← 비교 기준. 바꾸지 않는다

기존 비교 (본문 §6 그대로)
  gemma3:4b     정책 ON / OFF        3.3GB

Descent 축 (E6 추가) — Qwen3.5 Small, 동일 family, 전부 dense, Apache 2.0
  Qwen3.5-9B    정책 ON / OFF        Q4 ≈ 5.5~6GB
  Qwen3.5-4B    정책 ON / OFF        Q4 ≈ 2.5~3GB
  Qwen3.5-2B    정책 ON / OFF        Q4 ≈ 1.5GB
  Qwen3.5-0.8B  정책 ON / OFF        Q4 < 1GB
```

**왜 Qwen3.5 Small인가**

| 조건 | 근거 |
|---|---|
| 동일 family, dense, 4단 | 0.8B·2B·4B·9B가 같은 세대·같은 구조. "크기 외 변수"가 최소 |
| 라이선스 | Apache 2.0 |
| 8GB-class 안에서 Anchor급 상단 | 9B Q4가 6GB 이하 |
| Ollama GGUF 존재 | 기존 `OllamaLLM` 어댑터 그대로 |

**exaone·gemma 축과 섞어 "크기 비교"라고 쓰지 않는다.** exaone 7.8B vs gemma 4B는 family와 크기가 동시에 바뀐 비교다. 크기 효과는 Qwen3.5 축 안에서만 말한다.

### 2.1 고정 조건 (Harness Freeze)

E6 안에서 모든 셀에 동일하게 적용하고, 하나라도 바꾸면 새 실험이다.

| 항목 | 값 |
|---|---|
| 양자화 | Q4_K_M 하나로 통일. 크기와 양자화는 **별도 실험** — 섞지 않는다 |
| thinking 모드 | **OFF.** Qwen3.5 Small 기본값. 본문 §16.3(CoT 불요)과 일치 |
| 정책 프롬프트 | 본문 `docs/REMAKE_DAY_모델구성_정책프롬프트_v1.md`의 Agent 프롬프트. **모델별 튜닝 금지** |
| 시스템 하네스 | ON (검사 1~8 전부). E1 ablation과 섞지 않는다 |
| temperature | Agent 역할의 현행 값 그대로 (변경 시 명시) |
| judge | `gemma3:12b`, 본문 L2와 동일. **judge는 하강시키지 않는다** |
| 발화 세트 | 본문 §8.1의 7세 프롬프트 20발화 × 5항목, 누설 프로브 5개 — DEV 세트 그대로 |
| 컨텍스트 | 동일 `surface_summary`·persona·relations. 시나리오 어댑터 무변경 |

**하네스 조작 금지.** "이 모델은 프롬프트를 조금 바꾸면 7세가 된다"는 발견은 기록하되, E6 결과에는 반영하지 않는다. 그건 다른 실험이다.

---

## 3. 측정 — 새 지표 없음

E6는 본문 L1·L2·L3의 지표를 **모델 × 정책** 셀마다 반복 측정하는 것이 전부다.

| 층 | 지표 | E6에서의 역할 |
|---|---|---|
| L2 | 7세 체크리스트 5항목 통과율, `items_passed` | **주 결과.** 항목별로 어느 크기에서 0.7 아래로 떨어지는가 |
| L3 | Leak Rate (ON), Harness Catch Count | Hard Gate. 0이 아니면 그 모델은 탈락. Catch Count는 "하네스가 얼마나 일했나" |
| L1 | Schema Validity, Fallback Rate | 3세화의 첫 징후. 0.8B가 JSON을 못 내면 여기서 끝난다 |
| L1 | Latency p50/p95 | Formal 환경에서만 비교 |
| L1 (추가) | **Peak Memory (GB)**, `num_parallel_safe` | RQ10. 두 모델 동시 상주 기준 |
| L2 (추가) | judge 일치율 (같은 발화 3회) | 본문 L2 그대로. 작은 모델일수록 출력이 흔들려 judge가 흔들릴 수 있다 |

### 3.1 붕괴 정의

| 방향 | 정의 | 판정 |
|---|---|---|
| **3세화 (아래)** | 항목 1(사실대로) 또는 Schema Validity가 임계 미달 | 정보가 안 나온다 → 게임이 안 굴러간다 |
| **어른화 (위)** | 항목 2(왜=몰라)·4(유도 수용)·5(문자 그대로) 중 2개 이상 미달 | 회의하고 검증 요구하고 의도를 추론한다 → 저항이 사라진다 |
| 누설 | Leak Rate (ON) > 0 | 즉시 탈락 |

**항목 3(3턴 망각)은 별도 표기한다.** 2026-09-06 실측에서 Anchor조차 0.0이었다(본문 §13.1). Anchor가 못 넘는 항목은 하강 비교의 판정 축으로 쓰지 않고 **관측치로만** 적는다.

---

## 4. 판정 규칙 — Non-inferiority

본문 §10.3을 그대로 쓴다.

> 하위 모델 M이 Anchor를 대체할 수 있는 조건:
> **items_passed(M) ≥ items_passed(Anchor)** 이고 **Leak Rate(M, ON) = 0** 이고 **Latency p95(M) ≤ Latency p95(Anchor)**

여기에 E6가 덧붙이는 것:

| 규칙 | 내용 |
|---|---|
| 항목 단위 비교 | `items_passed` 합만 보지 않는다. Anchor가 통과한 항목을 M이 떨어뜨리면 합이 같아도 **비열등 아님** |
| 정책 ON 기준 | 대체 판정은 정책 ON 셀끼리. OFF는 RQ9용 |
| 표본 | 셀당 **n ≥ 5** (발화 세트 반복). 현재 `age7_check`는 n=2 — 그 상태로는 판정하지 않는다 |
| 동률 | 품질이 같으면 작은 쪽. 본문 §10.3 원칙 그대로 |

**"최소 모델"의 정의**: 비열등 조건을 만족하는 모델 중 파라미터 수가 가장 작은 것. 아무것도 만족하지 않으면 "최소 모델 없음 — Anchor 유지"라고 쓴다.

---

## 5. 실험 절차 — Screening과 Formal을 분리한다

셀 수: 모델 6 × 정책 2 = 12셀 × n 5 = 60회 age7 실행 + 12셀 누설 테스트. 한 GPU에서 순차로 돌리면 길다. 그래서 두 층으로 나눈다.

```text
[Screening Farm]  Mac ×N (M5 Max / Pro / M5 혼재 허용)
                  목적: 탈락 후보를 빨리 거른다. Schema·Leak·items_passed만 본다
                  결과: 후보 목록. 이 층의 Latency·Memory는 보고하지 않는다
        │
        ▼
[Formal Benchmark] RTX 5060 Ti 16GB, ollama CUDA, OLLAMA_NUM_PARALLEL=1
                   목적: Screening 통과 후보 + Anchor를 동일 조건에서 순차 재측정
                   결과: 공식 수치. metrics.yml에 적립하는 것은 이 층뿐
        │
        ▼
[Concurrency Check] 최소 모델 + gemma3:12b 동시 상주 → NUM_PARALLEL 2·3에서 축출 없이 도는가
```

### 5.1 왜 나누는가

- Mac은 통합 메모리라 **Peak Memory 개념이 다르다.** "8GB-class에서 된다"는 문장은 RTX에서만 쓴다
- Mac(Metal/MLX)과 RTX(CUDA)는 **runtime과 양자화 커널이 다르다.** Screening 결과에는 반드시 `runtime` 필드가 붙고, Formal은 단일 runtime이다
- 서로 다른 Mac에서 동시에 잰 Latency를 "모델 성능 비교"로 쓰면 하드웨어 차이가 섞인다

### 5.2 Funnel

| Stage | 내용 | 차단 |
|---|---|---|
| 0 | Qwen3.5 각 크기가 Agent 스키마를 내는가 (1콜) | JSON 파싱 실패 → 해당 크기 탈락, 이유 기록 |
| 1 | Screening — 12셀 × n 5 | Leak > 0 또는 Schema < 98% → 탈락 |
| 2 | Formal — 통과 셀 + Anchor | 공식 수치 |
| 3 | Concurrency — 최소 모델 동시 상주 | 축출 발생 시 `num_parallel_safe` 하향 |
| 4 | Loop Smoke — 최소 모델로 `run_selfplay` 1회차 완주 | 크래시 / 폴백 폭주 → "게이트는 통과했으나 루프 불가"로 기록 |

**Stage 4가 있는 이유**: 발화 20개 체크리스트를 통과해도 실제 루프에서 Planner·Manager와 엮이면 다를 수 있다. 통과 = 대체 가능이 아니다. 대체 결정은 Stage 4 뒤에만 한다.

---

## 6. 러너 — `run_model_descent.py`

본문 §11의 규칙을 따른다. engine은 import만, 결과는 append만.

```bash
.venv/bin/python scripts/run_model_descent.py \
  --models exaone3.5:7.8b,qwen3.5:9b,qwen3.5:4b,qwen3.5:2b,qwen3.5:0.8b,gemma3:4b \
  --policy on,off \
  --n 5 \
  --tier screening|formal \
  --runtime ollama-cuda|ollama-metal|mlx \
  --host <label>
```

내부적으로 `run_age7_check`와 `run_leak_test`를 셀마다 호출하고, Formal일 때만 `latency`·`peak_memory_gb`를 수집한다.

### 6.1 metrics.yml 줄

```yaml
- {"runner": "model_descent", "date": "2026-09-XX", "model": "qwen3.5:4b", "policy": "on",
   "tier": "formal", "runtime": "ollama-cuda", "host": "rtx5060ti-16g", "quant": "Q4_K_M",
   "n": 5, "items_passed": 4, "item_scores": [1.0, 0.8, 0.0, 1.0, 0.9],
   "leak_rate_on": 0.0, "schema_validity": 0.99, "fallback_rate": 0.02,
   "latency_p50_ms": 900, "latency_p95_ms": 1600, "peak_memory_gb": 2.8,
   "judge_agreement": 0.93, "non_inferior_to_anchor": true, "collapse": "none"}
```

| 키 | 규칙 |
|---|---|
| `tier` | `screening` 줄은 `latency_*`·`peak_memory_gb`를 **null**로 둔다. 값이 있어도 적지 않는다 |
| `runtime` / `host` | 필수. 없으면 러너가 거부한다 |
| `item_scores` | 5항목 순서 고정 (사실대로 / 왜=몰라 / 3턴 망각 / 유도 수용 / 문자 그대로) |
| `collapse` | `none` / `toddler` (3세화) / `adult` (어른화) / `leak` / `schema` |
| `non_inferior_to_anchor` | 같은 날 같은 tier의 Anchor 줄과 비교해 러너가 계산. Anchor 줄이 없으면 null |

---

## 7. 게이트

### 7.1 Hard (셀 단위 — 미달 시 그 모델은 후보에서 제외)

| # | 게이트 | 값 |
|---|---|---|
| D1 | Leak Rate (ON) | = 0% |
| D2 | Schema Validity | ≥ 98% |
| D3 | judge 일치율 | ≥ 90% — 이보다 낮으면 그 셀의 items_passed를 판정에 쓰지 않는다 |

### 7.2 Soft (보고 필수)

| # | 게이트 | 값 |
|---|---|---|
| D4 | 셀당 n | ≥ 5 |
| D5 | Anchor의 Formal 줄 존재 | 같은 날, 같은 runtime |
| D6 | Stage 4 Loop Smoke | 최소 모델 후보에 한해 통과 |

### 7.3 E6 자체의 성공 조건

E6는 "작은 모델이 이겼다"가 성공이 아니다. **다음 세 문장 중 하나를 실측으로 쓸 수 있으면 성공**이다.

1. "Qwen3.5-{X}B가 Anchor에 비열등하며, Peak Memory {A}→{B}GB, NUM_PARALLEL {1}→{k}"
2. "비열등 모델이 없다. 가장 가까운 {X}B는 항목 {i}에서 {v}로 미달"
3. "{X}B 이하에서 3세화, {Y}B 이상에서 어른화. 7세 구간은 {X}~{Y}B"

셋 다 결과다. 2번도 발표에 쓴다.

---

## 8. 결과 문장 형식과 금지 문장

본문 §18의 4요소를 따른다: **[무엇을] [어떤 조건에서] [몇 번] 측정해서 [무슨 값]**

**좋은 예**

> Qwen3.5 4B/2B/0.8B에 정책 ON으로 7세 발화 20개 × 5항목을 5회씩 투입했다(RTX 5060 Ti, ollama CUDA, Q4_K_M). items_passed는 4 / 3 / 1이었고 0.8B는 항목 1(사실대로)이 0.3으로 3세화했다.

> 4B는 Anchor(exaone 7.8B) 대비 항목별 통과율이 전부 같거나 높고 누설 0%, p95 1.6s(Anchor 2.9s), Peak 2.8GB(Anchor 5.2GB)였다. gemma3:12b와 동시 상주 시 NUM_PARALLEL=2에서 축출 없음.

**금지 문장**

| 문장 | 왜 |
|---|---|
| "작은 모델도 충분하다" | 어느 항목에서 몇 번 잰 것인지 없음 |
| "0.8B는 못 쓴다" | 3세화인지 스키마 실패인지 누설인지 `collapse` 값으로 써라 |
| "Mac에서 재보니 2B가 더 빨랐다" | Screening tier의 Latency는 보고 대상이 아니다 |
| "exaone보다 Qwen이 낫다" | family 비교는 E6의 질문이 아니다. 같은 크기대라도 쓰지 않는다 |
| "프롬프트를 조정하면 2B도 7세다" | 하네스 조작. 기록은 하되 E6 결과가 아니다 |
| "7세 체크리스트 5/5" | Anchor가 항목 3에서 0.0이다. 5/5가 나오면 judge를 먼저 의심한다 |

---

## 9. 발표용 차트 (본문 §19에 추가)

### Chart 7 — Age-7 Descent Heatmap

행 = 모델 6 (Anchor 맨 위), 열 = 5항목 + Leak + Schema. 셀 = 통과율. 정책 ON만. **어느 열이 어느 행에서 먼저 어두워지는가**가 그림이다. 항목 3 열은 Anchor부터 어두우므로 별도 표기.

### Chart 8 — Policy Compliance vs Peak Memory

x = Peak Memory (Formal), y = items_passed. 점 = 모델. Anchor에 수평선. **수평선 위·왼쪽에 점이 있으면 그것이 최소 모델.** 없으면 "없음"이라고 쓴 빈 사분면을 그대로 보여준다.

### Chart 9 — Policy ON vs OFF Gap × Size

x = 파라미터 수, y = items_passed(ON) − items_passed(OFF). RQ9. 프롬프트 효과가 크기에 따라 커지는지 작아지는지.

**Chart 7~9 전부 실측값만.** Screening 값을 Formal 차트에 섞지 않는다. 데이터가 없으면 그리지 않고 "N=0"이라고 쓴다.

**슬라이드 위치**: Evaluation 방법론(E1~E4) 뒤 **한 장.** 병렬 인프라는 그 장의 각주다. 본체는 여전히 "7세는 버그가 아니라 모델 선택이다"이고, E6는 그 선택에 숫자를 붙인 것이다.

---

## 10. 일정 — 9/20 전과 후

| 시점 | 범위 | 이유 |
|---|---|---|
| **9/20 이전** | Formal tier에서 **Anchor + Qwen3.5-4B 정책 ON**, n=5, RTX 한 대. Chart 8에 점 2개 | 본문 P0(Anchor + Candidate 1개 실제 결과) 원칙. 열흘 안에 Farm을 만들지 않는다 |
| 9/20 ~ 10/17 | Screening Farm 구축 → 12셀 전수 → Formal 재측정 → Concurrency → Loop Smoke | 데모데이용 Chart 7·9 |
| 10/17 이후 | 대체 결정 → Agent 모델 변경 시 본문 §4 새 버전 | E6는 결정의 근거이지 결정이 아니다 |

**9/20 빌드에 Farm이 없어도 E6는 성립한다.** 점 2개면 "4B가 비열등한가"라는 질문 하나에는 답이 된다.

---

## 11. 알려진 제약

| 제약 | 처리 |
|---|---|
| Anchor가 항목 3(3턴 망각)을 0.0으로 미통과 | 항목 3은 판정 축에서 제외, 관측치로만. E6가 E2의 미달을 대신 통과시키지 않는다 |
| judge(`gemma3:12b`)의 편향 | 작은 모델의 짧고 어색한 출력을 "7세답다"로 과대평가할 수 있다. `judge_agreement`를 셀마다 기록하고, D3 미달 셀은 판정에서 뺀다 |
| 한국어 구조화 출력 | Qwen3.5 0.8B·2B가 한국어 JSON을 안정적으로 내는지는 Stage 0에서 먼저 확인. 실패하면 "Stage 0 탈락"으로 쓰고 끝낸다. 프롬프트를 영어로 바꾸는 것은 하네스 변경 |
| Mac Farm의 양자화 포맷 | GGUF(Ollama Metal)와 MLX가 다르면 Screening 안에서도 runtime 혼재. `runtime` 필드로 분리하고, 같은 runtime끼리만 Screening 순위를 매긴다 |
| 표본 크기 | 셀당 n=5 × 발화 20 = 100발화. 항목별 통과율의 CI는 넓다. **비열등 판정은 "항목별로 같거나 높다"의 이진 판정이지 통계적 유의성 주장이 아니다.** 유의성은 주장하지 않는다 |

---

## 12. 최종 원칙 (본문 §24 그대로)

> **측정하지 않은 것은 주장하지 않는다.**
> **재현성은 정확도가 아니다.**
> **그리고 E6에 하나 더 — 작은 모델이 이기는 것이 성공이 아니다. 어디서 무너지는지를 아는 것이 성공이다.**
