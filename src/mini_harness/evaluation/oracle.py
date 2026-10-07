"""Golden scripted tool trajectories ONLY for deterministic harness regression."""

from mini_harness.evaluation.fixtures import Fixture
from mini_harness.evaluation.tasks import Task, TaskV2
from mini_harness.providers.base import ModelResponse, ToolCall


def scripted_responses(task: Task, f: Fixture, skills: bool) -> list[ModelResponse]:
    if isinstance(task, TaskV2):
        return scripted_v2(task, f)
    result: list[ModelResponse] = []

    def tool(tool_name: str, **arguments: object) -> None:
        result.append(
            ModelResponse(
                tool_calls=[ToolCall(id=str(len(result)), name=tool_name, arguments=arguments)]
            )
        )

    category = task.category
    if skills and category in {"Bug Fix", "Test Generation", "Multi-tool"}:
        tool("activate_skill", name="python-testing")
    if category == "Code Understanding":
        tool("list_dir")
        tool("grep", pattern="__main__", glob="*.py")
        tool("read_file", path=f.expected[0])
        result.append(
            ModelResponse(content=f"Entry {f.expected[0]} function {f.expected[1]} calls compute.")
        )
    elif category == "File Search":
        tool("grep", pattern="class " + f.expected[1])
        tool("read_file", path=f.expected[0])
        result.append(ModelResponse(content=" ".join(f.expected)))
    elif category in {"Bug Fix", "Test Generation", "Multi-tool"}:
        assert f.spec
        tool("list_dir")
        tool("grep", pattern="def " + f.spec.name)
        tool("read_file", path="module.py")
        if category != "Test Generation":
            tool("edit_file", path="module.py", old=f.spec.buggy, new=f.spec.correct)
        test = (
            f"from module import {f.spec.name}\ndef test_boundaries():\n"
            + "\n".join("    " + line for line in f.spec.checks.splitlines())
            + "\n"
        )
        tool("write_file", path="test_generated.py", content=test)
        tool("run_tests", paths=["test_existing.py", "test_generated.py"])
        result.append(ModelResponse(content="Implemented and tested boundaries."))
    elif category == "Tool Failure":
        tool("list_dir")
        tool("read_file", path="config/settings.py")
        tool("read_file", path="config/settings.py")
        result.append(ModelResponse(content=f.expected[0]))
    elif category == "Context Stress":
        tool("read_file", path="result.txt")
        result.append(ModelResponse(content=f.expected[0]))
    elif category == "Permission / Safety":
        assert f.safety_call
        name, args = f.safety_call
        result.append(ModelResponse(tool_calls=[ToolCall(id="safety", name=name, arguments=args)]))
        result.append(ModelResponse(content="Denied: policy does not permit this operation."))
    elif category == "Recovery":
        result.append(ModelResponse(content="Recovery done."))
    return result


def scripted_v2(task: TaskV2, fixture: Fixture) -> list[ModelResponse]:
    """Privileged reference data stays in regression only; never sent to real provider."""
    result: list[ModelResponse] = []

    def tool(name: str, **arguments: object) -> None:
        result.append(
            ModelResponse(
                tool_calls=[ToolCall(id=str(len(result)), name=name, arguments=arguments)]
            )
        )

    if task.kind in {"Bug Fix", "Test Generation", "Multi-tool"}:
        tool("list_dir")
        tool("grep", pattern="def " + task.function)
        tool("read_file", path=task.source_path)
        if task.kind != "Test Generation":
            tool(
                "edit_file", path=task.source_path, old=task.mutant_source, new=task.correct_source
            )
        test = (
            f"from engine import {task.function}\ndef test_boundaries():\n"
            + "\n".join("    " + line for line in task.hidden_checks.splitlines())
            + "\n"
        )
        tool("write_file", path=task.generated_test, content=test)
        tool("run_tests", paths=["."])
        result.append(ModelResponse(content="Changed and observed passing collected tests."))
    elif task.kind in {"Code Understanding", "File Navigation", "Context Stress", "Tool Failure"}:
        tool("list_dir")
        for path in task.read_paths:
            tool("read_file", path=path)
            if task.fault:
                tool("read_file", path=path)
        result.append(ModelResponse(content=" ".join(task.expected)))
    elif task.kind == "Permission / Safety":
        assert fixture.safety_call
        name, args = fixture.safety_call
        tool(name, **args)
        result.append(ModelResponse(content="Denied by host policy."))
    elif task.kind == "Recovery":
        result.append(ModelResponse(content="Recovery done."))
    return result
