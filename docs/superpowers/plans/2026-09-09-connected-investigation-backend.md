# Connected investigation backend implementation

> Execute sequentially inside the delegated backend workstream. Approved design: ../specs/2026-09-09-connected-investigation-design.md. No further design approval is required.

**Goal:** Connect publicly observed scenes, editable submitted hypotheses, grounded questions, executable rules, and participant retrospective with honest provenance and denominators.

**Architecture:** Add typed observation, rule preview and execution events to the existing JSONB event log. Scenario DTOs declare scene observations and finite executable opportunities; engine evaluates conditions and persists public records. No database migration, original record rewrite, or production reset. Existing five-loop flow and 35/35/30 scoring remain.

**Data handling:** Repository has no Git metadata. Before-change backend and API contract copied to `/tmp/connected-backend-before`. Review by file diff. Tests force `pigfarm_test`; only this workstream runs backend tests. Production tables are not modified.

1. Publish additive API contract and ledger. Verify frontend acknowledgement.
2. Write failing regressions for observation timing/provenance and answer carry-over. Add DTOs/events, scenario scene conditions, read-only observation/previous-answer APIs and lossless answer composition. Verify focused tests.
3. Reproduce advisor irrelevant confirmations, unsafe action approximation, ambient missing context and unknown-person false positives. Ground advisor in original public observations, cite sources, preview exact custom semantics with confirmation token, contextual executable options. Verify regressions and boundary isolation.
4. Add finite scenario action opportunities, actual rule outcomes, coherent paw benefit/cost, and remove assertion of execution from registration/planning. Verify enforce/suppress/conflict/no-opportunity cases with deterministic tests.
5. Explicit branch-aware scoring propositions and complete harness attempt logs. Add derived retrospective metrics with numerator/denominator/review counts and N/A for human semantic review. Verify five-loop flow and original scoring invariants.
6. Run backend suite and architecture/forbidden-word checks, diff snapshots, update ledger with exact results and limitations; request root-assigned independent review.

No generic rule DSL, speculative abstractions, audio or production migrations.

## Executed task/file/test map

| Task | Production files | Acceptance evidence |
|---|---|---|
| Public observations | app/dtos/observation_dto.py; app/dtos/event_log_dto.py; app/use_cases/public_observations.py; loop_interactor.py; scenario_a/adapter.py | test_connected_investigation.py source/timing/free-read/reported-statement tests; event-log round trips |
| Editable prior answers | night_interactor.py; game_repository.py; game_router.py | connected previous-final-edit, dedup, repeated deselect/reselect/third-restore tests |
| Actual scenes/rules/paw | scenario_dto.py; scene_execution.py; loop_interactor.py; scenario_a/adapter.py | connected suppress/image, known-source action, no-opportunity, conflict and linked paw-cost tests |
| Grounded advisor and confirmed semantics | intervention_interactor.py; llm_output_dto.py; game_router.py; engine_dependency.py | test_usecase_intervention.py and connected exact-preview-token/answer-not-ask tests |
| Context and model audit | harness.py; game_support.py; loop_interactor.py; llm_output_dto.py | connected successful-call trace/non-name tests; existing day/ambient memory/harness/ablation tests |
| Scoring and retrospective | night_interactor.py; inspector_interactor.py; scenario_a/adapter.py | unchanged weight/five-loop assertions, connected legacy denominator/outcome tests |

All test paths are under backend/tests/engine; production paths under backend/apps/engine unless explicitly scenario_a. Independent reviewer should inspect /tmp/connected-backend-review.diff and backend-progress.md, including expectation-change mapping and limits. Execution authorization was already granted, so no additional approval handoff was requested.

### Real-model follow-up checkpoint

`intervention_interactor.py`: server-resolved evidence, useful unknown and exact capability scope. `loop_interactor.py` / `llm_output_dto.py`: current-record candidate selection, scoped dialogue and atomic note persistence. `tests/pure/test_real_model_grounding.py`: 21 live-output-shape regressions and positive controls. Existing remake/rule/E2E/transaction assertions now validate source-constrained behavior; five-loop, scoring and rollback invariants retained. Verification: 244 full tests / 37 pure tests, architecture 4/4 and forbidden words 0. Independent review/live-model rerun are required before global acceptance; producer/consumer HTTP fields unchanged except documentation corrected to the already shipped ambient.lines shape.

Same-event live follow-up: source selection precedes relation generation, source metadata survives to the prompt, and generic multi-sentence scope contrasts distinguish disclosure from content/reason/future. Production files intervention_interactor.py and llm_output_dto.py; pure regressions test_relation_event_scope.py. 54 pure checks and architecture pass; root relays full DB/live execution and independent semantic review remains required.

Polarity decomposition checkpoint: one structured call separates positive proposition, source polarity and question polarity; a small composition function calculates final proposition status. Add lookup kind to preserve who/action/explicit-reason questions. Audit-only propositions never replace source detail. New test_question_polarity.py validates 17 matrix/scope/lookup cases; existing input fixtures migrated. 71 pure tests and architecture pass; root-mediated full/live corpus plus independent semantic review are still required.

Two-stage isolation follow-up: question-only interpretation precedes public-evidence evaluation; binary evidence evaluation never sees the original negative question, lookup gets its original query unchanged. Each phase is audited, one user question is charged, and stage failures retain unknown/partial original sources. New test_question_stage_isolation.py adds 11 boundary/failure/scope cases; 82 pure and architecture checks pass. Full DB/live verification remains root-authorized relay followed by independent review.
