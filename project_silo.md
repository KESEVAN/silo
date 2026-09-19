# Silo — Zero-Trust Agent Swarm

A build plan, not a tutorial. Each iteration exists because the previous one hit a
real wall — that wall, and how you resolved it, is the actual resume material.
Code you can't explain the tradeoffs of is vibe code, however clean it looks.

---

## 0. Read this before writing a line of code

**Language:** Python for Iterations 0–4. You already know it cold, so the syntax
won't compete with your attention for the actual lesson (interfaces, ownership,
failure handling). Iteration 6 is where you optionally port the Porter's
enforcement path to Go — treat that as Phase 2, not this weekend's job. The
tests you write now become the acceptance tests for that port later.

**Five rules that apply to every iteration below:**

1. **Depend on interfaces, not implementations.** An `Agent` depends on the
   `Tool` interface, never on a concrete tool class. A `Porter` depends on a
   `PolicyEngine` interface, never on `RBACPolicyEngine` directly. This is what
   lets you swap the in-memory queue for Redis in Iteration 6 without touching
   agent code.
2. **One class, one reason to change.** If describing a class needs the word
   "and," split it. `Porter` should not sign messages, enforce rate limits,
   *and* log — those are three collaborators it holds, not three jobs it does.
3. **Composition over inheritance, always.** `Porter` *has-a* `Router`,
   *has-a* `RateLimiter`, *has-a* `PolicyEngine`. No `class Porter(Router,
   RateLimiter, PolicyEngine)`. Multiple inheritance here is a God Object
   wearing a trench coat.
4. **No module reaches into another's internals.** `departments/mechanical.py`
   never imports from `departments/judiciary.py`. Departments only know the
   `Message` schema and the `Porter` interface. This constraint is what forces
   real messaging instead of disguised function calls.
5. **A test exists before the PR does.** Not strict TDD — write code and test
   in the same sitting, same commit. If you can't write a test for it yet, you
   don't understand the interface yet.

---

## 1. Repo structure (create this shell first, empty files are fine)

```
silo/
├── README.md
├── SILO_ROADMAP.md              <- this file
├── pyproject.toml
├── src/
│   └── silo/
│       ├── core/
│       │   ├── agent.py         # Agent ABC: perceive / decide / act
│       │   ├── tool.py          # Tool interface (strategy pattern)
│       │   └── message.py       # Message schema (frozen dataclass)
│       ├── identity/
│       │   ├── keys.py          # Ed25519 keypair generation
│       │   └── signer.py        # sign() / verify()
│       ├── policy/
│       │   ├── engine.py        # PolicyEngine interface (PDP)
│       │   └── rbac.py          # RBACPolicyEngine implementation
│       ├── porter/
│       │   ├── queue.py         # MessageQueue interface, FIFO + Priority impls
│       │   ├── router.py        # Directory + routing table
│       │   ├── rate_limit.py    # token bucket
│       │   └── porter.py        # composes queue + router + policy + signer
│       ├── departments/
│       │   ├── mechanical.py
│       │   ├── judiciary.py
│       │   ├── doctors.py
│       │   └── farmers.py
│       ├── resilience/
│       │   ├── circuit_breaker.py
│       │   └── retry.py
│       └── audit/
│           └── event_log.py     # append-only log
├── tests/
│   ├── unit/                    # mirrors src/silo structure exactly
│   └── integration/
├── docs/
│   └── adr/                     # one ADR per iteration, see template below
├── docker-compose.yml           # arrives in Iteration 6
└── .github/workflows/ci.yml
```

If a file sits empty for two iterations, delete it. Structure should reflect
what exists, not what you're planning to build in week four.

---

## 2. Honest weekend scope

Iteration 0 and 1, fully tested, is a legitimate weekend — and a stronger
portfolio artifact than most finished-but-untested "AI agent" repos on GitHub.
Iteration 2 partially done (signing works, policy checks are basic) is a good
stretch goal for Sunday night. **Iterations 3–6 are the next two to three
weekends, not this one.** If you try to cram all six into 48 hours you will
ship exactly the vibe-coded thing you said you didn't want — rushed tests,
copy-pasted error handling, no ADRs. A finished, tested Iteration 1 beats a
half-working Iteration 4.

Suggested split:
- **Saturday morning:** Iteration 0
- **Saturday afternoon:** Iteration 1
- **Sunday:** Iteration 2 (as far as it goes cleanly — stop and commit even if incomplete)

---

## Iteration 0 — One agent, direct calls

**Goal:** Get `perceive → decide → act` running end to end. Learn the agent
primitive cold before anything else touches it.

**Build:**
```python
# core/agent.py
from abc import ABC, abstractmethod

class Agent(ABC):
    def __init__(self, tools: dict[str, "Tool"]):
        self._tools = tools          # injected, never hardcoded
        self._memory: list[dict] = []

    @abstractmethod
    def perceive(self, inbox: list[dict]) -> dict: ...

    @abstractmethod
    def decide(self, context: dict) -> "Decision": ...

    def act(self, decision: "Decision") -> dict:
        tool = self._tools[decision.tool_name]   # depends on Tool interface
        result = tool.execute(decision.args)
        self._memory.append(result)
        return result

# core/tool.py
class Tool(ABC):
    @abstractmethod
    def execute(self, args: dict) -> dict: ...
```
One `PorterAgent` with three tools: `LogTool`, `SendTool`, `ReadTool`. No other
agents exist yet.

**Clean code focus:** constructor injection (tools passed in, not
instantiated inside `Agent`), type hints on every signature, `decide()` is a
pure function — no I/O inside it, which is exactly what makes it testable.

**Tests required:**
- Unit test `decide()` with 4–5 different contexts → assert correct `Decision`.
- Unit test `act()` with a mock `Tool` → assert the right tool gets called with the right args, and memory gets appended.

**Definition of done:**
- [ ] `Agent` and `Tool` are abstract classes with nothing concrete leaking in
- [ ] One working CLI script runs the loop and prints a result
- [ ] `pytest` passes locally
- [ ] ADR-001 written (see template)

---

## Iteration 1 — Two agents, real messaging

**Goal:** Force a real architectural decision: agents talk only through
messages, never by calling each other's code.

**Build:**
```python
# core/message.py
from dataclasses import dataclass
from time import time

@dataclass(frozen=True)
class Message:
    sender: str
    recipient: str
    payload: dict
    priority: int = 0
    timestamp: float = time()

# porter/queue.py
class MessageQueue(ABC):
    @abstractmethod
    def push(self, msg: Message) -> None: ...
    @abstractmethod
    def pop(self) -> Message: ...

class FIFOQueue(MessageQueue): ...
class PriorityQueue(MessageQueue): ...   # judiciary jumps the line — your call, justify it in the ADR
```
`Mechanical` and `Judiciary` agents exchange `Message` objects through one of
these queues. Neither imports the other's module.

**Clean code focus:** `FIFOQueue` and `PriorityQueue` must be fully
interchangeable (Liskov substitution) — anything that holds a `MessageQueue`
should not need to know which one it got.

**Tests required:**
- Unit test both queue implementations independently — ordering behavior, especially priority-queue tie-breaks.
- Integration test: Mechanical sends, Judiciary receives, payload round-trips intact.

**Definition of done:**
- [ ] Zero direct imports between department modules
- [ ] Both queue implementations pass the same test suite (parametrize it)
- [ ] ADR-002: why FIFO vs. priority, and for which message types

---

## Iteration 2 — Identity and zero-trust (the differentiator)

**Goal:** Right now any agent can forge a message as anyone. Fix that.

**Build:**
```python
# identity/signer.py
def sign(private_key, message: Message) -> bytes: ...
def verify(public_key, message: Message, signature: bytes) -> bool: ...

# policy/engine.py
class PolicyEngine(ABC):
    @abstractmethod
    def evaluate(self, identity: "Identity", action: str, resource: str) -> bool: ...

# policy/rbac.py
class RBACPolicyEngine(PolicyEngine):
    """Roles -> permissions -> resources as an adjacency structure. Keep it a
    plain dict-of-sets first. Don't reach for a graph library until a plain
    dict actually fails you."""
```
Every message gets signed. The Porter verifies the signature, then asks
`PolicyEngine.evaluate(...)` before delivering. This is a miniature version of
the real PDP/PEP pattern used in enterprise IAM — the Porter is the PEP, the
`PolicyEngine` is the PDP.

**Clean code focus:** `PolicyEngine` is an interface for a reason — this is
the exact module you'd swap for a Go service calling real OPA later, without
touching the Porter's other responsibilities.

**Tests required:**
- Table-driven tests: 10+ (identity, action, resource) combinations, both allow and deny, including edge cases (expired-looking timestamp, unknown identity, right role wrong level).
- Integration test: a forged signature gets rejected before policy is even consulted; a replayed message gets rejected by timestamp/nonce check.

**Definition of done:**
- [ ] Unsigned or forged messages never reach `PolicyEngine.evaluate`
- [ ] At least one test proves a *legitimate* identity gets denied for an out-of-scope resource
- [ ] ADR-003: how the RBAC structure is modeled, and its known limits

---

## Iteration 3 — N agents, routing *(next weekend)*

**Build:** `Directory` (who exists, what level), `Router` using it,
`RateLimiter` (token bucket) — three separate classes the `Porter` composes,
not three responsibilities crammed into `Porter` itself. Scale to 10–15
department agents.

**Tests:** token bucket refill math; integration test with all departments
registered and a noisy agent visibly throttled.

**Definition of done:**
- [ ] `Porter` constructor takes `Directory`, `Router`, `RateLimiter`, `PolicyEngine` as arguments — none instantiated inside it
- [ ] ADR-004

---

## Iteration 4 — Shared state and audit *(next weekend)*

**Build:** `EventLog` interface, append-only, in-memory then file-backed
implementation. Judiciary reconstructs history by reading the log — never by
querying live mutable state.

**Tests:** log is provably append-only (attempt a mutation, assert it's
rejected or structurally impossible); concurrent-writer ordering test.

**Definition of done:**
- [ ] No department holds mutable shared state directly — only append/read through `EventLog`
- [ ] ADR-005: why event sourcing over mutable state here

---

## Iteration 5 — Failure is normal *(next weekend)*

**Build:** `CircuitBreaker` as an explicit state machine (closed → open →
half-open), `RetryPolicy` (exponential backoff), a dead-letter queue.

**Tests:** kill an agent mid-exchange; assert the breaker opens after N
failures, half-opens on schedule, and undeliverable messages land in the DLQ
rather than vanishing.

**Definition of done:**
- [ ] `CircuitBreaker` state transitions are unit-tested for all three states
- [ ] ADR-006

---

## Iteration 6 — Distribute and measure *(the weekend after that)*

**Build:** each department as its own container via `docker-compose`. Swap
the in-memory queue for a real broker only after you've demonstrated why it
breaks (can't survive a restart, becomes a bottleneck past N agents) — that
demonstration is itself a test/benchmark you keep. Load-test 50–100 agents,
capture p50/p99 latency and throughput.

**Optional fork here:** port the Porter's enforcement path to Go, and swap
`RBACPolicyEngine` for a real Open Policy Agent call. Your Iteration 2 test
suite becomes the acceptance test for that port — if it passes against the Go
service, the port is correct.

**Definition of done:**
- [ ] `docker-compose up` brings the full system online from a clean checkout
- [ ] A `results/` folder with real numbers, not adjectives

---

## Architecture Decision Record — template

One paragraph per iteration, saved to `docs/adr/00X-title.md`. This is a
better artifact than the code itself when you're explaining the project in an
interview.

```markdown
# ADR-00X: <short title>

**Context:** what problem forced this decision.
**Decision:** what you built.
**Alternatives considered:** what else you could have done, and why not.
**Consequences:** what this makes easier, what it makes harder, what you'd
revisit if the project grew.
```

---

## Minimal CI — add this in Iteration 0, not later

`.github/workflows/ci.yml`:
```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: mypy src/
      - run: pytest --cov=silo tests/
```
This is your "staging" discipline for a solo project: nothing is done until
it's green in an environment that isn't just your head. `docker-compose` in
Iteration 6 becomes your actual staging environment once there's something
worth staging.

---

## Cheat sheet — pin this above your desk

**Do:** interfaces before implementations · constructor injection · one class
one job · test the same day you write the code · commit an ADR every
iteration · stop at a clean, tested stopping point even mid-iteration.

**Don't:** import a framework before you've felt the problem it solves ·
write department "personality" before Iteration 3 · let `Porter` do
everything itself · skip the test because "it obviously works" · try to
finish all six iterations this weekend.