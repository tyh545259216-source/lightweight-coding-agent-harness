"""Configurable observation-first guard; only successful tool results are evidence."""

import hashlib
import json
from pathlib import PurePosixPath
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mini_harness.providers.base import ToolCall
from mini_harness.security.workspace import Workspace
from mini_harness.tools.result import ExecutionResult


class ObservationPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding: bool = False
    enforce: bool = True
    prefer_patch: bool = False
    require_complete_read: bool = True
    max_replans: int = Field(default=8, ge=0, le=30)


class ObservationState(BaseModel):
    inspected: list[str] = Field(default_factory=list)
    located: list[str] = Field(default_factory=list)
    read: dict[str, str] = Field(default_factory=dict)
    read_excerpts: dict[str, list[str]] = Field(default_factory=dict)
    read_ranges: dict[str, list[list[int]]] = Field(default_factory=dict)
    total_lines: dict[str, int] = Field(default_factory=dict)
    observed_keys: list[str] = Field(default_factory=list)
    violations: dict[str, int] = Field(default_factory=dict)
    replanning_count: int = 0


class ObservationController:
    def __init__(
        self, workspace: Workspace, policy: ObservationPolicy, state: ObservationState | None = None
    ):
        self.workspace, self.policy = workspace, policy
        self.state = state or ObservationState()
        self.events: list[dict[str, Any]] = []

    def path(self, raw: str) -> str:
        return self.workspace.resolve(raw).relative_to(self.workspace.root).as_posix()

    def violation(self, kind: str, tool: str, missing: list[str]) -> dict[str, Any]:
        self.state.violations[kind] = self.state.violations.get(kind, 0) + 1
        if self.policy.enforce:
            self.state.replanning_count += 1
        value = {
            "error_type": "policy",
            "tool": tool,
            "violation": kind,
            "missing_evidence": missing,
            "retryable": self.state.replanning_count <= self.policy.max_replans,
            "hint": "Inspect the workspace, locate the relevant path using listing/search, read its source, then edit and verify. Tool evidence only; a plan is not evidence.",
        }
        self.events.append({"event": "policy_violation", **value})
        return value

    def before_edit(self, tool: str, args: dict[str, Any]) -> dict[str, Any] | None:
        if not self.policy.coding or tool not in {"edit_file", "write_file", "apply_patch"}:
            return None
        path = self.path(str(args.get("path", "")))
        missing = []
        if not self.state.inspected:
            missing.append("workspace_inspected")
        existing = self.workspace.resolve(path).exists()
        parent = str(PurePosixPath(path).parent)
        if existing:
            if self.policy.prefer_patch and tool in {"write_file", "edit_file"}:
                missing.append("use_apply_patch_with_observed_sha256")
            if path not in self.state.located:
                missing.append("target_located")
            if path not in self.state.read:
                missing.append("target_source_read")
            elif args.get("old") and not any(
                str(args["old"]) in part for part in self.state.read_excerpts.get(path, [])
            ):
                missing.append("edit_context_not_observed")
            elif self.policy.require_complete_read and path in self.state.total_lines:
                seen: set[int] = set()
                for start, end in self.state.read_ranges.get(path, []):
                    seen.update(range(start, end + 1))
                if len(seen) < self.state.total_lines[path]:
                    missing.append("target_full_source_read")
        else:
            if parent not in self.state.inspected:
                missing.append("target_parent_inspected")
            if not self.state.read:
                missing.append("relevant_existing_source_read")
        if missing:
            value = self.violation("edit_before_observation", tool, missing)
            return value if self.policy.enforce else None
        return None

    def before_final(self) -> dict[str, Any] | None:
        if not self.policy.coding:
            return None
        missing = [
            name
            for name, present in [
                ("workspace_inspected", self.state.inspected),
                ("relevant_file_located", self.state.located),
                ("relevant_source_read", self.state.read),
            ]
            if not present
        ]
        if not missing:
            return None
        value = self.violation("premature_final", "final_answer", missing)
        return value if self.policy.enforce else None

    @property
    def exhausted(self) -> bool:
        return self.policy.enforce and self.state.replanning_count > self.policy.max_replans

    def observe(self, call: ToolCall, key: str, result: ExecutionResult) -> None:
        if not result.ok or key in self.state.observed_keys:
            return
        self.state.observed_keys.append(key)
        args = json.loads(call.arguments) if isinstance(call.arguments, str) else call.arguments
        collected = []
        if call.name == "list_dir":
            parent = self.path(str(args.get("path", ".")))
            if parent not in self.state.inspected:
                self.state.inspected.append(parent)
            for entry in result.content.splitlines():
                if entry.startswith("["):
                    continue
                try:
                    path = self.path(str(PurePosixPath(parent) / entry.rstrip("/")))
                except PermissionError:
                    continue
                if path not in self.state.located:
                    self.state.located.append(path)
            collected.append("workspace_inspected")
        elif call.name == "grep":
            for line in result.content.splitlines():
                if ":" not in line:
                    continue
                try:
                    path = self.path(line.split(":", 1)[0])
                except PermissionError:
                    continue
                if path not in self.state.located:
                    self.state.located.append(path)
            collected.append("search_locations")
        elif call.name in {"repository_map", "symbol_search"}:
            payload = json.loads(result.content)
            if call.name == "repository_map":
                parent = self.path(str(args.get("path", ".")))
                if parent not in self.state.inspected:
                    self.state.inspected.append(parent)
            for item in payload.get("files", payload.get("matches", [])):
                path = self.path(item["path"])
                if path not in self.state.located:
                    self.state.located.append(path)
            collected.append("repository_locations")
        elif call.name == "read_file":
            path = self.path(str(args["path"]))
            try:
                payload = json.loads(result.content)
            except ValueError:
                payload = None
            if isinstance(payload, dict) and "total_lines" in payload:
                source = payload.get("content", "")
                digest = str(payload.get("sha256", ""))
                if self.state.read.get(path) != digest:
                    self.state.read_ranges[path] = []
                    self.state.read_excerpts[path] = []
                self.state.total_lines[path] = payload["total_lines"]
                if source.strip():
                    self.state.read[path] = digest
                    excerpts = self.state.read_excerpts.setdefault(path, [])
                    if source not in excerpts:
                        excerpts.append(source[:8000])
                    self.state.read_excerpts[path] = excerpts[-8:]
                    self.state.read_ranges.setdefault(path, []).append(
                        [payload["start_line"], payload["end_line"]]
                    )
                    collected.append("source_read")
            elif result.content.strip():
                self.state.read[path] = hashlib.sha256(result.content.encode()).hexdigest()
                self.state.read_excerpts[path] = [result.content[:64000]]
                collected.append("source_read")
        if collected:
            self.events.append(
                {
                    "event": "evidence_collected",
                    "tool": call.name,
                    "kinds": collected,
                    "path": args.get("path", "."),
                }
            )
