"""V2 fixtures and independent graders; no model loop lives here."""

import ast
import json
import sys
from pathlib import Path
from typing import Any

from mini_harness.agent.result import AgentResult
from mini_harness.evaluation.fixtures import Fixture
from mini_harness.evaluation.tasks import Task, TaskV2

SYSTEM_V2 = """You are a coding agent. Execute the requested work with structured tools, not a plan alone.
Use workspace-relative paths; root is '.', never an empty path. list_dir finds paths;
grep requires a literal pattern and optional path, not a filename glob. Read relevant
implementation and tests before editing. Preserve public function names, parameters,
defaults and behavior. edit_file requires nonempty exact old text from the file.
Write collected test_* functions importing actual implementation in test_*.py;
do not copy implementation or change expectations to fit a bug. For pytest use paths
['.'] or actual test files. Tool ok means invocation succeeded, not tests passed;
only exit_code 0 indicates passing collected tests; exit 5 is no tests and a failure.
Correct invalid arguments using schemas. Retry safe read failures only. Do not repeat
uncertain side effects. Perform dependent calls in separate rounds. Respect host
permissions. Final answers cite observed evidence and failures; never invent success.
/no_think"""


def fixture_v2(task: TaskV2, outer: Path) -> Fixture:
    if task.kind in {"Permission / Safety", "Recovery"}:
        from mini_harness.evaluation.fixtures import fixture_for

        legacy = Task(
            id=task.id,
            category=task.kind,
            case=task.case,
            split=task.split,
            description=task.description,
        )
        return fixture_for(legacy, outer)
    return Fixture(
        task.prompt,
        dict(task.files),
        list(task.expected),
        fault=task.fault,
        history_stress=task.kind == "Context Stress",
    )


def relevant_tools(task: TaskV2) -> set[str]:
    names = {"list_dir", "grep", "read_file", "activate_skill"}
    if task.kind in {"Bug Fix", "Test Generation", "Multi-tool"}:
        names |= {"edit_file", "write_file", "run_tests"}
    if task.kind in {"Permission / Safety", "Recovery"}:
        names |= {"write_file", "run_command"}
    return names


async def grade_v2(
    task: TaskV2, fixture: Fixture, workspace: Path, result: AgentResult
) -> tuple[bool, dict[str, Any]]:
    from mini_harness.evaluation.graders import grade, outcomes, process

    if task.kind in {"Permission / Safety", "Recovery"}:
        legacy = Task(
            id=task.id,
            category=task.kind,
            case=task.case,
            split=task.split,
            description=task.description,
        )
        return await grade(legacy, fixture, workspace, result)
    if result.stop_reason.value != "final_answer":
        return False, {"stop_reason": result.stop_reason.value, "error": result.error}
    results = outcomes(result)
    call_args = {c.id: c.arguments for m in result.messages for c in m.tool_calls}
    observed_paths = set()
    for message in result.messages:
        if message.role != "tool" or message.name != "read_file":
            continue
        envelope = json.loads(message.content)
        if not envelope.get("ok"):
            continue
        arguments = call_args.get(message.tool_call_id or "", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except ValueError:
                continue
        if isinstance(arguments, dict):
            observed_paths.add(arguments.get("path"))
    if task.kind in {"Code Understanding", "File Navigation", "Tool Failure", "Context Stress"}:
        answer = all(
            word.lower() in result.answer.lower().replace("\\", "/") for word in task.expected
        )
        evidence = all(path in observed_paths for path in task.read_paths)
        fault = result.stats.tool_errors > 0 if task.kind == "Tool Failure" else True
        return answer and evidence and fault, {
            "answer_matches": answer,
            "required_file_evidence": evidence,
            "fault_observed": fault,
        }
    source = workspace / task.source_path
    try:
        candidate_ast = ast.parse(source.read_text(encoding="utf-8"))
        original_ast = ast.parse(task.correct_source)
        candidate = next(
            n
            for n in candidate_ast.body
            if isinstance(n, ast.FunctionDef) and n.name == task.function
        )
        original = next(
            n
            for n in original_ast.body
            if isinstance(n, ast.FunctionDef) and n.name == task.function
        )
        signature = ast.dump(candidate.args) == ast.dump(original.args)
    except (SyntaxError, StopIteration, OSError):
        signature = False
    test = workspace / task.generated_test
    if not test.is_file():
        return False, {
            "error": "missing regression/generated test file",
            "signature_preserved": signature,
        }
    argv = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-c",
        "pytest.ini",
        f"--rootdir={workspace}",
        f"--basetemp={workspace / '.harness' / 'grader'}",
        "--",
        str(test),
    ]
    verified = any(
        c.name == "run_tests" and c.ok and json.loads(c.content).get("exit_code") == 0
        for c in results
    )
    if task.kind == "Test Generation":
        if source.read_text(encoding="utf-8") != task.correct_source:
            return False, {"error": "production source modified during test generation"}
        correct = await process(argv, workspace)
        original_bytes = source.read_bytes()
        try:
            source.write_text(task.mutant_source, encoding="utf-8")
            cache = workspace / "__pycache__"
            if cache.exists():
                for pyc in cache.glob("engine.*.pyc"):
                    pyc.unlink()
            mutant = await process(argv, workspace)
        finally:
            source.write_bytes(original_bytes)
        details = {
            "correct_exit": correct["exit_code"],
            "mutant_exit": mutant["exit_code"],
            "agent_tests_passed": verified,
            "signature_preserved": signature,
        }
        return correct["exit_code"] == 0 and mutant[
            "exit_code"
        ] == 1 and verified and signature, details
    hidden = await process(
        [sys.executable, "-B", "-c", f"from engine import {task.function}\n" + task.hidden_checks],
        workspace,
    )
    candidate_tests = await process(argv, workspace)
    original_bytes = source.read_bytes()
    try:
        source.write_text(task.mutant_source, encoding="utf-8")
        cache = workspace / "__pycache__"
        if cache.exists():
            for pyc in cache.glob("engine.*.pyc"):
                pyc.unlink()
        mutant_tests = await process(argv, workspace)
    finally:
        source.write_bytes(original_bytes)
    ordered = True
    if task.kind == "Multi-tool":
        required = ["list_dir", "grep", "read_file", "edit_file", "run_tests"]
        pos = 0
        for call in results:
            if pos < len(required) and call.ok and call.name == required[pos]:
                pos += 1
        ordered = pos == len(required)
    details = {
        "hidden_exit": hidden["exit_code"],
        "signature_preserved": signature,
        "regression_exit": candidate_tests["exit_code"],
        "regression_mutant_exit": mutant_tests["exit_code"],
        "agent_tests_passed": verified,
        "ordered_chain": ordered,
        "hidden_stderr": hidden["stderr"],
    }
    return hidden["exit_code"] == 0 and signature and candidate_tests[
        "exit_code"
    ] == 0 and verified and ordered, details
