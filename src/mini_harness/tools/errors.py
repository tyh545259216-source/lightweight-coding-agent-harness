"""Bounded diagnostic data; hints never authorize or execute a guessed replacement."""

import json
from difflib import get_close_matches
from typing import Any

from pydantic import BaseModel, Field

from mini_harness.security.workspace import Workspace


class ToolErrorDetail(BaseModel):
    error_type: str
    tool: str
    invalid_field: str | None = None
    received: Any = None
    expected: Any = None
    retryable: bool = False
    hint: str = ""
    candidates: list[str] = Field(default_factory=list)
    violation: str | None = None
    missing_evidence: list[str] = Field(default_factory=list)
    total_lines: int | None = None
    legal_range: list[int] | None = None


class ToolInputError(ValueError):
    def __init__(self, detail: ToolErrorDetail):
        self.detail = detail
        super().__init__(detail.hint)


def limited(value: Any) -> Any:
    encoded = json.dumps(value, ensure_ascii=False, default=str)
    return value if len(encoded) <= 256 else encoded[:256] + "[truncated]"


def nearby(workspace: Workspace, raw: str) -> list[str]:
    from mini_harness.tools.builtin.navigation import candidates

    try:
        workspace.resolve(raw)
        names = [p.relative_to(workspace.root).as_posix() for p in candidates(workspace, ".")]
    except PermissionError:
        return []
    return get_close_matches(raw.replace("\\", "/"), names, n=3, cutoff=0.4)
