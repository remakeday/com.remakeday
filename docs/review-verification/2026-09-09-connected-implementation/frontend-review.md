# Connected Investigation — Independent Frontend Review

Date: 2026-09-09
Reviewer: `/root/frontend_review`
Assessment: **Frontend review accepted after focused independent recheck.** All five P2 findings and the exact-original contract correction are closed. No remaining P1/P2 finding in the reviewed frontend change; live backend integration remains separate.

## Scope and evidence

Reviewed root/frontend instructions, approved connected-investigation spec (visual A overrides the old E03 scope), frontend implementation plan, additive API contract, implementation files, and browser test sources. Initial stable artifact was `/tmp/demo-pigfarm-connected-frontend.diff`, 1,430 lines, SHA256 `1a33c86425d28590dab806bc51da1d9b7ac73670875d2f538729ad0866e55bd9`. The owner applied review fixes. Final independently rechecked artifact: 1,665 lines, SHA256 `210cb43e8a7cb5271aebbdad499169786435bee37f2aeef0a7181bfa63245f6e`. The hash was confirmed before and after the recheck.

Independent browser probe used the existing localhost:3500 frontend and intercepted every localhost:8500 request. No game records, DB, servers, build outputs, or Git metadata were changed by this review. Chrome failed under the sandbox with `setsockopt: Operation not permitted`; the same bounded probe ran successfully after escalation. Probe code was evaluated from the existing mock fixture in memory, with additional delayed-response, focus, comparison, and geometry checks. Screenshot: `/tmp/connected-review-day390.png`.

## Final independent recheck

The reviewer independently ran the final expanded connected browser fixture against the existing localhost:3500 server, with every backend request intercepted and `TEST_ARTIFACT_DIR=/tmp/pigfarm-connected-review-final`. Additional in-memory assertions checked initial control geometry, twelve Shift+Tab steps in each main modal, inert day/night background controls, zero next-beat calls during notebook browsing, and unchanged raw input. Exit 0; no page errors. No rebuild, server lifecycle operation, or DB access occurred.

A second bounded probe waited until all four fixed portraits had decoded, then checked and captured both 390×844 and 1440×844 layouts. Exit 0. At 390px the input now starts at x=53.609375, width=143.84375, y=798, height=38; all four portraits and both action buttons fit. At 1440px the input starts at x=498.609375, width=748.84375. The loaded 390px screenshot was visually inspected and shows portraits above readable narration and the full input/action row.

| Original issue | Independent final result |
|---|---|
| Mobile day controls outside viewport | Closed: full control bounds and loaded 390/1440 screenshots pass. |
| Modal focus escapes to game | Closed: Tab and Shift+Tab remain in notebook/gallery; nested source focus, topmost Escape and opener restoration pass; background is inert and notebook browsing issues no advance request. |
| Comparison follows click order | Closed: select loop 3 then loop 1; displayed order is loop 1 then loop 3. |
| Question example uses discarded claim | Closed: replace the first claim in confirmation; the intervention placeholder contains the final edited claim. |
| Delayed previous answer overwrites editing | Closed: initial delayed 503 and delayed successful retry keep draft controls disabled; final edited answer and inherited/current IDs restore correctly. |
| Exact original custom input lost | Closed: surrounding spaces remain in input and the exact preview/apply payload; preview issues no apply request until the explicit click. |

Artifacts: `/tmp/pigfarm-connected-review-final/results.json`, `day-loaded-390.png`, `day-loaded-1440.png`, `connected-mobile.png`, and `retrospective-mobile.png`. The original failure screenshot remains `/tmp/connected-review-day390.png` for before/after comparison.

## Initial findings and resolution history

### P2 — Day conversation controls are outside the mobile viewport

`frontend/components/screens/DayScreen.tsx:335`–375 places the four-portrait strip and the entire chat panel in one horizontal flex row. At 390px, the portrait strip consumes about 360px; the input starts at x=414.609375 with width=74.5. The screenshot shows only a sliver of narration/chat while conversation input and actions are offscreen. Document-level `scrollWidth <= innerWidth` passes because overflow is inside a horizontal container, so the existing test misses this usability failure.

Reproduction: start mocked play with four NPCs at 390×844; continue to day, inspect the input and actual initial viewport before clicking any control that auto-scrolls it into view. Fix mobile layout so portraits and conversation both fit; verify the input and beat controls' own bounding boxes, not only root overflow. Closed by the final independent recheck above.

### P2 — Notebook/gallery dialogs do not contain keyboard focus

`frontend/components/screens/DayScreen.tsx:613`, `frontend/components/EvidenceGallery.tsx:34`, and the source detail overlays render modal roles without moving/trapping focus or making the background inert. The browser probe opened the notebook: `activeElement` stayed on the underlying notebook opener; the next Tab moved to the underlying Chaeyeon portrait, outside the dialog. Keyboard users can reach and activate day controls beneath a screen that says time does not decrease while browsing notes. Gallery and nested source overlays use the same incomplete pattern.

Fix focus entry, containment, background inaccessibility, Escape handling for the topmost dialog, and restoration to the opener. Test Tab/Shift+Tab and underlying beat/request counts while dialogs are open. Closed by the final independent recheck above.

### P2 — Comparison claims chronological order but uses checkbox click order

`frontend/components/EvidenceGallery.tsx:26`–31 and 58–66 retain selection order and label the result “내가 본 순서.” Selecting the loop-3 image and then the loop-1 image reproduced `1. 3회차 … / 2. 1회차 …`. This reverses evidence chronology in the central investigation comparison.

Sort the two selected records by disclosed observation order (or explicit loop/beat chronology with stable ties). Closed by the final independent recheck above.

### P2 — Intervention example uses a discarded pre-confirmation hypothesis

`frontend/app/play/page.tsx:183` passes `night.claims[0]` to GodScreen. That parent value comes from the draft response. `frontend/components/screens/ConfirmScreen.tsx:89` stores the final PATCHed claims only in local state, and `onSubmitted` returns only the score result. Replacing the first claim in confirmation therefore leaves the intervention question example tied to the earlier, discarded claim.

Propagate the actual final claims back to the parent or return them with submission success, then derive the example from those claims. This concerns the newly added hypothesis wiring. Closed by the final independent recheck above.

### P2 — Delayed previous-answer restore can overwrite new writing (owner fixed)

Initial `frontend/components/screens/NightScreen.tsx:52`–60 unconditionally restored the asynchronous previous response while textarea, note toggles, and submit were enabled. A slow/retried response could overwrite current edits or allow submission without inherited IDs.

Owner added `previousReady`, keeps editing/selection/submission disabled until a successful previous-answer response (including null), and added a delayed-response regression. Static review confirms the guard; the independent browser probe ran after hot reload and observed new text retained after waiting for restoration. Final stable artifact and delayed failure/retry case independently verified; closed.

### Contract fidelity correction — Raw custom input was trimmed (owner fixed)

Initial GodScreen preview/apply sent `customText.trim()` and compared the preview against the trimmed input. This did not change the executable words, but it prevented exact preservation of the user-original field required by the agreed contract. Owner now uses trim only for blank validation, sends/compares the raw string, and tests surrounding spaces. Static and independent browser review confirm the change; closed. No semantic corruption is claimed from whitespace normalization alone.

## Strengths and spec assessment

- Public observation DTOs are explicit; shared cards distinguish hearing a statement from confirming its content. Notebook reads do not issue utterance or next-beat requests.
- Portrait selection is stable at E01/E04/E07/E10; event images come through the allowlisted clue mapping. Gallery items derive from returned public observations, with no invented hidden images or causal arrows.
- Restored evidence attachment IDs and immutable inherited IDs are separate. Toggling attachments does not rewrite player prose, and the UI explains that distinction. Screen unmounting between phases prevents cross-loop component state reuse in the current play flow.
- Questions show backend status, evidence and next-observation guidance. Variable-length options render without filling to three. Custom rules have explicit preview and apply steps; alternatives require another preview and failed applications show conflict/reason feedback.
- DayScreen consumes the post-scene `budget_left` when present, including day completion, while keeping legacy compatibility.
- Retrospective uses recorded opportunities/actual actions/results instead of registration as success. Null values and zero denominators display N/A; legacy call coverage is distinguished. Story understanding and system quality remain separate.
- Existing play transitions keep final story before retrospective and start a new attempt with new mounted state. No score threshold was introduced into five-loop progression.

## Verification limits and targeted follow-up

Owner reports final typecheck, webpack build, five-loop 0/100, and scene browser suites green. This review independently reran the expanded connected browser flow with added focused assertions, but did not rebuild or rerun the full five-loop/scene suites. Remaining validation limits:

- The five-loop fixture returns `previous_answer: null` each night, so it does not test two consecutive final-edited restores or third-night inherited IDs end to end. The connected fixture supplies one preconstructed loop-2 answer at loop 3.
- Expanded connected fixture now independently covers supported/unknown/contradicted, zero options followed by refresh, displayed preview conflict, and failed previous-answer load/retry. It still does not prove unsupported-preview or failed-application/retry races. A displayed conflict followed by mocked success proves feedback rendering, not the backend conflict policy.
- Retrospective fixture covers obeyed/not-evaluable and null metrics, not violated/conflict, a zero-opportunity experiment, or nullable legacy model-call counters in the browser.
- Root document overflow alone remains insufficient for nested scrolling; the corrected test and independent final probe now check individual control bounds and loaded portrait screenshots.
- Backend source truth, question relevance, rule execution, unobserved branch suppression, live CORS/runtime behavior, and independent human metric judgments remain the backend/integration review responsibility. Mocked next-observation text cannot prove the suggested action exists in the live game.
- Pre-existing ConfirmScreen truncation of edited claims to eight lines was observed outside the reviewed diff; it was not changed or promoted into this change's findings.

Frontend acceptance recommendation: proceed with the reviewed final artifact; all reported frontend defects are closed. Keep the remaining end-to-end/backend and human-validation limits explicit. Broad unrelated refactoring is unnecessary.
