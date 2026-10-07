"""Explicit registration of the seven built-in coding capabilities."""

from mini_harness.security.workspace import Workspace
from mini_harness.tools.builtin.filesystem import EditFile, ListDir, ReadFile, WriteFile
from mini_harness.tools.builtin.navigation import ReadFileV3, RepositoryMap, SymbolSearch
from mini_harness.tools.builtin.patch import ApplyPatch
from mini_harness.tools.builtin.search import Grep
from mini_harness.tools.builtin.shell import RunCommand, RunTests
from mini_harness.tools.registry import ToolRegistry


def builtin_registry(
    workspace: Workspace, *, navigation_v2: bool = False, patch: bool = False
) -> ToolRegistry:
    registry = ToolRegistry()
    for tool in (
        ListDir(workspace),
        (ReadFileV3(workspace) if navigation_v2 else ReadFile(workspace)),
        Grep(workspace),
        WriteFile(workspace),
        EditFile(workspace),
        RunCommand(workspace),
        RunTests(workspace),
    ):
        registry.register(tool)
    if navigation_v2:
        registry.register(RepositoryMap(workspace))
        registry.register(SymbolSearch(workspace))
    if patch:
        registry.register(ApplyPatch(workspace))
    return registry
