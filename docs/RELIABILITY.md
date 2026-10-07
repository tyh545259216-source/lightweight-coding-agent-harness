# Reliability mechanisms

## Permission boundary

The LLM proposes a call. The host decides which tools exist and which permissions are granted; the executor validates and checks policy before execution. Workspace resolution rejects escape paths and protects selected files. Tests/Python and trusted MCP servers retain host-process privileges. This is not an OS sandbox or a production-security guarantee.

## Durable journal and recovery

A session records intent and completed outcomes. A completed call can reuse a known result. If a side effect might already have happened but its outcome was not durably recorded, recovery blocks replay and requires reconciliation. Local crash/recovery tests exercise this boundary. Neither append-only journaling nor filesystem replacement provides general exactly-once semantics across arbitrary external services.

The V3 recovery fixture's safe replay block is HarnessMechanismSuccess. It is not evidence of model-generated code or task completion.

## Context budget

ContextManager bounds the request using a byte estimate. It preserves complete tool-call/result groups and can retain recent path/test evidence. A hard-budget stop is an honest runtime outcome; it may prevent task completion and is not coding success. Presence of retained evidence does not prove the model used it correctly.

[Architecture](ARCHITECTURE.md) · [Evaluation philosophy](EVALUATION_PHILOSOPHY.md) · [Security](../SECURITY.md)
