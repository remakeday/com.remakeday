# Connected Investigation Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the five-loop interface into a connected investigation where every claim, question, rule, image, and retrospective result can be traced to observations the player actually saw.

**Architecture:** Keep the existing `/play` state machine and backend-owned game flow. Add the backend's public additive DTOs to `frontend/contracts/api.ts`, then render focused, reusable observation and rule components inside the existing day, night, intervention, and retrospective screens. Preserve legacy fallbacks by treating missing additive arrays as empty and nullable records as unavailable; never infer hidden facts.

**Tech Stack:** Next.js 16.3 App Router, React 19 client components, TypeScript 5.9, Tailwind CSS 4, Node Playwright scripts with mocked API and real frontend/assets.

**Spec:** `docs/superpowers/specs/2026-09-09-connected-investigation-design.md`

## Global Constraints

- Keep five loops regardless of score, followed by final narrative and only then the retrospective.
- Keep free questions and the three-question per-loop budget.
- Preserve retry behavior, keyboard operation, reduced motion, and a usable 390px layout.
- Use four stable compact portraits: E01 Chaeyeon, E04 Minseok, E07 Eunsang, E10 Jun. Keep engine mood data but do not switch portrait art by mood.
- Reuse only images already disclosed by public observations. Do not show hidden branches or add causal arrows.
- Show statement provenance without promoting the statement's content to confirmed truth.
- Custom rules require preview and an explicit matching apply action; unsupported alternatives are never silently substituted.
- Show N/A for unmeasured metrics and zero-opportunity rates; do not manufacture success.
- No audio, new dependency, backend mutation outside existing API calls, or broad refactor.
- The repository has no usable Git metadata. Preserve `/tmp/demo-pigfarm-frontend-before-connected-20260909` and produce a diff artifact instead of commits.

---

### Task 1: Public API Contract

**Files:**
- Modify: `frontend/contracts/api.ts`
- Test: `frontend/tests/connected-investigation.cjs`

**Interfaces:**
- Consumes: additive contract in `docs/spec/api_contract.md`.
- Produces: `Observation`, `PreviousAnswer`, `RulePreview`, `Experiment`, `Metric`; API calls `getObservations`, `getPreviousAnswer`, and `previewRule`; expanded existing DTOs.

- [x] **Step 1: Write a failing browser contract test** whose mocked handlers require `GET /loops/{id}/observations`, `GET /loops/{id}/night/previous`, inherited note IDs in draft requests, and preview-before-apply requests.
- [x] **Step 2: Run** `NODE_PATH=/tmp/pigfarm-image-browser/node_modules node tests/connected-investigation.cjs` from `frontend/`; expect failure because the UI never calls the additive endpoints.
- [x] **Step 3: Add exact DTOs and typed request methods** from the published contract, retaining existing fields and optional legacy response handling only at render boundaries.
- [x] **Step 4: Run** `npx tsc --noEmit`; expect no contract type errors.

### Task 2: Observation Cards and Stable Portraits

**Files:**
- Create: `frontend/components/ObservationCard.tsx`
- Modify: `frontend/components/screens/DayScreen.tsx`
- Modify: `frontend/lib/imageMap.ts`
- Modify: `frontend/app/globals.css`
- Test: `frontend/tests/connected-investigation.cjs`

**Interfaces:**
- Consumes: `Observation`, current beat illustrations, existing NPC mood/code.
- Produces: `ObservationCard({observation, compact?, onOpen?})`, `stableNpcImage(code)`, accessible day notebook overlay.

- [x] **Step 1: Extend the failing browser test** to open the day notebook without consuming budget, verify an observation's loop/scene/source label and image, reopen its source scene, and confirm an unseen branch image is absent.
- [x] **Step 2: Run the focused test** and verify failures are caused by missing notebook/source controls and mood-dependent portrait URLs.
- [x] **Step 3: Implement a compact four-button portrait strip** using E01/E04/E07/E10 while retaining mood text/status semantics and responsive horizontal scrolling at 390px.
- [x] **Step 4: Add the day notebook** with purpose copy on first available note/observation, explicit source labels (`장면에서 관찰`, `이미지에서 관찰`, `발언을 들음`, `규칙 결과`), image replay, and close/return focus behavior.
- [x] **Step 5: Run the focused browser test** and confirm budget does not change, source navigation works, unseen images remain absent, and no horizontal overflow appears.

### Task 3: Previous Draft and Evidence Gallery

**Files:**
- Modify: `frontend/components/screens/NightScreen.tsx`
- Modify: `frontend/components/screens/ConfirmScreen.tsx`
- Create: `frontend/components/EvidenceGallery.tsx`
- Test: `frontend/tests/connected-investigation.cjs`

**Interfaces:**
- Consumes: notes with `sources`, `getPreviousAnswer`, `getObservations`.
- Produces: restored editable draft, distinct previous/current evidence selections, source-image modal and seen-only comparison.

- [x] **Step 1: Add a failing flow** with a previous submitted answer, edited claims, prior selected note IDs, current notes, duplicate note text from distinct observations, and two seen images from the same scene.
- [x] **Step 2: Run the test** and verify the prior answer is not restored and evidence is currently deduplicated by display text.
- [x] **Step 3: Restore `draft_text` into the textarea** with a visible “지난 회차에서 이어 쓴 초안” label; preserve original values until the player edits them.
- [x] **Step 4: Preserve prior evidence selection separately** and send the full current selection (retained old IDs plus new IDs) as `tapped_note_ids`; always send the original restored ID set as `inherited_note_ids` so old evidence text is not appended again after off/on toggles. Label that deselection changes evidence attachment without deleting or rewriting player-authored claim prose.
- [x] **Step 5: Render already-seen image cards** with loop, scene, observation, and source. Allow full-image/source review and compare only two images present in returned public observations; show sequence language instead of causal claims.
- [x] **Step 6: Keep edited claims intact through confirmation** and ensure returning data is neither auto-submitted nor copied into a new attempt.
- [x] **Step 7: Run the browser flow** across two consecutive restores and assert the full-current/original-inherited request sets, preserved edits, no duplicate restored claim/evidence text, hidden-image absence, modal keyboard close, and mobile fit.

### Task 4: Grounded Questions and Contextual Rule Choices

**Files:**
- Modify: `frontend/components/screens/GodScreen.tsx`
- Test: `frontend/tests/connected-investigation.cjs`

**Interfaces:**
- Consumes: question `status/evidence/next_observation`; option `reason/action/evidence_ids/expected_observation`; rule preview/apply DTOs.
- Produces: grounded response cards, 0–3 contextual option cards, custom interpretation confirmation UI.

- [x] **Step 1: Add failing question cases** for supported, contradicted, and unknown responses. Assert evidence/source details for grounded answers and a concrete next observation for unknown, with no fabricated confirmation note.
- [x] **Step 2: Add failing option cases** for two candidates and zero candidates; each candidate must expose reason, changed action, evidence, and expected observation.
- [x] **Step 3: Add failing custom-rule cases** for executable preview, conflicting preview, unsupported preview with alternatives, changed text after preview, and explicit apply.
- [x] **Step 4: Run the focused flow** and verify the current one-click custom rule application fails every new expectation.
- [x] **Step 5: Render response status and evidence** and phrase unknown as a limit plus the backend-provided next observation.
- [x] **Step 6: Render variable-count contextual options** and an honest empty state that directs the player to rewrite a custom rule.
- [x] **Step 7: Replace direct custom apply with preview** showing original text, execution meaning, limits, conflicts, and selectable alternative text. Enable apply only for executable, unchanged input using the returned `preview_id`.
- [x] **Step 8: Run the focused flow** and verify no rule POST occurs before explicit confirmation, alternatives require another preview, and the exact preview ID/text are submitted.

### Task 5: Participant-Specific Retrospective

**Files:**
- Modify: `frontend/components/Retrospective.tsx`
- Test: `frontend/tests/connected-investigation.cjs`

**Interfaces:**
- Consumes: `HarnessRes.experiments`, `HarnessRes.metrics`, expanded summary call counts.
- Produces: intent → interpretation → opportunity → action → harness/check → outcome timeline and separate story/system statistics.

- [x] **Step 1: Add a failing retrospective fixture** containing obeyed, violated, conflict, and not-evaluable opportunities plus null/zero-denominator metrics.
- [x] **Step 2: Run the test** and verify the current retrospective shows registration counts without the participant's actual experiment chain.
- [x] **Step 3: Render the first real experiment prominently** in the required sequence, including absent actions, failures, conflicts, observation references, and side effects without recasting them as intentional lessons.
- [x] **Step 4: Render remaining experiments compactly** and label story understanding separately from system operation quality.
- [x] **Step 5: Format each metric from stored numerator/denominator/value/reviewed/method**; show `N/A` for null values or zero denominators and distinguish model calls, attempts, interventions, and fallbacks.
- [x] **Step 6: Run the retrospective case** and verify all result states and honest N/A labels, then run the original five-loop browser regression.

### Task 6: Integrated Verification and Evidence

**Files:**
- Modify: `frontend/tests/five-loop-flow.cjs`
- Modify: `frontend/tests/scene-illustrations.cjs`
- Modify: `docs/review-verification/2026-09-09-connected-implementation/frontend-progress.md`
- Create: `/tmp/demo-pigfarm-connected-frontend.diff`

**Interfaces:**
- Consumes: all preceding frontend changes and final image manifest.
- Produces: reproducible type/build/browser evidence and before/after patch.

- [x] **Step 1: Update existing complete API fixtures** with the additive fields they exercise and keep all API requests mocked so no player records are created.
- [x] **Step 2: Run** `npx tsc --noEmit` and `npm run build`; require exit 0.
- [x] **Step 3: Coordinate server ownership with the root agent**, then run the connected flow, five-loop 0/100 flow, and scene-image flow using `/usr/bin/google-chrome` and `/tmp/pigfarm-image-browser/node_modules`.
- [x] **Step 4: Inspect 390px screenshots** for overflow, readable source captions, compact portraits, preserved keyboard focus, and usable gallery/preview dialogs.
- [x] **Step 5: Compare owned files against `/tmp/demo-pigfarm-frontend-before-connected-20260909`** and save `/tmp/demo-pigfarm-connected-frontend.diff`; confirm `frontend/public/assets/**` was not modified by frontend work.
- [x] **Step 6: Record exact commands, results, screenshots, accepted choices, and limits** in the progress ledger.
