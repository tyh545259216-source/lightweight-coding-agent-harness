# Contributing

Use Python3.12+, install `python -m pip install -e ".[dev]"` in a virtual environment,
and read AGENTS.md plus docs/ARCHITECTURE.md. Keep dependencies minimal.
Providers transport; the runner orchestrates; the executor owns validation,
permissions and execution journaling; tools implement capabilities.

Required checks:

```text
python -m pytest --cov=mini_harness --cov-report=term-missing --cov-report=json:eval/results/coverage.json
python -m ruff check src tests examples
python -m ruff format --check src tests examples
python -m mypy src/mini_harness
python -m mini_harness.cli demo --workspace work/new-demo
python examples/mcp_demo.py
python scripts/audit_release_candidate.py
```

Demo requires a new directory. EXECUTE runs trusted Python/pytest code and is not
an OS sandbox. Never run untrusted repos or weaken permission/recovery invariants.
Never replay uncertain side effects. Never add shell=True or arbitrary executable
paths. Tests should verify real behavior rather than mirror implementation.

V1 and V2 heldout data are frozen. Development cases may inform changes; heldout
model outcomes must not guide prompts/rules, fixture edits or hyperparameters.
Record protocol/source/task hashes before genuine runs, preserve raw failures,
and use new output directories. FakeProvider means scripted harness regression;
never describe it as model intelligence. Distinguish unavailable usage from zero.

Publication excludes raw sessions, traces, benchmark workspaces, credentials,
model files, caches and local archives. Public projections retain task IDs,
metrics, redacted bad cases and hashes. Keep originals locally for audit. The
public scanner checks the declared export inventory; it does not secure arbitrary
runtime outputs or execute trusted tests in isolation.

Changes require meaningful checks and synchronized PLAN/docs. No remote
publication, secret changes, or new external service is required for local work.

Ordinary CI runs offline and does not fetch benchmark repositories or models.
The clean Release Candidate has 229 passed and 6 skipped tests: those six optional
real-repository integration tests require the separately prepared pinned repository
cache. Skips indicate an unavailable optional fixture, not test failures. Full local
real-repository evaluation requires preparing that cache outside ordinary CI.
