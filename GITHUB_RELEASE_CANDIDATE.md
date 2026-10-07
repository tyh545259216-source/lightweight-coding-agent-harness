# GitHub Release Candidate

**LOCAL_GITHUB_READY** — local clean-export acceptance passed on Windows / Python3.12. Date:2026-10-07. Remote CI: **NOT RUN**.

## 1. Final public project name

**Lightweight Coding Agent Harness** — 轻量级 Coding Agent 执行框架（自研 Agent Runtime）。Local branch `release/github-v1`; Python import remains `mini_harness`. No package-name refactor.

## 2. Repository description

A lightweight Agent Runtime built from scratch for structured tool calling, context management, recovery, Skills, MCP and agent evaluation.

Suggested repository: `lightweight-coding-agent-harness`. [Metadata/topics](docs/GITHUB_METADATA.md).

## 3. Public directory tree

```text
README.md / LICENSE / CONTRIBUTING.md / SECURITY.md / AGENTS.md
pyproject.toml / requirements-lock.txt / .env.example
GITHUB_RELEASE_CANDIDATE.md / release_files.json
src/mini_harness/
tests/
examples/tutorials/
skills/
docs/evaluation/           # current experimental evidence
docs/archive/              # limited historical material
scripts/                   # selected audited utilities
eval/tasks/                # frozen datasets
eval/public/v3/            # safe numerical projections
eval/real_repo/            # pinned source manifest only
.github/workflows/ci.yml
```

Public deliverable: the explicit clean export, not the entire development checkout. In the development workspace it is `work/github-rc-validated/`. Its `release_files.json` declares183 publication files. Ignore its generated `work/` acceptance artifacts. Existing root experimental reports/raw evidence remain preserved privately. No broad git-add, commit or remote operation was performed.

## 4. README status

COMPLETE: recruiter-oriented positioning, four highlights, Mermaid architecture, why/runtime boundaries, Quick Start, implemented versus external components, concise evaluation and limitations. The first screen does not reproduce the experiment report.

## 5. Architecture docs

COMPLETE: [architecture](docs/ARCHITECTURE.md), [request lifecycle](docs/REQUEST_LIFECYCLE.md), [reliability](docs/RELIABILITY.md), [Skills](docs/SKILLS.md), [MCP](docs/MCP.md), [evaluation philosophy](docs/EVALUATION_PHILOSOPHY.md). Actual code files/functions and runner/provider/registry/executor/context/session/journal/trace responsibilities are documented.

## 6. Offline demo result

PASS in clean export: two independent scripted FakeProvider tutorials with real reads, SHA/context patch, pytest and completion verification. Each has seven total tool calls/seven scripted rounds, VERIFIED_SUCCESS and unchanged read-only test bytes. Legacy CLI scripted demo and actual stdio MCP integration also pass.

These are **Tutorial / Demonstration only, not benchmark scores or model intelligence**. [Walkthrough](docs/DEMO_WALKTHROUGH.md) links actual redacted offline event samples. No hidden dataset/oracle is imported into the new tutorials.

## 7. Ollama tutorial result

Actual LLM generation: **NOT RUN for this RC**. Optional tutorial is model-dependent / best effort, single-attempt and bounded; no model download. The unavailable local-endpoint case was executed: concise setup hint, exit2 and no traceback. No live-model success sample is claimed.

## 8. Tests

**229 passed, 6 skipped, 235 collected; zero failures/errors** in a fresh Python3.12 venv from the clean public export. Locked dependencies installed from official PyPI; editable installation and `pip check` passed.

Initial clean setup lacked the parent `work/` directory for pytest basetemp. CI/local setup now creates it before pytest; the unchanged test suite then passed. Six optional integration tests require the pinned real-repository cache, which is excluded from the public export. They intentionally skip offline; no private workspace was copied and no network repository/benchmark was run. The original frozen V3235-passed acceptance remains a different run. Initial failed logs remain private. Example import/protection/CRLF SHA wiring issues were fixed only in tutorials; V3 runtime/tests/grader/results were not changed.

## 9. Core coverage

Core excludes evaluation and both CLIs: **93.17% statement / 83.06% branch**. Statements 2127/2283; branches 618/744. Measured with --cov-branch; not combined coverage.

## 10. Whole-project coverage

All mini_harness source: **86.96% statement / 74.95% branch**. Statements 2961/3405; branches 820/1094. Examples are separate demonstrations, not extra suite coverage.

[FINAL_REPORT_V3](docs/evaluation/FINAL_REPORT_V3.md) retains its original acceptance facts; RC acceptance is a separate engineering run.

## 11. Lint/type status

PASS: Ruff check and format --check on src/tests/examples; strict mypy on src/mini_harness; dependency consistency. CI prepares the same offline engineering checks for Ubuntu/Windows Python3.12, but remote/Linux results are NOT RUN.

## 12. Public audit

PASS:183-file publication allowlist, forbidden-file/type checks, secret/personal-path scan and internal relative Markdown link check. `python scripts/audit_release_candidate.py` audits the declared publication files; generated ignored artifacts are outside that scope. Pattern scans cannot prove absence of every secret.

## 13. Secret/path scan

Zero secret/personal absolute-host-path findings; zero broken internal relative file links. Public documents use relative example paths and contain no personal username paths. Two small tutorial JSON samples are explicitly redacted scripted event projections, not raw sessions/traces.

## 14. Git tracked-file audit

Source branch index:130 tracked files, zero forbidden model/private files. The clean export is **NOT_A_GIT_CHECKOUT**; its own index check is N/A, not an invented Git-index pass. The allowlist includes untracked V3/RC files as publication candidates. No files were staged/committed for publication, no remote was created and nothing was pushed.

## 15. Known limitations

Reliable autonomous coding is not established. Both models have **0/8 real-repository AgentTaskSuccess** and **0/8 wider diagnostic**;4b was severely response-latency constrained on CPU. Skills have no demonstrated default task-success benefit; forced patch preference has insufficient evidence. Workspace guards are not an OS sandbox; Python/tests/MCP servers have host privileges. Recovery is not general exactly-once execution. MCP is the implemented legacy2025-06-18 stdio subset, not a full modern platform.

Tool success, test invocation success, safety refusal and recovery protection are not coding success. Frozen V3 failures/unrun groups remain disclosed; no benchmark rerun or behavior tuning occurred.

## 16. Resume-safe bullets

- 自研异步 Agent Runtime，独立实现 AgentRunner、Provider 抽象、严格 schema 的 Tool Registry 与统一 Executor，串联本地工具和限定 stdio MCP 执行链。
- 实现上下文预算、完整 tool-call/result 分组、显式权限、持久化 journal/session 与恢复策略，对不确定副作用阻止盲目重放，提供可观察编辑和验证护栏。
- 建立分层评测与 Trace 失败分析，区分 AgentTaskSuccess 与 HarnessMechanismSuccess；冻结V3验收通过235项自动化测试（干净RC为229 passed/6 optional integration skipped），并保留双模型0/8真实仓库与诊断等负结果及CPU限制。

[Full résumé guide](docs/RESUME_GUIDE.md). Do not claim reliable autonomous coding, significant success gains, production sandbox, full MCP or strong-model superiority. Ollama, Qwen, Pydantic/httpx/jsonschema/pytest are external dependencies; their capabilities are not claimed as self-implemented.

## 17. Files excluded from publication

Excluded: Ollama storage/blobs/model weights, gguf/bin files, raw traces/sessions, private repository/workspaces, virtual environments, bytecode, pytest/coverage temporary outputs, runtime cache, credentials, real .env, local logs/archives and validation environments. Curated datasets and safe numeric projections remain public.

V3 freeze audit: **17,538 existing files; zero changed hashes**, including source, protocols/tasks/graders, results and experimental facts. Originals remain; relocated public Markdown copies adjust links only. No model download, benchmark run, new framework/Multi-Agent/RAG/WebUI or coding-success tuning.

## 18. Remote CI status

**NOT RUN.** No GitHub repository, push or release publication. `.github/workflows/ci.yml` prepares Ubuntu/Windows Python3.12 tests/coverage/lint/types/offline demos/audit. It does not download Ollama models, run Qwen or schedule benchmarks.

LOCAL_GITHUB_READY means the local public candidate passed clean-export acceptance. It does not mean remote CI passed, Linux was tested or publication occurred.
