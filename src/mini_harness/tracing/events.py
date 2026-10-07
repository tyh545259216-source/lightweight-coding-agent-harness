"""Trace events use explicit layer labels for failure localization."""

from typing import Any

from pydantic import BaseModel, Field


class TraceEvent(BaseModel):
    turn_id: str
    iteration: int
    model: str
    layer: str
    data: dict[str, Any] = Field(default_factory=dict)
