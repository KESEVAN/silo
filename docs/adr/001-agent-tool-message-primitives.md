# ADR-001: Agent, Tool, and Message as the core primitives

**Context:** Iteration 0 needs one agent running perceive -> decide -> act
end to end before any messaging, identity, or policy exists. The primitive
has to be right early, because every later department and the Porter itself
build directly on top of it.

**Decision:** `Agent` is an abstract class holding only injected tools and
its own memory; it never instantiates a tool itself. `Tool` is a one-method
strategy interface (`execute`). `Message` is a frozen dataclass so nothing
in flight can be mutated by a department that merely handles it. `act()`
looks up the tool by name and appends its result to memory -- that's the
entire responsibility of the base class.

**Alternatives considered:** A single `Agent` class with tool methods baked
in (`self.log()`, `self.send()`) was rejected -- it collapses the strategy
pattern the roadmap calls for and makes swapping a tool's implementation a
subclassing exercise instead of a constructor argument.

**Consequences:** Adding a new capability is adding a new `Tool`
implementation and wiring it into the `tools` dict -- no change to `Agent`.
The cost is one extra layer of indirection (`self._tools[name].execute(...)`)
for every action, which is a fine trade at this scale.
