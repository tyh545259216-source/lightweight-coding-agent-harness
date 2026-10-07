"""Minimal scalar frontmatter parser; no YAML execution or eager body loading."""

from pathlib import Path

from mini_harness.skills.models import SkillMetadata


class SkillFormatError(ValueError):
    pass


def read_header(path: Path) -> tuple[dict[str, str], int]:
    fields: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        if handle.readline().strip() != "---":
            raise SkillFormatError("Missing frontmatter")
        for index in range(1, 31):
            line = handle.readline()
            if line.strip() == "---":
                return fields, index + 1
            if not line or len(line) > 2048:
                raise SkillFormatError("Invalid frontmatter")
            if not line.strip():
                continue
            if ":" not in line:
                raise SkillFormatError("Only scalar key: value fields supported")
            key, value = line.split(":", 1)
            key, value = key.strip(), value.strip()
            if key not in {"name", "description"} or key in fields:
                raise SkillFormatError("Unknown/duplicate metadata field")
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key] = value
    raise SkillFormatError("Frontmatter exceeds 30 lines")


def discover_skills(root: Path) -> dict[str, SkillMetadata]:
    root = root.resolve(strict=True)
    skills: dict[str, SkillMetadata] = {}
    for path in sorted(root.glob("*/SKILL.md")):
        safe = path.resolve(strict=True)
        if not safe.is_relative_to(root):
            raise SkillFormatError("Skill symlink escapes configured root")
        fields, _ = read_header(safe)
        try:
            metadata = SkillMetadata(path=safe, **fields)
        except ValueError as exc:
            raise SkillFormatError(str(exc)) from exc
        if metadata.name != path.parent.name:
            raise SkillFormatError("Skill name must match directory")
        if metadata.name in skills:
            raise SkillFormatError("Duplicate skill")
        skills[metadata.name] = metadata
    return skills
