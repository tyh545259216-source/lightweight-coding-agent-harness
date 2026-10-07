# V3 behavior optimization plan

V2 baseline commit: a0f6759. Branch: v3-behavior-optimization.
V2 reports, public/raw outcomes, frozen task data and graders remain immutable.
No multi-agent feature, WebUI, planner framework, RAG/database or OS sandbox.
Each phase records implementation, meaningful validation and empirical limits here.

- [x] K: V2 audited130-file baseline committed; private4799-file evidence hashes preserved locally. Dedicated branch created. Existing V2 archive retained.
- [x] L: configurable observation-first policy, trusted evidence, structured replanning, tests and real comparison.
- [x] M: bounded repository map/symbol search and explicit read coverage metadata.
- [x] N: structured validation errors and bounded retry accounting.
- [x] O: preconditioned patches, preview/no-op/stale checks.
- [x] P: policy-specific completion verification and external independent checks.
- [ ] Q: compact/full optional skills; same three skill names.
- [ ] R: evidence-retaining managed context and request inspection trace.
- [ ] S: installed model/resource check, approved stronger-model comparison.
- [x] T: separately attributed/pinned lightweight real repositories.
- [x] U: repeated controlled runs; variance/range and incomplete token usage.
- [x] V: evidence-based default configuration rationale.
- [x] W: honest public presentation and quantitative highlights.
- [ ] X: fresh clone/local checks, actual remote Windows/Linux CI, final report.

Resource precheck: installed inference model only qwen3:1.7b; nomic-embed-text is embedding-only. Physical memory15.79GiB, available5.28GiB at observation,8 logical processors. User authorized qwen3:4b download to D drive. Download is in progress under work/ollama-models-v3, using a separate local Ollama daemon on port11435; system model storage is unchanged. Remote repository destination is not yet supplied; remote CI cannot be claimed before observed completion.

L implementation validated:58 observation/runner/verification/security/recovery tests passed; mypy49 source files passed. Two initial test-fixture wiring failures corrected; the default temporary-directory permission issue was resolved by using a workspace-local pytest base. Real free-loop/observation comparison remains pending frozen V3 protocol.

M implementation validated:56 navigation/observation/tools/security tests pass; Ruff and mypy50 source files pass. No V2 grader/fixture/report changes. Same-task navigation outcome comparison remains pending.

N implementation validated:75 structured-error/navigation/observation/tools/MCP/security tests pass. Schema, range and confirmed missing-path hints are bounded; repeated identical invalid calls are limited, corrected calls are model-produced. Policy feedback fields preserved; legacy missing-path outer error_type remains execution, with detailed path_not_found classification. V2 tests preserved. Real recovery/error-rate comparison pending.

O implementation validated:52 patch/verification/tools/observation/argument tests pass; mypy53 source files pass. Windows CRLF fixture hashes corrected to hash actual bytes, with explicit CRLF preservation regression. No V2 fixture/grader weakening. Patch/API/no-op/stale empirical metrics pending.

P implementation validated:41 completion/verification/patch/process-crash/recovery tests pass. Explicit changed-target/current-test/host-check gate and bounded independent-failure repair added. Fresh-bytecode canonical tests fix a demonstrated runtime stale-test hazard; CRLF-only changes do not count as substantive completion. V2 scores/grader preserved. Empirical verified-completion rates pending.

Q implementation validated:22 compact/full/legacy-skill/context tests pass. Same three metadata names/descriptions; original full bodies retained as on-demand references and in V2 commit. No automatic activation in the planned V3 default. Real compact/full token comparison pending.

R implementation validated:31 context/skill/session tests pass; Ruff/mypy54 source files pass. MANAGED_V3 pins current source/map/failure exchanges and silently records request projections. V2 naive/managed observations unchanged. Full pre-experiment acceptance is running; all empirical phase comparisons still pending.

2026-10-06: host independent grading now receives a deep snapshot of completed evidence, preventing an unfinished host tool pair from contaminating graders. Eleven completion tests pass; Ruff and mypy57 pass. Full acceptance is running. Real-repository recipes and V3 CLI implemented; empirical outcomes remain pending.

Pre-evaluation protocol frozen at eval/protocol_v3.json: 69 runtime/skill/dataset/driver hashes. Prespecified model batches: development50, heldout40, ablation120, context60, skills15, real-repository8, independent repeat-core72 records per model. Six repeat-core task IDs were selected by category before results, to bound CPU-only cost; no reused trials. No real V3 model results yet.

Full local acceptance:228 tests passed in182.06s, statement coverage about89% (exact JSON at eval/results/coverage-v3-validation.json); Ruff source/tests/examples and mypy57 source files passed. Subsequent metric-only adapter checks:9 behavior/real-repository tests passed.

S download completed2026-10-06: qwen3:4b Q4_K_M, model size2497293931 bytes, digest359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7, stored entirely under D-drive work/ollama-models-v3. First actual loading/generation succeeded; a16-token smoke response did not follow the requested OK-only instruction, so this is transport/loading evidence only. No intelligence score inferred. First frozen genuine V3 batch started:4b real-repository8 tasks.
2026-10-06 execution amendment (supersedes earlier execution status): user prohibited GitHub publication/push/remote creation and further model downloads. Existing main protocol/data remain frozen. The former long process chain was stopped; 137 qwen3:4b records and one additional interrupted artifact are preserved. Development first-response timeouts48/50=96%, so qwen3:4b fixed-budget main is DEPLOYMENT-INFEASIBLE UNDER CURRENT CPU BUDGET and remaining main groups are NOT RUN, not model failures. Heldout had already completed before the amendment and is retained. Recovery safety passes are HarnessMechanismSuccess, not ModelCodingSuccess. Independent eight-task diagnostic uses unchanged shared180/360 budgets, in two-task durable batches. New non-streaming instrumentation leaves TTFT/generation tokens/s UNAVAILABLE. Five execution-observation/atomic persistence/concurrency tests pass; full final acceptance still pending. See docs/EVALUATION_EXECUTION_V3.md and work/V3_LOCAL_PENDING.md. Phase X remote operations are explicitly skipped, not waiting for a destination.

V3 LOCAL COMPLETED: 1.7b authorized closing groups complete; unrun development/heldout/context/skills groups explicitly NOT RUN. Preserved early-stopped 4b main evidence, independent diagnostic, repeated runs, coverage and local audits completed. Empirical negative findings and causal limitations are reported in FINAL_REPORT_V3.md. Phase X remote creation/push/CI explicitly skipped by user; no remote operations performed.
Q/R/S: PARTIAL empirical scope. Independent V3 Skills/Context contrasts and standalone1.7b development/heldout NOT RUN under final closeout authorization;4b main stopped by deployment feasibility.






