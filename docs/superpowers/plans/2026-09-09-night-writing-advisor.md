# Night writing and conversational advisor implementation plan

**Goal:** Restore the player's previous free-text answer exactly and give short, contextual answers without displaying a wall of source records.

**Approved scope:** The user wants each night's own writing restored on the next night, with editing and additions. They selected the recommendation that questions can also use basic surface-world rules, excluding hidden identities and endings. Prefer this original writing flow over adding a new fragment-generation feature.

**Architecture:** Keep stored free text separate from scoring claims and selected evidence. Load optional reference panels on demand. Generate an advisor reply, question kind, and at most two source assessments in one structured call, using a bounded selection of public observations, recent questions/answers, and the scenario's surface summary. Retain source validation and audit records; source-verdict metadata must not replace the conversational answer with a generic refusal.

**Constraints:** Preserve existing attempts/scores, the five-night flow, three-question budget, model/provider selection and pacing. No browser windows, DB reset, new dependencies, hidden-truth context, or changes to NPC dialogue/rule generation. This workspace has no Git metadata; pre-change files are in `/tmp/pigfarm-night-advisor-before-20260909`.

## 1. Restore writing and simplify the night screen

- [x] Regression: store distinct free text, final scoring claims and selected notes. Check exact raw text restoration through nights 2–5 and no cross-attempt leakage. Selected old notes must still contribute to scoring separately from prose.
- [x] Return `night.free_text` as `previous_answer.draft_text`; retain existing response fields for callers. Stop omitting selected notes merely because their IDs were inherited.
- [x] Put the text field and submit action before reference material. Fetch notes only when their panel opens; fetch observations only when the gallery is requested. Keep references optional and preserve retry/accessibility behavior.
- [x] Browser checks: text ready without loading reference APIs, existing/new note toggles do not change prose, gallery remains accessible, exact submitted text survives repeated nights.

## 2. Answer questions conversationally in one call

- [x] Regression: preserve the original question, pass only public observations/basic world rules and recent Q&A, exclude hidden cause chains and future observations, return a concise answer, validate source IDs/quotes, consume one question, and record the call.
- [x] Add a structured reply schema with short answer, question kind and at most two source assessments. Select up to eight distinct public records within a bounded context before calling the model once; failed schema/source checks may use the existing bounded repair attempts.
- [x] Inject only `surface_summary` from the scenario in the composition root. Keep assumptions, reported speech, actual observations and rules distinct in the reply instructions.
- [x] Display the natural answer first. Put source details/cards and legacy metadata inside a collapsed reference section, preserving old response rendering without showing duplicated answer text.
- [x] Adapt old two-stage test fixtures to the new single-call contract while retaining relevant negation, source validity, event-scope and budget regressions. Old recorded model failures remain untouched.

## 3. Verify and activate

- [x] Run focused regressions red then green, full backend suite on `pigfarm_test`, TypeScript and architecture checks, and relevant existing browser scripts with mock APIs.
- [x] Run a small real Gemini question sample with the screenshot's question, follow-up, explicit negation and hidden-identity boundary. Record latency/output without creating a player attempt.
- [x] Review the diff, update the API contract and handoff, and restart only this project's backend after validation. Report remaining semantic/performance limitations, not just fake-model success.

Verification evidence: `docs/review-verification/2026-09-09-night-writing-advisor/README.md`. Review found cross-loop deduplication lost repeated events; reproduced and fixed by preserving loop/beat scope and prioritizing explicitly requested loop numbers.
