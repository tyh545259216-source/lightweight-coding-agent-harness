"""Compact selection remains metadata-only; full references load only when requested."""

from pathlib import Path

import pytest

from mini_harness.skills.discovery import SkillFormatError
from mini_harness.skills.loader import ActivateInput, ActivateSkill, SkillLoader, SkillMode

ROOT = Path(__file__).resolve().parents[1]


def test_same_three_names_and_shorter_body_at_identical_selection():
    loader = SkillLoader(ROOT / "skills")
    assert sorted(loader.metadata) == ["bug-fixing", "code-review", "python-testing"]
    assert not loader.active
    assert loader.configure(SkillMode.NO_SKILL, "fix bug") == []
    compact = loader.configure(SkillMode.SELECTED_SKILL_COMPACT, "fix bug")
    short = loader.active[compact[0]]
    full = loader.configure(SkillMode.SELECTED_SKILL_FULL, "fix bug")
    long = loader.active[full[0]]
    assert compact == full == ["bug-fixing"] and len(short) < len(long)
    assert "Preserve function name" in short and "Preserve function name" in long


async def test_explicit_full_activation_does_not_eager_load_other_references():
    loader = SkillLoader(ROOT / "skills")
    tool = ActivateSkill(loader)
    await tool.execute(ActivateInput(name="python-testing"))
    short = loader.active["python-testing"]
    await tool.execute(ActivateInput(name="python-testing", detail="full"))
    assert len(loader.active["python-testing"]) > len(short)
    assert (
        sorted(loader.active) == ["python-testing"]
        and loader.active_details["python-testing"] == "full"
    )


def test_oversized_full_reference_cannot_be_injected(tmp_path):
    directory = tmp_path / "demo"
    directory.mkdir()
    (directory / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Demo compact instructions.\n---\nCompact", encoding="utf-8"
    )
    ref = directory / "references"
    ref.mkdir()
    (ref / "FULL.md").write_text("x" * 65537, encoding="utf-8")
    loader = SkillLoader(tmp_path)
    assert loader.activate("demo") == "Compact"
    with pytest.raises(SkillFormatError, match="exceeds"):
        loader.activate("demo", full=True)
    assert loader.active["demo"] == "Compact"
