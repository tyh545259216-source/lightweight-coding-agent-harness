# Reading the V2 additions

1. Start with eval/analysis/FAILURE_ANALYSIS.md and its evidence. Separate observed failures from hypotheses.
2. Follow agent/verification.py policy → state → TestOutcome → observe → dirty/ready/exhausted. Then read runner.py integration and tests/test_verification.py.
3. Follow context/manager.py message_groups → truncate_output → execution_state → priority/drop projection. Compare modes and tests/test_context_v2.py. Durable history is not the projected context.
4. Follow skills/discovery.py metadata → loader.select/configure/activate → runner pinned injection and saved names. Read tests/test_skills_v2.py.
5. Follow evaluation/tasks.py TaskV2 → v2.fixture_v2 → evaluator.run_task → v2.grade_v2. Identify which reference data never reaches a real provider.
6. Read independent API/behavior/test/mutant checks and tests/test_evaluation_v2.py before trusting success rates.
7. Inspect eval/protocol_v2.json and scripts/run_experiments_v2.py. Explain identical resources, fixed subsets and explicit Full reuse.
8. Follow scripts/collect_results_v2.py raw hashes → metrics/projection → bad cases → docs/ABLATION.md. Explain partial token observations after a timeout.
9. Read public_audit.py inventory and exclusions before packaging. Trace hashes without raw bytes are provenance references, not publicly verifiable full transcripts.
10. Finally read FINAL_REPORT_V2.md and discuss what is implemented, partial and unimplemented. Do not turn scripted regression or synthetic safety/recovery success into broad model intelligence claims.
