"""Explicit/model-selected activation uses the same registry as any local tool."""

import re
from enum import StrEnum
from pathlib import Path
from typing import Literal

from mini_harness.skills.discovery import SkillFormatError, discover_skills, read_header
from mini_harness.tools.base import BaseTool, InputModel


class SkillMode(StrEnum):
    NO_SKILL = "NO_SKILL"
    SELECTED_SKILL_COMPACT = "SELECTED_SKILL_COMPACT"
    SELECTED_SKILL_FULL = "SELECTED_SKILL_FULL"
    NO_SKILLS = "NO_SKILLS"
    SELECTED_SKILL = "SELECTED_SKILL"
    ALL_SKILLS_LOADED = "ALL_SKILLS_LOADED"
    MODEL_SELECTED = "MODEL_SELECTED"


class SkillLoader:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve(strict=True)
        self.metadata = discover_skills(self.root)
        self.active: dict[str, str] = {}
        self.active_details: dict[str, str] = {}
        self.mode = SkillMode.MODEL_SELECTED

    def catalog(self) -> str:
        return "Available skills (use activate_skill only when relevant):\n" + "\n".join(
            f"- {m.name}: {m.description}" for m in self.metadata.values()
        )

    def select(self, task: str) -> str | None:
        """Transparent lexical routing over metadata only; not a model prediction."""
        words = set(re.findall(r"[a-z]+", task.lower()))
        ignored = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "to",
            "in",
            "of",
            "with",
            "for",
            "use",
            "when",
            "is",
            "it",
        }
        words -= ignored
        scores = {}
        for name, metadata in self.metadata.items():
            title = set(re.findall(r"[a-z]+", name))
            description = set(re.findall(r"[a-z]+", metadata.description.lower())) - ignored
            scores[name] = len(words & description) + 3 * len(words & title)
        if not scores or max(scores.values()) == 0:
            return None
        return min(scores, key=lambda name: (-scores[name], name))

    def configure(self, mode: SkillMode, task: str) -> list[str]:
        self.mode = mode
        self.active.clear()
        self.active_details.clear()
        selected = (
            self.select(task)
            if mode
            in {
                SkillMode.SELECTED_SKILL,
                SkillMode.SELECTED_SKILL_COMPACT,
                SkillMode.SELECTED_SKILL_FULL,
            }
            else None
        )
        names = (
            sorted(self.metadata)
            if mode == SkillMode.ALL_SKILLS_LOADED
            else ([selected] if selected else [])
        )
        for name in names:
            self.activate(name)
        return names

    def activate(self, name: str, *, full: bool | None = None) -> str:
        full = self.mode == SkillMode.SELECTED_SKILL_FULL if full is None else full
        detail = "full" if full else "compact"
        if name in self.active and self.active_details.get(name) == detail:
            return self.active[name]
        metadata = self.metadata[name]
        path = metadata.path.resolve(strict=True)
        if not path.is_relative_to(self.root):
            raise SkillFormatError("Skill path escaped root")
        _, lines = read_header(path)
        with path.open(encoding="utf-8") as handle:
            for _ in range(lines):
                handle.readline()
            body = handle.read(65537)
        if len(body) > 65536:
            raise SkillFormatError("Skill body exceeds 64 KiB character limit")
        if full:
            reference = (metadata.path.parent / "references/FULL.md").resolve()
            if not reference.is_relative_to(self.root):
                raise SkillFormatError("Full skill reference escaped root")
            if reference.is_file():
                with reference.open(encoding="utf-8") as handle:
                    body = handle.read(65537)
                if len(body) > 65536:
                    raise SkillFormatError("Full skill reference exceeds64KiB")
        self.active_details[name] = detail
        self.active[name] = body.strip()
        return self.active[name]


class ActivateInput(InputModel):
    name: str
    detail: Literal["compact", "full"] = "compact"


class ActivateSkill(BaseTool[ActivateInput]):
    name, description, input_model = (
        "activate_skill",
        "Load compact instructions for one catalog skill; detail=full explicitly requests its full reference. No automatic script execution.",
        ActivateInput,
    )

    def __init__(self, loader: SkillLoader) -> None:
        self.loader = loader

    async def execute(self, arguments: ActivateInput) -> str:
        return f"[Activated skill: {arguments.name}]\n" + self.loader.activate(
            arguments.name, full=arguments.detail == "full"
        )
