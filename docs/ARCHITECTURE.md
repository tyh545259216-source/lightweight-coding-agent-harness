# Architecture

The runner orchestrates; providers transport; tools implement capabilities; the executor owns validation, permission checks and execution journaling. No imported agent framework controls the loop.

## Runtime boundaries

- [AgentRunner](../src/mini_harness/agent/runner.py): `run`, `resume` and `_drive` bound iterations/time, prepare requests, dispatch proposed calls and decide when to stop. Verification and observation controllers add explicit workflow checks.
- [Provider](../src/mini_harness/providers/base.py): `complete` accepts messages/tool definitions and returns `ModelResponse`. [OpenAICompatibleProvider](../src/mini_harness/providers/openai_compatible.py) handles HTTP; it cannot grant permissions or directly edit files.
- [ToolRegistry](../src/mini_harness/tools/registry.py): registers capabilities, produces definitions and `prepare_call` validates arguments. [ToolExecutor](../src/mini_harness/tools/executor.py): `execute`/`_execute` apply permission, workspace and journal decisions before invoking a tool.
- [ContextManager](../src/mini_harness/context/manager.py): `prepare` builds a bounded model request. Complete tool exchanges are retained/dropped together; MANAGED_V3 can pin observed source/map/failure evidence. The budget is a byte proxy, not a tokenizer guarantee.
- [SessionStore](../src/mini_harness/session/store.py): persistent append/load and exclusive lease. Session is durable execution history; context is a request-sized projection of history, not another source of persistence.

## Journal, trace and recovery

Journal events participate in execution/recovery decisions. [TraceRecorder](../src/mini_harness/tracing/recorder.py) records diagnostic events for inspection and external grading; a trace alone is not a transaction log.

The executor checks host [PermissionPolicy](../src/mini_harness/security/permissions.py), then tools resolve paths through [Workspace](../src/mini_harness/security/workspace.py). `execute` permission does not confer OS isolation.

[plan_recovery](../src/mini_harness/session/recovery.py) reconciles journal state. Completed calls can reuse saved results. An in-doubt side-effect call is blocked for manual reconciliation; it is never blindly replayed. This is deliberately weaker than exactly-once execution.

## Skills and MCP

[SkillLoader](../src/mini_harness/skills/loader.py) discovers SKILL.md metadata, exposes a catalog and loads selected bodies through `activate`/`ActivateSkill`. Instructions are not execution authority; optional references/scripts remain capabilities an application must explicitly expose. Skills are optional/on-demand.

[MCPClient.register_tools](../src/mini_harness/mcp/client.py) creates namespaced `MCPTool` adapters. Remote schemas are checked, host-specified permissions are attached, and calls enter the same registry/executor/journal chain. Server hints never grant permissions. Implemented scope is legacy 2025-06-18 stdio JSON-RPC, not full modern MCP.

[Request lifecycle](REQUEST_LIFECYCLE.md) follows one concrete tutorial. [Reliability](RELIABILITY.md) describes guarantees and limits. Evaluation remains outside the runtime's trust decisions.
