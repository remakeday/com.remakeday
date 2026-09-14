# Connected Investigation — Frontend Progress

Date: 2026-09-09
Owner: `/root/frontend`
Status: frontend implementation and mocked-browser verification complete; independent review and root-owned live API integration pending

## Accepted Choices

- Visual direction A is final: four compact stable portraits plus event images and a daytime notebook/night evidence gallery.
- Stable portrait assets are E01 (Chaeyeon), E04 (Minseok), E07 (Eunsang), and E10 (Jun). Mood remains engine state and may be expressed in text; it does not choose a portrait variant.
- Event assets use `clue-07` through `clue-12` from the image workstream's final manifest. No E03 remake and no emotion variants.
- Previously seen original images are reused at night. The UI exposes source scene and earlier/current comparison only for returned public observations, with no causal arrows.
- The backend additive contract published in `docs/spec/api_contract.md` is authoritative. Empty/null values remain empty/null; the frontend does not infer evidence, rule success, or unobserved branches.
- Previous-night request semantics are agreed: `tapped_note_ids` is the full current selection; `inherited_note_ids` is the complete ID set restored with the previous draft even after toggles. Deselecting evidence changes attachment only and never deletes or rewrites player-authored prose.
- Existing `/play` phases, five-loop progression at any score, final narrative before retrospective, retries, keyboard controls, and mobile support remain.
- Next-beat `budget_left` is consumed when present so a scene/paw consequence updates the visible counter immediately; legacy responses without it keep the last known value.
- Confirmation returns the final PATCHed claims to the play state, so the next intervention's question example uses the accepted final hypothesis rather than the discarded draft.
- No audio, new dependencies, backend-owned file edits, public asset edits, arbitrary spoiler art, or broad refactor.
- Browser tests mock the API and therefore do not create player records. Live backend/DB verification is coordinated by the root agent.

## Preservation

- `git status` fails because `.git` is an empty read-only directory. No repository was initialized or repaired.
- Pre-change frontend snapshot: `/tmp/demo-pigfarm-frontend-before-connected-20260909`
- Planned final diff: `/tmp/demo-pigfarm-connected-frontend.diff`

## Milestones

- [x] Read root and frontend `AGENTS.md` files.
- [x] Read the accepted connected-investigation spec, tester evidence, visual direction, and relevant installed Next.js client-component/image/accessibility docs.
- [x] Read the published additive API contract and coordinated stable portrait/event IDs with the image owner.
- [x] Wrote concrete frontend implementation plan.
- [x] Captured a red browser test: it timed out on the missing `낮의 노트 열기` control before any implementation.
- [x] API types and client methods.
- [x] Day notebook, traceable observations, stable compact portraits.
- [x] Previous draft, selected evidence preservation, seen-only gallery/comparison.
- [x] Grounded questions, contextual options, custom preview/confirm.
- [x] Participant-specific retrospective and honest metrics.
- [x] Type/build/browser verification and artifact review.

## Verification Ledger

All browser runs use a real Next.js frontend with the API intercepted in Playwright. They create no player records.

- RED: `NODE_PATH=/tmp/pigfarm-image-browser/node_modules node tests/connected-investigation.cjs` failed by timing out on the absent `낮의 노트 열기` control before implementation.
- `npx tsc --noEmit` — exit 0 on the final source.
- `npm run build` — blocked first by the sandbox's Google-font network restriction, then Turbopack's internal port bind (`EPERM`). This is an execution-environment limitation rather than a source failure.
- `npx next build --webpack` — exit 0; compiled, typechecked, generated 4/4 pages, and emitted `/`, `/play`, `/harness/[attemptId]`, and `/inspector/[attemptId]`.
- `NODE_PATH=/tmp/pigfarm-image-browser/node_modules node tests/connected-investigation.cjs` — exit 0. Verified free source-linked daytime notebook; four fixed portraits; all chat/action controls inside the 390px viewport; notebook/gallery/detail focus containment, Escape, and opener restoration; chronological comparison even when selected in reverse; no unseen clue-12; 1536×1024 clue-08/clue-11 loading and 390px fit; delayed previous-answer failure/retry keeps draft locked; previous loop-2 edited draft restored in loop 3; inherited evidence toggled off/on; new evidence added; full current `[1,2,3]` and inherited `[1,2]` request sets; no prose rewrite; final confirmation edit supplies the intervention hypothesis; grounded supported/unknown/contradicted results and next observation; zero-option state then contextual refresh; preview conflict; no custom apply before preview; exact raw preview ID/text including surrounding whitespace; next-beat 5→4 budget refresh; experiment chain; honest `N/A`; no page errors or horizontal overflow.
- `NODE_PATH=/tmp/pigfarm-image-browser/node_modules node tests/five-loop-flow.cjs` — exit 0. Verified five loops at both final 0% and 100%, retrospective gating/retry, ending-before-retrospective, new-attempt retry, and 390px fit.
- `NODE_PATH=/tmp/pigfarm-image-browser/node_modules node tests/scene-illustrations.cjs` — exit 0. Verified new/legacy/unknown image sequences, 390px and 1440px containment, illustration navigation without beat advancement, and outcome-specific hidden-image behavior.

## Artifacts

- Before snapshot: `/tmp/demo-pigfarm-frontend-before-connected-20260909`
- After snapshot: `/tmp/demo-pigfarm-frontend-after-connected-20260909`
- Reviewer diff: `/tmp/demo-pigfarm-connected-frontend.diff`
- Connected screenshots/report: `/tmp/pigfarm-connected-frontend/`
- Five-loop screenshots/report: `/tmp/pigfarm-five-loop-browser/`
- Scene screenshots/report: `/tmp/pigfarm-scene-illustrations/`

## Limits and Integration Follow-up

- Live backend/DB play is root-owned and waits for the backend's final suppressed-action evidence fix. The mocked tests cover the exact published consumer contract but do not prove deployed CORS/process configuration.
- Image usefulness is not claimed from technical loading/click checks. The generated-image workstream separately reviewed art continuity; user comprehension still requires participant evaluation.
- The 390px gallery check proves both small-detail images can be opened at valid source dimensions and stay in the viewport. It does not measure whether a player correctly interprets the notebook marks or wristband.

## Independent Review Corrections

- Fixed asynchronous previous-answer overwrite/early-submit risk by keeping note, prose, and submission controls disabled until the previous response settles successfully; retry remains locked.
- Preserved the exact custom-rule original through preview/apply and use trimming only to reject blank input.
- Replaced the clipped horizontal mobile day layout with a compact portrait row above the full-width chat controls.
- Added modal background inertness, focus containment, Escape handling, nested-detail focus, and opener restoration.
- Sorted comparisons by actual loop/beat order instead of checkbox click order.
- Propagated confirmation-edited claims into the intervention's contextual question prompt.
