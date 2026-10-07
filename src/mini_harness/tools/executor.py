"""Unified validation, authorization and durable at-most-once recovery guard."""

import asyncio
import hashlib
import json

from mini_harness.agent.observation import ObservationController
from mini_harness.providers.base import ToolCall, ToolDefinition
from mini_harness.security.permissions import PermissionPolicy
from mini_harness.session.recovery import RecoveryBlocked
from mini_harness.session.store import SessionStore
from mini_harness.tools.argument_repair import ArgumentRepairController
from mini_harness.tools.errors import ToolErrorDetail, ToolInputError, nearby
from mini_harness.tools.registry import ToolArgumentError, ToolRegistry
from mini_harness.tools.result import ExecutionResult


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        policy: PermissionPolicy | None = None,
        journal: SessionStore | None = None,
        observation: ObservationController | None = None,
        argument_repair: ArgumentRepairController | None = None,
    ) -> None:
        self.registry = registry
        self.policy = policy or PermissionPolicy()
        self.journal = journal
        self.observation = observation
        self.argument_repair = argument_repair
        self._lock = asyncio.Lock()

    def definitions(self) -> list[ToolDefinition]:
        return self.registry.get_definitions()

    async def execute(self, call: ToolCall, key: str, *, origin: str = "model") -> ExecutionResult:
        async with self._lock:
            if self.argument_repair:
                detail = self.argument_repair.before(call)
                if detail:
                    return ExecutionResult(
                        call_id=call.id,
                        name=call.name,
                        ok=False,
                        content=detail.model_dump_json(),
                        error_type="retry_limit",
                        error_detail=detail,
                    )
            result = await self._execute(call, key, origin=origin)
            if self.argument_repair:
                self.argument_repair.observe(call, key, result)
            return result

    async def _execute(self, call: ToolCall, key: str, *, origin: str = "model") -> ExecutionResult:
        def failed(
            kind: str, content: str, detail: ToolErrorDetail | None = None
        ) -> ExecutionResult:
            value = detail or ToolErrorDetail(
                error_type=kind, tool=call.name, retryable=False, hint=content[:512]
            )
            return ExecutionResult(
                call_id=call.id,
                name=call.name,
                ok=False,
                content=value.model_dump_json(),
                error_type=kind,
                error_detail=value,
            )

        try:
            prepared = self.registry.prepare_call(call)
        except KeyError:
            return failed("unknown_tool", f"Unknown tool: {call.name}")
        except ToolArgumentError as exc:
            return failed("arguments", str(exc), exc.detail)
        if prepared.tool.host_only and origin != "verification":
            return failed("permission", "Tool is available only to trusted host verification")
        try:
            await self.policy.check(call.name, prepared.tool.permission, prepared.raw)
        except PermissionError as exc:
            return failed("permission", str(exc))
        if self.observation:
            try:
                feedback = self.observation.before_edit(call.name, prepared.raw)
            except PermissionError as exc:
                return failed("permission", str(exc))
            if feedback:
                return failed(
                    "policy", json.dumps(feedback), ToolErrorDetail.model_validate(feedback)
                )
        fingerprint = hashlib.sha256(
            json.dumps(
                {"name": call.name, "args": prepared.raw}, sort_keys=True, ensure_ascii=False
            ).encode()
        ).hexdigest()
        if self.journal:
            records = [
                e
                for e in self.journal.load()
                if e["event"].startswith("execution_") and e["data"].get("key") == key
            ]
            if any(e["data"]["fingerprint"] != fingerprint for e in records):
                raise RecoveryBlocked("Execution key reused with different arguments")
            completed = [e for e in records if e["event"] == "execution_completed"]
            if completed:
                result = ExecutionResult.model_validate(completed[-1]["data"]["result"])
                result = result.model_copy(update={"replayed": True, "call_id": call.id})
                if self.observation:
                    self.observation.observe(call, key, result)
                return result
            if records and prepared.tool.side_effect:
                raise RecoveryBlocked(
                    f"In-doubt side effect {key}; inspect workspace and journal before manual reconciliation"
                )
            self.journal.append(
                "execution_started",
                {
                    "key": key,
                    "fingerprint": fingerprint,
                    "name": call.name,
                    "arguments": prepared.raw,
                    "side_effect": prepared.tool.side_effect,
                },
            )
        try:
            async with asyncio.timeout(prepared.tool.timeout):
                content = await prepared.tool.execute(prepared.arguments)
            result = ExecutionResult(call_id=call.id, name=call.name, ok=True, content=content)
        except ToolInputError as exc:
            result = failed("arguments", str(exc), exc.detail)
        except FileNotFoundError:
            workspace = getattr(prepared.tool, "workspace", None)
            raw = str(prepared.raw.get("path", ""))
            matches = nearby(workspace, raw) if workspace else []
            result = failed(
                "execution",
                "Path does not exist",
                ToolErrorDetail(
                    error_type="path_not_found",
                    tool=call.name,
                    invalid_field="path",
                    received=raw,
                    expected="existing workspace-relative path",
                    retryable=True,
                    candidates=matches,
                    hint="Inspect/list/search to confirm a candidate path before submitting a corrected call. No guessed replacement is executed.",
                ),
            )
        except PermissionError as exc:
            result = failed("permission", str(exc))
        except TimeoutError:
            result = failed("timeout", "Tool deadline exceeded")
        except asyncio.CancelledError:
            raise  # started intent remains durable; no false completion
        except Exception as exc:
            result = failed("execution", f"{type(exc).__name__}: {exc}")
        if self.journal:
            event = (
                "execution_uncertain"
                if prepared.tool.side_effect and not result.ok
                else "execution_completed"
            )
            self.journal.append(
                event, {"key": key, "fingerprint": fingerprint, "result": result.model_dump()}
            )
        if self.observation:
            self.observation.observe(call, key, result)
        return result
