# Gemini adapter phase — 2026-09-09

This is a new user-requested adapter workstream, separate from the earlier connected-investigation pytest invocation counts and unresolved Ollama RM1 semantic review.

Implemented the approved `docs/superpowers/plans/2026-09-09-swappable-llm-adapters.md` using existing LLMPort/settings/factory. Added only GeminiLLM as an outbound adapter; the Gemini factory branch now uses the existing configured key/model. No new dependency, Port, HTTP schema, use case, harness policy, automatic provider fallback or model downloader was added. The installed and pinned google-genai version is1.29.0. Runtime provider/model selection remains independent for NPC and core.

The adapter translates system instructions and user/model messages, supports system-only requests, passes JSON schema and temperature (including0), and returns JSON objects only. SDK errors propagate unchanged; blocked/abnormally terminated generation includes termination reasons; empty/invalid/nonobject JSON raises LLMParseError. SDK requests remain single-attempt; the existing harness owns retries and records model/error outcomes. A120-second timeout is passed to the SDK as120000ms.

## Owner verification

Three pytest invocations in this phase, all DB-free:

1. New focused suite: **18 failed**, adapter module absent,0.27s (tool6e48fc). This is the intentional red checkpoint.
2. Focused green: **18 passed**,0.23s (71d679), one installed SDK Python3.14 deprecation warning.
3. Whole pure: **118 passed**,0.31s (fb1961), the same warning.

Architecture: **4 kept/0 broken**,120 files/234 dependencies (e7252d). Forbidden-word scan: **0/84** (881dc8). Existing DB factory test was updated from Gemini NotImplementedError to mocked construction while preserving fake/Ollama/unknown-provider assertions; root owns its full-suite execution. The prior307 full-suite checkpoint predates this adapter.

SDK local preflight also verified that response_json_schema including existing nested definitions reaches the installed SDK request converter unchanged. This made no client/network call. Existing key presence was checked as a boolean only and returned true; no key value was printed or written.

## Artifacts and ownership

- Focused diff `/tmp/connected-gemini-review.diff`
- Before/after snapshots `/tmp/connected-gemini-before`, `/tmp/connected-gemini-after`
- Exact hashes `/tmp/connected-gemini-sha256.json`
- Exact five-file list `/tmp/connected-gemini-changed-files.txt`
- Configuration guide `backend/docs/llm-providers.md`

Gemini adapter hash: `7a1b5e84a707bcfb3b9f299f5659ae00856c87d5b5f76ff2c8a5a6dc464e2ab8`; factory hash: `17c724caf3a6c73ae0c3c7bdd12491b85c2fc5beb0d307c23533de9a77cd7fed`. Root received code/test freeze before its full DB relay. Backend did not run DB tests or make live API/server/play requests. The actual .env and running providers have not been modified by this owner.

The user subsequently authorized actual Gemini2.5Pro core activation for Tester2 while retaining Exaone NPC and Gemini embedding. Root coordinates the separately logged connectivity test, final config instruction and server restart. Adapter green is not a Gemini quality result or RM1 closure. Those live steps remain pending their own evidence.


## User quota follow-up: shared completion pacing

Added a process-wide lock/monotonic gate to GeminiLLM, shared across newly constructed adapters and parallel calls. Settings adds positive `GEMINI_REQUESTS_PER_MINUTE` (default10); factory supplies it. Each SDK attempt waits inside complete(), so audit elapsed includes waiting; provider failures consume admission slots. SDK retry policy remains unchanged. Current single-worker scope and provider-enforced daily1500 limit are documented; no DB quota counter or runtime .env edit was made by backend.

Owner pytest count in this adapter phase is now **5**, adding:

4. Pacing red: **2 failed**,0.23s, missing monotonic/pacer (3b9383).
5. Full pure green: **120 passed**,0.32s, one installed SDK deprecation warning (d2d68a). Mock clock/sleep tests cover concurrent adapters, default6-second spacing, custom rate, and failed provider attempts consuming slots. Existing SDK mock tests bypass the real wait.

Latest architecture **4 kept/0 broken**,121 files/237 dependencies (7af236); forbidden scan **0/84** (799004). These commands are not pytest invocations. Root owns the separate full-suite relay. Artifacts listed above have been regenerated for the current **seven files**; current hashes supersede the initial five-file values above.
