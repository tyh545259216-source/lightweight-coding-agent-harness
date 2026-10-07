"""Versioned task schema. Runtime fixture recipes are deterministic and model-independent."""

import json
from pathlib import Path

from pydantic import BaseModel, Field


class Task(BaseModel):
    id: str
    category: str
    case: int = Field(ge=0, le=5)
    split: str
    description: str


class TaskV2(Task):
    version: int = 2
    kind: str
    prompt: str
    files: dict[str, str] = Field(default_factory=dict)
    expected: list[str] = Field(default_factory=list)
    read_paths: list[str] = Field(default_factory=list)
    expected_skills: list[str] = Field(default_factory=list)
    source_path: str = "engine.py"
    function: str = ""
    signature: str = ""
    correct_source: str = ""
    mutant_source: str = ""
    hidden_checks: str = ""
    generated_test: str = "test_generated.py"
    fault: str | None = None


def load_tasks(root: Path, split: str = "all") -> list[Task]:
    tasks: list[Task] = []
    for path in sorted(root.glob("*.jsonl")):
        tasks.extend(
            (TaskV2 if json.loads(line).get("version") == 2 else Task).model_validate(
                json.loads(line)
            )
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        )
    if len({t.id for t in tasks}) != len(tasks):
        raise ValueError("Duplicate task IDs")
    return [t for t in tasks if split == "all" or t.split == split]
