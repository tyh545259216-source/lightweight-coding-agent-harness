# Agent loop
AgentRunner.run adds the user task, then performs at most max_iterations rounds.
Provider.complete returns ModelResponse. Calls are executed sequentially and each gets a correlated
role=tool message. Tool failures are data so the model can correct them. Provider failures stop.
Without verification, final text without calls is the answer. With verification, a final answer is accepted only when the current patched revision passed canonical tests; otherwise feedback continues the bounded loop. Empty text stops as empty_response. Duplicate IDs are rejected.
asyncio.timeout bounds both model and total task time. Cancellation becomes an auditable terminal result.
Usage is provider-reported or explicitly unavailable; FakeProvider does not invent tokens.

## Inspecting one round

1. Runner chooses the current iteration, obtains definitions and projects context.
2. It records model_requested, starts the model deadline, then calls Provider.complete.
3. It records model_received and adds only the reported usage. Duplicate IDs stop the round.
4. With no calls: nonempty text becomes final_answer only if the optional verification gate is satisfied; a rejected completion gets host feedback. Blank text becomes empty_response.
5. With calls: persist the assistant exchange before effects, execute in listed order, append each correlated tool result, then request the next model response.
6. Exhausted iterations, context_limit, provider_error, timeout, cancellation or recovery_blocked produce explicit terminal results and statistics.

A pending side-effect intent can survive process interruption; resume reconstructs the original call identity. Its in-doubt replay is blocked rather than entrusted to a model guess. A completed final assistant message with a missing terminal event can be finalized without another model request only if saved verification state permits it. A previously rejected final cannot bypass the gate.

Read tests/test_runner.py first: loop(0), loop(1), loop(3) isolate protocol control; then follow tests/test_security_recovery.py and test_process_recovery.py. The actual AgentResult contains complete messages, while Provider receives a temporary bounded projection.

After a dirty revision, the host appends a correlated assistant/test-result exchange, captures structured canonical status, then either accepts verified completion or consumes a repair round. A test-tool failure stops without automatic uncertain replay. Trace origins distinguish model-selected calls from host verification calls.
