from pathlib import Path

from mini_harness.agent.runner import AgentRunner
from mini_harness.context.budget import TokenBudget
from mini_harness.context.manager import ContextManager, ContextMode
from mini_harness.providers.base import ModelResponse, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.session.store import SessionStore
from mini_harness.skills.loader import ActivateSkill, SkillLoader, SkillMode
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tools.registry import ToolRegistry

ROOT = Path(__file__).resolve().parents[1]


def test_metadata_selection_without_loading_body():
    loader = SkillLoader(ROOT / "skills")
    assert loader.select("Fix bug and repair failure preserving function signature") == "bug-fixing"
    assert (
        loader.select("Write regression tests with pytest assertions and boundary cases")
        == "python-testing"
    )
    assert (
        loader.select("Review code and explain repository behavior from evidence") == "code-review"
    )
    assert not loader.active
    assert loader.select("xyz123") is None
    assert loader.configure(SkillMode.NO_SKILLS, "fix bug") == []
    assert loader.configure(SkillMode.SELECTED_SKILL, "fix bug") == ["bug-fixing"]
    assert loader.configure(SkillMode.ALL_SKILLS_LOADED, "task") == sorted(loader.metadata)


async def test_selected_body_injected_in_raw_mode_and_persisted(tmp_path):
    loader = SkillLoader(ROOT / "skills")
    store = SessionStore(tmp_path / "session")
    provider = FakeProvider([ModelResponse(content="done")])
    await AgentRunner(
        provider,
        skills=loader,
        skill_mode=SkillMode.SELECTED_SKILL,
        context=ContextManager(TokenBudget(), mode=ContextMode.NO_COMPACTION),
        session=store,
    ).run("fix bug")
    request = provider.requests[0][0]
    assert any(m.name == "harness_skill" and "Preserve function name" in m.content for m in request)
    states = [e for e in store.load() if e["event"] == "skill_state"]
    assert states[-1]["data"]["names"] == ["bug-fixing"]


async def test_lazy_model_activation_survives_context_pressure():
    loader = SkillLoader(ROOT / "skills")
    registry = ToolRegistry()
    registry.register(ActivateSkill(loader))
    provider = FakeProvider(
        [
            ModelResponse(
                tool_calls=[
                    ToolCall(id="s", name="activate_skill", arguments={"name": "python-testing"})
                ]
            ),
            ModelResponse(content="done"),
        ]
    )
    await AgentRunner(provider, ToolExecutor(registry), skills=loader).run("write tests")
    assert not any(m.name == "harness_skill" for m in provider.requests[0][0])
    assert any(m.name == "harness_skill" and "Exit 0" in m.content for m in provider.requests[1][0])
