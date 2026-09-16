# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## Browser game tests

- Starting the frontend or demo server must not open a browser. Do not append macOS `open`, `open -a Safari`, AppleScript browser commands, or `xdg-open` to startup/readiness/retry commands. Report the URL for the user to open; server startup alone is not a request for a visible browser.
- Preserve `.vscode/settings.json` port attributes with `onAutoForward: silent`. Do not enable browser-opening port actions or add a browser-opening `serverReadyAction` when preparing a test.
- Automated UI checks use the existing `frontend/tests/*.cjs` Playwright scripts with `headless: true`. Do not open a visible browser just to check server readiness; use an HTTP request.
- For interactive testing, inspect existing tabs without creating one (`createIfEmpty: false` for Claude in Chrome). Reuse the test tab owned by this task. Create at most one test tab if none exists and the browser connection is healthy; retain its tab ID for the whole test.
- If browser connection, navigation, or a UI action fails, inspect the error and the existing tab. Do not retry by opening another window/tab, repeatedly calling `createIfEmpty: true`, relaunching the browser, or switching browser tools to create another instance. A disconnected browser must be reconnected before continuing.
- Keep one browser owner per test. Do not run browser workers or launch commands concurrently. Wait for an existing test process to finish before starting another; a timeout is not permission to launch a replacement while the old process is alive.
- `/play` creates a game session on load and does not restore an in-progress game after reload. Do not reload or navigate back to `/play` to recover from a slow response. Wait for the current action and inspect its result in the same tab.
- Close only the test pages/processes created by the task when finished, including on failure (`try/finally`). Never close the user's browser or unrelated tabs.

## 검토 강도 등급 (Review Intensity Tiers)

작업의 중요도에 따라 검토 절차를 세 등급으로 나눈다. 계획을 실행할 때 장부(ledger) 첫 줄에 등급을 적고 그 등급의 절차만 돈다. 사용자가 "이 기능은 가볍게/무겁게"라고 지정하면 그 지정이 우선한다. 리뷰어가 Critical을 내면 자동으로 한 등급 올린다. 하향은 사용자 지시로만.

| 등급 | 대상 | 절차 |
|---|---|---|
| **A 무거움** | 비용·보안·인증·결제·데이터 손실 가능(과잉 사용 허들, 외부 API 어댑터, DB 마이그레이션, 채점 로직, 배포·환경 설정) | task마다 구현+검토(sonnet), 최종 전체 리뷰(opus), 수정 1회 + 범위 재검토 |
| **B 보통** | 게임 로직·UI 동작 변경(신의 질문, 무의미 입력, 원숭이손 엔진 등) | task 검토는 sonnet/haiku, 순수 함수·문서·설정 task는 개별 검토 생략, 최종 전체 리뷰 sonnet 1회, 수정 1회, 재검토는 컨트롤러의 diff 확인으로 대체 |
| **C 가벼움** | 시나리오 문장·문서·자산 등록·테스트 정리·평가 러너 실행 | 구현 후 컨트롤러가 diff와 테스트 결과만 확인, 전체 리뷰 생략(원하면 haiku 1회) |

기본 배정 예: 개발 계정 로그인 = A(인증). 원숭이손 엔진 = B, 소원 문장 작성 = C. Anthropic 평가 러너 실행 = C.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## [Shared] Part II — GoF Design Patterns

### 5. GoF Patterns (Gang of Four)

**`if/else` = the caller knows the branching → caller must change when behavior changes.**
**GoF pattern = the object knows its own branching → OCP achieved naturally.**

Telling AI "use Strategy here" compresses 10 lines of `if/elif/else` intent into one word.
Prefer `@abstractmethod` and polymorphism over any conditional that dispatches on type or state.

### Conditional → Pattern Mapping

| Bad code (conditional) | GoF Pattern | Category |
|---|---|---|
| `if type == "A": ... elif type == "B":` | **Strategy** | Behavioral |
| `if state == "PENDING": ... elif state == "PAID":` | **State** | Behavioral |
| `if format == "JSON": ... elif format == "XML":` | **Factory / Abstract Factory** | Creational |
| `if a: do_a(); if b: do_b();` | **Chain of Responsibility** | Behavioral |
| `if event == "click": ... elif event == "hover":` | **Observer / Command** | Behavioral |
| `for item in list: item.do()` | **Iterator + Visitor** | Behavioral |
| `obj = ClassA() if x else ClassB()` | **Factory Method** | Creational |
| `if cache: return cache; else: fetch()` | **Proxy** | Structural |
| `obj.a(); obj.b(); obj.c();` fixed order | **Template Method** | Behavioral |
| `if A and B and C: do()` complex condition | **Specification** | Behavioral |
| `result = step1(step2(step3(x)))` nested calls | **Decorator** | Structural |
| `global_var = None; if not global_var: init()` | **Singleton** | Creational |
| `try: ... except TypeA: ... except TypeB:` | **Command + Handler** | Behavioral |
| `if legacy_api: adapt(); else: use_new()` | **Adapter** | Structural |
| `obj1.notify(obj2); obj1.notify(obj3);` manual propagation | **Observer** | Behavioral |
| `if flag: do_extra()` feature toggle | **Decorator** | Structural |
| `if subsystem_a: ...; if subsystem_b: ...` | **Facade** | Structural |
| `copy = deepcopy(obj)` manual copy | **Prototype** | Creational |
| `for`-loop directly traversing a tree | **Composite + Iterator** | Structural + Behavioral |
| `if obj_type == "remote": ... elif "local":` | **Bridge** | Structural |

### GoF 23 Pattern Reference

```
Creational (5)
├── Singleton       ← global variable + if None check
├── Factory Method  ← if/else object creation
├── Abstract Factory← platform-specific if/else
├── Builder         ← telescoping constructor (too many __init__ args)
└── Prototype       ← manual deepcopy

Structural (7)
├── Adapter         ← if legacy / new API
├── Bridge          ← if remote / local
├── Composite       ← tree traversed directly with for
├── Decorator       ← nested function calls, flag-toggled features
├── Facade          ← complex subsystem if-chain
├── Flyweight       ← repeated object creation for identical data
└── Proxy           ← if cache / if auth / if lazy-load

Behavioral (11)
├── Chain of Responsibility ← if a: do_a; if b: do_b
├── Command         ← direct method call with no undo/queue
├── Iterator        ← direct for-loop over internals
├── Mediator        ← objects holding direct references to each other
├── Memento         ← state saved manually in dict/list
├── Observer        ← manual notify calls listed in sequence
├── State           ← if state == "X": elif state == "Y":
├── Strategy        ← if type == "A": elif type == "B":
├── Template Method ← fixed-order procedural calls
├── Visitor         ← for + if isinstance() dispatch
└── Interpreter     ← string parsing with if/elif chains
```

**Rules:**
- Replace any `if/elif` that dispatches on **type or state** with Strategy or State.
- Replace any object creation `if/else` with Factory Method or Abstract Factory.
- Replace any `for + if isinstance()` with Visitor.
- Use `@abstractmethod` to enforce contracts. Never check `isinstance` in business logic.
- When AI is asked to implement branching logic, default to the pattern — not the conditional.
