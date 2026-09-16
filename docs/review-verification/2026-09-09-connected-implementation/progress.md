# Connected investigation finalization ledger

Approved spec: `docs/superpowers/specs/2026-09-09-connected-investigation-design.md`. Approved visual A is four fixed portraits (E01/E04/E07/E10), six conditional event scenes (clue-07…12), and a seen-only night evidence gallery. BGM and voice remain outside this work.

Git detection: this workspace is not a repository. No git init/commit. Review uses explicit artifacts and file hashes.

| Gate | Current evidence | Final status |
|---|---|---|
| Backend implementation and review | Connected contracts, failure boundaries, grounding repairs, and Gemini/Ollama adapter are implemented. Current full DB suite: 325 passed, 3 existing dependency warnings, exit0. Owner pure118 and independent adapter targeted18 passed. | Adapter code gate passed. Actual Gemini generation and semantic gate remain separate. |
| Frontend | Final TypeScript/build/browser owner checks passed; independent focused review accepted the repaired mobile controls, modal focus, chronological comparison, edited hypothesis use, delayed draft restore, and exact custom input. | Accepted within tested scope. |
| Images | Six 1536×1024 event images and four fixed portraits passed independent technical review with two documented minor limits. | Accepted technically; user comprehension remains unmeasured. |
| Fake live API | Guarded `test_db`, fake providers, five loops, 25 checks, 117 request/response records, 0 failed checks. This run predates the final C3/RM repairs. | Preserved as integration evidence; not final-source smoke. |
| Live browser | Real frontend 3500 + guarded fake API: one mobile390 and one desktop1440 day/night composite, 2 checks, page errors0, failed requests0, screenshots and API raw preserved. | Accepted within first-day/night scope. |
| Mock browser regressions | Five-loop 0/100/retry: 14 checks, errors0. Connected edited-draft/grounded-rule/retrospective: 3 composites, errors0. | Accepted as frontend contract regression evidence. |
| Actual Ollama | Twelve full-corpus raw runs are preserved through 07:35 UTC; eleven contain real provider responses and one records provider access blocking. Final run: 45/45 accepted, errors0, fallback0, kind21/21, valid quotes30, but SPC2 opposite-fact answer was supported and several intermediate semantic errors were only caught by guards. | **OPEN / P1:** choose stronger truth-judgment model evaluation or a source-text-centered product contract. No further code iteration in this delivery. |
| Runtime 8500 | Tester2 preview runs final-prompt source in foreground session32276/PID1478841. Read-only GET verified scenario a, harness on, real Ollama models, Gemini embedding, DB ok, three connected OpenAPI paths, and frontend `/play` HTTP200. | Ready for a new five-loop manual play. RM1 remains disclosed; serving the preview is not semantic approval. |

Producer/consumer agreement: backend owns Observation, previous_answer, grounded question, option, preview/confirmed apply, experiment/metric JSON contracts; frontend owns matching TypeScript/UI. Draft `inherited_note_ids` prevents duplicating prior evidence when restoring final claims. Images are selected by actual public scene conditions, never raw model choice.

Data policy: no production reset, migration, attempt creation or regrading during finalization. Tests use `test_db` under one owner. Existing records keep original scores and empty provenance where unmeasured. Automated executions are not human playtest samples.
