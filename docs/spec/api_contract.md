# API 계약 v1 (MVP) — backend 8500 / frontend 3500

모든 응답은 JSON. 에러는 `{detail: string}` + 4xx/5xx. 잘못된 상태 전이는 409.

## 세션·회차 (P1)

### POST /sessions
req: `{prior_attempt_id?: string}`
res: `{attempt_id: string, attempt_n: number, entry_lines: string[3], prior_cell_results: CellScores|null}`

### POST /sessions/{attempt_id}/loops
res: `{loop_id: string, loop_n: number, morning_text: string, damage_level: 0|1|2|3, budget_left: number, beat: 1, beat_title: string, narration: string, broadcast: string|null, illustrations: Illustration[], aftermath: string|null}`
- 회차 1..5 순서 강제. 이전 회차가 안 닫혔으면 409
- `aftermath`: 전날 걸린 규칙이 부작용을 만들었을 때만 — "어제는 없던 일이 있었다" 톤 한 줄 (내용은 밝히지 않는다)
- `Illustration`: `{image_id: string, caption: string}`. 시나리오가 지정한 현재 비트의 관찰 이미지 목록. `image_id`는 프론트의 허용된 이미지 매핑 키이며 URL·LLM 출력이 아니다. 이미지 없는 비트는 빈 배열. 프론트는 필드가 없는 구버전 응답과 알 수 없는 ID에 기존 비트 배경을 사용한다.

### POST /loops/{loop_id}/utterances
req: `{target: string(code), text: string, request_id?: string(UUID)}`
res: `{utterance_id: string(UUID), reply: string, npc: {code: string, name: string, mood: "calm"|"uneasy"|"wary", uttered: boolean}, budget_left: number, beat: number, tool_used: boolean, observations: Observation[]}`
- 한 장면에서 NPC마다 성공한 대화는 1회만 가능하다. `uttered=true`인 NPC에게 새로운 질문을 보내면 409이며 예산은 줄지 않는다. 다른 NPC는 대화 가능하고, 다음 장면에서 다시 말을 걸 수 있다. 성공한 질문마다 예산 1회를 쓰며 장면은 이동하지 않는다.
- 같은 회차의 같은 `request_id`/대상/질문은 장면당 1회 제한과 무관하게 저장된 성공 응답을 반환하고 추가로 차감하지 않는다. 다른 질문에 ID를 재사용하면 409. ID 생략 요청은 각각 새 발화다.
- 예산 소진·대화할 수 없는 상대·낮 종료는 409. 모델 응답 실패는 503이며 예산·대화 기억·노트가 변경되지 않는다. 네트워크 오류 후에도 같은 질문과 ID로 재전송한다.
- 발화·예산·관찰·노트를 한 트랜잭션으로 저장한다. 발언별 관찰 ID는 서로 다르며 응답의 관찰 ID로 노트와 연결한다.

### POST /loops/{loop_id}/beats/next
res: `{beat: number, beat_title: string, narration: string, broadcast: string|null, illustrations: Illustration[], paw_offer: {offer_id: string, rule_label: string, shown_reason: string|null}|null, day_done: boolean,
      ambient: {lines: {code: string, name: string, text: string}[]}|null,
      note_found: {id: number, kind: string, text: string}|null}`
- day_done=true면 이후 발화·비트 넘기기 409, 밤으로
- `illustrations`: 현재 비트만 전달하며 낮 종료 시 빈 배열. 장면 넘겨 보기는 발화 예산·비트 진행에 영향을 주지 않는다. 폐쇄 이미지는 이 목록에 넣지 않고 밤의 `world_outcome=closure`에서만 표시한다.
- `ambient`: 실제 발생한 행동과 참여 인물 조건을 충족한 시나리오의 작성 대화. 참여자 기억에 발언별로 저장한다. 조건을 충족하지 못하면 null (발화 예산 무관).
- `note_found`: 이 비트에서 새로 발견된 감각 파편 (노트에 적힌 직후)

### POST /loops/{loop_id}/paw/respond
req: `{offer_id: string, accept: boolean}`
res: `{applied: boolean, rule_label: string|null}`

### GET /loops/{loop_id}/notes
res: `{notes: [{id: number, kind: "fragment"|"confirmed"|"rule_observation", text: string, loop_n: number}]}`

### GET /loops/{loop_id}/npcs
res: `{npcs: [{code, name, mood}]}` (대화 가능 인물만)

## 밤 (P2)

### POST /loops/{loop_id}/night/draft
req: `{tapped_note_ids: number[], free_text: string}`
res: `{night_id: string, claims: string[]}` (≤8)
- 자유서술과 선택한 노트의 원문을 문장·줄 단위로 나눈다. 8개를 넘으면 나머지를 마지막 항목에 모아 보존한다.
- 정리 단계는 LLM 요약이나 어휘 필터로 내용을 추가·폐기하지 않는다. 정오 판정은 제출 시 수행한다.

### PATCH /nights/{night_id}/claims
req: `{claims: string[]}` — **1회만**, 2번째 409
res: `{claims: string[]}`

### POST /nights/{night_id}/submit
res: `{total: number, passed: boolean, loop_n: number, world_outcome: "truck"|"quiet"|"closure"|null,
      is_final: boolean, closed_by: "clear"|"doom"|"understood"|"understood_all"|null,
      cells: CellScores|null, cookie: {text: string, cell: string, level: 1|2|3}|null,
      intervention_available: boolean,
      ending_lines: string[]|null, cell_feedback: string|null, wrong_claim_count: number,
      night_clue: {loop_n: number, caption: string, image_ids: string[], voice_id: string,
                   broadcast: string, outcome_line: string|null}|null}`
- `total`: 상황 70점(원인35 + 동기35) + 정체30점. 부작용은 채점하지 않는다.
- `night_clue`: 밤 단서 시퀀스(밤단서 v2 P.1) — 결말 전환에서 관리자 밤 방송(`voice_id` MA08~12, 대본 `broadcast`) → 치지직 띠 안 `image_ids`(1~2장) → 바탕 위에 남는 `caption` 순서로 재생한다. 트럭 결말 밤에는 `outcome_line`(기존 트럭 파편)이 캡션 뒤에 한 줄 더 붙는다. 서버는 제출 시 `caption`을 「N회차 · 소등 후」 관찰(scene), `broadcast`를 전언(statement)으로 저장해 다음 밤의 근거로 탭할 수 있게 한다. 회차 표가 없는 시나리오는 null.
- `cell_feedback`: 매일 밤 — 칸별 점수는 숨긴 채 정성 문장만 ("원인은 조금 잡혔다. 동기는 비어 있다." 톤. 잡혔다≥80% / 조금 잡혔다>0 / 비어 있다=0). 부작용 피드백 없음.
- `wrong_claim_count`: 세계와 닿지 않은 주장 수 (감점 없음, 정보만)
- 1~4회차 → 점수 무관 is_final=false, intervention_available=true (신의개입으로)
- 5회차 → 점수 무관 판 종료(is_final=true, closed_by·cells·ending_lines 채움), intervention_available=false
- `passed`(≥50%)와 `closed_by`는 기존 분류 호환용이다. 생존·회차 종료·회고 접근 조건이 아니다.
- `world_outcome`은 모든 제출에서 세계 상태로 결정한다. 이해도가 100%여도 생존으로 바뀌지 않는다.
- `ending_lines`는 1~4회차에 null이다. 시나리오 결말 → 개발 회고 순서로 표시한다.
- `cookie`는 호환용 null이다. 점수에 따른 기존 쿠키 대신 모든 최종 점수에서 결말과 회고를 제공한다.
- 칸별 점수(cells)는 판 종료 때만 반환. 밤마다는 total만

## 신의개입 (P3) — 멸망한 밤에만

### POST /nights/{night_id}/questions
req: `{text: string}` → res: `{verdict: string, answer: string, detail: string|null, remaining: number, status: "supported"|"contradicted"|"unknown", evidence_ids: string[], evidence: Observation[], unlocked_note: null, next_observation: string|null}`
- `verdict`: "맞다." / "아니다." / "그건 알 수 없다." / "왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다."(왜/이유/어떻게 질문만)
- 판정은 3종으로 축소 — "그런 일은 없었다"는 기록 부재와 미발생을 혼동시킨다는 테스터1 소견(docs/review-verification/2026-09-09-first-play/tester1-findings.md)에 따라 제외.
- `answer`: 한다체 문장. 첫 문장은 verdict 또는 그 요지. 최대 3문장
- `unlocked_note`: 항상 null (호환성 유지)
- `next_observation`: 세계 구조 기반 조언 한 줄 — 항상 "네 기록의 「{닻 관찰 문장}」." 으로 시작하고 뒤에 "내일 {인물}에게 … 물어봐라." 또는 "{인물}: {행동} 규칙을 걸어 봐라."가 붙는다. 닻(플레이어 공개 관찰)이 없으면 null
- status="supported"일 때 kind "confirmed" 노트 저장(source_key `confirmed-{observation_id}`). 다음 밤 근거 목록에 확인 그룹으로 표시

### GET /nights/{night_id}/options
res: `{options: [{index: 1|2|3, label: string}]}`

### POST /nights/{night_id}/rule
req: `{choice: "1"|"2"|"3"|"custom", custom_text?: string}`
res: `{ok: boolean, rule_label: string|null, conflicts: string[], reason: string|null}`
- ok=true 후 다음 회차 시작 가능 (POST /sessions/{id}/loops)

## 판 종료 후 (P5)

### GET /attempts/{attempt_id}/harness — 5회차 제출 완료·판 종료 시 점수 무관 200, 아니면 403
res: `{rules: [...], harness_summary: {...}}`
- 진행 중 및 기존 조기 종료 기록은 403이다. 인스펙터 토큰 정책은 별개로 유지한다.
- `rules`: rule_id, source(monkey_paw/user_choice/user_custom), target, when_beat, effect, action, shown_reason, hidden_side_effect, created_loop, conflict.
- `harness_summary`: total_events, harness_interventions, fallbacks, paw_accepted, recommended_rules, custom_rules, rule_conflicts, questions_asked, rule_success_rate(null), tool_side_effects([{loop_n, beat, text}]).
- 추천/직접 규칙은 실제 저장된 규칙만 센다. 거부된 직접 제안은 포함하지 않는다. 충돌 개수는 모든 출처의 등록 규칙 기준이다.
- hidden_side_effect는 설계된 대가이며 발생 확인이 아니다. tool_side_effects는 도구 실행 기록 전체이며 원숭이손과의 인과관계를 확정하지 않는다.
- harness_interventions는 위반·폴백이 기록된 모델 호출 수다. 전체 호출 수 또는 사용자가 건 규칙의 성공률이 아니다. 규칙 이행 성공률은 아직 미측정이므로 null이다.

### GET /attempts/{attempt_id}/inspector?token={INSPECTOR_TOKEN}
res: `{events: [...], patches: [...], paw_rules: [...], scoring: [...]}`

### GET /health
res: `{scenario, harness, models: {npc, core, embedding}, db}`

## 타입
CellScores = `{cause: number, motive: number, side_effect: number, identity: number}`

2026-09-08 이후 제출의 side_effect는 저장 호환용 0이다. 화면은 상황(원인·동기 평균)과 정체를 각 100% 기준으로 보여주며 총점 반영 비중은 70:30이다. 기존 제출 기록은 재채점하지 않는다.

## Connected investigation additive contract (2026-09-09)

Existing fields remain unless explicitly corrected below. Empty arrays/null are valid; clients must not manufacture evidence or rule success.

- `Observation = {observation_id: string, attempt_id: string, loop_id: string, loop_n: number, beat: number, scene_id: string, scene_title: string, actor: string|null, text: string, source_kind: "scene"|"image"|"statement"|"rule_result", verification: "observed"|"reported", illustrations: Illustration[], rule_id: string|null}`. An observed statement means it was said, not that its content is true.
- Start-loop and next-beat responses add `observations: Observation[]`; utterance responses also add that field. These are newly disclosed public records. Notes GET adds `observation_ids: string[]` and `sources: Observation[]` to every note. Legacy notes return empty sources rather than invented provenance.
- `GET /loops/{loop_id}/observations` returns `{observations: Observation[]}` for all already disclosed observations in this attempt up to this loop. This is read-only and consumes no game budget.
- `GET /loops/{loop_id}/night/previous` returns `{previous_answer: null | {loop_n: number, free_text: string, claims: string[], tapped_note_ids: number[], draft_text: string}}`. `draft_text` equals the previous submitted night's exact `free_text`, including line breaks and whitespace. `claims` remains the separate confirmed/scored claim list. New attempts return null. Draft POST still accepts optional `inherited_note_ids: number[]` for compatibility, but all currently selected `tapped_note_ids` contribute to claims; inheritance no longer suppresses selected evidence. Original free_text and selected IDs remain stored separately.
- Question response adds `status: "supported"|"contradicted"|"unknown"`, `evidence_ids: string[]`, `evidence: Observation[]`, `next_observation: string|null`. Full question, answer and detail persist. Unknown has no confirmed note. Grounding uses original public observations, never hidden truth/user hypotheses/model summaries.
- Each option adds `target: string, action: string, effect: "enforce"|"suppress", when_beat: number|"any", reason: string, evidence_ids: string[], expected_observation: string`. May return 0–3 candidates. If empty, free input/rewrite remains available.
- `POST /nights/{night_id}/rule/preview` request `{custom_text: string}` returns `{preview_id: string, original_text: string, executable: boolean, interpretation: string|null, limitations: string[], alternatives: string[], conflicts: string[], rule: null|{target: string, action: string, effect: "enforce"|"suppress", when_beat: number|"any", label: string}}`. Preview does not apply a rule or end intervention. The client must show original/meaning/limits/conflicts and require an explicit apply click.
- Rule POST accepts `preview_id?: string` with choice custom. Custom apply requires a current successful preview matching exact custom_text; without it returns ok=false with reason. Confirmed apply uses stored preview semantics without remapping. Unsupported alternative is never applied silently.
- Harness GET adds `experiments: [{rule_id: string, intent: string|null, interpretation: string, opportunities: [{loop_n: number, beat: number, condition: string, actual_action: string|null, result: "obeyed"|"violated"|"conflict"|"not_evaluable", observation_ids: string[], side_effect: string|null}]}]` and `metrics: {note_source_linkage: Metric, rule_compliance: Metric, question_grounding: Metric, recommendation_relevance: Metric, custom_semantics: Metric, checker_accuracy: Metric}`. `Metric = {numerator: number|null, denominator: number, value: number|null, reviewed: number, method: string}`. Human semantic/accuracy metrics remain null with reviewed=0 until independently reviewed. No opportunity means denominator=0 and value=null.
- `harness_summary` adds `model_calls: number, model_attempts: number`; `harness_interventions` counts calls with violations/fallback only; `rule_success_rate` is evaluable rule opportunity proportion or null. Tool side effects remain separate from paw-linked effects.

Draft selection clarification: `tapped_note_ids` is the FULL current selection, old retained plus new. Selecting/deselecting a note changes the scoring evidence without mutating the player's prose. Night 2 restores night 1's direct writing, night 3 restores night 2's, and so on within the same attempt. Confirm-screen claim edits affect that night's scoring, not the separately saved direct writing. Night UI shows the editable prose first; notes and the observation gallery load only when opened.

Historical coverage correction: `harness_summary.model_calls` and `model_attempts` are nullable; legacy incomplete logs return null and `model_call_coverage: "legacy_partial_or_unavailable"`. Complete new logged calls use `"complete_logged_calls"`. These counts do not claim human checker accuracy. Harness response also includes `measurement_version`.

Next-beat response additionally returns `budget_left: number` (including day_done). It is the current post-scene budget, so a pawn consequence updates the visible counter immediately. Frontend consumes it when present for backward compatibility.

Scene failure handling: loop start and next-beat persist scene progress, budget effects, observations and notes atomically. A storage failure rolls those changes back; retry returns the same next scene rather than skipping it. Optional ambient provider failures return the scene with a safe current-record dialogue candidate (or null when no safe candidate exists) and a retained failure audit. Model-call audit records persist separately from public scene records and are never player evidence. Identical active pawn benefits are not offered again; historical compatible duplicate pawn rules share one actual explanation and one originating cost.

Question answers (2026-09-09): `answer` is a short natural-language string, no longer a fixed verdict enum. It may explain the scenario's public surface rules, connect observed events and clearly qualified possibilities, and use the last two question/answer pairs in the current loop for conversational continuity. Hidden truth, hidden cause chains, unrevealed observations and endings are never passed to this model. Prior answers provide conversational context only, not proof.

A successful advisor question uses one structured model call (`advisor_answer`) returning `{question_kind: "proposition"|"lookup", evidence: [{id, quote, relation}], answer: string}`. Answer length is 1–400 characters; evidence contains at most two original public records. Input retrieval chooses at most eight distinct records with at most 6,000 source-text characters by topic, actor, wording and recency, prioritizing explicitly requested loop numbers. Repeated wording in different loops/scenes retains its event scope. Original question wording and complete selected source sentences are preserved. Invalid IDs, non-verbatim quotes and contradictory duplicate assessments trigger bounded repair attempts; provider failures stop without repeated calls. All actual attempts are audited, and one question is charged once. Capability guidance requires no model call.

HTTP `status` remains a conservative assessment of what the quoted observations establish about the original question, separate from the natural answer's explanation of basic rules or qualified inference. A related citation does not by itself prove a reason, identity, future event or execution of a reported instruction. Unknown metadata does not replace a natural answer with a refusal. `detail` is server-rendered optional source text/limits; the model cannot supply it. Unknown may recover at most two topical partial records when no relevant source was selected. `next_observation` points to a known scene or actor when available. The UI presents the short answer first and puts source cards and inspection guidance under a collapsed disclosure; it does not append the entire notebook to every answer.

Current ambient dialogue and its original statement records are saved as notes in the same scene transaction. Its internal model schema is `{candidate_index: integer|null}`; HTTP ambient stays `{lines:[{code,name,text}]}`. Trusted quotation candidates retain scene/erasure/forbidden-word guards and do not run speculative unknown-person recognition intended for free generation.

## Gameplay clarity and authored dialogue (2026-09-10)

- Loop start adds optional `ambient: {lines:[{code:string,name:string,text:string}]}|null`, same as next-scene. Initial `observations` includes those newly heard lines. UI seeds this dialogue once.
- Ambient speech is authored scenario data selected deterministically from the actual scene, participants and completed action prerequisites. No ambient model call is made. Suppressed actions and absent actors cannot supply their original dialogue. It consumes no player conversation budget. Spoken lines remain `statement`/`reported` observations with source-linked notes and participant memory. First-person explanations produced by information rules are likewise statements, not independently verified facts.
- Scene and action observations remain available in the notebook. Day log uses a short save notice rather than repeating the source text. Pawn-offer refusal identifies the offer explicitly.
- UI labels describe scenes and today's shared conversation budget: six scenes per day,8/7/6/5/4conversations across five days, one per actor per scene. Scene advance/notebook/ambient are free; advance does not replenish the budget. Existing special-rule conversation costs remain. Initial guide is compact with expandable detailed rules and can be reopened during play.
- Custom preview recognizes the player's report-question condition, for example `민석이 보고하는 것을 내가 물어보면 상세하게 설명한다.` It stores canonical action `보고를 물으면 자신이 한 일을 자세히 설명한다` in the existing rule field, with original text preserved in the preview/audit and natural interpretation shown to the player. No migration is required. Currently eligible actors are declared by scenario question-reply data; unsupported actors/conditions are explicitly declined. Conditional requests are not replaced with a generic observation-explanation alternative.
- These rules are excluded from autonomous planning and activate only on a direct report-related question/request to the target. Looking-at/wearing homonyms, room-location questions, explicit topic exclusion and declarative promises do not activate them. A player's own report is not reinterpreted as the NPC's report.
- A triggered report rule selects authored character knowledge using actual current-loop action prerequisites, never future/suppressed actions. This can reveal what the actor personally reported even though an outside observer did not hear it. Responses before a room visit describe preparation/intention. Responses after altered actions use different authored branches. This is deliberate story content, not model-invented evidence. Ordinary direct conversation still uses the configured NPC model.
- `RuleExecutionEvent` records the actual spoken response and its observation ID. Authored fulfilled responses are `obeyed`; unavailable legacy conditional configurations are not self-certified as successful merely because a model produced text.
- Image damage remains a visual layer. Dialogue, inputs, controls and notebooks have no inherited damage transform/filter. Main reading text is18px, supporting text16px, with1.7line height.
