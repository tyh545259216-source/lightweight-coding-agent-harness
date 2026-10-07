"""Tools expose only declared schemas; no arbitrary function dispatch."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict

from mini_harness.providers.base import ToolDefinition
from mini_harness.security.permissions import Permission


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class BaseTool[T: BaseModel](ABC):
    name: str
    description: str
    permission: Permission = Permission.READ
    input_model: type[T]
    host_only: bool = False
    side_effect: bool = False
    timeout: float = 30

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.input_model.model_json_schema(),
        )

    def validate(self, arguments: dict[str, Any]) -> T:
        return self.input_model.model_validate(arguments)

    @abstractmethod
    async def execute(self, arguments: T) -> str: ...
