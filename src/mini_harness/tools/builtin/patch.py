"""Single-target exact-context patch with hash precondition, bounded diff and no-op rejection."""

import difflib
import hashlib
import json
from typing import NoReturn

from pydantic import Field

from mini_harness.security.permissions import Permission
from mini_harness.security.workspace import Workspace
from mini_harness.tools.base import BaseTool, InputModel
from mini_harness.tools.builtin.filesystem import MAX_BYTES, atomic_write, bounded_read
from mini_harness.tools.errors import ToolErrorDetail, ToolInputError


class PatchInput(InputModel):
    path: str
    expected_sha256: str = Field(pattern="^[a-f0-9]{64}$")
    old: str = Field(min_length=1, max_length=MAX_BYTES)
    new: str = Field(max_length=MAX_BYTES)
    preview_only: bool = False


class ApplyPatch(BaseTool[PatchInput]):
    name, description, input_model = (
        "apply_patch",
        "Patch one observed file: require its read_file sha256 and unique exact old/context text; preview_only optional. Returns changed line count, bounded diff and new sha256. Rejects stale/mismatch/no-op; preserve API and verify.",
        PatchInput,
    )
    permission, side_effect = Permission.WRITE, True

    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    async def execute(self, arguments: PatchInput) -> str:
        path = self.workspace.resolve(arguments.path, write=True)
        source = bounded_read(path)
        current = hashlib.sha256(source.encode()).hexdigest()
        relative = path.relative_to(self.workspace.root).as_posix()

        def refuse(kind: str, field: str, received: str, expected: str, hint: str) -> NoReturn:
            raise ToolInputError(
                ToolErrorDetail(
                    error_type=kind,
                    tool=self.name,
                    invalid_field=field,
                    received=received[:256],
                    expected=expected,
                    retryable=True,
                    hint=hint,
                )
            )

        if current != arguments.expected_sha256:
            refuse(
                "stale_revision",
                "expected_sha256",
                arguments.expected_sha256,
                current,
                "File changed since the observed revision. Re-read the current source and formulate a new explicit patch.",
            )
        count = source.count(arguments.old)
        if count != 1:
            refuse(
                "context_mismatch",
                "old",
                str(count),
                "exactly one occurrence",
                "Use an observed, unique exact context; no source was changed.",
            )
        result = source.replace(arguments.old, arguments.new, 1)
        if result == source:
            refuse(
                "no_op",
                "new",
                arguments.new,
                "text differing from old",
                "Unchanged patch rejected; inspect source and apply a meaningful change.",
            )
        old_lines, new_lines = source.splitlines(keepends=True), result.splitlines(keepends=True)
        delta = list(
            difflib.unified_diff(old_lines, new_lines, fromfile=relative, tofile=relative, n=3)
        )
        operations = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False).get_opcodes()
        removed = sum(j - i for tag, i, j, _, _ in operations if tag in {"delete", "replace"})
        added = sum(j - i for tag, _, _, i, j in operations if tag in {"insert", "replace"})
        preview = "".join(delta)
        digest = hashlib.sha256(result.encode()).hexdigest()
        if not arguments.preview_only:
            atomic_write(path, result)
        return json.dumps(
            {
                "path": relative,
                "changed": not arguments.preview_only,
                "preview_only": arguments.preview_only,
                "changed_line_count": removed + added,
                "lines_removed": removed,
                "lines_added": added,
                "diff": preview[:4000],
                "diff_truncated": len(preview) > 4000,
                "sha256": current if arguments.preview_only else digest,
                "proposed_sha256": digest,
            },
            ensure_ascii=False,
        )
