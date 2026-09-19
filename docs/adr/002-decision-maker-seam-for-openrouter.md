# ADR-002: DecisionMaker interface as the seam for OpenRouter

**Context:** The original Iteration 0 sketch has `decide()` as a pure,
in-process function on `Agent` -- easy to unit test, but it has nowhere to
put a call to an LLM without either breaking the "no I/O inside decide()"
rule or hardcoding a specific provider into every agent subclass. We want
to start immediately with a real model (OpenRouter, free-tier Nemotron)
rather than deferring reasoning to a later iteration, without giving up the
testability the roadmap insists on.

**Decision:** Introduce `DecisionMaker` as its own interface
(`silo.core.decision_maker`), constructor-injected into `PorterAgent`
exactly like `Tool` instances are. `Agent.decide()` becomes a one-line
delegation. Two implementations exist from day one:
`RuleBasedDecisionMaker` (no dependencies, no network, used as the default
and in most tests) and `LLMDecisionMaker` (wraps anything matching the
`Completer` protocol -- currently `OpenRouterClient` -- and turns its JSON
reply into a `Decision`). `OpenRouterClient` itself only knows how to POST
to `/chat/completions`; it has no notion of agents, tools, or decisions.

**Alternatives considered:** Putting the OpenRouter call directly inside
`PorterAgent.decide()` was rejected -- it would make every test that
exercises `PorterAgent` either need a real API key or a monkeypatched HTTP
layer, and it would tie the agent class to one specific provider's request
shape. Making `Agent.decide()` itself allowed to perform I/O (dropping the
roadmap's purity rule) was also rejected -- `DecisionMaker` gets the same
effect without weakening the rule for every future agent.

**Consequences:** Testing `PorterAgent` never touches the network -- fakes
implement `DecisionMaker` directly. Testing `LLMDecisionMaker` never
touches the network either -- fakes implement `Completer`. Only
`OpenRouterClient` itself needs HTTP mocking, and it's the only class that
imports `httpx`. This also means Iteration 3's `Router`/`RateLimiter`
composition and Iteration 2's `PolicyEngine` seam are now precedented by
`DecisionMaker` rather than being the first interface of their kind.
The cost: one more interface than the original roadmap sketch, and a
degree of freedom (which `DecisionMaker` is active) that has to be wired up
somewhere -- currently `silo.cli.build_decision_maker()`, chosen by whether
`OPENROUTER_API_KEY` is set.
