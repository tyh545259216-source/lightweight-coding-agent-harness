"""Serializable tool outcome shared by executor, context and recovery."""

from pydantic import BaseModel

from mini_harness.tools.errors import ToolErrorDetail


class ExecutionResult(BaseModel):
    call_id: str
    name: str
    ok: bool
    content: str
    error_type: str | None = None
    error_detail: ToolErrorDetail | None = None
    replayed: bool = False
