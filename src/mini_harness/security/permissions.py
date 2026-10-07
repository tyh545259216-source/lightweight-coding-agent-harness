"""Capabilities are explicit; execute is never an implied read/write permission."""

from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any


class Permission(StrEnum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DANGEROUS = "dangerous"


Approval = Callable[[str, Permission, dict[str, Any]], Awaitable[bool]]


class PermissionPolicy:
    def __init__(
        self, allowed: set[Permission] | None = None, approval: Approval | None = None
    ) -> None:
        self.allowed = {Permission.READ} if allowed is None else allowed.copy()
        self.approval = approval

    async def check(self, name: str, level: Permission, arguments: dict[str, Any]) -> None:
        if level in self.allowed:
            return
        if self.approval and await self.approval(name, level, arguments):
            return
        raise PermissionError(
            f"{name} requires explicit {level.value} permission or human approval"
        )
