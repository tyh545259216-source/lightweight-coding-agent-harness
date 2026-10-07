# Stability analysis

VERIFIED: 72 prespecified attempts, six unchanged tasks, four configurations, three runs each. AgentTaskSuccess is separate from HarnessMechanismSuccess. No Permission/Recovery tasks occur in this six-task subset. Repeated outcomes are not replacements for official main results. One additional FULL_V3 repeat-2/v2-dev-05-01 attempt was externally interrupted and permanently retained outside these 72 completed outcomes; it is not a model failure. Its scheduled run was executed once in a fresh isolated fixture, without replay of the uncertain old workspace. Total attempts including that interruption: 73.

## FREE_LOOP

Per-run successes: [1, 1, 1]; rates: [0.16666666666666666, 0.16666666666666666, 0.16666666666666666]. Mean Task Success 0.1667; min/max 0.1667/0.1667. Coding Success 0/9 (0.00%).
Timeouts 1; context_limit 6; repair_exhausted 0; empty_response 0. Mean model rounds 3.222; mean model tool calls 6.222; mean latency 52.322s.
Provider usage observed records 18/18; complete 17/18; partial 1/18. Observed prompt/completion sums 96541/5056; missing usage is UNAVAILABLE, never zero. Partial sums are lower bounds, not comparable total task token costs.

## OBSERVATION_FIRST

Per-run successes: [1, 0, 1]; rates: [0.16666666666666666, 0.0, 0.16666666666666666]. Mean Task Success 0.1111; min/max 0.0000/0.1667. Coding Success 0/9 (0.00%).
Timeouts 0; context_limit 4; repair_exhausted 0; empty_response 0. Mean model rounds 3.500; mean model tool calls 6.389; mean latency 48.349s.
Provider usage observed records 18/18; complete 18/18; partial 0/18. Observed prompt/completion sums 110987/4920; missing usage is UNAVAILABLE, never zero. Partial sums are lower bounds, not comparable total task token costs.

## GATE_V3

Per-run successes: [0, 1, 1]; rates: [0.0, 0.16666666666666666, 0.16666666666666666]. Mean Task Success 0.1111; min/max 0.0000/0.1667. Coding Success 0/9 (0.00%).
Timeouts 1; context_limit 4; repair_exhausted 3; empty_response 1. Mean model rounds 2.944; mean model tool calls 5.500; mean latency 57.061s.
Provider usage observed records 18/18; complete 17/18; partial 1/18. Observed prompt/completion sums 93614/3893; missing usage is UNAVAILABLE, never zero. Partial sums are lower bounds, not comparable total task token costs.

## FULL_V3

Per-run successes: [1, 1, 1]; rates: [0.16666666666666666, 0.16666666666666666, 0.16666666666666666]. Mean Task Success 0.1667; min/max 0.1667/0.1667. Coding Success 0/9 (0.00%).
Timeouts 1; context_limit 6; repair_exhausted 2; empty_response 0. Mean model rounds 2.944; mean model tool calls 6.000; mean latency 60.008s.
Provider usage observed records 18/18; complete 17/18; partial 1/18. Observed prompt/completion sums 91858/4324; missing usage is UNAVAILABLE, never zero. Partial sums are lower bounds, not comparable total task token costs.

## Fixed-task stability

- v2-dev-01-01: 0/12 (0.00%); per-configuration successes {'FREE_LOOP': 0, 'OBSERVATION_FIRST': 0, 'GATE_V3': 0, 'FULL_V3': 0}; stop states {'final_answer': 12}.
- v2-dev-02-01: 0/12 (0.00%); per-configuration successes {'FREE_LOOP': 0, 'OBSERVATION_FIRST': 0, 'GATE_V3': 0, 'FULL_V3': 0}; stop states {'final_answer': 12}.
- v2-dev-03-01: 0/12 (0.00%); per-configuration successes {'FREE_LOOP': 0, 'OBSERVATION_FIRST': 0, 'GATE_V3': 0, 'FULL_V3': 0}; stop states {'context_limit': 12}.
- v2-dev-04-01: 0/12 (0.00%); per-configuration successes {'FREE_LOOP': 0, 'OBSERVATION_FIRST': 0, 'GATE_V3': 0, 'FULL_V3': 0}; stop states {'context_limit': 6, 'final_answer': 4, 'empty_response': 1, 'max_repair_rounds': 1}.
- v2-dev-05-01: 0/12 (0.00%); per-configuration successes {'FREE_LOOP': 0, 'OBSERVATION_FIRST': 0, 'GATE_V3': 0, 'FULL_V3': 0}; stop states {'timeout': 3, 'final_answer': 3, 'context_limit': 2, 'max_repair_rounds': 4}.
- v2-dev-06-01: 10/12 (83.33%); per-configuration successes {'FREE_LOOP': 3, 'OBSERVATION_FIRST': 2, 'GATE_V3': 2, 'FULL_V3': 3}; stop states {'final_answer': 12}.
