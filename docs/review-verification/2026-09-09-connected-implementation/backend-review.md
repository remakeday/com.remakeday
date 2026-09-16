# Independent backend review — 2026-09-09

Reviewer: `/root/backend_review`. **FINAL DISPOSITION: changes requested; RM1 P1 remains unresolved. The frozen 07:35 final run classifies all21 questions correctly and validates30 verbatim quotes, yet SPC2 answers “맞다”/supported to a nonpublication question against an explicitly published source. No further code/test iterations are requested. Prior BR1–BR7 and concrete RM2/RM3 closures remain bounded; final semantic/production approval is withheld.** No P0 found. This report preserves initial findings and both independent follow-ups. The final section is the current disposition; earlier open/fix-request language is review history.

## Scope and evidence

Reviewed root/backend AGENTS, connected-investigation design, tester1 findings, additive API contract, the implementation handoff, `/tmp/connected-backend-review.diff`, `/tmp/connected-backend-changed-files.txt`, and actual implementations. Baseline is `/tmp/connected-backend-before`; there is no usable Git repository and none was created. The visual scope is approved A: four fixed portraits, six added event images, seen-image gallery.

The reviewer ran isolated in-memory probes via `PYTHONPATH=backend backend/.venv/bin/python /tmp/backend-review-probes.py`; these do not import database repositories, run tests using the shared database, or start a server. Production code was not edited. The owner's 198-test result is reported evidence, not a suite independently rerun here. Independently ran `.venv/bin/lint-imports --no-cache` (4 contracts kept, 0 broken; 116 files) and `bash scripts/check_forbidden_words.sh` (0 findings across 81 files); both exited 0. Login-shell environment warnings did not prevent either check.

## Findings

### BR1 — P1: static fragments reassert actions that the current rule suppressed

Location: `backend/apps/engine/app/use_cases/loop_interactor.py:524`–`:530`; loop-2 fragment declarations in `backend/apps/scenarios/scenario_a/adapter.py`.

Repro: apply `채연 / 배급을 남긴다 / suppress / any` before loop 2 and execute its first scene. The rendered scene says `채연은 오늘 쟁반을 옆으로 밀지 않는다. 먹은 양은 확인하지 못했다.` The same response's persisted public records and notes nevertheless include `채연이 아침에 배급을 남긴다.` with `verification=observed`. Suppressing Minseok's broadcasting-room visit similarly leaves the scheduled `민석이 방송실 근처를 서성인다.` fragment. The adjacent scheduled rumor attribution also bypasses the actual rumor outcome.

Cause: fragment publication checks loop/beat and erasure, but never the executed opportunity/result. Consequence: the original source ledger and advisor can contradict the actual intervention while still claiming source linkage. This directly breaks the central connected-investigation acceptance condition.

Requested correction: remove redundant scheduled action/rumor fragments or derive their publication from the actual scene execution. Regression must inspect every public observation and note, not just rendered narration/images. Owner acknowledged and is fixing.

### BR2 — P2: compatible overlapping rules are counted as conflicts

Location: `backend/apps/engine/app/use_cases/scene_execution.py:50`–`:52` and `:65`–`:66` at the reviewed checkpoint.

Repro: R1 is a user rule forcing Chaeyeon to explain known observations at any beat. R2 is the monkey-paw rule forcing the same explanation at beat 3. Both effects are `enforce`. Executing beat 3 yields R1=`conflict`, R2=`obeyed`, although the explanation satisfies both. The same rule-ID comparison affects base actions. The domain's `find_conflicts` correctly sees these equal-polarity rules as compatible.

Cause: any earlier rule ID is labeled a loser without comparing its effect to the winning effect. Consequence: the participant's experiment is incorrectly shown as conflicting and excluded from the compliance denominator. Ordinary paw acceptance can trigger it; no malformed request is needed.

Requested correction: reserve conflict for incompatible effects; let one actual action satisfy all compatible rules, while emitting its narration and any linked paw cost only once. Test compatible overlaps as well as opposite-polarity conflicts.

### BR3 — P2: historical linkage is presented as a measured failure

Location: `backend/apps/engine/app/use_cases/inspector_interactor.py:75`–`:76`.

Repro: a closed legacy five-loop attempt with one old note and no observation events returns `note_source_linkage={numerator:0, denominator:1, value:0.0}`. Legacy note source keys predate observation instrumentation, so the old play is displayed as a measured 0% linkage failure rather than unavailable measurement.

Requested correction: distinguish instrumented notes from legacy unmeasured notes. Return an unavailable value when coverage does not exist; for mixed attempts retain a clearly defined measured denominator and separately identify legacy/unmeasured records. Add legacy notes to the current retrospective test (it presently covers legacy harness records and zero opportunities only).

Related coverage concern in the same component: `coverage = all(existing harness events have the new version)` does not establish complete attempt coverage. An in-progress old attempt with successful pre-upgrade calls has no old harness events at all; completing its remaining loops after upgrade can falsely produce `complete_logged_calls`. Whole-attempt coverage needs an explicit scope/version boundary, or a conservative check covering every played loop. This is a concrete missing-data case, not a claim that currently retained new calls are omitted.

### BR4 — P1: lexical prefilter discards the public evidence needed for ordinary questions

Location: `backend/apps/engine/app/use_cases/intervention_interactor.py:118`–`:130`.

Repro using actual scenario source wording: with the public observation `채연이 자기 몫을 반쯤 남기고 슬그머니 옆으로 민다.` (actor Chaeyeon), ask `누가 밥을 남겼어?`. The result is unknown, no evidence, generic “read the notes again” guidance, and **zero model calls**. Prefixes `누가/밥을/남겼` match neither the original sentence nor actor field. A model capable of answering never sees the source.

For the tester1-style `채연 말고 밥을 남긴 사람이 있어?`, the gate excludes the directly relevant `어둑해진 방. 음식이 남은 쟁반 세 개가 보인다.` and its image caption: `밥` differs from `음식`, and `남긴` differs from `남은`. The actor-only records may be retained in a full play, but the three-tray observation is withheld, preventing an answer that separates “three trays were observed” from “their other owners are unknown.” Similarly, the recipient gate insists on `에게/한테` and drops the manager's relevant public instruction `이상한 점은 방송실로 알립니다.` for `민석은 누구에게 보고하는 거야?`.

Requested correction: use a bounded original-public-record context fallback or robust retrieval that preserves partially relevant scene context; retain grounded scope checks. Do not infer tray owners, a completed report, or an ear-tag definition from these records. Unknown about the requested identity/recipient can remain correct, while still acknowledging the available related observation and stating its exact limitation. Test synonyms/morphology and these actual tester1 source combinations, then perform live-model probes. Owner received the isolated counterexamples.

## Spec compliance assessment

The change meaningfully improves the required architecture of the experience:

- Original public observations are separate from hypotheses/model summaries, scoped to the attempt and disclosed loop. NPC replies and ambient speech retain `reported` status. Advisor requests read original records, require valid IDs and exact citations, and reject record-absence as negation.
- Custom rules use a finite grammar and an unchanged-original preview token; unsupported tester1 requests receive explicit alternatives. No nearest-action rewrite is performed.
- Scene execution changes actual narration and illustrations and emits rule opportunity records. Registration is no longer counted as execution; no opportunity leaves a null compliance value. BR1 and BR2 must be corrected before this portion is reliable.
- Paw benefit and cost are linked to an execution event; cost is conditional on remaining utterance budget. The new `budget_left` next-beat field matches that behavior.
- Prior final edited claims and full selected note IDs are restored within the same attempt; inherited IDs prevent selected evidence from being appended again. The added regression includes a third loop and detached evidence.
- Five-loop completion and 35/35/30 scoring are preserved. Revised truth wording separates policy from actual closure; final text distinguishes truck/quiet from closure.
- Successful harness calls now retain input, output, attempts, acceptance, timing, model and version. Semantic accuracy metrics correctly remain unreviewed/null. Historical metric coverage requires BR3's correction.
- Image execution guards remove suppressed action images and erased co-participants; the first-morning scene image is limited to the first loop. Actual visual continuity remains the visual/integration reviewers' scope.

## Code quality and regression review

Dependencies remain directed inward: scenario-specific scene/action content comes through DTOs, the composition root supplies rule templates, and no new application import of SQLAlchemy/FastAPI/adapters was found. The finite action representation is appropriately smaller than a general rule language.

The test rewrites primarily remove obsolete behavior (ordinal fragments, nearest-action translation, forced three options, prompt-internal assertions and generated paw side-effect claims). New tests cover source IDs, fabricated citations, preview enforcement, three-loop inheritance, actual suppression, paw costs and final outcomes. The reported passing suite did not cover cross-source contradictions, equal-polarity overlap, or legacy notes; those gaps, plus lexical retrieval synonym coverage, explain the findings above. No evidence was found that five-loop or score-weight assertions were removed to hide failures.

There is some stale code/documentation left by the replacement paths (old advisor prompt helpers/nearest-action docstring, unused chain/narration imports). It does not justify unrelated cleanup during this fix. The new scene execution module also holds domain policy in the use-case layer; if that policy grows, moving the pure resolution into a domain service would better match the backend's thin-orchestrator rule.

## Remaining verification and limitations

- Live-model relevance/contradiction quality is not proven by exact-citation validation. Korean token-prefix retrieval and a few question-shape filters are coarse; the tester1 tray-owner, ear-tag, and report-recipient probes still need live and human review. Returning a real quote is not sufficient evidence that the question was answered.
- Recommendation selection is deterministic and actor-context based. It does not yet prove semantic hypothesis fit; that metric correctly stays unreviewed. Unknown-answer guidance is mostly generic and must be checked in the actual flow for usefulness.
- Existing repository methods commit independently. New scene publication performs several such writes before the full response is delivered. A persistence/transport failure can leave a committed beat or some public records even though the client did not receive that scene; advancing again is not an idempotent replay. The observation key protects repeated individual inserts, but not the whole request. This pre-existing transaction boundary remains an explicit unmet crash-recovery risk under design section 6; no DB failure injection was run by this reviewer.
- Full output logging covers calls that return through `run_with_harness`; provider exceptions outside `LLMParseError` and an exception in a parallel evaluator batch can still prevent retention of surrounding completed calls. Error-path completeness needs separate failure injection before claiming universal call coverage.
- No production records, tester1 scores, schema migrations, or historical regrading were touched by this review. Integrated browser flow and fresh participant difficulty remain outside this code review.

## Handoff

Review artifact delivered while fixes are still in progress. BR1's redundant fragments have been removed in the working tree; a repeated in-memory probe no longer sees the contradictory Chaeyeon fragment. The subsequent stable diff and owner-reported 204-test result were received and rechecked below.

## Focused recheck of stable 204-test checkpoint

Re-read final implementation, refreshed diff and backend-progress. Independently executed `/tmp/backend-review-final-recheck.py` with the backend virtualenv and `PYTHONPATH=backend`; all four assertion groups passed. No database repositories, shared test database, server or reset operations were used. Fresh architecture checks: 4 contracts kept, 0 broken; forbidden-word check: 0 across 81 files.

| Original finding | Recheck result |
|---|---|
| BR1 | Closed. Both suppressed loop-2 action fragments are absent from all emitted original observations. Redundant scripted rumor attribution was removed as well. |
| BR2 | Closed for the reported defect. Equal-polarity user+paw rules both record obeyed, one explanation, one paw charge; opposing effects still produce conflict. Separate two-paw edge case is BR5 below. |
| BR3 | Closed. Legacy notes return value=null, denominator=0 and unmeasured count. Instrumented-loop starts define the measured population; mixed old/new loop starts cannot claim complete model coverage. Provider-error coverage is a separate BR6. |
| BR4 | Closed for deterministic retrieval failure. All bounded public records reach the advisor; synonym question can cite the source, unknown tray-owner and report-recipient answers can retain validated partial records. Tests use fake responses; live semantic usefulness remains unverified. |

### BR5 — P2: two accepted paw offers charge twice for one explanation

Location: `scene_execution.py:72`–`:79`; `_maybe_offer_paw` in `loop_interactor.py:587` onward.

Both first and second eligible paw offers select the same first future scene: Chaeyeon explaining at beat 3. Accepting both is an ordinary supported play path (first loop offers unconditionally; next eligible loop offers when prior score reaches the threshold). In later scenes, the compatible rules now share one explanation, but each paw rule deducts one utterance and appends the same cost sentence. Pure reproduction returns one explanation, two identical cost lines, budget 10→8 and two side-effect events. This contradicts the asserted shared-action/one-cost behavior and attributes two time costs to one utterance.

Preferred correction: do not offer an identical benefit already active; skip it or choose a distinct executable opportunity. This keeps the second offered choice meaningful. Also make cost accounting robust for existing duplicate rules: one actual explanation consumes one utterance budget, with one originating cost observation/event and compatible rules sharing that result rather than independently charging. Simply emitting two benefits would change the approved meaning and is unnecessary.

Probe: `/tmp/backend-review-recheck.py`, `DOUBLE_PAW` output.

### BR6 — P2: provider failure drops successful sibling-call logs but still claims complete coverage

Location: `harness.py:57` onward catches only `LLMParseError`; `night_interactor.py:260`–`:264` builds the entire `pool.map` result before persisting any report; `inspector_interactor.py:38`–`:40` establishes coverage from loop versions alone.

Independent no-DB reproduction uses actual `_judge`, three truth comparisons, and an LLM boundary fake that raises `RuntimeError` on call 2. Calls 1 and 3 complete successfully, but `list(pool.map(...))` raises and zero reports are retained. Retrying succeeds with three more calls. With five instrumented loop starts, the inspector returns `model_calls=3` and `complete_logged_calls` although the boundary actually received six calls, five successful. This disproves whole-attempt complete coverage even for successful calls.

Minimum correction: represent provider failure in the harness report and return through the ordinary fallback/report path so all completed sibling calls are persisted, including the error call's attempt metadata. Alternatively, preserve successful futures individually and explicitly mark incomplete coverage when any call cannot be retained. Keep the final label conservative; loop-start version alone cannot establish call completeness after an exception.

Probe: `/tmp/backend-review-failure-paths.py`, `CALL_COVERAGE` output (`total_calls=6`, `total_successes=5`, `reported_calls=3`).

### BR7 — P2: failed scene publication advances state and retry skips the unrecovered scene

Location: `loop_interactor.py:386`, `:397`–`:399`; `public_observations.py:28`; `event_log_repository.py:18`–`:20`.

This is more specific than the pre-existing general absence of a unit-of-work framework. On **beat 2→3**, manager checks and new paw offers do not run. The new execution path records/commits scene and paw effects before note publication and ambient generation. The event repository's commit flushes the same session's loop mutation and budget charge. Two independently injected boundary failures demonstrate the resulting behavior:

1. Ambient provider error after the new records: the request fails, but beat 3 and budget 9 are committed. Retrying next-beat returns beat 4; the beat-3 response and its paid-for explanation were never delivered.
2. First note-upsert failure after scene records commit: the request fails with six beat-3 observation records and no notes. Retrying returns beat 4, and none of those six notes are recovered by that retry.

The no-DB probe uses the actual use case and scene helpers with repository doubles modeling the existing documented shared-session commit behavior; SQL fault injection was deliberately not run while integration owns the database. Before this change, beat-3 ambient ran before fragment/save, so a provider error at that point did not introduce these new observation/charge commits. The general repository architecture predates the task, but the concrete commit-before-disclosure path is introduced by it.

Minimum boundaries to address: provider errors should enter the existing optional-ambient fallback, allowing the paid scene to return normally (also helps BR6). **That alone does not fix note/storage failure.** Scene publication needs an adapter transaction boundary that commits loop progress, cost, observations and notes together, or a persisted incomplete-scene/replay mechanism that resumes this beat and repairs missing notes before advancing. A general transaction framework is not required, but silently treating the next request as a new beat fails the approved retry/source-linkage promise. Do not merely mark source linkage complete for the subset of notes that happened to be written.

Probe: `/tmp/backend-review-failure-paths.py`, `SCENE_RETRY` and `NOTE_WRITE_RETRY` outputs (`retried_response_beat=4`, `beat3_notes_recovered=0`).

## Final focused-review handoff

Original BR1–BR4 are closed on independently checked finite behavior. BR5–BR7 need correction and focused regressions; live-model quality remains a separate required verification. Root has the findings and exact probe paths. Reviewer made no production implementation changes and performed no database/server operations.

## Final recheck — BR5–BR7 closed, 211-test checkpoint

Reviewed the refreshed 31-file diff, actual transaction port/adapter, composition wiring, all changed repository commit paths, separate harness-audit session handling, new pure regressions, and three real PostgreSQL fault-injection regressions. The owner reports **211 passed**; the reviewer inspected those database tests but did not rerun them because integration owns `test_db`.

Independent checks freshly executed:

- `.venv/bin/python -m pytest tests/pure --confcutdir=tests/pure -q --tb=short`: **4 passed**. `--confcutdir` excludes the parent database/autouse fixtures.
- `/tmp/backend-review-final-recheck.py`: original BR1–BR4 assertions still pass.
- `/tmp/backend-review-final-boundary-recheck.py`: actual scene-transaction adapter with an in-memory session protocol rolls back progress, cost, observations and notes on injected note failure; retry returns beat 3 once, charges once and recovers all source notes. The prior parallel provider-failure scenario now returns and counts all three reports.
- Import-linter: **4 kept, 0 broken**, 119 files. Forbidden words: **0**, 83 core files.

| Finding | Final evidence and disposition |
|---|---|
| BR5 | **Closed.** Offer selection excludes an active overlapping explanation; existing identical paw rules still share one explanation and one originating cost. Both rule executions are obeyed and cite the same cost observation, while only the originating execution carries the side effect. Pure regression covers both offer avoidance and pre-existing duplicate rules. |
| BR6 | **Closed.** Exceptions from the provider call become an error-bearing harness fallback report. Parallel evaluation retains the failed call and both successful siblings instead of discarding the batch. The earlier 3-call counterexample now produces 3 logged calls, 3 attempts and one fallback. Optional ambient generation returns no ambient on provider outage, allowing the paid scene response to complete. |
| BR7 | **Closed for the reproduced persistence/provider failure paths.** `start_loop` and `advance_beat` wrap the injected scene transaction; repository saves flush inside that scope and commit once at its successful exit. Failure rolls back loop creation/progress, budget, scene observations, notes and execution records together. Harness audit uses a separate session, and its ORM has no loop/attempt foreign key; a rolled-back first scene therefore does not erase the completed model call or block its audit insert. The concrete production adapter is wired in the composition root. |

The three PostgreSQL tests are meaningful: they inject a real aborted SQL transaction at note write, verify same-beat retry and single cost; verify paid-scene return with failed ambient; and verify failed first-loop publication retains planner audit without retaining the new loop or public observations. Independent no-DB checks confirm control flow and adapter scope; actual PostgreSQL execution remains attributed to the backend owner's 211-test run.

The transaction change is narrowly scoped to scene start/advance through an application port and an outbound adapter. No framework dependency enters the use case. Existing request commit behavior remains in effect outside the scene scope. No additional material regression was found in this focused review.

Remaining limitation: a successfully committed server response lost in transport is not an idempotent API replay; this is distinct from the now-fixed storage/provider-failure case. Whole-system recovery from a process crash or audit storage outage is not proven by these tests. Neither limitation is presented as an unresolved instance of BR5–BR7. Live-model relevance, scope accuracy and participant usefulness still require the separately planned raw-response review; fake responses and passing code tests do not establish them.

**Current handoff:** code-review findings BR1–BR7 closed. No database/server/reset operations performed by the reviewer. Ready for the separate real-model and integration verification gates.

## Runtime-model follow-up — 244-test checkpoint

Reviewed the updated 34-file diff, custom-name boundary, server-resolved advisor IDs, partial-evidence helper/unknown guards, capability guidance, reported-speech guard, and production ambient candidate selection plus statement/note persistence. Independently ran pure tests **37 passed**, import contracts **4 kept / 0 broken**, and forbidden words **0 / 83**. The provider-failure and shared-cost pure regressions remain included; scene transaction wiring is retained, including the new ambient note upserts inside the same start/advance boundary. No DB or server operation was performed.

The new live artifact `probes-20260909T041723Z.json` proves three positive controls still fail the question-relation contract: direct observed action and recorded speech yield unknown; explicitly nonpublic medical results yield supported for the question asking whether they were public. This is open **RM1 P1**, despite correct ID selection and exact source rendering. Blanket topic supplementation/weak next-action focus is **RM2 P2**; server-generated `들은 말이야` candidate rejected as unknown person `말이` is **RM3 P2**. Exact raw evidence, source hashes, independent counts and minimum correction recommendations are in [real-model-review.md](real-model-review.md), 04:17 recheck section.

BR1–BR7 are not reopened by these narrower runtime-model findings, but the previous finite-code approval does not constitute semantic approval of the new path. Current disposition is changes requested for RM1–RM3, followed by fresh real-model controls and source/statement trace review.

## Latest relation-contract checkpoint — model validation not yet established

Reviewed required `AdvisorRelationOutput.relation`, relation-to-user-status mapping, bidirectional negation and reported-speech examples, narrow selected-evidence/fallback correction, source-time/actor next paths, and removal of the name heuristic from trusted server ambient quotations. Independently ran database-free pure tests: **47 passed in 0.10s**. Root reports final full suite **254 passed / 3 existing warnings / 6.23s**, exec session78183 exit0; no old sandbox-error log is cited. The reviewer performed no DB/server/network/model operations or escalation requests.

Filesystem evidence confirms a new `/tmp/demo-integration/ollama-results/probes-20260909T044044Z.json`, but all **18 provider attempts** have `ConnectError: [Errno1] Operation not permitted`, output=null and fallback=true. The file's successful script exit does not establish model success. PC1–4 relation outcomes are therefore unvalidated; the ambient outputs demonstrate safe server fallback, not model selection. This distinction and exact raw/source/diff hashes are recorded in the latest section of [real-model-review.md](real-model-review.md).

RM1–RM3 code changes address the known reproductions and no new concrete code regression was found in this focused read/pure check. **Final real-model semantic approval remains pending an authorized successful rerun.** BR1–BR7 are not reopened.


## 05:41 actual-model recheck — RM1 remains open

Independently inspected the fresh authorized provider artifact and copied it byte-identically to [probes-20260909T054143Z.json](real-model-artifacts/probes-20260909T054143Z.json), SHA-256 `ec0b66e7101ff0681aef8c75e1c9e34a6347eee515961e6f58925f69900230c2`. All 18 provider records have successful accepted outputs, no error and no fallback. This supersedes the prior permission-only run as the latest actual-model evidence.

PC1 observed action, PC2 reported utterance occurrence, and PC4 explicit nonpublication return supported correctly. **PC3 asks whether Chaeyeon's medical results were published, selects the exact observed source saying they were not published, and still returns unknown. RM1 P1 remains open.** The same scene/time and explicit prompt contrast support contradicted; adding hypothetical future disclosure or unasked reasons does not justify this unknown. Grounding checks IDs at `intervention_interactor.py:215`; `:230` accepts the model relation and the generic unknown explanation adds an unasked relation/reason limitation. This is a semantic failure, not provider failure or fallback.

Q1–11 preserve legitimate unknown conclusions with original partial sources; Q12 gives real capability guidance without a model call. RM2's unrelated/excluded sources and incorrect next-path examples no longer reproduce. All returned evidence objects exactly match that question's public records and have no future loop. Q8's model-level supported is corrected to unknown by the server and must not be counted as unassisted model correctness.

All three ambient cases now make successful model calls: A1/A3 select a safe candidate; A2 intentionally selects null. Final lines, reported statement observations, note source keys, current loop/beat and both participants' memories match. The A3 `말이야` false positive is gone through actual selection and storage, closing RM3 for this reproduction. Three custom previews preserve original targets and honest nonexecution/knowledge limits. No additional concrete P1/P2 was found in these finite cases. Next paths refer to existing conversation/note/next-day affordances, but this probe does not establish the usefulness of the subsequent player interaction.

Current recommendation: retain BR1–BR7 closure and close RM2/RM3 finite cases; request a narrow same-event/time proposition correction and a fresh positive/negative live pair for RM1. Do not implement a generic negative-word inversion or hardcode the PC sentence. The code/diff hashes remain the same as the previous 47-pure/254-suite checkpoint, recorded in real-model-review.md. No production edits, DB/server/network/model operations, or reviewer escalation requests occurred. Provider success, gate counts, and independent AI review are not human accuracy or global usability metrics.


## 05:54 scope correction — PC4 regression, changes still requested

Reviewed `/tmp/connected-rm1-scope.diff` and actual files against its SHA manifest. The focused change preserves full original observations with actor/loop/scene context, adds general same-event elliptical-subject and publication-versus-content examples, and generates evidence IDs before relation. It adds no PC-specific execution branch or unsafe negative-word inversion. Independently ran **54 pure tests passed in 0.11s**. Root reports session8668 **261 passed / 3 existing warnings / 6.95s**, plus architecture4/4; no reviewer database execution.

The authorized fresh [055416 raw](real-model-artifacts/probes-20260909T055416Z.json), SHA `e1d29431c8ed8f1d83debe7b735f47e28dddb13bcc60d64b9c2becb1e57fa78b`, contains **20 successful provider returns across 18 harness tasks**, of which 18 are accepted and 2 invalid-ID Q2 outputs are rejected and retried. Provider errors0, fallbacks0. All rejected attempts are logged; this is distinct from claiming every output passed validation.

PC1/PC2 stay correct; PC3 is now contradicted correctly. **PC4 asking whether the results were not published is also contradicted, despite its source explicitly saying they were not published.** Exact path `positive_controls[3].harness[0].call_records[0].output`; accepted=true with no violations. The negative proposition should be supported. ID validation cannot establish the model relation's semantic correctness, and source-generation order does not solve that remaining contract failure. **RM1 P1 remains open.** The focused fake-model tests verify context/shape/passthrough, not actual-model polarity reasoning.

All 12 original final answers retain the prior source and next-path behavior; all evidence objects match available originals with no future loop. Q8/Q11 model supported outputs are corrected to unknown by guards. Custom3 remain honest nonexecution alternatives. Ambient A1 selects the safe candidate and preserves statement/note/memory linkage; A2/A3 both intentionally select null with no persistence. These are actual selector decisions, not fallback or name-filter failures. BR1–BR7 and RM2/RM3 stay closed for their finite reproductions.

Latest file/diff hashes, precise call counts, control table and remaining limits are recorded in the final section of [real-model-review.md](real-model-review.md). No final semantic approval, human accuracy, or global usability claim is warranted. Reviewer changed reports/artifact only and made no DB/API/network/server call.


## 06:10 polarity/lookup recheck — inverse source still fails

Read the eight-file focused diff and verified every current source hash against `/tmp/connected-rm1-polarity-sha256.json`. The small composition function preserves the four binary cases and unknown/null, while lookup supports affirmed concrete answers without inversion. Source rendering and existing guards remain intact. Independent pure tests **71 passed in 0.12s**. Root reports full suite session35068 **278 passed / 3 existing warnings / 7.22s** and architecture4/4. No reviewer DB execution.

Fresh [061038 raw](real-model-artifacts/probes-20260909T061038Z.json), SHA `cb2be29b556162e630f2bf6b3ffc21e67da4e90f135e9c0b8cc0bb76a1d0e21e`, has **24 accepted actual provider outputs, no rejected attempts, errors or fallbacks**. Original PC1–5 and the nonpublication positive/negative pair pass with proper internal values. However **SPC2 uses an explicitly published source and a negative publication question, yet the model labels evidence denied and final status supported. Expected evidence affirmed and status contradicted. RM1 P1 remains open.** Verified the actual call's messages contain `결과를 공개했다`, matching both control source and available records; this is not a synthetic-metadata-only probe defect.

PC6 why becomes a mere action claim/affirmed; PC7 loses tomorrow; PC8 changes actual instruction compliance into giving an instruction. Final unknowns are appropriate but do not validate those internal claims. Several original lookup questions likewise substitute related actions/terms for requested roles/recipients/definitions; existing guards keep final answers unknown. Passing composed output cases or schema validation cannot establish semantic adherence.

All final evidence/source/time checks, original next paths, custom3 and production ambient3 remain coherent. A1 selects the current visit record; A2 omits; A3 selects the known-source quote. Statement/note/memory consistency passes independent assertions. BR1–7/RM2–3 stay closed within reviewed reproductions. Detailed per-control judgment, code/diff hashes, raw input verification and uncertainty are recorded in the latest real-model-review section. Final approval remains changes requested, without human accuracy or broad usability claims.


## Two-stage code checkpoint — live rerun pending

Read current question-only interpretation, isolated positive-claim evidence input, unchanged-original lookup input, both audit roles, scope checks, and 11 new stage-boundary regressions. Independently ran database-free pure tests: **82 passed in 0.12s**. Binary evidence input does not receive the original negative question or interpretation polarity; the first call receives no world observations. First-stage provider failure skips the second stage while preserving its audit; second-stage failure preserves both audits. Both paths consume one question and retain available partial source text. The tests also verify explicit time-marker loss retries before evidence consultation and forbid rewriting lookup into a known action at interpretation.

No additional confirmed code P1/P2 found in this focused read/pure check. The marker check is limited lexical scope preservation, not general meaning validation; models can still misclassify question kind, alter an unrecognized temporal expression or choose an incorrect evidence relation. Actual successful two-stage raw and all opposite-source/lookup controls remain required before closing RM1. Current hashes before the requested handoff artifact arrives:

- `backend/apps/engine/app/use_cases/intervention_interactor.py`: `202142583bfb7a217a2abd3bd53afa5c0f47d7e5faa325771e93f4b30540135d`
- `backend/apps/engine/app/dtos/llm_output_dto.py`: `54dea5c669753798d3682e12bf1757ee6c546ea6e433c8130a14fcbf63f00189`
- `backend/tests/pure/test_question_stage_isolation.py`: `c38e7aab43e20ffc0e35dc46d9264e49bd5b43e45f8d5effd17224ac61c0ca0b`


## 06:28 two-stage live recheck — changes still requested

[Latest raw](real-model-artifacts/probes-20260909T062838Z.json), SHA `049f9acd282d878416d59313c6d035c47e742d224c698a00444f0589cbc9dc3b`, contains 39 harness tasks (interpretation21/evidence15/ambient3) and **51 provider outputs: accepted33/rejected18, provider errors0, fallbacks6**. Q7/PC1/PC2/PC3/PC7/SPC1 each exhaust three interpretation attempts and skip evidence. Actual prompt assertions confirm question-only interpretation, normalized-positive-only binary evidence input, unchanged lookup input and preserved public originals. Every response charges one question; every returned evidence object matches its available original without future-loop leakage.

**RM1 P1 remains open.** PC1/PC2/PC3/SPC1 repeatedly return proposition/open and fall back to unknown. PC4 interprets correctly but evidence returns empty/unknown despite explicit nonpublication. Thus five required final controls fail. PC5 lookup and SPC2 inverse-source negative question pass through correct stages. PC6 final unknown masks evidence-affirmed for an unsupported reason, PC7 drops tomorrow and falls back, PC8 sets negative polarity on a positive execution question. Correct final unknowns do not establish correct intermediate meaning.

Original Q1–11 final unknowns remain appropriate, but multiple evidence classifications rely on server guards. Q11 now omits its public wristband comparison record, and PC8 returns no related instruction source; report these recall limitations instead of claiming full useful grounding. Optional generated detail—including Q2's invented manager role—is still ignored and never rendered. Custom3 and safe ambient selection/persistence remain coherent; no new event invention was found. A1 selects source0 and preserves statements/notes/memories; A2/A3 intentionally omit.

Current9 source hashes still match the two-stage manifest and previous independent pure82 checkpoint. Root reports full suite **289 passed, 6.61s**, not independently rerun against DB. Detailed control states, exact call counts and hashes are in the final real-model-review section. This code/pipeline verification does not authorize final semantic approval or human accuracy/usability claims. Reviewer performed no DB/API/network/server operation.


## Enum/temperature code checkpoint — actual semantics pending

Read the five-file `/tmp/connected-rm1-enum.diff` and verified all current hashes against its manifest. Independent database-free pure tests: **86 passed in 0.12s**. `question_type` replaces the independently combinable kind/polarity fields with positive_proposition/negative_proposition/lookup; the original four-case composition and lookup behavior remain consistent. Binary stage input still excludes the original question, lookup receives the original unchanged, interpretation sees no records, and only original evidence is rendered. Both advisor calls explicitly pass temperature0; the harness records and forwards that exact value and the Ollama adapter preserves zero instead of replacing it with its default. Other roles retain their settings.

The narrow broadcast cue now includes `방송 지시`, allowing empty-unknown execution questions to retain already-public instruction text without asserting actual compliance. Its regression checks original source recall and unknown status. The changed enum cannot express the prior proposition/open combination, but does not prove the model chooses the correct question type, preserves time, or classifies evidence correctly. No new confirmed code P1/P2 was found in this focused check. RM1 remains open pending the authorized actual rerun; the 06:28 failed artifact is not reclassified.

Checkpoint hashes:

- focused diff `c2a8cf3f48c0e68c51885129c60cc534e85210b8b8a796fd17c4b22ea51e255c`
- intervention interactor `fab2e038afe7cd73da926bb30a647b1dd318e6c29d61f782c1f5598f93da8c5b`
- DTO `86181c3f3029dafaf60fa40a1628e38c81fac223094c00f22cf197802681e078`

No DB/network/API/server operation or permission request was made by the reviewer.


## 06:38 enum/temperature actual recheck — normalization contract still fails

[Latest raw](real-model-artifacts/probes-20260909T063851Z.json), SHA `db8885673b0672ebfbd2f1fbfda1272aded4513d71e90ea36f0281a208a7e316`, has **45 harness tasks / 47 provider outputs / accepted44 / rejected3 / provider errors0 / fallback1**. Both advisor stages actually use temperature0, preserve input isolation and charge one question. All final evidence objects, loop scope and ambient statement/note/memory links pass independent assertions. Current5 source hashes still match the enum manifest; root full suite reports **293 passed, 6.84s**, while the reviewer previously verified pure86 and made no DB execution.

**RM1 P1 remains open.** PC3 repeats denied with no evidence IDs three times and falls back to unknown despite its explicit nonpublication source. PC4/SPC2 both interpret the negative question with negative_proposition but leave `공개되지 않았다` inside positive_claim. Actual evidence prompts contain that negative claim. For SPC2's explicitly published source, evidence denied is consistent with the supplied negative claim, but server inversion produces incorrect supported. PC4's incorrect evidence denied happens to cancel the normalization error, so its correct final supported is not a semantic pass. The source/fixture inputs were independently matched to actual prompt text.

PC1/2/5, future scope PC7, execution scope PC8 and synthetic positive SPC1 improve or remain correct. PC6 still classifies an unsupported why lookup affirmed before the guard corrects it. Several original unknown questions likewise rely on guards; Q7's unsupported return denial and fabricated optional details are not exposed as facts. Custom3 and ambient3 retain safe original-source behavior. Latest real-model-review contains the per-control table, exact input evidence and restricted follow-up advice. Code/pipeline tests and lower fallback counts do not authorize final meaning or human accuracy/usability claims.


## Whole-claim entailment code checkpoint — actual review pending

Independently read the current DTO/interactor/harness and stage regressions; pure tests **87 passed in 0.11s**. The interpretation schema now requests claim/question_kind and preserves the original negation, subject, condition, time and quoted clauses. Evidence classifies the complete supplied claim directly; the old question polarity/positive normalization/matrix flip is removed. Lookup still receives the original query and contradicted lookup outcomes remain unknown. Public evidence originals alone are rendered; no model detail or generated claim becomes a new public fact.

`retry_feedback` defaults false and is enabled only for the two advisor calls. Harness copies the input message list, logs each actual attempt's message snapshot, and appends concrete schema/scope/ID feedback only before another attempt. First-stage time feedback uses the original question marker, not public records. Second-stage missing-evidence feedback lists only IDs already in the stage's public record input; it does not create an ID or establish relation by itself. Unknown without IDs remains valid and nonunknown still requires valid IDs. Provider exceptions retain their prior stop/fallback behavior, both audit roles and one question cost. Existing other-role input behavior is covered by opt-in regression.

No new confirmed code P1/P2 found in this static/pure check. Claim paraphrase and evidence entailment still require actual semantic verification; removing the old double-inversion path does not prove those model judgments are correct. RM1 remains open pending the authorized rerun. Verified current hashes equal the root handoff:

- DTO `b020c54f34fa699d8f861f5dda229e0a6ac256878263bcf89ae84df8111be011`
- interactor `b747ec497c7350f826c0e68efc90f72225cd8166dfd95b1881021511275d2380`
- harness `8c617034a31e661907c42b00375c915e0ed628c74b461b5c62dc0d414c8ae2e2`

No reviewer DB/API/network/server or permission operation occurred.


## 06:47 whole-claim actual recheck — explicit contradiction still unknown

[Latest raw](real-model-artifacts/probes-20260909T064753Z.json), SHA `7c6b057b8913128f3b4ddcff9ed58d8e27a668e62d348229de1f7cbdd0f443a9`, has **44 harness tasks / 46 outputs / accepted43 / rejected3 / provider errors0 / fallback1**. Q9 fails lookup-null validation three times despite actual appended feedback; evidence is skipped. Input isolation, all advisor temperatures0, source/time equality, one question cost and ambient persistence trace pass independent assertions. Current10 manifest hashes remain unchanged; root reports full suite **294 passed, 6.63s**, with prior independent pure87.

PC4 and synthetic SPC2 now preserve the negative claim and directly return supported/contradicted correctly; the old normalization/second inversion is absent. **PC3 still returns accepted unknown despite the actual evidence prompt containing the published-results claim and explicitly nonpublic observed result. RM1 P1 remains open.** PC6 transforms why into an action-occurrence proposition; Q6 changes fever condition to `열리면` (opens). PC7 preserves tomorrow but calls today's checkup broadcast supported for tomorrow's result publication. Final unknown guards prevent false user conclusions in those cases but do not validate the intermediate meaning.

Original source/next paths and custom3 remain bounded and honest; Q11 restores both comparison records. Ambient A1/A2 omit, A3 selects and persists the source quote with matching statements/notes/memories. Latest real-model-review gives the control table and prompt verification. No final semantic approval or human accuracy/usability claim is justified; no reviewer DB/network/API/server operation occurred.


## 06:55 exaone comparison — no production model switch recommended

Independently verified the helper clone differs only in its advisor model constructor, reported model metadata and output filename. Questions and public record contents exactly match the preceding gemma run. Production/code10 hashes remain unchanged. All harness model records identify exaone3.5:7.8b; **45 tasks / 51 outputs / accepted45 / rejected6 / provider errors0 / fallback0**. Six invalid nonnull lookup interpretations recover on feedback. [A/B raw](real-model-artifacts/probes-exaone-20260909T065504892941Z.json) SHA `d797217ce956e5256bf98928ff396bece7bbee2c74ec5278f24635ec03be315c`.

PC3 still returns unknown for explicit nonpublication; SPC2 wrongly supports a nonpublication claim against an explicitly published source. Both actual prompts were checked. **RM1 P1 remains open.** Exaone preserves fever wording and improves why/future controls after lookup repair, but reverses Q7 return polarity and invents ear-tag definition, medical follow-up, truck purpose and relation answers in question-only interpretation. Guards keep final unknowns and original-source rendering, so these are not shown as new public facts; they nevertheless fail the internal semantic contract. Q8 also loses the directly related public term source.

All source/time/budget/isolation and safe ambient persistence assertions pass. The comparison is not a production model change, general quality improvement, human accuracy metric or basis for final semantic approval. A possible overcautious/mixed-context prompt effect on shared PC3 failure remains a hypothesis requiring a bounded controlled diagnostic, not a proven cause. Full details and A/B limitations are in the latest real-model-review section. No reviewer DB/network/model/server operation occurred.


## 07:07 bounded extraction diagnostic — promising isolated result, product still unapproved

Independently checked [12-call diagnostic raw](real-model-artifacts/nli-diagnostic-20260909T070729518766Z.json), SHA `717be685f46e28bbb40c637a11118466d0551da29b26fcf75d22511883b32f8a`. All12 HTTP responses are200 with gemma3:12b provider identity, temperature0, exact raw/parsed outputs and no errors. Same claim, expected relation and full source records were verified against 064753; original messages are exact, original/concise schemas match, and extract_first adds quote instructions plus a leading quote field. All six extracted quotes are valid source substrings.

Original and concise each match3/4 relations; extract_first matches4/4. However extract_first PC3/SPC1 also cite reported public1, so the existing blanket reported guard would downgrade their whole product result to unknown. This is not a production pass. Per-source quote/relation validation and eligible-source aggregation can separate unrelated reported context from decisive observed evidence, but that new schema/aggregation and removal of claim rewriting remain untested by this diagnostic. Full original corpus/lookup/negative pairs must be rerun after implementation. RM1 stays open; no human accuracy or broad quality claim is supported. Reviewer performed no DB/network/model operation.


## Kind-only/source-assessment code checkpoint — live evidence pending

Independently read current DTO/interactor and source/stage tests; database-free pure tests **100 passed in 0.13s**. All8 handoff manifest hashes match current files. First stage has only question_kind and cannot emit a rewritten claim; second stage receives the original question unchanged. Each source assessment requires a real ID, nonempty verbatim quote and relation. Unknown IDs, whitespace/nonverbatim quotes and duplicate IDs with conflicting relations trigger feedback/retry; identical duplicates render once. Eligible observed sources and reported utterance-occurrence sources contribute separately; unknown context does not veto a decisive source, and both relation directions remain unknown. Unresolved-scope guards run against each full original source, preserving context beyond the short quote. Lookup contradiction remains unknown.

Single-question budget, both audit roles, provider-failure boundaries, original evidence rendering and other-role retry behavior remain covered. No additional confirmed code P1/P2 found. This verifies extraction/aggregation mechanics, not model judgment accuracy or complete source recall; original whole-corpus and opposite-source live controls remain required before RM1 closure.

Hashes: focused diff `918845fc794e12584fa75d25ef0c92ced56f630556d98a0c48c08f8b147a3069`; DTO `0a7374c489dcd7042e009ddb0aa34eadc882eac0104e673853be7903792dcc3c`; interactor `7f93b0bdfb4897c6b0fee0d98fb6098b5cd8d33df4a1275966cddc37764de5a4`. No reviewer DB/API/network/server operation or approval request occurred.


## 07:19 source-local actual recheck — accurate quotes do not establish correct relations

[Latest raw](real-model-artifacts/probes-20260909T071926Z.json), SHA `2f07c1fc432460e3601d086423b99170716b9709f1d396eabf3f5059f856b814`, contains **45 harness tasks / 46 outputs / accepted45 / rejected1 / provider errors0 / fallback0**. Q11's changed quotation marks are rejected and repaired. All79 accepted quotes match the cited originals. Actual first-stage world isolation, unchanged original second-stage questions, temperature0, source/time consistency, one-question cost and ambient statement/note/memory linkage pass independent assertions. Current8 manifest hashes are unchanged; independent pure100 and root full307/6.66s remain code/pipeline evidence.

**RM1 P1 remains open.** PC3 publication question and SPC2 nonpublication question are both misclassified lookup; the exact contradictory public6 sources are labeled supported and final status is supported. The UI answer is 기록은 이렇다, but the agreed relation contract is still wrong. PC1/PC4/PC7/PC8/SPC1 also get lookup despite being propositions. PC7's wrong current-source contradiction becomes final unknown only because lookup contradictions are discarded. PC6's unsupported why-source supported is corrected by scope guard. Thus final matching statuses cannot validate the intermediate contract.

Per-source extraction/eligibility/aggregation follows its tested mechanics, and reported background no longer vetoes decisive observed evidence. The production two-call semantic result nevertheless does not reproduce the isolated diagnostic's4/4. Original final unknowns remain safe largely through filters/guards; multiple source relations still confuse context with answers. Custom3 and safe ambient3 remain coherent, with no new event invention. Full case table, original prompts, quote counts and version hashes are in the latest real-model-review section. No production semantic approval or human accuracy/usability claim is justified.


## 07:25 classification isolation diagnostic — evidence failures persist with correct types

[28-call raw](real-model-artifacts/kind-diagnostic-20260909T072515636890Z.json), SHA `47429c71ac0840369a03867c5e098f99bda4d56d60959c35b0a5d6a2637fd0f9`, has28 HTTP200 responses, gemma3:12b/temperature0, no errors. Verified original questions/expectations/observations and byte-identical evidence source blocks. A six-example generic classification candidate matches all21 expected kinds. Seven separate evidence calls force the correct type through captured production prompts; they do not assume classification and evidence were jointly successful.

All11 quotes are verbatim, but PC3/SPC2 remain wrongly supported; PC6 confuses action with reason and PC7 wrongly supports tomorrow's publication from today's broadcast while contradicting it from current nonpublication. Independent no-DB application of current filtering/eligibility/aggregation yields wrong final PC3=supported, SPC2=supported and PC7=contradicted with correct types. Previous PC7 unknown was masked by lookup contradiction suppression. These are two separable failure stages; classifier success alone cannot close RM1 or establish the new production gate. Detailed limits and provenance are in real-model-review. No code change or reviewer network/DB execution occurred.


## 07:29:00 explicit-answer-meaning diagnostic — improvement with SPC2 still wrong

[Seven-call raw](real-model-artifacts/answer-semantics-diagnostic-20260909T072900364027Z.json) is copied byte-identically, **139,670 bytes**, SHA-256 **`db33d6c4619008f31e8b997add83467b732f427055d98ad6dfc27bd752f8cd59`**. Root session52784 exit0, `07:29:00.364027Z`–`07:29:17.576876Z`. Independently verified all7 HTTP200 responses, gemma3:12b, temperature0, raw/parsed agreement and no errors. All9 quotes are nonempty substrings of their cited originals. Questions, forced correct kinds, expected relations/IDs, whole public source blocks and schema exactly match the previous forced-kind diagnostic. Only candidate evidence instructions change; this is not a new production run.

PC3 now returns contradicted correctly; PC4 and SPC1 remain supported correctly; PC7's two sources now correctly say unknown for tomorrow's disclosure; PC8's instruction/visit sources remain unknown. **SPC2 still wrongly supports the negative disclosure question against an explicitly published original. PC6 still labels observed food leaving supported for a why question without any reason.** Thus five cases have appropriate source semantics and two do not. Current reason-scope guard protects PC6's final unknown, so six final expectations would match under aggregation, but that is not seven-case source-semantic success.

This candidate is a bounded improvement over the preceding seven-call diagnostic while RM1 remains open. No new architecture/diagnostics are requested. The final production prompt-only change and single full-corpus rerun will determine the final unresolved disposition; old failed artifacts and unchanged expectations remain preserved. This diagnostic provides no human accuracy, statistical performance or usability estimate. Reviewer performed no network/DB/model/server operation and changed reports/raw copies only.


## Frozen final prompt checkpoint — exact diagnostic text reuse

Reviewed `/tmp/connected-final-prompts.diff`: only classification/evidence prompt strings change, with schema, extraction, eligibility, aggregation, audit and API behavior otherwise unchanged. AST literal evaluation verifies the actual concatenated production first prompt exactly equals the successful21-question classification diagnostic's CLASSIFY string, and second prompt components exactly equal the seven-case semantics diagnostic's COMMON/LOOKUP/PROPOSITION strings. No helper import or model call was required. Current interactor hash is **`6fb42a732b4def2fb24892a7e741cb4593271de4004c976ade78a51d03a2d8d9`**; focused diff SHA **`7218f7035fe76dc79b39f2095f969b2acfbacbe7744f894afe2bbcb3879f6076`**. Pure tests were not repeated; root is running the final full suite and one complete model corpus. Previous diagnostic SPC2/PC6 limits remain acknowledged. Final semantic disposition awaits that sole last raw; no further architecture/diagnostic iterations are requested.


## FINAL — 07:35 frozen full-corpus recheck

[Final raw](real-model-artifacts/probes-20260909T073556Z.json), SHA **`adf69d8b2df289aefdb964fb2aa6282417a76481ce5dc70b8495e13cdbb969a4`**, is copied byte-identically. Root session45347 exit0; **45 harness tasks / 45 actual provider outputs / accepted45 / rejected0 / provider errors0 / fallback0**. All21 kinds match expected classifications, all30 accepted quotes are exact source substrings, original questions remain unchanged in evidence inputs, and first-stage world isolation, source/time consistency, temperature0 and one-question cost pass independent assertions. Custom3 retain honest nonexecution; A1/A3 safe quotations and A2 omission preserve statement/note/memory links.

**Unresolved P1 SPC2:** question “채연의 검진 결과가 공개되지 않았어?” receives proposition correctly; actual public6 says “결과를 공개했다.” The model quotes this exact observed source but assigns supported, which eligible aggregation returns as **answer=맞다/status=supported**. Expected contradicted. Exact source and question were checked in `positive_controls[9].harness[1].call_records[0].messages`, output and final result. This is neither a fixture/communication error nor an invalid quote. The model's incorrect relation passes source validation at `intervention_interactor.py:231` and aggregation at `:252`–`:259`. **RM1 stays open and final semantic approval is withheld.**

PC3/PC4 now both pass, as do direct action, reported utterance occurrence, who lookup, future unknown, execution unknown and synthetic positive-source controls. PC6's why-source supported remains an internal error guarded to final unknown. Several original lookup source relations also confuse context with requested answers, and Q3/Q9/Q11 omit available comparison/partial records. Original final Q1–11 unknowns remain appropriate, but neither those safe final outcomes nor9/10 final control agreement establishes complete internal meaning or participant usefulness.

Frozen interactor SHA **`6fb42a732b4def2fb24892a7e741cb4593271de4004c976ade78a51d03a2d8d9`** matches at final read; DTO `0a7374c489dcd7042e009ddb0aa34eadc882eac0104e673853be7903792dcc3c`. Final prompt diff `7218f7035fe76dc79b39f2095f969b2acfbacbe7744f894afe2bbcb3879f6076`; whole diff `949605a4934b15c1dcdd4b4cd4dab25253fd20b2fd8c7bb0e26be2aab5ffbbb8`; changed list `eaaf107b9688db2a70857e6a5d8e55a983023b64751bc9421a3443d44f8b5d0c`. Prior independent pure100/0.13s plus AST exact prompt reuse verification are distinct from root's final full **307 passed/6.73s**. No reviewer shared-DB execution.

Review ends here without additional implementation or diagnostics. Preserve old operating server until a separate informed decision; this review grants no promotion approval. All failed artifacts and expected controls remain unchanged. BR1–7 and the prior specific RM2/RM3 reproductions stay closed, while RM1 and advisor semantic acceptance remain unresolved. No human accuracy/statistical quality/usability metric is asserted. Reviewer changed only reports and copied artifacts, and performed no DB/network/API/server or permission operation.


## Gemini/Ollama interchangeable adapter: independent bounded review (2026-09-09 08:04 UTC)

Scope: `/tmp/connected-gemini-review.diff`, five files listed in `/tmp/connected-gemini-changed-files.txt`. All five current files matched `/tmp/connected-gemini-sha256.json`. Production adapter SHA256 `7a1b5e84a707bcfb3b9f299f5659ae00856c87d5b5f76ff2c8a5a6dc464e2ab8`; factory `17c724caf3a6c73ae0c3c7bdd12491b85c2fc5beb0d307c23533de9a77cd7fed`.

No new confirmed P1/P2 in this bounded adapter change. SDK types remain in the outbound adapter; the existing LLMPort and composition root preserve independent CORE/NPC selection. Reviewed system-only requests, system/user/model mapping, nested original JSON schema, explicit temperature zero, JSON object parsing, blocked/abnormal finish handling, empty/malformed parse failure, SDK exception propagation and model audit identity. SDK 1.29 defaults to one HTTP attempt; the adapter does not add a retry loop. Independent DB-free command `.venv/bin/python -m pytest tests/pure/test_gemini_llm.py --confcutdir=tests/pure -q --tb=short` passed **18 tests in 0.24s**, one existing SDK deprecation warning. Root separately reported full **325 passed in 6.49s**; this reviewer did not run DB tests.

This is implementation approval for the interchangeable adapter boundary, not live provider or semantic approval. Root-run connectivity artifact `/tmp/demo-gemini-connectivity-results/20260909T080110233223Z.json` lists 54 models and Gemini 2.5 Pro generation support, but its actual generation returned **ClientError 404**. Model listing alone therefore does not establish generation availability or quota. Existing **RM1 remains unresolved**; switching providers does not close it. Gemini 3.x official sampling-default guidance differs from the retained explicit temperature contract; the adapter deliberately does not silently change the caller's value. Any 3.x probe must record the actual value and assess its outputs independently.

Reviewer prepared root-only helpers `/tmp/demo-gemini-connectivity.py` (model argument, safe error summaries) and `/tmp/demo-gemini-adapter-probe.py` (one product adapter call). Both syntax-compiled; this reviewer performed no credential reads, live API calls, DB/server changes, or escalations.


## Gemini shared pacing: independent final checkpoint (08:11 UTC)

Reviewed updated seven-file `/tmp/connected-gemini-review.diff`; all current hashes match `/tmp/connected-gemini-sha256.json`. Adapter SHA256 `d94af0f4c86165010875adb496fa6105272ddd3a8a723e0c80a0eea510eb7350`, factory `604ba0c32546ea6285ee76a234ec82e0b77afe17e10264636fee7a29eb88f926`, settings `90a6c67872a612cec6775851ac324c1f7be9e4c3127b86ede0824bdd06fee87c`. No new confirmed P1/P2 for the documented single-worker scope. Module-global lock and monotonic admission time share default six-second spacing across instances and concurrent calls; failed calls consume a slot. Factory receives a positive validated rate, SDK retry behavior is unchanged, and waiting occurs inside the harness measurement. This is process-local completion admission pacing, not distributed project quota enforcement or a daily 1,500-request counter; the documentation explicitly distinguishes those limits.

Independent DB-free target command `.venv/bin/python -m pytest tests/pure/test_gemini_pacing.py tests/pure/test_gemini_llm.py --confcutdir=tests/pure -q --tb=short`: **20 passed in 0.25s**, one existing SDK deprecation warning. No live API, database or server action by this reviewer.
