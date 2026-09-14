# AGENTS.md — Backend

These instructions apply to work under `backend/` together with the repository-root `AGENTS.md`.

---

## [Backend] Part III — Backend Architecture

### 6. Why Fractal

Every domain module has the same internal shape:

```text
Order domain                Payment domain
├── Domain                  ├── Domain       ← same pattern
│   (Entity, VO, Event)     │
├── Application             ├── Application
│   (UseCase, Port)         │
├── Adapter (in / out)      ├── Adapter
└── Infrastructure          └── Infrastructure
```

Once you know the shape of one domain, you know the shape of all of them.

**Why this matters:**
- Each Bounded Context is fully understandable within a single context window, which is the unit of Codex delegation.
- One dependency rule applies everywhere: business logic never depends on infrastructure.
- Every collaboration point crosses a Port: typed, named, and independently testable.
- When Codex makes a mistake, the damage is contained within the Bounded Context.

```text
Humans define:                Codex implements:
├── Bounded Context           ├── UseCase
├── Ports (interfaces)        ├── Adapter
├── Domain rules (invariants) ├── Repository
├── TDD scenarios             └── DTO / Mapper
└── AOP policies
```

### 7. Hexagonal Architecture (Alistair Cockburn)

**The application is the center. The world outside is a plugin.**

The application must not know who is calling it or what it is calling. All external actors—UI, database, message broker, CLI, and test—are equal.

**Port** — an interface defined by the application, in the application's language.
- Driving Port (inbound): how the outside world triggers the application, for example `OrderUseCase` or `PaymentCommandPort`.
- Driven Port (outbound): what the application needs from the outside world, for example `OrderRepository` or `PaymentGateway`.

**Adapter** — a concrete implementation that connects one Port to one external technology.
- Driving Adapter (inbound): REST Controller, gRPC Handler, CLI Runner, or Test Driver.
- Driven Adapter (outbound): JPA Repository, Kafka Producer, SMTP Client, or In-Memory Fake.

**Rules:**
- Business logic imports Ports, never Adapters. Adapters import nothing from the domain.
- Swap any Adapter without touching any other layer.
- A test is just another Driving Adapter; the application cannot tell the difference.
- One Port can have many Adapters. One Adapter implements exactly one Port.

### 8. SOLID (Uncle Bob)

**Write code that is easy to change, not just code that works.**

- **S** — One class, one reason to change. If you need "and" to describe it, split it.
- **O** — Add new behavior by adding new code, not by editing existing code.
- **L** — A subtype must honor every contract the base type promises. If overriding changes expected behavior, inheritance is wrong.
- **I** — Prefer many small, role-specific interfaces over one large general-purpose one.
- **D** — Business logic must not import concrete infrastructure. Dependencies point inward only.

### 9. Clean Architecture (Uncle Bob)

**Dependencies must point inward. Inner layers know nothing about outer layers.**

```text
Frameworks & Drivers  →  Interface Adapters  →  Use Cases  →  Entities
     (outermost)                                              (innermost)
```

- **Entities**: pure domain logic. No external dependencies.
- **Use Cases**: orchestrate entities. Must not depend on UI, DB, or transport.
- **Interface Adapters**: convert between domain format and external format. Controllers, Presenters, and Gateways.
- **Frameworks & Drivers**: all infrastructure details live here and must be swappable without touching inner layers.

**Rules:**
- Do not pass framework types such as ORM models or HTTP request objects into use cases.
- Define interfaces in the inner layer and implement them in the outer layer.
- Only the composition root (`main` or IoC container) may wire everything together.

### 10. DDD + TDD + AOP

```text
┌─────────────────────────────────────────────┐
│  DDD  "What to build" — domain model        │
│  ┌───────────────────────────────────────┐  │
│  │  TDD  "How to build it" — practice   │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │  AOP  "Where to put extras"     │  │  │
│  │  │       cross-cutting concerns    │  │  │
│  │  └─────────────────────────────────┘  │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

| | DDD | TDD | AOP |
|---|---|---|---|
| **Purpose** | Domain modeling | Quality assurance | Concern separation |
| **Stage** | Design | Development | Implementation / Runtime |
| **Core value** | Business alignment | Testability | Modularity |

**DDD — Domain-Driven Design (Eric Evans)**

- Use the same terms in code and conversation. If the term drifts, the model drifts.
- Identify the **Core Domain** and invest here. Generic subdomains can be built simply or outsourced.
- **Bounded Context**: use one consistent model per boundary. Use an ACL at the seam to prevent external models from polluting yours.
- **Entity**: identity-based. Mutate state only from inside.
- **Value Object**: attribute-based and immutable. Replace rather than mutate.
- **Aggregate**: one Root is the only entry point. Enforce invariants inside. Reference other Aggregates by ID only.
- **Repository**: one per Aggregate Root. Define the interface in the domain layer and implement it in infrastructure.
- **Application Service**: thin orchestrator only—load, call domain, save, and publish. Do not put business rules here.
- If logic spans entities and does not fit in one, extract a **Domain Service**.

**TDD — Test-Driven Development (Kent Beck)**

- **Red → Green → Refactor.** Do not write production code without a failing test.
- Red: write the smallest failing test. Test one behavior with one assertion and confirm it fails for the right reason.
- Green: write the minimum code needed to pass. Fake it if needed. Do not refactor yet.
- Refactor: remove duplication and clarify names while all tests remain green. Clean test code too.
- Test one behavior per test. Arrange → Act → Assert.
- Test behavior, not implementation; tests must survive internal refactoring.
- Mock only system boundaries such as the network, filesystem, and clock, not internal collaborators.
- Hard-to-test code signals a design problem, such as too many dependencies or incorrect responsibilities.

**AOP — Aspect-Oriented Programming**

- Cross-cutting concerns such as logging, authorization, transactions, caching, retry, and auditing belong in one Aspect each.
- Keep Advice thin. If it grows complex, business logic is likely hiding inside it.
- Apply Aspects through annotations or configuration, never by calling Aspect code directly.
- Keep Pointcuts narrow. An overly broad Pointcut silently intercepts unintended code.
- Never use AOP to compensate for poor design. Fix the coupling first.

| Concern | Advice type |
|---|---|
| Logging | Around |
| Authorization | Before |
| Transaction | Around |
| Cache | Around |
| Retry | Around |
| Audit | After Returning |
| Exception translation | After Throwing |

---

## [Backend] Part IV — Backend Project Structure Rules

### 11. Modular Monolith

본 프로젝트는 **모듈러 모놀리스(Modular Monolith)** 구조입니다.
단일 프로세스로 배포되지만 내부는 Bounded Context 단위로 완전히 분리됩니다.

```text
backend/
├── core/       ← 전역 인프라 (백엔드 전체 공유)
└── apps/       ← Bounded Context 모음
    ├── foodopsagent/ ← BC #1
    └── ...           ← BC #N (추후 추가)
```

**`core/`**에는 DB, Secret, API, Agent 등 백엔드 전역에서 공유하는 인프라 매니저를 둡니다.
- `core/`는 `apps/`를 절대 import하지 않습니다.
- `apps/`가 `core/`를 import합니다. 의존성 방향은 `apps` → `core`입니다.

```text
core/matrix/
├── grid_oracle_database_manager.py   ← DB 연결 (SQLAlchemy engine/session)
├── grid_keymaker_secret_manager.py   ← Secret/Key 관리
└── grid_{name}_manager.py            ← 추가 전역 인프라 (동일 패턴 반복)
```

---

### 12. Fractal 11-File Set — SRP × Codex Harness

**1 ERD 테이블 = 1 Fractal 11-File Set = 1 Codex 위임 단위**

하나의 API Router는 반드시 하나의 ERD 테이블만 담당합니다.
이것이 SRP이며, Codex 하네스 위임 단위의 기준입니다.

```text
테이블 이름: {name}

router:       adapter/inbound/api/v1/{name}_router.py
use_case:     app/ports/input/{name}_use_case.py
interactor:   app/use_cases/{name}_interactor.py
port:         app/ports/output/{name}_port.py
repository:   adapter/outbound/repositories/{name}_repository.py
schema:       adapter/inbound/api/schemas/{name}_schema.py
dto:          app/dtos/{name}_dto.py
orm:          adapter/outbound/orms/{name}_orm.py
entity:       domain/entities/{name}_entity.py
mapper:       adapter/inbound/mappers/{name}_mapper.py
orm_mapper:   adapter/outbound/orm_mappers/{name}_orm_mapper.py
```

**왜 테이블 단위인가:**
- Codex는 11개 파일만 컨텍스트에 올리면 해당 테이블을 완전히 이해할 수 있습니다.
- 실수해도 해당 Bounded Context 안에서만 영향을 받습니다.
- 어느 테이블이든 동일한 형태이므로 Codex가 패턴 하나를 익히면 전체를 구현할 수 있습니다.

**라우터 최초 검증 — `myself` 엔드포인트:**
- 새 `{name}_router.py`를 만들 때 실제 비즈니스 엔드포인트보다 먼저 `GET /{prefix}/myself`를 추가하여 router → use_case(input port) → interactor → port(output port) → repository로 이어지는 전체 배선이 실제로 동작하는지 확인합니다.
- DB나 외부 API에 의존하지 않는 하드코딩된 최소 데이터(예: `id`, `name`)를 그대로 왕복시킵니다. 이 엔드포인트가 200을 반환하면 DI 및 컴파일 오류가 없다는 뜻이며, 이후 실제 비즈니스 로직을 추가합니다.

**Boundary Gate (경계 톨게이트):**
- **Inbound**: `mapper`가 `schema` ↔ `dto`를 변환합니다. Router → Interactor 경계입니다.
- **Outbound**: `orm_mapper`가 `entity` ↔ ORM을 변환합니다. Repository → DB 경계입니다.
- `domain/`과 `app/use_cases/` 레이어에서는 FastAPI, SQLAlchemy 등 외부 프레임워크를 import할 수 없습니다.

**설계 장치 3종:**

| 디렉터리 | 원칙 | 역할 |
|---|---|---|
| `app/ports/input/` | **ISP** | Driving Port — UseCase 인터페이스 (역할별로 분리) |
| `app/ports/output/` | **ISP** | Driven Port — Repository/Gateway 인터페이스 (역할별로 분리) |
| `dependencies/` | **DIP** | Composition Root — Port에 Adapter를 주입 (FastAPI `Depends`) |
| `domain/value_objects/` | **AOP 예외** | 프랙탈 밖 공통 VO — 여러 엔티티가 횡단 공유 |

**Codex 하네스 위임 공식:**

```text
"테이블 이름만 바꾸면 Codex가 나머지 11개 파일을 전부 채울 수 있는 구조"
```

---

### 13. ERD 설계 규칙

**정규화 원칙:**
- 모든 테이블은 **1NF → 2NF → 3NF** 순서로 정규화합니다.
- 성능 또는 편의를 위한 **부분적 역정규화(Denormalization)**는 허용하되 반드시 명시적인 근거가 있어야 합니다.
- 근거 없는 무분별한 역정규화는 절대 금지합니다.

**연결 원칙:**
- ERD의 모든 테이블은 **노드(Node)와 엣지(Edge)로 연결**되어야 합니다.
- 어떤 테이블도 고립된 상태로 존재할 수 없습니다.
- 연결되지 않은 테이블은 설계 오류로 간주합니다.

**Fractal과의 관계:**
- ERD 테이블 1개 = Fractal 11-File Set 1개이며 §12 규칙과 직접 연결됩니다.
- 테이블 간 관계(엣지)는 Repository 레이어에서 JOIN 또는 ID 참조로 구현합니다.
