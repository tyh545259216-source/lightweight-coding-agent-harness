# Request lifecycle

Concrete example: `python examples/tutorial_demo.py` repairs the tutorial calculator. This is a scripted offline demonstration using actual tools and protected tests, not an LLM benchmark.

1. **User → runner.** `examples/tutorial_demo.py:run_tutorial` creates a new fixture, grants read/write/execute and calls `AgentRunner.run` in `src/mini_harness/agent/runner.py`.
2. **Model request.** `_drive` calls `ContextManager.prepare` in `context/manager.py`, obtains `ToolExecutor.definitions` and awaits `Provider.complete`. The tutorial uses `FakeProvider.complete`; the optional tutorial uses `OpenAICompatibleProvider.complete`.
3. **Structured decision.** `ModelResponse.tool_calls` contains a `ToolCall` name/id/arguments. Scripted calls first inspect/list/search, then read `calculator.py`; every dependent call occurs in a separate response.
4. **Validation.** `ToolExecutor.execute` → `_execute` → `ToolRegistry.prepare_call` in `tools/registry.py` resolves the registered name and validates the strict input schema.
5. **Permission.** The executor checks `PermissionPolicy`; `ObservationController.before_edit` requires observed evidence for coding edits. Tool paths pass through `Workspace.resolve`, including protected-test enforcement.
6. **Journal → execution.** `SessionStore.append` records execution intent/completion. `ApplyPatch.execute` in `tools/builtin/patch.py` compares SHA/context before writing; `RunTests.execute` in `tools/builtin/shell.py` runs fixed Python/pytest with bounded output and no shell=True.
7. **Tool result → context.** `ExecutionResult` becomes a tool message. Runner updates observations, stats/session and emits TraceRecorder events. A successful invocation is not automatically a passing test.
8. **Next request.** Context preparation includes the actual result/error. The next scripted response runs pytest on the protected tutorial tests.
9. **Verification → final.** `VerificationController` interprets test exit status; `CompletionController` checks changed/current targets. Only then does the final response end the run. The tutorial also checks that protected test bytes remain unchanged.

The implementation files above are under [src/mini_harness](../src/mini_harness). [Architecture](ARCHITECTURE.md) explains the separate responsibilities. The protected tutorial fixture and hand-authored script are disclosed in [the demo](../examples/tutorial_demo.py); no hidden dataset/oracle is imported.
