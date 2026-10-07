"""Bounded repository metadata and Python symbols; no vector store or source dump."""

import ast
import hashlib
import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import Field

from mini_harness.security.workspace import Workspace, WorkspaceViolation
from mini_harness.tools.base import BaseTool, InputModel
from mini_harness.tools.builtin.filesystem import ReadFile, ReadInput, bounded_read
from mini_harness.tools.errors import ToolErrorDetail, ToolInputError


class ReadFileV3(ReadFile):
    description = "Read a bounded UTF-8 chunk. Returns path/start_line/end_line/total_lines/has_more/sha256/content. Follow has_more before drawing conclusions; default 200 lines, max 400."

    async def execute(self, arguments: ReadInput) -> str:
        path = self.workspace.resolve(arguments.path)
        text = bounded_read(path)
        lines = text.splitlines(keepends=True)
        total = len(lines)
        if arguments.start_line > max(1, total) or (
            arguments.end_line is not None
            and (arguments.end_line < arguments.start_line or arguments.end_line > total)
        ):
            raise ToolInputError(
                ToolErrorDetail(
                    error_type="range",
                    tool=self.name,
                    invalid_field="line_range",
                    received=[arguments.start_line, arguments.end_line],
                    expected=f"total_lines={total}; legal range=1..{max(1, total)}",
                    retryable=True,
                    total_lines=total,
                    legal_range=[1, max(1, total)],
                    hint=f"Use a valid 1-based range; total_lines={total}; legal range=1..{max(1, total)}. No read occurred.",
                )
            )
        end = min(
            arguments.end_line or arguments.start_line + 199, total, arguments.start_line + 399
        )
        return json.dumps(
            {
                "path": path.relative_to(self.workspace.root).as_posix(),
                "start_line": arguments.start_line,
                "end_line": end,
                "total_lines": total,
                "has_more": end < total,
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "content": "".join(lines[arguments.start_line - 1 : end]),
            },
            ensure_ascii=False,
        )


class MapInput(InputModel):
    path: str = "."
    max_files: int = Field(default=100, ge=1, le=300)


class SymbolInput(MapInput):
    symbol: str = Field(min_length=1, max_length=100)


EXCLUDED = {
    ".git",
    ".venv",
    "__pycache__",
    ".sessions",
    ".traces",
    ".harness",
    ".pytest_cache",
    "node_modules",
}


def candidates(workspace: Workspace, raw: str) -> Iterator[Path]:
    root = workspace.resolve(raw)
    if root.is_file():
        yield root
        return
    visited = 0
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(
            d
            for d in dirs
            if d not in EXCLUDED
            and not (Path(current) / d).is_symlink()
            and not (Path(current) / d).is_junction()
        )
        for name in sorted(files):
            visited += 1
            if visited > 2000:
                return
            if name.startswith(".env") or name.endswith((".pem", ".key")):
                continue
            try:
                path = workspace.resolve(str(Path(current) / name))
            except WorkspaceViolation:
                continue
            if path.is_file():
                yield path


def metadata(workspace: Workspace, path: Path) -> dict[str, Any]:
    row = {
        "path": path.relative_to(workspace.root).as_posix(),
        "type": "python" if path.suffix == ".py" else path.suffix.lstrip(".") or "text",
        "size": path.stat().st_size,
        "line_count": None,
        "symbols": [],
    }
    try:
        text = bounded_read(path)
    except (ValueError, OSError, UnicodeError):
        return row
    row["line_count"] = len(text.splitlines())
    if path.suffix == ".py":
        try:
            tree = ast.parse(text)
        except (SyntaxError, RecursionError):
            return row
        row["symbols"] = [
            {
                "name": node.name,
                "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                "start_line": node.lineno,
                "end_line": node.end_lineno,
            }
            for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        ][:100]
    return row


class RepositoryMap(BaseTool[MapInput]):
    name, description, input_model = (
        "repository_map",
        "Bounded repository paths/type/size/line count/top-level Python symbols. No full source; use read_file for evidence.",
        MapInput,
    )

    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    async def execute(self, arguments: MapInput) -> str:
        found = list(candidates(self.workspace, arguments.path))
        return json.dumps(
            {
                "path": self.workspace.resolve(arguments.path)
                .relative_to(self.workspace.root)
                .as_posix(),
                "files": [metadata(self.workspace, p) for p in found[: arguments.max_files]],
                "truncated": len(found) > arguments.max_files or len(found) >= 2000,
            },
            ensure_ascii=False,
        )


class SymbolSearch(BaseTool[SymbolInput]):
    name, description, input_model = (
        "symbol_search",
        "Find Python class/function/method definitions by literal case-insensitive name substring. Returns location/line range; does not read function bodies into context.",
        SymbolInput,
    )

    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    async def execute(self, arguments: SymbolInput) -> str:
        results = []
        for path in candidates(self.workspace, arguments.path):
            if path.suffix != ".py":
                continue
            try:
                tree = ast.parse(bounded_read(path))
            except (ValueError, SyntaxError, UnicodeError, OSError, RecursionError):
                continue
            definitions = [
                node
                for node in ast.walk(tree)
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            for node in definitions[:500]:
                symbol = {
                    "name": node.name,
                    "kind": "class" if isinstance(node, ast.ClassDef) else "function",
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                }
                if arguments.symbol.casefold() in str(symbol["name"]).casefold():
                    results.append(
                        {"path": path.relative_to(self.workspace.root).as_posix(), **symbol}
                    )
                    if len(results) >= arguments.max_files:
                        return json.dumps({"matches": results, "truncated": True})
        return json.dumps({"matches": results, "truncated": False})
