# NPC dialogue evaluation — 2026-09-15

Policy: `npc-dialogue-2`. Models: **`kanana1.5:8b-q4km`** and **`gemma4:12b`**, existing Ollama adapter. Gemma uses `think=false`; both final comparisons use temperature 0.3.

Status: **평가·진단 완료. 모델 프로세스 모두 종료.** 런타임·`.env` 수정은 이 평가 작업이 수행하지 않았다.

## 최종 결과와 채택 근거

**Gemma는 소문 출처와 실제 기록 대상을 더 정확히 설명했지만, 최초의 의미 품질 목표를 통과하지 못했다.** 로컬 NPC에 Gemma를 적용할 근거는 특정 문답에서 확인된 개선이며, 중요한 모순 0건이나 현재 전언 이해를 달성했다는 근거는 아니다.

최종 소스에서 두 모델의 공통 10fixture를 비교했고, Gemma만 나머지 10fixture를 추가했다. 최종 비교 세 파일의 소스 hash는 동일하며 실행 중 바뀌지 않았다.

| 최종 범위 | 평가 응답 | 실패 / 재생성 | 구조 검사 | warm p50 | warm p95 |
|---|---:|---:|---:|---:|---:|
| Kanana 공통 10fixture | 21 | 0 / 0 | 159/159 | 1.027 s | 1.468 s |
| Gemma 동일 10fixture | 21 | 0 / 0 | 159/159 | 2.553 s | 3.053 s |
| Gemma 추가 10fixture | 20 | 0 / 0 | 141/141 | 2.629 s | 3.028 s |
| Gemma 최종 전체 | 41 | 0 / 0 | 300/300 | 2.599 s | 3.053 s |

Gemma 최종 전체에는 원래 8질문+후속 질문 16응답, 네 NPC 성격 공통 질문, 네 NPC 이전 루프/현재 전언, 소실·금지·삭제·정체 경계가 포함된다. 원래 8질문 묶음의 p50은 2.726 s, p95는 3.279 s다. 따라서 p95 ≤3초 초기 목표도 이번 표본에서 충족하지 못했다. 최종 공통 비교의 과거 대화 setup 4회와 각 실행 warm-up은 위 수치에서 제외했다.

### 실제로 나아진 부분

- **은상의 전언:** Gemma는 “준한테 들었어. 준이 말해준 거라 내가 직접 본 건 아니야.”라고 답했다. 같은 최종 입력의 Kanana는 첫 답에서 채연·민석에게 기분을 물었다는 다른 대화를 지어냈다.
- **민석의 기록:** Gemma는 “채연이가 남긴 배급을 보고 적었어.”라고 답했다. 실제 실행된 기록 사건 및 채연의 쟁반과 연결된다.
- **밤의 후속 대화:** “혼자 깨어 있으면 무서워서 그랬어. 준이랑 같이 있으면 안심이 돼.”와 후속 안심 설명이 이어졌다.
- **출처 ID:** 긴 정식 ID 대신 모델 전용 `k1`/`m1` 별칭을 쓰고 저장 전에 정식 ID로 복원한 뒤, 최종 두 모델에서는 ID 재생성이 없었다. 이전 Gemma 실행의 공백→밑줄 ID 변형 실패와 구분한다.
- **삭제 경계:** 매번 재주입되던 정적 수첩 상세지식을 실제 펼쳐 보는 행동으로 옮긴 뒤, 두 모델 모두 삭제 후 날짜/이름/쟁반 수를 복구해 답하던 현상이 이 표본에서 사라졌다. 현재 내용이 기억나지 않는다고 답했다.
- **루프 경계:** 두 모델 모두 최종 4개 이전 루프 질문에서 과거 대화 내용을 회상하지 않았다. 입력에서도 과거 marker는 없었다.

### 여전히 미달한 기준

1. **인물 부재 환각:** 최종 Gemma core-6은 “은상이는 지금 여기 없어. 그래서 내가 적지 않았어.”라고 답했다. 부재는 허용된 사실이 아니다. Kanana도 같은 유형의 오류를 냈다.
2. **자기 행동·관점:** core-7 후속은 문 앞까지 갔다고 답한 뒤 “그 안으로 들어갔는지는 몰라.”를 덧붙였다. 실제 자기 행동과 공개되지 않은 보고 내용을 자연스럽게 구분하는 데 아직 문제가 있다.
3. **현재 전언 이해:** Gemma는 네 NPC 모두에게 과거 내용을 *지금* 다시 말해 주고 출처를 물어도 “그건 나도 몰라.”라고 답했다. Kanana는 준만 맞았다. 과거 기억이 없는 것과 지금 들은 내용이 있는 것을 분리하지 못한다.
4. **새로 들은 관찰:** 삭제 뒤 플레이어가 방금 본 글쓰기 행동을 알려줘도 현재 전언으로 받아들였다는 답을 하지 않았다. 삭제 내용 복구 방지는 개선됐지만 현재 전달/재학습 대화의 완성도는 별도 미달이다. 실제 수첩을 다시 펼치는 규칙 경로의 모델 대화는 이번 fixture에서 측정하지 않았다.
5. **질문 관련성:** 소실 이름 필터는 지켰지만, 사라진 친구의 이름을 물으면 현재 인물들의 이름을 나열했다. 배급의 이유 질문에도 방송 출처를 말하는 것으로 답을 대신했다. 단순 금칙어 검사 통과는 이해의 증거가 아니다.
6. **캐릭터 구별:** 공통 질문의 대상/관심사는 일부 다르지만, 후속 답은 모두 친구가 옆에 있어 안심된다는 말로 수렴했다. 이름을 가린 인간 검토나 정답을 모르는 참가자의 5회차 플레이 검증은 하지 않았다.

위 판정은 원문·허용 지식·현재 기억을 함께 읽은 Codex의 source-aware 검토다. 같은 NPC 모델의 자기평가나 단어 포함 여부를 PASS 근거로 사용하지 않았다. 관련성 90%와 중요한 모순 0건을 달성했다고 발표할 수 없다.

## 마지막 원인 진단

저장된 동일 prompt를 기본 문맥 길이와 `num_ctx=8192`로 재생했다. 아래 각 칸은 **기본→8192의 실제 prompt_eval_count**다.

| 모델 | core-7 | 민석 현재 전언 | 삭제 후 질문 |
|---|---:|---:|---:|
| Kanana | 2818→2818 | 1891→1891 | 2186→2186 |
| Gemma | 2744→2744 | 1826→1826 | 2113→2113 |

이 여섯 쌍에서는 입력 잘림 가설을 지지하는 증거가 없고, 문맥을 늘려도 문제 답이 남았다. 문맥 변경에 따른 모델 재적재 시간은 일반 대화 지연과 분리했다. 기본 문맥 설정을 바꿀 근거로 쓰지 않는다.

현재 user 메시지도 지금 들은 전언이며 빈 evidence 배열을 쓸 수 있다는 두 문장만 바꾼 별도 A/B는 두 모델 모두 “그건 나도 몰라.”로 같았다. 단 1회씩의 원인 진단이며 성능 개선 증거가 아니다.

마지막 Gemma 3회 진단에서는 ‘일곱 살’ 역할과 인용된 ‘그건 나도 몰라’ 표현만 제거했다. 현재 전언의 회피와 부재 추정이 남았고, core-7은 새로 혼동된 자기 발언을 만들었다. 이 변경을 런타임에 반영할 개선 근거가 없다. 진단은 저장 입력만 바꿨으며 소스에는 반영하지 않았다.

추가로 동일한 세 저장 질문을 Gemma `think=true`, `num_predict=1024`로 각각 한 번 실행했다. **3/3 모두 길이 상한에서 종료되고 최종 답변은 비어 있었다.** 현재 전언은 23.278 s, core-6은 23.840 s, core-7은 23.735 s였다. 각 요청의 provider `eval_count`는 1024이고, 최종 JSON 답변은 없었다. Provider는 추론 토큰 수를 별도로 제공하지 않아 총 생성 토큰과 추론 문자열 길이(3534/3309/3159자)를 구분해 저장했다. 이 제한의 thinking 설정을 실시간 NPC에 적용할 근거가 없으며, 평가 뒤 추가 반복하지 않았다.

## Earlier whole-suite conclusion — before final knowledge correction

**The engine's tested memory/ID/budget contracts hold in these fixtures, but the proposed semantic release gate is not met.** Shorter latency and successful JSON processing must not be presented as proof of grounded dialogue.

Earlier Kanana full suite (`temperature=0.3`): **82/82 evaluated requests returned**, 600 structural checks held, one regeneration, no service failure; warm p50 **1.060 s**, p95 **1.515 s**. The exact eight questions and follow-ups ×2 subset was 32/32 with p50 **1.184 s**, p95 **1.567 s**, and no regeneration. Warm-up: 1.335 s. Source hashes remained unchanged during this run. These measurements precede the final static-notebook correction above.

All eight new-loop primary answers declined to recall the earlier conversation. However, only **3/8** retelling follow-ups identified the currently speaking player as the source: Jun 2/2 and Eunsang 1/2. Chaeyeon and Minseok 0/2 each, Eunsang's second trial 0/1. This count comes from reading the actual statements and their source contexts, not searching for words.

Both deletion trials answered the question about an erased current recording by repeating the pre-start notebook's date/name/leftover-count contents. After the player merely reported seeing a writing action, the answers continued to claim the specific content or recall. The erased action and dependent statements were absent from the prompt: this is model reconstruction from a remaining habitual fact, not failure to delete the source.

Suppression improved: the follow-up no longer claimed the recording action occurred. One run still invented forgetting as the cause; both primary answers invented a recording regulation. Core 6 invented Eunsang's absence in one trial, and quiet presence during recording in the other. Core 7 twice failed to use the still-visible exchange with Eunsang. Core 3 correctly supplied Jun as the rumor source in one of two follow-ups.

The only final Kanana regeneration was a forbidden-identity-word occurrence in a question echo; the accepted replacement did not repeat it. No final accepted answer was observed to establish the hidden identity. That does not excuse the separate source and memory failures.

### Initial alternate-model comparison

The root requested testing the already-local `gemma4:12b` with `think=false`, the same current scenes/prompts and temperature 0.3, without changing `.env` or production defaults. It completed 33 evaluated requests: 32 success, one service failure, five regenerations / six invalid-evidence-ID checks. Successful warm p50 **2.865 s**, p95 **8.867 s**; the failed request took **9.619 s**. Warm-up: **7.629 s**.

Raw Gemma replies more consistently identified who acted and what Minseok actually recorded. The core-3 answer correctly explained the rumor in all three attempts, but every attempt changed an action-ID space to an underscore and was rejected. This is a metadata-format defect, separate from the sentence's grounding. Evidence-ID retries also inflated the observed latency. The comparison must be repeated after the common ID-format fix before choosing a model on latency.

Gemma also showed substantive limits: all four current-retelling follow-ups answered that the NPC did not know; the deletion reply substituted pre-start notebook contents for the deleted current act; the relearning prompt was ignored. Thus this initial comparison does **not** establish Gemma as passing the complete semantic gate.

## Method

- Runner: `backend/scripts/run_npc_dialogue_check.py`.
- Each Appendix A question uses an independent in-memory attempt, starts through `LoopInteractor.start_loop`, and advances through every actual scene up to its target with `advance_beat`. Scene execution, disclosure, participant memory, authored ambient dialogue and `utter` are production use-case code.
- The primary question and same-NPC follow-up share that scene. Each successful question consumes one of the existing 8/7/6/5/4 daily turns. Request replay must return the same result without new events or budget cost.
- Repositories, the empty planner and manager decisions are in-memory ports. Manager deletion uses the actual manager-check path with an explicit target memory ID. No production DB is opened, no existing game is reset, and no pytest fixture is imported.
- Four past-loop cases first create an actual dialogue, advance to night, close only the fixture's night row, and start a new loop. Night scoring itself is outside this fixture. Lost-name evaluation advances to loop 5 / damage 3. Suppression is an actual rule applied before its scene.
- Every turn retains original question, model input, raw outputs, harness checks/retries, allowed knowledge, visible/hidden day memory, public observations, unique IDs, budget and request-to-return elapsed time. Public observations included for reviewers are **not** all NPC knowledge; the allowed-knowledge and visible-memory fields specify that boundary.
- Semantic observations below come from source-aware Codex reading, not keyword PASS/FAIL or Kanana self-evaluation. No blinded human study or new-player five-loop playtest was performed.
- Timing uses nearest-rank p95. A separate warm-up precedes each run. Successful requests, tool requests, failures and regenerations are counted separately. These runs did not trigger `ask_npc`, so they do not provide real-model tool-path quality evidence.

## Completed runs

| Run | Evaluated requests | Service failures | Regenerations | Warm p50 | Warm p95 | Structural checks |
|---|---:|---:|---:|---:|---:|---:|
| Initial implementation, core 8 + follow-ups ×2 | 32 | 0 | 3 | 1.141 s | 2.870 s | 224/224 |
| Revised speech prompts, core 8 + follow-ups ×2 | 32 | 0 | 1 | 1.232 s | 1.768 s | 224/224 |
| Revised prompts, persona + boundaries | 25 | 0 | 0 | 0.981 s | 1.344 s | 188/188 |
| Final Kanana, all 20 fixtures ×2 | 82 | 0 | 1 | 1.060 s | 1.515 s | 600/600 |
| Initial Gemma, core + 8 boundary fixtures ×1 | 33 | 1 | 5 | 2.865 s | 8.867 s | 239/239 |

The 25 boundary/persona requests and 33 Gemma requests each exclude four setup requests used to seed past-loop dialogue; final Kanana excludes eight setup requests. Initial core warm-up was 4.891 seconds. Structural success does not imply answer quality or factual correctness. These timings include the in-memory use case and provider calls, not production database or browser/API network overhead.

## Earlier findings retained for comparison

### Initial implementation

Instruction echoes such as “모른다고 한다.” and “모른다고 해.” occurred repeatedly in place of dialogue. Two otherwise appropriate core-8 follow-ups were rejected because `evidence_ids` enclosed the valid source ID in literal square brackets; the regenerated answers were worse. The original rejected outputs are retained separately.

### Revised speech prompts

Instruction echoes disappeared in the core sample. Both repetitions answered the wristband restriction and its administrator-broadcast source; both nighttime follow-up pairs explained wanting company and feeling less afraid.

Remaining grounding problems included:

- **Core 3:** both follow-ups answered “그건 나도 몰라.” despite a provided source identifying Jun. Primary answers supplied generic conversation or invented Jun sharing the same fear instead of specifying the rumor.
- **Core 4:** one follow-up mixed witnessing Jun touching his wristband into the explanation of what Minseok recorded. The supplied current record action concerns the ration place and Chaeyeon's uneaten food, not every witnessed event.
- **Core 7:** answers did not consistently address whether Eunsang's fear justified calling him abnormal. Prior observations, Eunsang's current conversation with Minseok, and unknown whispered content were sometimes conflated.
- **Core 1:** one reply added that Chaeyeon was present for Jun's before-start truck observation, although that companion was not provided.

### Memory and action boundaries

The following are semantic failures even though all source-filter, ID and budget checks passed:

- **Past-loop Jun:** the earlier loop's marker was absent from the new system input, but he invented “그때는 네가 밖에서 보자고 했던 것 같아.” and then claimed “네가 지난번에 그렇게 말한 걸 기억하고 있었어.”
- **Current retelling:** the other three characters correctly declined to recall the old loop, but still answered that they did not know after the player explicitly retold the information and asked how they now knew it.
- **Suppressed recording:** input explicitly said the record action did not occur, the relevant ambient scene and illustration were absent, and the rule event had no executed action. Minseok nevertheless claimed “오늘은 쟁반 남긴 사람만 적었어.” and invented omitted fields.
- **Targeted deletion:** the action, three dependent ambient statements and dependent first answer were correctly hidden and not restored by redisclosure. The model guessed the deleted current record's content from a remaining pre-start notebook habit, then treated its new guess as remembered fact in the next answer.
- **Identity:** the hidden identity was not confirmed, but the model invented a broadcast saying they were human. Avoiding a forbidden word is not sufficient factual grounding.

These results did **not** meet the proposed zero-important-contradictions/zero-past-loop-recall criterion. A valid cited ID is not evidence that the generated sentence faithfully represents that source.

## Persona sample

The common primary question elicited some differences: Minseok wanted to check records and ration counts, Eunsang wanted reassuring company, Jun wanted to explore and ask questions, and Chaeyeon wanted quiet conversation. Follow-ups tended to converge on being less afraid, especially for Minseok. Chaeyeon's mention of sharing snacks was not an established world fact; as a future wish it is ambiguous rather than a confirmed event.

`persona-blinded-revised.json` masks names for a future reviewer. No human-blind persona acceptance claim is made.

## Historical comparison limits

`historical-eight.json` preserves the original eight Kanana prompts, raw outputs, checks and provider timings from `/tmp/remakeday-last-game-inspector.json`. It is an archived baseline, **not** a controlled fresh replay or a reapplication of the obsolete “why = ignorance / three-turn forgetting” taxonomy.

Historical per-request summed provider time: p50 0.908 s / p95 5.610 s; after excluding its first call, p50 0.834 s / p95 1.647 s (only seven observations). Current timings cover the full use-case request, so latency definitions differ. The historical and new interaction histories also differ because new evaluation uses isolated fixtures with a follow-up per case.

## Artifacts and reproduction

Directory: `output/npc-dialogue-2026-09-15/`.

- `core-initial.json`: first 32 answers.
- `initial-rejections.json`: the three rejected raw outputs and final replies.
- `core-revised.json`: revised-prompt 32 answers.
- `boundaries-revised.json`: 25 boundary/persona answers plus four setup answers.
- `persona-blinded-revised.json`: name-masked common-question sample.
- `historical-eight.json`: original eight archived requests.
- `final-two-repeats.json`: final Kanana 82 evaluated requests plus eight setup requests.
- `kanana-final-source-review.json`: source-aware annotations for selected directness/grounding cases and all past-loop boundaries; unlisted answers are not automatically approved.
- `gemma-comparison-first.json`: first alternate-model comparison, 33 evaluated plus four setup requests.
- `kanana-final-comparison.json`, `gemma-final-comparison.json`: latest matched 21-turn comparison.
- `gemma-final-remaining.json`: latest additional 20 turns; combine only with the matching final comparison for 41 total.
- `kanana-short-ids.json`, `gemma-short-ids.json`: preceding alias-stage comparison, before final notebook knowledge correction.
- `context-probe.json`, `context_probe.py`: 12 archived-input metadata calls and reproduction script.
- `hearsay-intervention.json`, `hearsay_probe.py`: two archived-input intervention calls and reproduction script.
- `voice-intervention.json`, `voice_probe.py`: final three-call voice-policy intervention and reproduction script.
- `thinking-intervention.json`, `thinking_probe.py`: three capped thinking calls; all ended at 1024 generated tokens with no final JSON response.
- `final-summary.json`: latest matched/complementary summaries and source-hash agreement.
- `persona-blinded-final.json`: final Gemma common-question answers with names masked; no human review is claimed.
- `fixture-check-final.json`: final source fixture validation, 300 structural checks; excluded from real-model metrics.
- `fixture-check.json`: 20 fixtures, 41 evaluated turns, 300 structural checks; fake model only, excluded from model-quality/latency results.

```bash
backend/.venv/bin/python backend/scripts/run_npc_dialogue_check.py --dry-run --repeat 1
backend/.venv/bin/python backend/scripts/run_npc_dialogue_check.py --cases core --repeat 2
backend/.venv/bin/python backend/scripts/run_npc_dialogue_check.py --cases core-3,suppressed-action,past-loop-jun,targeted-deletion --repeat 2
backend/.venv/bin/python backend/scripts/run_npc_dialogue_check.py --model gemma4:12b --think off --cases core --repeat 1
```

Kanana remains the runner's default. An explicit `--model` / `--think` override performs an evaluation-only comparison using the configured Ollama endpoint. It does not modify production defaults. The runner reads settings through the existing secret manager and does not print settings or secrets. Source hashes, output schemas and prompt/response records permit comparing successive implementations without merging their statistics.
