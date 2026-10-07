# FINAL_REPORT_V2 — Lightweight Coding Agent Harness

本轮完成失败分析、有界测试验证/修复、上下文三模式、技能对比、独立评测与公开仓库验证。工程机制可测试，现有小模型的自主编码能力仍为 PARTIAL；没有把安全停止、脚本回归或空测试通过当成编码成功。

## 1. Final architecture

Task → AgentRunner → ContextManager/Skills → Provider transport → typed calls → ToolRegistry/ToolExecutor validation + permissions + journal → capabilities → structured results → optional verification/repair → next round. Session is authoritative for replay; trace is diagnostic; working context is a lossy projection. Independent graders sit outside the model loop. Architecture Mermaid and boundaries are in README/docs/ARCHITECTURE.md.

## 2. Implemented features

- Original asyncio runner, strict local/external schemas, seven built-in tools, bounded deadlines and structured stops. No imported agent-loop/registry/context framework.
- Permission/path guards, single-writer durable journal, cached completed execution and uncertain-effect replay refusal.
- Optional canonical tests, revision invalidation, initial/final test status, bounded repair rounds/output, trace origins and saved verification policy.
- Raw/naive/managed contexts with complete exchanges, recent retention, system/skill priority, extractive rolling summary and observed state.
- Three practical skills, metadata parsing, lexical selection, lazy activation and pinned injection; real legacy MCP stdio through one executor.
- Frozen50/40-task V2 dataset, stronger path/API/behavior/mutant grading,12 metrics and redacted public evidence.

## 3. Partial features

Autonomous coding remains PARTIAL. A passing configured suite proves only its scope; empty/pass-only tests can pass it and fail the independent mutant grader. Context uses a conservative byte proxy and lossy summary. Skills selection is lexical rules, not model intelligence. Permission guards and trusted execute are not a full sandbox. MCP covers a legacy protocol subset. CLI skill availability is controlled by --skills; omit the root to disable all skill tools, rather than only disabling preload.

## 4. Not implemented

No OS sandbox, network isolation, atomic filesystem+journal transaction, exactly-once semantic deduplication, modern MCP/Streamable HTTP/auth platform, multi-agent feature or WebUI. No model download or paid service was required.

## 5. Unit/integration tests

162 pytest cases passed; 0 skipped; 0 failures/errors. Actual process crash/recovery, filesystem/junction guards, stdio MCP, nested pytest and mutant graders are exercised. Public export tests verify locations-only secret reporting, preserved private evidence and no escaping directory walk. Original local Git clean-clone observation: tests=162, offline demo=final_answer, MCP=final_answer; evidence source=local actual clean-clone validation.

## 6. Coverage

Core runtime (excluding CLI/evaluation): statement **94.74%**, independent branch **85.12%**, combined **92.46%**.
All mini_harness: statement **91.22%**, independent branch **82.48%**, combined **89.15%**.
V1用户摘要中的91.52%是核心语句+分支合并覆盖率，独立分支当时为82.16%；本报告没有混用这些口径。Raw evidence: eval/results/validation-v2; public numerical projection: eval/public/validation_v2.json.

## 7. Real model benchmark

Full development: **12/50** (24.0%). Genuine qwen3:1.7b, local Ollama CPU/Q4_K_M, loaded context4096; one trial per task/configuration. The dataset is small and synthetic. V1/V2 data/prompts/graders differ, so their total scores are not a controlled before/after effect.
Read-only Ollama smoke: FAIL; rounds=2, tool successes=1. This is provider/structured-read integration, not autonomous coding intelligence.

Toy coding smoke: PASS; rounds=3, tools=3, initial/final canonical test success=True/True. It uses three scoped tools, a two-line arithmetic implementation and protected pre-existing tests; the task supplies the sum contract but no exact patch. The recorded success flag requires observed read, changed source, preserved API, canonical tests and independent behavior checks. This one easier toy does not change dataset scores or establish general autonomous coding reliability.

Full development category outcomes: Bug Fix 0/5; Code Understanding 0/5; Context Stress 2/5; File Navigation 0/5; Multi-tool 0/5; Permission / Safety 5/5; Recovery 5/5; Skills 0/5; Test Generation 0/5; Tool Failure 0/5. All Bug Fix/Test Generation/Multi-tool/Skills categories remained0 in the frozen survey.

## 8. Held-out benchmark

Full heldout: **12/40** (30.0%). Dataset/source/skills were frozen before model experiments. No heldout outcome informed prompts, rules, fixture edits or hyperparameters. Coding APIs differ across splits, while context/safety/recovery structures remain correlated. Initial heldout execution briefly overlapped local final unit validation; host load/order/cache and unreported timeout usage limit latency interpretation.

Heldout category outcomes: Bug Fix 0/4; Code Understanding 0/4; Context Stress 4/4; File Navigation 0/4; Multi-tool 0/4; Permission / Safety 4/4; Recovery 4/4; Skills 0/4; Test Generation 0/4; Tool Failure 0/4.

## 9. Ablation

Fixed20 development tasks (two per category), same model/temperature/output/context/round/time limits. Full reuses exact matching observations from the50-case development survey; it is not a repeat trial.
- baseline: 5/20; executed=18; reported input=67889; mean rounds=3.39; mean agent latency=55.03s.
- context: 6/20; executed=18; reported input=57155; mean rounds=2.83; mean agent latency=48.81s.
- verification: 4/20; executed=18; reported input=54669; mean rounds=3.11; mean agent latency=56.74s.
- skills: 2/20; executed=18; reported input=107131; mean rounds=3.89; mean agent latency=46.81s.
- recovery: 8/20; executed=20; reported input=56767; mean rounds=2.65; mean agent latency=36.08s.
- full: 5/20; executed=20; reported input=39280; mean rounds=1.95; mean agent latency=78.70s.

Recovery enables both checkpoint cases; its off-target navigation gain cannot be attributed to recovery intelligence. Context restores synthetic-overflow capability. Verification and skills have no demonstrated coding-success gain. Off-target and one-shot variation prevent strong causal claims; docs/ABLATION.md contains paired transitions and category counts.

## 10. Failure taxonomy

All54 original real traces were reviewed before runtime changes.36 failed: PLANNING15/36=41.67%; EDIT_QUALITY9/36=25.00%; TOOL_ARGUMENT and FILE_NAVIGATION each4/36=11.11% (tie for third); VERIFICATION/CODE_UNDERSTANDING/TOOL_SELECTION/PROVIDER each1. Secondary labels can overlap. Three priorities: execute with observed file/API contracts; test-driven verification and bounded repair; preserve recent paths/test evidence/skills. No demonstrated V1 primary context-loss or permission/recovery failure was inferred.
All18 V1 coding tasks lacked observed passing tests; nine tasks had no-tests exit5; no skill activations. Original03-01 had hidden_exit0 but observed pytest5; its API rename was a grader gap, not an observed hidden assertion failure. V2 checks AST parameters/defaults and mutant rejection. See eval/analysis/failures.csv, FAILURE_ANALYSIS.md and redacted evidence.

## 11. Context comparison

- baseline: 5/20; reported input=67889 on 16 tasks; context-limit stops=2; rounds=3.39; latency=55.03s.
- naive: 6/20; reported input=73458 on 18 tasks; context-limit stops=0; rounds=3.50; latency=50.34s.
- context: 6/20; reported input=57155 on 18 tasks; context-limit stops=0; rounds=2.83; latency=48.81s.

Naive and managed both passed both Context Stress cases and tied overall6/20; this sample does not establish a task-success benefit from rolling summary/state over naive truncation. Preflight stops have unavailable usage, not free successful inference. Reported tokens cover completed responses only; timeout/cancellation consumption may be unreported. Public rows mark complete/partial usage and unobserved response rounds.

## 12. Skills comparison

- baseline: 0/5; exact active-set accuracy=0%; reported input=21899; latency=58.45s.
- skills: 0/5; exact active-set accuracy=100%; reported input=28746; latency=60.91s.
- all_skills: 0/5; exact active-set accuracy=0%; reported input=28935; latency=80.97s.

Selected routing matched5/5 expected sets but task success stayed0/5. Selected/all increased reported input cost. All-loaded deliberately over-selects, so0 accuracy under this exact-set metric is not failed discovery. Five cases do not prove general routing accuracy.

## 13. Repair-loop comparison

- baseline paired subset: first canonical pass=0/0; repair rounds=0; final canonical passes=0; bug-fix rate=0%.
- verification paired subset: first canonical pass=0/4; repair rounds=7; final canonical passes=0; bug-fix rate=0%.
- full paired subset: first canonical pass=1/1; repair rounds=0; final canonical passes=1; bug-fix rate=0%.

Full50-case survey: first canonical pass=2/5; repair rounds=4; final canonical passes=2. Unobserved first patches are not counted as failed patches. Verification can refuse unsupported completion and stop after exhaustion; it cannot ensure a correct edit or meaningful test. The one lower Verification aggregate score came from a navigation task with verification disabled, not evidence of harmful coding repair.

## 14. Security limitations

EXECUTE runs trusted pytest code on the host; it can access files/network outside the workspace. No full OS sandbox. Path guards do not solve TOCTOU, hardlinks or malicious tests. No atomic effect+journal commit: uncertain effects require reconciliation, never blind replay. New distinct calls are not semantically deduplicated. Safety rates measure fixture sentinels/refusal, not general host safety. Legacy MCP host grants do not trust readOnlyHint. Public scanning covers known patterns in the declared inventory, not every secret or runtime output.

## 15. Known bad cases

- V2 Full development word_counts03-04: only a function header read, wrong replacement implementation, missing-import/wrong-expectation tests, repeated no-op edits; real two-round repair exhaustion. Raw trace line pointers retained.
- V2 Full development take_last Test Generation04-01: pass-only test_* functions; canonical suite passed, independent mutant_exit0 rejected the task. Passing tests did not mean meaningful generated tests.
- Guessed file paths, out-of-range grep parameters, early plans/finals, unchanged source and model/task timeouts remain observed failures.
Read-only smoke hello.py: the model read only line1, then falsely concluded the function was unimplemented; the requested value check failed. Actual transport/read succeeded but task understanding did not. The separate arithmetic coding smoke passed and is explicitly scoped.

All failed records and redacted candidate source/test excerpts are in eval/public/bad_cases_v2.jsonl. Full raw traces/sessions/workspaces remain locally preserved and excluded from publication. Hashes alone cannot publicly verify excluded raw bytes without the originals.

## 16. Exact reproduction commands

```text
python -m venv .venv
# Activate the virtual environment using the platform command in README.
python -m pip --isolated install --index-url https://pypi.org/simple -r requirements-lock.txt -e .
python -c "from pathlib import Path; Path('eval/results/validation-v2').mkdir(parents=True, exist_ok=True)"
python -m pytest --basetemp=work/pytest-final-v2 --cov=mini_harness --cov-branch --cov-report=term-missing --cov-report=json:eval/results/validation-v2/coverage.json --junitxml=eval/results/validation-v2/pytest.xml > eval/results/validation-v2/pytest.txt
python -m ruff check src tests examples > eval/results/validation-v2/ruff-check.txt
python -m ruff format --check src tests examples > eval/results/validation-v2/ruff-format.txt
python -m mypy src/mini_harness > eval/results/validation-v2/mypy.txt
python -m mini_harness.cli demo --workspace work/new-demo
python examples/mcp_demo.py
python scripts/run_experiments_v2.py
python scripts/run_experiments_v2.py --heldout
python scripts/collect_results_v2.py --heldout
python examples/ollama_smoke_v2.py
python examples/ollama_coding_smoke_v2.py
python scripts/public_audit.py --output eval/results/public-audit-final.json
python scripts/report_v2.py
```
Use new output/demo directories; existing raw evidence is never overwritten. Generic evaluator accepts --dataset v2 --provider ollama --variants full --split development --model-timeout 60 --task-timeout 120 with a fresh --output. The report generator expects detailed validation under eval/results/validation-v2 (the exact acceptance command is below). Raw experiment records are excluded from the public package; reproduce the frozen runs before collecting them.
```text
python -m pytest --basetemp=work/pytest-final-v2 --cov=mini_harness --cov-branch --cov-report=term-missing --cov-report=json:eval/results/validation-v2/coverage.json --junitxml=eval/results/validation-v2/pytest.xml
```

## 17. GitHub readiness checklist

- [x] LICENSE, .env.example, CONTRIBUTING.md, portable README/docs and explicit publication exclusions.
- [x] Audited public export: private sessions/raw workspaces/models/caches/personal paths excluded; failures retained and projected.
- [x] Local clean clone → fresh install →162 tests → offline coding/MCP demos; runtime bytes match frozen hashes.
- [x] Windows/Linux Python3.12 Actions configuration for tests/coverage/Ruff/mypy/demos/public scan.
- [x] Frozen source/skill/data hashes, genuine results, paired ablation and known bad-case evidence.
- [ ] Remote GitHub workflow execution and repository publication (not requested/performed).

Final public scan at generation: 130 inventory files,0 findings. Repeat after report/validation projection generation; see final packaging manifest. Pattern audit is not an exhaustive secret detector.
