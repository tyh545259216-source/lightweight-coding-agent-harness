# Real-model ablation v2

Genuine local qwen3:1.7b observations under the frozen protocol in `eval/protocol_v2.json`.
20 development cases (two per category); one observation per task/configuration.
Full reuses matching observations from the50-case development survey. This is not20 new repeat trials.

## Six configurations

- baseline: 5/20 success; input tokens 67889; mean rounds 3.388888888888889; mean agent latency 55.025065161111144s; repairs 0.
- context: 6/20 success; input tokens 57155; mean rounds 2.8333333333333335; mean agent latency 48.80575551111107s; repairs 0.
- verification: 4/20 success; input tokens 54669; mean rounds 3.111111111111111; mean agent latency 56.738752666667s; repairs 7.
- skills: 2/20 success; input tokens 107131; mean rounds 3.888888888888889; mean agent latency 46.81227824999991s; repairs 0.
- recovery: 8/20 success; input tokens 56767; mean rounds 2.65; mean agent latency 36.076583074999874s; repairs 0.
- full: 5/20 success; input tokens 39280; mean rounds 1.95; mean agent latency 78.70183069999993s; repairs 0.

## Context modes

The comparison isolates context with verification/skills/recovery disabled.
- baseline: 5/20; observed input tokens 67889 on 16 tasks; context-limit stops 2; mean rounds 3.388888888888889; latency 55.025065161111144s.
- naive: 6/20; observed input tokens 73458 on 18 tasks; context-limit stops 0; mean rounds 3.5; latency 50.337385366666744s.
- context: 6/20; observed input tokens 57155 on 18 tasks; context-limit stops 0; mean rounds 2.8333333333333335; latency 48.80575551111107s.

Input cap stops before any model call have unavailable usage, not free successful model execution. Reported token totals cover completed responses only; timed-out/cancelled requests can consume unreported tokens. Public records mark complete/partial usage and unobserved model rounds.

## Skill modes

Five Skills-category development cases; exact metadata-selected-set accuracy, not model intelligence.
- baseline: 0/5; selection accuracy 0.0; input tokens 21899; latency 58.44743591999977s.
- skills: 0/5; selection accuracy 1.0; input tokens 28746; latency 60.90857562000019s.
- all_skills: 0/5; selection accuracy 0.0; input tokens 28935; latency 80.97258529999962s.

## Verification and repair

- baseline: bug-fix success 0.0; first canonical post-patch pass 0/0; total repair rounds 0; observed final canonical passes 0.
- verification: bug-fix success 0.0; first canonical post-patch pass 0/4; total repair rounds 7; observed final canonical passes 0.
- full: bug-fix success 0.0; first canonical post-patch pass 1/1; total repair rounds 0; observed final canonical passes 1.

## Interpretation and limits

Paired transitions are stored in ablation.json; they describe this small sample, not statistical significance. A gain concentrated in synthetic context overflow or checkpoint recovery shows harness reliability in those recipes, not general coding intelligence. Verification can block an unverified final answer, but cannot force the model to produce a correct patch or meaningful tests. Skills may add input cost, over-select, or decrease success; all outcomes are retained. A passing canonical test suite is not sufficient for the independent hidden/API/mutant grader.

Capability-relevant tool selection can be high even for invalid arguments, guessed paths or premature completion. Read separate argument/error rates and bad-case evidence. One model, temperature0, no repeat trials and correlated fixtures limit causal/generalization claims. Full development and heldout surveys are not paired with V1 because data/prompt/runtime changed.

Public evidence: eval/public/records_v2.jsonl and bad_cases_v2.jsonl; raw local traces remain preserved, excluded from publication. SHA256 provenance permits local integrity checks.

## Observed mechanism attribution

Raw context failed both synthetic Context Stress cases; naive and managed each passed both. Their total task score ties at6/20, so this sample does not show a success gain from managed summaries/state over naive truncation.
Recovery enables both previously unsupported checkpoint cases. Its additional navigation success is outside the recovery mechanism and should not be attributed to recovery intelligence.
Verification has0 successes on the evaluated coding/Skills categories, as does baseline. Its one lower aggregate success comes from File Navigation, where verification is disabled; this off-target difference cannot establish a harmful repair-loop effect.
Skills modes all scored0/5 on dedicated tasks; selected/all increased reported input tokens. Selected routing matched5/5 expected name sets, but task success stayed0/5; all-loaded intentionally over-selects. Do not interpret its selection penalty as failed discovery.
The50-case Full development survey observed bounded repairs (e.g. word_counts03-04). Its20-case ablation subset recorded0 repair rounds and one canonical pass rejected by mutant grading (pass-only test functions); there is no demonstrated coding success gain in the paired subset.
Single temperature0 runs are not perfectly byte-identical inputs: call IDs and isolated safety/error paths differ; variant ordering, caching and host load can also affect observations. These and the small sample prevent strong causal claims about off-target changes or latency.
