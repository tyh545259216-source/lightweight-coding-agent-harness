"""Separately attributed pinned real-repository recipes and deterministic graders."""

import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from mini_harness.agent.result import AgentResult
from mini_harness.evaluation.graders import outcomes, process
from mini_harness.evaluation.tasks import TaskV2


class RealRepositoryTask(TaskV2):
    version: int = 3
    repository: str
    commit: str
    license: str = "MIT"
    readonly_paths: list[str] = Field(default_factory=list)
    protected_hashes: dict[str, str] = Field(default_factory=dict)
    answer_alternatives: list[str] = Field(default_factory=list)


def load_real_tasks(root: Path) -> list[RealRepositoryTask]:
    manifest = json.loads((root / "eval/real_repo/manifest_v3.json").read_text(encoding="utf-8"))
    snapshot = root / "work/real-repositories/schedule-v3"
    source_files = {}
    for name, digest in manifest["hashes"].items():
        path = snapshot / name
        if not path.exists():
            raise FileNotFoundError("Fetch pinned real-repository snapshot first")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Pinned source snapshot hash mismatch: " + name)
        source_files[name] = path.read_text(encoding="utf-8")
    source = "schedule/__init__.py"
    tasks = []
    for index, recipe in enumerate(manifest["tasks"]):
        files = dict(source_files)
        original = files[source]
        mutant = original
        old = recipe.get("mutation_old")
        if old:
            if original.count(old) != 1:
                raise ValueError("Mutation must match exactly once")
            mutant = original.replace(old, recipe["mutation_new"], 1)
        if recipe["kind"] == "Bug Fix":
            files[source] = mutant
        files["test_contract_v3.py"] = manifest["contract_tests"]
        files["pytest.ini"] = "[pytest]\npython_files = test_contract_v3.py test_candidate_v3.py\n"
        readonly = ["test_contract_v3.py", "pytest.ini", "LICENSE.txt"]
        if recipe["kind"] == "Test Generation":
            readonly.append(source)
        protected = {
            path: hashlib.sha256(files[path].replace("\r\n", "\n").encode()).hexdigest()
            for path in readonly
        }
        tasks.append(
            RealRepositoryTask(
                id=recipe["id"],
                category=recipe["kind"],
                kind=recipe["kind"],
                case=index % 6,
                split="real_repository",
                description=recipe["prompt"],
                prompt=recipe["prompt"],
                files=files,
                expected=recipe.get("expected", []),
                read_paths=[source],
                source_path=source,
                correct_source=original,
                mutant_source=mutant,
                generated_test="test_candidate_v3.py",
                repository=manifest["repository"],
                commit=manifest["commit"],
                readonly_paths=readonly,
                protected_hashes=protected,
                answer_alternatives=recipe.get("answer_alternatives", []),
            )
        )
    return tasks


def api_signatures(source: str) -> list[tuple[str, str]]:
    tree = ast.parse(source)
    return sorted(
        (node.name, ast.dump(node.args))
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


async def grade_real(
    task: RealRepositoryTask, workspace: Path, result: AgentResult
) -> tuple[bool, dict[str, Any]]:
    protected = all(
        (workspace / path).is_file()
        and hashlib.sha256((workspace / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        == digest
        for path, digest in task.protected_hashes.items()
    )
    if not protected:
        return False, {"protected_contracts_preserved": False}
    if result.stop_reason.value != "final_answer":
        return False, {
            "stop_reason": result.stop_reason.value,
            "protected_contracts_preserved": True,
        }
    observed = outcomes(result)
    from mini_harness.context.manager import message_groups

    read = False
    for group in message_groups(result.messages):
        calls = {call.id: call for call in group[0].tool_calls}
        for message in group[1:]:
            call = calls.get(message.tool_call_id or "")
            if not call or call.name != "read_file":
                continue
            arguments = (
                json.loads(call.arguments) if isinstance(call.arguments, str) else call.arguments
            )
            envelope = json.loads(message.content)
            read = read or bool(envelope.get("ok") and arguments.get("path") == task.source_path)
    if task.kind in {"File Navigation", "Code Understanding"}:
        answer = result.answer.lower().replace("\\", "/")
        matches = all(word.lower() in answer for word in task.expected)
        alternatives = not task.answer_alternatives or any(
            word in answer for word in task.answer_alternatives
        )
        return read and matches and alternatives, {
            "required_file_evidence": read,
            "answer_matches": matches,
            "boundary_matches": alternatives,
            "protected_contracts_preserved": True,
        }
    source = workspace / task.source_path
    current = source.read_text(encoding="utf-8")
    try:
        api = api_signatures(current) == api_signatures(task.correct_source)
    except SyntaxError:
        api = False
    verified = any(
        item.name == "run_tests" and item.ok and json.loads(item.content).get("exit_code") == 0
        for item in observed
    )

    def argv(path: str) -> list[str]:
        return [
            sys.executable,
            "-B",
            "-X",
            f"pycache_prefix={workspace / '.harness' / 'real-check-bytecode'}",
            "-m",
            "pytest",
            "-q",
            "-c",
            "pytest.ini",
            f"--rootdir={workspace}",
            f"--basetemp={workspace / '.harness' / 'real-grader'}",
            "--",
            path,
        ]

    if task.kind == "Bug Fix":
        check = await process(argv("test_contract_v3.py"), workspace)
        changed = current != task.mutant_source
        return check["exit_code"] == 0 and api and verified and changed, {
            "independent_exit": check["exit_code"],
            "signature_preserved": api,
            "agent_tests_passed": verified,
            "source_changed": changed,
            "protected_contracts_preserved": True,
        }
    if current != task.correct_source:
        return False, {"production_preserved": False, "signature_preserved": api}
    candidate = workspace / task.generated_test
    if not candidate.is_file():
        return False, {"error": "missing generated candidate tests"}
    correct = await process(argv(task.generated_test), workspace)
    original = source.read_bytes()
    try:
        source.write_text(task.mutant_source, encoding="utf-8", newline="\n")
        mutant = await process(argv(task.generated_test), workspace)
    finally:
        source.write_bytes(original)
    return correct["exit_code"] == 0 and mutant["exit_code"] == 1 and verified and api, {
        "correct_exit": correct["exit_code"],
        "mutant_exit": mutant["exit_code"],
        "signature_preserved": api,
        "agent_tests_passed": verified,
        "production_preserved": True,
        "protected_contracts_preserved": True,
    }
