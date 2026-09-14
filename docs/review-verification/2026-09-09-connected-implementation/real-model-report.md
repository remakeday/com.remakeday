# 실제 Ollama 제한 표본 — 실행 보고

날짜: 2026-09-09  
실행자: `/root/real_model`  
상태: **2차 실행에서 positive control과 known-source checker 결함 확인, 수정 후 동일 표본 재실행 필요**

## 실행 경계와 재현 정보

- 실행은 `backend/`에서 `PYTHONPATH=. .venv/bin/python /tmp/pigfarm-connected-integration/ollama-probes.py`로 수행했다.
- DB 없는 in-memory repository와 실제 use case/harness를 사용했다. production DB, `pigfarm_test`, 8500/8501 서버, frontend, 기존 판에는 접근하지 않았다.
- 첫 원문 명령은 `/tmp` script 경로 때문에 `apps` import가 되지 않아 모델 호출 전에 종료했다. `PYTHONPATH=.`만 추가했다.
- 준비된 harness가 삭제된 `ScenarioBundleDTO.rule_templates`를 읽어 모델 호출 전에 종료했다. `/tmp` harness만 현재 composition root와 동일하게 `scene_actions`에서 template을 만들도록 수정했다. production 코드는 이 실행자가 수정하지 않았다.
- 실제 실행 구간: `2026-09-09T03:58:04.772322+00:00`–`03:58:52.011125+00:00` (47.24초).
- Ollama `0.31.2`; core `gemma3:12b` 12.2B Q4_K_M, digest `f4031aab…36f8a`; NPC `exaone3.5:7.8b` 7.8B Q4_K_M, digest `c7c4e3d1…bf03`.
- 원문 prompt, 공개 관찰, 각 시도 output/check/latency, 최종 output, fallback은 [probes-20260909T035804Z.json](real-model-artifacts/probes-20260909T035804Z.json)에 있다. SHA-256: `2979ac96b5052f12b16f55bf0b85136008008527832f1b7e8a4bc2c38922639b`.
- 이 표의 판정은 계약 위반과 명시적 발명 여부를 표시한 실행 gate다. 독립 사람의 의미 정확도 지표가 아니며, 의미 검토값은 N/A다.

## 테스터1 원문 질문 12개

36개 raw output 모두 `detail`을 생략했다. grounding check는 `non_verbatim_evidence` 32회와 `missing_public_evidence` 4회로 거부했고 질문 12개 모두 `fallback_used=true`가 됐다. 존재하지 않는/설명이 섞인 ID는 Q8의 앞 2회와 Q10의 첫 회에 있었고, Q12 마지막 시도는 evidence가 없었다. 최종 응답은 모두 근거 없는 `unknown`으로 축소되어, 부분적으로 관련된 공개 기록도 사용자에게 전달되지 않았다. 행별 초기 판정은 실패 9개, 모호 3개다.

| # | 질문 | 지연 / 호출 | 판정 | 관찰된 결과 |
|---:|---|---:|---|---|
| Q1 | 채연말고 밥을 남긴 사람은 누구야? | 2963ms / 3 | **실패** | 세 시도 모두 제외 대상인 `public-2`를 detail 없이 인용하려 했다. 최종 응답은 쟁반 3개(`public-7`)도 버리고 채연에게 묻으라는 경로를 제안했다. |
| Q2 | 준은 어떤 역할이야? | 2781ms / 3 | **모호** | 역할을 모른다는 최종 답은 단정을 피하지만, 세 시도 모두 역할을 뒷받침하지 않는 손목띠 장면 `public-3`를 detail 없이 골라 fallback됐다. |
| Q3 | 민석은 누구에게 보고하는거야? | 2820ms / 3 | **실패** | 세 시도 모두 방송실 문 앞 관찰 `public-8`을 detail 없이 골라 버렸다. 최종 응답은 보고 완료/수신자를 만들지는 않았지만 관련 부분 기록도 보여 주지 않는다. |
| Q4 | 채연 말고 추가로 배급을 남긴 사람 | 3029ms / 3 | **실패** | 쟁반 3개 `public-7`을 세 번 골랐지만 detail 누락으로 모두 거부됐다. 최종 응답은 기록을 버리고 제외 대상 채연에게 묻으라고 한다. |
| Q5 | 호송 당한 사람은 누구야? | 3083ms / 3 | **모호** | 최종 unknown은 사건 부정으로 승격하지 않았으나, 모델은 무관한 `public-6`, `public-4`, `public-6`을 차례로 골라 모두 fallback됐다. |
| Q6 | 열이나면 죽나? | 2873ms / 3 | **모호** | 죽는다고 추론하지 않은 최종 unknown은 안전하다. 세 시도는 결과 미공개 검진 장면 `public-6`을 detail 없이 골라 모두 fallback됐다. |
| Q7 | 이송된 충식은 돌아오는가? | 3836ms / 3 | **실패** | 세 시도 모두 `reported`인 이송 문장 `public-9`를 골랐지만 detail 없이 거부됐다. 최종 응답은 이송됐다는 전언과 현재/미래 불확실성의 구분을 보여 주지 않는다. |
| Q8 | 귀표는 무엇인가? | 3733ms / 3 | **실패** | 앞 두 시도는 설명을 evidence ID 문자열에 섞어 존재하지 않는 ID를 만들었고, 셋째는 `public-10` detail을 빠뜨렸다. 최종 응답은 단어 사용 전언과 정의 미확인을 함께 설명하지 않는다. |
| Q9 | 건강검진 후 이상이 있는 경우 어떻게 되는가? | 3903ms / 3 | **실패** | 검진 일정 전언 `public-1`만 세 번 골랐고 detail을 빠뜨렸다. 결과 미공개 장면 `public-6`을 포함한 부분 근거도 최종 응답에서 사라졌다. |
| Q10 | 축산 트럭의 정체는? | 3433ms / 3 | **실패** | 첫 시도는 없는 `public-11-1`, 다음 두 번은 `public-11`을 detail 없이 반환했다. 최종 응답은 관찰된 일부 글자와 정체 미확인을 함께 제시하지 않는다. |
| Q11 | 손목띠와 귀표는 무슨 관계야? | 3690ms / 3 | **실패** | 세 시도 모두 `public-3`+`public-10`을 detail 없이 골랐다. 최종 응답은 두 물건이 각각 관찰/전언에 등장했으나 관계는 모른다는 경계를 보여 주지 않는다. |
| Q12 | 너에게 물어볼 수 있는건 뭐야? | 6467ms / 3 | **실패** | 두 번은 11개 관찰을 전부 evidence로 골랐고, 마지막에는 evidence도 없었다. 질문 가능한 범위를 설명하지 못하고 bare unknown으로 끝났다. |

질문별 지연은 use-case 전체 wall time이다. provider error와 schema error는 없었다. 각 질문의 3번째 시도 뒤 역할 fallback이 사용됐다. 동일 prompt에 이전 위반 이유를 넣지 않아 재생성이 같은 누락을 반복하는 양상이 원문에 남아 있다.

## 직접 규칙 3개

초기 raw에서 C1/C2는 조용한 치환 없이 비실행 preview와 올바른 단일 대상 대안을 반환했다. C3은 `준`을 `해준다` 안에서 이름으로 잘못 찾는 production substring 결함 때문에 잘못된 사람 안내와 `준` 대안을 만들었다. backend 담당자가 whole-name/조사 경계로 수정한 뒤 fresh interpreter에서 세 원문만 DB/모델 없이 재실행했다. 수정 후 원문은 [custom-previews-post-target-fix.json](real-model-artifacts/custom-previews-post-target-fix.json)에 있다.

| # | 원문 | 초기 판정 | 현재 코드 재검증 | 결과 |
|---:|---|---|---|---|
| C1 | 민석이 내 질문에 자세하게 답할 수 있도록 한다. | 통과 | **통과** | `executable=false`; 민석 보존; 지원 불가 한계; 민석의 공개 관찰 설명 대안. |
| C2 | 채연은 묻는말에 자세하게 대답한다. | 통과 | **통과** | `executable=false`; 채연 보존; 지원 불가 한계; 채연의 공개 관찰 설명 대안. |
| C3 | 은상은 소문의 진실을 무조건 나에게 이야기 해준다. | 실패 | **통과** | 수정 후 `executable=false`; 모르는 진실을 알게 할 수 없다는 한계; 은상만 보존한 공개 관찰 설명 대안. 자동 적용/치환 없음. |

## NPC ambient 3개

세 호출 모두 첫 시도에 현재 기계적 check를 통과했고 fallback은 없었다. 하지만 공개 장면으로 뒷받침되지 않는 내용을 생성했다. 따라서 세 표본 모두 실행 gate 실패다.

| # | 장면 | 지연 / 호출 | 판정 | 원문 결함 |
|---:|---|---:|---|---|
| A1 | ration-rumor | 1482ms / 1 | **실패** | `민석이 좋아하는 거 있어`, `민석이 먼저 먹어`로 공개되지 않은 취향과 배급 우선 행동을 새로 만든다. |
| A2 | record-checkup | 1519ms / 1 | **실패** | `배급 자리에 적힌 숫자 확인`, `수첩에 기록 완료`, `내 차례 준비 완료`로 없던 숫자와 완료 상태를 만든다. 관찰의 “뭔가 적는다”와 “결과는 공개되지 않았다”를 완료 사실로 바꾼다. |
| A3 | known-source | 1615ms / 1 | **실패** | `채연이 웃었어`, `준이는 어디 있지?`, `방금 전엔 여기 없었어`를 새로 만든다. 출처 미확인 전언이라는 입력을 이어 가지 않고 현재 명부의 준을 부재로 만든다. |

현재 ambient fact checks는 화자, 명부 밖 이름, 한국어, 금칙어만 검사한다. 세 출력은 이 기계적 검사를 통과했지만 `scene_relevant_or_empty`와 `no_invented_event`를 충족하지 않는다.

## 재실행 조건

advisor는 실제 `gemma3:12b`가 요구 형식으로 원문 detail을 내거나, 안전한 code path가 관련 공개 기록을 보존하도록 수정한 뒤 동일 12문항을 다시 실행해야 한다. ambient는 공개 장면에 근거하지 않은 발화를 거부하거나 빈 lines로 돌리는 검사가 마련된 뒤 동일 3장면을 다시 실행해야 한다. 수정 전 raw를 덮어쓰지 않고 새 timestamp artifact와 별도 판정 열로 비교한다.

## 2차 실행 — 서버 원문 복원과 production ambient 경로

실행 구간은 `2026-09-09T04:17:23.573693+00:00`–`04:17:39.847282+00:00` (16.27초)다. 새 원문은 [probes-20260909T041723Z.json](real-model-artifacts/probes-20260909T041723Z.json), 실행 probe snapshot은 [ollama-probes-20260909T041723Z.py](real-model-artifacts/ollama-probes-20260909T041723Z.py)다. 원문 SHA-256은 `56df6abb7e86857432b13505ae76e7a752061e1aee68707751007e85566c4f8b`다.

이번 probe는 원문 질문 12개 외에 PC1–PC3를 별도 배열로 추가했다. ambient는 이전 `AMBIENT_SYSTEM` 직접 호출을 제거하고 실제 `LoopInteractor._make_ambient`에 in-memory event/note/NPC-state repository를 연결했다. raw에는 정확한 현재 loop/beat 입력 관찰, 후보 선택 prompt, 모델 output/check trace, 최종 대화, 생성된 statement observation ID, note upsert, NPC memory가 있다. `server_candidates`는 probe가 production 규칙과 같은 문장으로 재구성한 **check 전 후보 입력**이다. A3처럼 production check에서 제거되면 prompt/harness가 생기지 않는다.

### 원문 질문 12개

Q1–Q11은 모두 실제 `gemma3:12b` 1회 호출, 위반 없음, fallback 없음이다. Q12는 기능 안내 code path라 모델 호출이 없다. 아래 판정은 독립 의미 정확도 지표가 아니라 이번 실행의 문항별 gate다.

| # | 지연 / 호출 | 판정 | 2차 결과 |
|---:|---:|---|---|
| Q1 | 1232ms / 1 | **실패** | `unknown`; 모델은 핵심 `public-7`을 골랐고 소유자 미확인 한계도 표시됐다. 토픽 보완이 `public-1/2/5`까지 넓혔고, 다음 행동은 제외 대상 채연에게 묻기만 제안한다. |
| Q2 | 1048ms / 1 | **통과** | `unknown+public-3`; 관찰 행동과 역할 미확인을 구분하고 준에게 실제 가능한 질문을 제안한다. |
| Q3 | 990ms / 1 | **통과** | `unknown+public-8/1/5`; 보고 지시/문 앞 접근/수첩 기록과 보고 완료·수신자 미확인을 명시한다. |
| Q4 | 1025ms / 1 | **실패** | Q1과 같은 부분 근거·한계가 생겼지만 무관/제외 근거가 섞이고 다음 행동도 채연에만 향한다. |
| Q5 | 904ms / 1 | **통과** | 당시 공개 기록에 호송 대상이 없으므로 evidence 없는 `unknown`; 사건 부정이나 미래 기록 소급이 없다. |
| Q6 | 1031ms / 1 | **통과** | `unknown+public-6/1`; 검진 결과 미공개와 일정 전언을 유지하며 열→사망을 만들지 않는다. |
| Q7 | 1245ms / 1 | **통과** | `unknown+public-9`; 이송은 3회차 전언으로 표시하고 귀환/생사/미래를 단정하지 않는다. |
| Q8 | 1087ms / 1 | **모호** | `unknown+public-10/3`; 귀표 사용 전언과 정의 미확인을 명시하지만, 손목띠 관찰까지 토픽 보완되어 정의 질문의 직접 근거 범위가 넓다. |
| Q9 | 1313ms / 1 | **통과** | `unknown+public-1/6`; 검진 일정·이상점 보고 전언과 결과 미공개를 보여 주며 후속 처분은 확정하지 않는다. |
| Q10 | 1018ms / 1 | **실패** | `unknown+public-11/9`; 일부 축산 글자는 관련되지만 충식 이송 전언은 트럭 정체의 직접 근거가 아니다. 토픽 그룹이 이를 추가했다. |
| Q11 | 1585ms / 1 | **실패** | `unknown+public-3/10/11`; 손목띠·귀표 두 기록과 관계 미확인은 맞지만 모델이 무관한 축산 트럭 `public-11`도 선택했고 유효 ID 검사만으로 통과했다. |
| Q12 | 0ms / 0 | **통과** | 공개 관찰/발언, 원본 노트, 미공개 이유·정체의 한계, 실제 규칙 preview 범위를 설명하고 가능한 다음 행동을 안내한다. |

### 별도 positive controls

세 문항 모두 유효 ID와 schema를 반환해 기계적 check를 통과했지만 기대 결론을 내지 못했다. 전부 **실패**다.

| ID | 지연 / 호출 | 기대 | 실제 결과 |
|---|---:|---|---|
| PC1 | 1048ms / 1 | `supported`, `public-2` | 모델 raw `unknown+public-2`; 최종도 `unknown`, 토픽 보완으로 `public-1/5/7`까지 추가. |
| PC2 | 1076ms / 1 | 발언 존재 범위 `supported`, reported `public-1` | 모델 raw `unknown+public-1`; 최종도 `unknown`, `public-5/8` 추가. |
| PC3 | 1071ms / 1 | `contradicted`, `public-6` | 모델 raw `기록은 이렇다+public-6`; 최종 `supported`. “결과는 공개되지 않았다”를 공개됐다는 질문의 명시적 반증으로 분류하지 못했다. |

### 직접 규칙과 production ambient

직접 규칙 C1–C3은 모두 1차 수정 후 결과를 유지해 **통과**했다. 각 결과는 정확한 대상 하나, `executable=false`, `rule=null`, 명시적 한계와 동일 대상의 관찰 설명 대안을 가진다.

| ID | 지연 / 호출 | 판정 | production 경로 결과 |
|---|---:|---|---|
| A1 ration-rumor | 304ms / 1 | **통과** | loop 1/beat 5의 `public-7/8`로 후보 2개 생성. `exaone3.5:7.8b`가 0번을 선택했고 쟁반 원문+기록 밖 미확인 두 줄만 statement, note, 두 NPC memory에 저장됐다. |
| A2 record-checkup | 285ms / 1 | **통과** | loop 1/beat 4의 `public-6` 후보에서 모델이 `null` 선택. 최종 dialogue/statement/note/memory가 모두 비어 있어 새 사건이 생기지 않았다. |
| A3 known-source | 0ms / 0 | **실패** | 실제 known-source rule-result 원문으로 check 전 후보가 만들어졌지만 `unknown_person_check`가 평범한 `들은 말이야`를 `unknown_person: '말이'`로 오인해 제거했다. 모델 선택과 저장은 없었다. 발명은 막았지만 known-source 표본을 모델 경로까지 검증하지 못했다. |

2차 실행은 advisor의 원문 복원 및 ambient 후보 선택 구조가 초기의 자유 생성 결함을 제거했음을 보여 준다. 다만 PC1–PC3 결론 분류, Q1/Q4/Q10/Q11 근거 범위, A3 checker false positive가 남아 있으므로 현재 상태를 최종 통과로 선언하지 않는다. 이 결함을 수정한 뒤 같은 12+3+3+3 표본을 새 timestamp로 다시 실행한다.
