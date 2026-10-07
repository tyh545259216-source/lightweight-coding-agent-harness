# Implementation plan
Target: repository root. Initial inspection: directory existed and was empty.
Develop phase-by-phase, run tests before progressing, preserve raw evaluation evidence.
## Phases
- [x] Phase 0: scaffold, architecture, Git, environment.
- [x] Phase 1: typed protocol, bounded loop, FakeProvider, errors/cancellation/usage.
- [x] Phase 2: registry/executor and seven built-in tools.
- [x] Phase 3: bounded context, atomic call/result grouping, durable JSONL session.
- [x] Phase 4: workspace/permission guards, execution intent/result journal and recovery.
- [x] Phase 5: skill metadata discovery, lazy activation, two examples.
- [x] Phase 6: legacy MCP 2025-06-18 stdio client, unified registry, runnable fixture server.
- [x] Phase 7: JSONL tracing, 54 tasks in dev/heldout, independent graders and metrics.
- [x] Phase 8: Ollama compatibility and actual integration smoke.
- [x] Phase 9: scripted and real-model benchmark, five ablation configurations.
- [x] Phase 10: documents, >=30 interview questions, full validation and final report.
## Validation log
Entries will be appended after each successful phase.

- Phase 0: Scaffold validated; Python 3.12.14 venv, public dependencies installed; empty target initialized as Git repo.

- Phase 1: 13 pytest cases passed: zero/one/multiple calls, errors, bounds, cancellation and timeout.


- Phase 2: 28 pytest cases passed; seven built-ins, strict validation, fixed argv, atomic exact edits and actual nested pytest verified.

- Phase 3: 39 pytest cases passed; context groups, truncation, compaction, overflow, torn JSONL and session continuation verified.

- Phase 4: 57 pytest cases passed; Windows junction escape, default-deny grants, single-writer lease, cached execution, in-doubt block and pending-turn recovery verified.

- Phase 5: 67 pytest cases passed; metadata-only discovery, lazy activation/cache, invalid frontmatter, body limits and model-selected activation verified.

- Phase 6: 77 pytest cases passed; real stdio fixture initialization/discovery/call, external schema, host grants, transport failures and cleanup verified.

- Phase 7: 91 pytest cases passed before provider phase; frozen 54 tasks, independent mutant/functional graders, traces and ablation toggles implemented. Initial CLI benchmark exposed relative-output path error; preserved as INVALID_GRADER_RUN and will rerun after fix.

- Phase 8: 100 offline pytest cases passed at provider validation; live Ollama returned genuine structured calls and reported usage. Initial and follow-up repository search tasks failed model grading; integration works but success is not claimed. Official thinking control probe recorded.

- Phase 9 (2026-10-05 Asia/Shanghai): final scripted regression 270 records: baseline/context/skills 48/54, recovery/full 54/54; recovery-disabled six cases UNSUPPORTED, not model failures. Earlier genuine qwen3:1.7b Full survey 18/54 (12/36 dev, 6/18 heldout), explicitly pre-final-hardening. Final-source controlled 9-case five-variant ablation: 1/9, 2/9, 1/9, 3/9, 3/9. Interruption preserved 39 records and partial old Full/04-01; six tasks continued in fresh directories, merged with exact code/task/model/config checks. Scripted and final real ablation source hashes match all46 source files. Guided live preset-patch integration succeeded: actual read/edit/pytest, 2 model rounds, 3 successful tools. Autonomous coding remains PARTIAL.
- Phase 10 (2026-10-05 Asia/Shanghai): final acceptance 125 passed in33.43s; line coverage89.97%, combined87.52%; runtime core line94.13%, combined91.52%, branch82.16%. Ruff check and format pass (63 files); mypy pass (46 source files); report/package/merge scripts also pass Ruff. Latest validation under eval/results/validation-final, earlier evidence retained. Eleven docs,42 interview questions,8 call chains plus actual tree/status/metrics/limits/learning order in FINAL_REPORT. All stages complete as scoped implementation/measurement work; model intelligence, OS sandbox and full MCP are explicitly limited, not claimed complete.

## V2 upgrade — 2026-10-05

V1 results and heldout stay immutable. New v2 development/heldout files will be separate; no prompt/rule tuning on v2 heldout. No WebUI, multi-agent additions or self-built OS sandbox. Every phase records checks and changes before progressing.

- [x] Phase A: review all54 actual traces; explicit failure taxonomy/CSV/evidence and recommendations before runtime changes.
- [x] Phase B: bounded permission-gated verification/repair with real test outcomes, telemetry and success/failure/limit tests.
- [x] Phase C: context v2 priority/recent-turn/pair/rolling-summary/execution-state retention and three experimental modes.
- [x] Phase D: three practical skills, lazy activation/injection and no/selected/all comparison.
- [x] Phase E: unified local/MCP executor audit and minimal demo; bounded transport scope.
- [x] Phase F: separate50 development/40 heldout v2 cases, independent graders, richer metrics, frozen protocol.
- [x] Phase G: six configurations with identical tasks/model/config/limits; raw outcomes and ablation.json/docs.
- [x] Phase H: public-file security audit, exclusions preserving private bad cases, license/env/contributing/CI, clean-clone checks.
- [x] Phase I: honest README rewrite with architecture diagram and verified reproduction instructions.
- [x] Phase J: final tests/coverage/lint/types/Ollama/heldout/ablation/security and FINAL_REPORT_V2.md.

Phase A in progress: runtime and54 raw traces hash-snapshotted; all36 failed tasks and18 successful tasks reviewed. Earlier03-01 attribution corrected: hidden_exit=0, but observedpytest exit=5 and agent_tests_passed=False; changing the signature exposes a v1 grader gap, not an observed hidden assertion failure.

Phase A complete:54 real traces audited,36 failed rows/11fields; PLANNING15, EDIT_QUALITY9, TOOL_ARGUMENT4 and FILE_NAVIGATION4 tie. Nine tasks observed no-tests exit5; all18 coding tasks lacked successful tests; zero skill activations. Source/trace SHA checks prove no behavior or raw evidence change. Related evaluation tests passed; artifacts at eval/analysis. Next phase is justified by failed verification across all18 coding tasks, not inferred context/permission failures.

Phase B complete: optional VerificationPolicy with canonical test paths, bounded repair rounds, structured no-tests/assertion/collection/tool failure, bounded head+tail output, revision invalidation, telemetry and trace events. CLI --verify requires explicit existing permissions. Saved requirements/revisions refuse weakened resume; cached test effects are not reexecuted; rejected textual final cannot bypass verification after restart.53 runner/security/recovery/CLI tests passed, plus17 verification/process-crash regression tests after origin bookkeeping change. Ruff/types pass. Changes recorded in docs/VERIFICATION.md; default legacy loop remains without verification.

Phase C complete: three bounded modes, indivisible exchanges, current-turn recent retention, trusted skill priority, structured head/tail truncation, lossy rolling summary and observed execution ledger.20 context/session tests pass;31 context/verification tests passed before adjusting a test pressure budget. Types pass; Ruff import cleanup complete. Docs synchronized; comparisons deferred to actual phase G runs.

Phase D complete: three reviewed practical bodies; transparent metadata-only selector, no/selected/all modes, lazy model activation and pinned injection in all context modes. Saved names support resume and cached activation.35 skill/context/runner/CLI tests pass; mypy pass. Skills comparisons will run under frozen experiment protocol.

Phase E complete:33 MCP/security tests pass; actual stdio demo completes. Same executor validation/host grants/journal/result confirmed. Latest 2026-07-28 official transport/protocol docs checked; optional latest/HTTP expansion deferred because a transport wrapper alone cannot satisfy changed protocol semantics. Legacy scope explicitly documented.

Phase F complete: separate immutable50/40-task dataset, distinct coding APIs across splits, shared evaluator dispatch, required-path evidence, AST API preservation, hidden checks and candidate-pass/mutant-reject regression grading.13 V2 tests and32 legacy evaluation/tool tests pass. Rich metrics/denominators documented; source/task/model/resource protocol frozen before real experiments.

Phase G complete:181 genuine local-model records, fixed20-case six-way ablation,20-case context and5-case skills comparisons. Full development12/50; ablation baseline5/context6/verification4/skills2/recovery8/full5 of20; skills modes0/5 each. All source/data hashes and configs checked; Windows path separators normalized in the derivative collector without modifying raw evidence. Public projections include partial usage accounting, candidate bad-case code and raw SHA provenance. No improvement assumed or negative result hidden.

Phase H complete: public inventory/exclusions, MIT license/env/contributing, Windows/Linux CI workflow and scanner/export scripts.3 publication tests pass (locations-only secret findings, private evidence preservation, junction escape exclusion). Initial base-junction scan omission fixed; failed initial export retained privately. Audited122-file export committed only as a technical local fixture and clean-cloned; fresh locked install via public PyPI succeeded.162 tests passed in58.41s; actual offline coding/MCP demos and cloned public audit pass. Runtime hashes byte-identical. .gitattributes preserves frozen bytes across platforms. Remote CI configured, not executed; no GitHub publication.

Phase I complete: README first screen defines scope/why/architecture/features, all requested sections and Mermaid, verified quick-start workspace sequence and honest measured/partial limits. Architecture/loop/skills docs synchronized; V2 reading/interview additions. Relative doc links verified except intentionally pending J report; public125-file scan clear, Ruff/format/mypy pass. No runtime/source/heldout changes.

Phase J complete: final162 tests pass (0 skipped/failures); Ruff check/format pass (72 source/test/example files), mypy48 source files pass. Core statement94.74%, independent branch85.12%, combined92.46%; all-code statement91.22%, branch82.48%, combined89.15%. Frozen-source real Full development12/50 and heldout12/40; coding categories remain0, no heldout tuning. Six-variant paired ablation, three context modes and three skill modes measured; negative outcomes and partial token usage retained. Genuine read-only smoke failed understanding after a successful read; separate three-tool toy arithmetic coding smoke passed actual read/edit/canonical tests and independent behavior/API checks, with no general coding claim. FINAL_REPORT_V2 records all17 requested sections. Public security inventory has no findings; private evidence and V1 archives remain preserved. Final audited ZIP/manifest provide the publication snapshot; remote GitHub publication/CI not performed.

V3 authorized local closeout: complete mechanism120, repeat72, real8/model, diagnostic8/model and final local acceptance. Separate1.7b development/heldout/context/skills NOT RUN;4b fixed-budget early stop retained. Remote publication/CI NOT RUN. See FINAL_REPORT_V3.md and PLAN_V3.md.




