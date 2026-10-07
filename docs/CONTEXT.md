# Context management v2

`ContextManager` projects durable history; it never edits the journal. `TokenBudget`
uses UTF-8 serialized bytes as a conservative proxy, **not exact model tokens**.
Provider usage is the source of measured input/output tokens in experiments.
The same input budget and output reserve apply to all three modes.

- `NO_COMPACTION`: complete history; fail before requesting the model if over budget.
- `NAIVE_TRUNCATION`: bounded tool output and oldest complete groups removed; no summary/state ledger.
- `MANAGED_CONTEXT`: additionally retain two recent exchanges in the current user turn,
  configured active skills, rolling extractive summary, and recent execution evidence.

System instructions, latest user, last complete group, and current verification
feedback are pinned. Stale host verification feedback is deduplicated. Assistant
calls and all their tool results form an indivisible group. Orphan, duplicate,
and incomplete results are rejected before transport. Active skill bodies come
from a trusted configured root; oversized pinned content stops safely.

Structured test output keeps exit/pass fields plus bounded head and tail. Derived
state records observed paths, latest test scope/status, and tool errors. These
advisory facts and lossy summaries use assistant messages, not privileged system
instructions. Never treat a summary or a passing subset as proof of full correctness.
If pinned content alone overflows, the manager raises `ContextLimitError`.
A summary may be omitted under pressure; full history remains available on disk.

Comparison results will be recorded from actual runs, with explicit mode, budget,
input-token usage, context-limit stops, rounds, success, and latency. V1 failure
analysis found no demonstrated context-loss root cause, so this is a reliability
mechanism, not an assumed explanation for V1 coding failures.

Guarantees apply to the client projection. There is no exact model tokenizer or server context negotiation; an independently configured provider may apply its own truncation. V2 observed Ollama loaded context4096 while the harness uses its declared byte-proxy budget. No unobserved context-loss cause is asserted.
