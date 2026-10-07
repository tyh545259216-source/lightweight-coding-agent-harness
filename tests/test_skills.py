from pathlib import Path

import pytest

from mini_harness.agent.runner import AgentRunner
from mini_harness.providers.base import ModelResponse, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.skills.discovery import SkillFormatError, discover_skills
from mini_harness.skills.loader import ActivateSkill, SkillLoader
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tools.registry import ToolRegistry


def create(root, name="sample", header=None, body="large body"):
    path = root / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        header or f"---\nname: {name}\ndescription: test description\n---\n{body}", encoding="utf-8"
    )
    return path


def test_discovery_reads_metadata_only(tmp_path, monkeypatch):
    create(tmp_path, body="SECRET_BODY")

    def blocked(*args, **kwargs):
        raise AssertionError("eager read_text forbidden")

    monkeypatch.setattr(Path, "read_text", blocked)
    result = discover_skills(tmp_path)
    assert result["sample"].description == "test description"
    assert "SECRET_BODY" not in str(result)


def test_lazy_activation_and_cache(tmp_path):
    p = create(tmp_path, body="before")
    loader = SkillLoader(tmp_path)
    assert not loader.active and "before" not in loader.catalog()
    p.write_text("---\nname: sample\ndescription: test\n---\nafter", encoding="utf-8")
    assert loader.activate("sample") == "after"
    p.unlink()
    assert loader.activate("sample") == "after"
    with pytest.raises(KeyError):
        loader.activate("missing")


@pytest.mark.parametrize(
    "header",
    [
        "bad",
        "---\nname: a\nname: b\n---",
        "---\nname: sample\nunknown: x\n---",
        "---\nname: different\ndescription: test\n---",
        "---\nname: sample\n---",
    ],
)
def test_bad_frontmatter(tmp_path, header):
    create(tmp_path, header=header)
    with pytest.raises(SkillFormatError):
        discover_skills(tmp_path)


def test_large_body(tmp_path):
    create(tmp_path, body="x" * 65537)
    with pytest.raises(SkillFormatError):
        SkillLoader(tmp_path).activate("sample")


async def test_activation_via_agent_registry(tmp_path):
    create(tmp_path, body="Run focused tests.")
    loader = SkillLoader(tmp_path)
    registry = ToolRegistry()
    registry.register(ActivateSkill(loader))
    provider = FakeProvider(
        [
            ModelResponse(
                tool_calls=[ToolCall(id="s", name="activate_skill", arguments={"name": "sample"})]
            ),
            ModelResponse(content="ready"),
        ]
    )
    result = await AgentRunner(provider, ToolExecutor(registry)).run(
        "test", system=loader.catalog()
    )
    assert result.stats.tool_successes == 1 and loader.active["sample"] == "Run focused tests."


def test_repository_examples():
    root = Path(__file__).resolve().parents[1] / "skills"
    loader = SkillLoader(root)
    assert set(loader.metadata) == {"python-testing", "bug-fixing", "code-review"}
    assert "run_tests" in loader.activate("python-testing")
