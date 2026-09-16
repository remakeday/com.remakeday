# AGENTS.md

Behavioral guidelines for Codex to reduce common coding mistakes. Apply these alongside the user's request and any more specific instructions in nested directories.

**Priority:** The user's explicit request takes precedence over these guidelines. These guidelines bias toward caution over speed; use judgment for trivial tasks.

## Project-specific instructions

- Before changing files under `backend/`, read and follow `backend/docs/AGENTS.md`.
- Before changing files under `frontend/`, read and follow `frontend/docs/AGENTS.md`.
- When a task spans both areas, apply both instruction files within their respective scopes.

## Browser game tests

- Starting the frontend or demo server must not open a browser. Do not append macOS `open`, `open -a Safari`, AppleScript browser commands, or `xdg-open` to startup/readiness/retry commands. Report the URL for the user to open; server startup alone is not a request for a visible browser.
- Preserve `.vscode/settings.json` port attributes with `onAutoForward: silent`. Do not enable browser-opening port actions or add a browser-opening `serverReadyAction` when preparing a test.
- Automated UI checks use the existing `frontend/tests/*.cjs` Playwright scripts with `headless: true`. Do not open a visible browser just to check server readiness; use an HTTP request.
- For interactive testing, inspect existing tabs without creating one (`createIfEmpty: false` for Claude in Chrome). Reuse the test tab owned by this task. Create at most one test tab if none exists and the browser connection is healthy; retain its tab ID for the whole test.
- If browser connection, navigation, or a UI action fails, inspect the error and the existing tab. Do not retry by opening another window/tab, repeatedly calling `createIfEmpty: true`, relaunching the browser, or switching browser tools to create another instance. A disconnected browser must be reconnected before continuing.
- Keep one browser owner per test. Do not run browser workers or launch commands concurrently. Wait for an existing test process to finish before starting another; a timeout is not permission to launch a replacement while the old process is alive.
- `/play` creates a game session on load and does not restore an in-progress game after reload. Do not reload or navigate back to `/play` to recover from a slow response. Wait for the current action and inspect its result in the same tab.
- Close only the test pages/processes created by the task when finished, including on failure (`try/finally`). Never close the user's browser or unrelated tabs.

## Review Intensity Tiers

Scale the review process to the importance of the work. Write the tier on the first line of the plan ledger and run only that tier's procedure. An explicit user instruction ("do this one lightly/heavily") overrides the default. A Critical finding from a reviewer raises the tier by one automatically; lowering requires a user instruction.

| Tier | Scope | Procedure |
|---|---|---|
| **A Heavy** | Cost, security, auth, payments, data loss (abuse guard, external API adapters, DB migrations, scoring logic, deployment/env config) | Implementer + reviewer per task (sonnet), final whole-branch review (opus), one fix wave + scoped re-review |
| **B Normal** | Game logic and UI behavior changes (god questions, nonsense input, monkey-paw engine) | Per-task review with sonnet/haiku; skip per-task review for pure-function, docs and config tasks; one final whole-branch review (sonnet); one fix wave; re-review replaced by the controller's diff check |
| **C Light** | Scenario text, docs, asset registration, test cleanup, evaluation runner runs | Controller checks the diff and test output after implementation; no whole-branch review (optional single haiku pass) |

Default assignments: dev-account login = A (auth). Monkey-paw engine = B, wish text authoring = C. Anthropic model evaluation (adapter smoke, runners, appendix A.19) = B (user-assigned 2026-09-16).

## 1. Think Before Coding

**Don't assume silently. Surface meaningful uncertainty and tradeoffs.**

Before implementing:
- State assumptions that materially affect the result.
- If multiple interpretations would produce meaningfully different outcomes, present them and ask a focused question.
- For routine implementation details, make a reasonable assumption and continue.
- If a simpler approach exists, say so. Push back when warranted.
- If missing information prevents a safe or correct implementation, name what is missing and ask.

## 2. Simplicity First

**Write the minimum code that solves the requested problem. Nothing speculative.**

- Do not add features beyond what was asked.
- Do not create abstractions for single-use code.
- Do not add flexibility or configurability that was not requested.
- Do not add error handling for impossible scenarios.
- If 200 lines can reasonably become 50 without harming clarity, simplify them.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what the task requires. Clean up only issues introduced by your changes.**

When editing existing code:
- Do not improve adjacent code, comments, or formatting unless the task requires it.
- Do not refactor code that is unrelated to the request.
- Match the existing style, even if you would normally choose another style.
- If you notice unrelated dead code or defects, mention them instead of changing them.

When your changes create unused code:
- Remove imports, variables, and functions made unused by your changes.
- Do not remove pre-existing dead code unless asked.

Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria and continue until the result is verified.**

Turn tasks into verifiable outcomes:
- "Add validation" → verify invalid inputs are rejected as intended.
- "Fix the bug" → reproduce the failure, apply the fix, and verify the original case.
- "Refactor X" → preserve observable behavior and run the relevant checks.

For multi-step tasks, state a brief plan when it helps the user follow the work:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Run checks in proportion to the change. Do not add tests that merely duplicate a trivial implementation, but add or update meaningful tests when they are needed to demonstrate correctness or prevent regression.

These guidelines are working when diffs contain fewer unrelated changes, implementations stay simple, and material ambiguity is resolved before it causes rework.

## 5. GoF Design Patterns

Use Gang of Four patterns when they make real variation easier to extend and understand. Do not introduce a pattern mechanically when a straightforward conditional is clearer and the behavior is unlikely to vary.

General principle:

**A conditional makes the caller own the branching. A suitable polymorphic design lets the relevant object own its behavior and can support the Open/Closed Principle.**

Prefer explicit interfaces or abstract methods when multiple implementations need a stable contract.

### Conditional-to-pattern reference

| Code shape or design pressure | Pattern to consider | Category |
|---|---|---|
| Behavior varies by interchangeable algorithm or type | **Strategy** | Behavioral |
| Behavior varies by lifecycle state | **State** | Behavioral |
| Object families vary by format or platform | **Factory / Abstract Factory** | Creational |
| Multiple handlers may process a request | **Chain of Responsibility** | Behavioral |
| Subscribers react to events | **Observer** | Behavioral |
| An action needs queuing, logging, or undo | **Command** | Behavioral |
| Construction varies by runtime choice | **Factory Method** | Creational |
| Access needs caching, authorization, or lazy loading | **Proxy** | Structural |
| An algorithm has a fixed skeleton with variable steps | **Template Method** | Behavioral |
| Complex business rules need composition | **Specification** | Behavioral |
| Responsibilities need composable wrapping | **Decorator** | Structural |
| An old interface must work with a new one | **Adapter** | Structural |
| A complex subsystem needs a simpler entry point | **Facade** | Structural |
| A tree should expose uniform leaf and container behavior | **Composite** | Structural |
| Abstraction and implementation must vary independently | **Bridge** | Structural |
| Operations vary across a stable object structure | **Visitor** | Behavioral |

### GoF 23-pattern reference

```text
Creational (5)
├── Singleton
├── Factory Method
├── Abstract Factory
├── Builder
└── Prototype

Structural (7)
├── Adapter
├── Bridge
├── Composite
├── Decorator
├── Facade
├── Flyweight
└── Proxy

Behavioral (11)
├── Chain of Responsibility
├── Command
├── Iterator
├── Mediator
├── Memento
├── Observer
├── State
├── Strategy
├── Template Method
├── Visitor
└── Interpreter
```

Rules:
- Consider Strategy or State when branching by type or state is repeated, growing, or owned by the wrong layer.
- Consider Factory Method or Abstract Factory when object construction varies and callers should not know concrete classes.
- Consider Visitor when many operations dispatch across a stable family of object types.
- Avoid `isinstance` checks in business logic when polymorphism can express the contract more clearly.
- Choose a pattern only when it reduces coupling or makes expected change easier; keep simple branching when it communicates the design better.
