"""Single registry shared by built-in and MCP tools."""

from __future__ import annotations

import builtins
import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from mini_harness.providers.base import ToolCall, ToolDefinition
from mini_harness.tools.base import BaseTool
from mini_harness.tools.errors import ToolErrorDetail, limited


class ToolArgumentError(ValueError):
    def __init__(self, detail: ToolErrorDetail):
        self.detail = detail
        super().__init__(detail.model_dump_json())


@dataclass(frozen=True)
class PreparedCall:
    tool: BaseTool[Any]
    arguments: BaseModel
    raw: dict[str, Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool[Any]] = {}

    def register(self, tool: BaseTool[Any]) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Duplicate tool: {tool.name}")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        del self._tools[name]

    def get(self, name: str) -> BaseTool[Any]:
        return self._tools[name]

    def list(self) -> list[str]:
        return sorted(self._tools)

    def get_definitions(self) -> builtins.list[ToolDefinition]:
        return [self._tools[n].definition() for n in self.list() if not self._tools[n].host_only]

    def prepare_call(self, call: ToolCall) -> PreparedCall:
        tool = self.get(call.name)
        try:
            raw = json.loads(call.arguments) if isinstance(call.arguments, str) else call.arguments
            if not isinstance(raw, dict):
                raise ValueError("Tool arguments must be a JSON object")
            parsed = tool.validate(raw)
        except (ValueError, TypeError, ValidationError) as exc:
            field = None
            if isinstance(exc, ValidationError):
                issue = exc.errors(include_url=False)[0]
                field = ".".join(str(part) for part in issue["loc"])
                received = limited(issue.get("input"))
                expected = issue["msg"]
            else:
                received = limited(call.arguments)
                expected = "JSON object conforming to the declared tool schema"
            raise ToolArgumentError(
                ToolErrorDetail(
                    error_type="arguments",
                    tool=call.name,
                    invalid_field=field,
                    received=received,
                    expected=expected,
                    retryable=True,
                    hint="Correct only the invalid argument using this tool's declared schema. Submit a new call; no execution happened.",
                )
            ) from exc
        return PreparedCall(tool, parsed, raw)
