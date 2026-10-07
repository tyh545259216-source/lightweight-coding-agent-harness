# Skills

A skill is a discoverable bundle of instructions. In this project a directory contains `SKILL.md` with metadata and a body; it may also contain references or optional scripts. `SkillLoader.catalog` exposes names/descriptions without eagerly injecting every body. `activate`/`ActivateSkill` loads a selected body; compact/full reference modes are implemented.

Skills are **optional/on-demand**. Experiments do not demonstrate that default activation improves Coding Success. Routing correctness and instruction-token cost are separate observations.

- A **prompt** is the current request/instruction text.
- A **Skill** is a discoverable, reusable instruction bundle; it cannot grant permissions.
- A **Tool** is an executable capability with a schema, host permission and result contract.
- **MCP** is the implemented protocol/transport adapter for external tool servers, not a skill or the agent loop.

Reference files remain explicit resources. A script inside a skill is not automatically executable authority. The runtime does not import a skill framework. See [loader code](../src/mini_harness/skills/loader.py), [sample bundles](../skills) and [default policy](evaluation/DEFAULT_CONFIGURATION.md).
