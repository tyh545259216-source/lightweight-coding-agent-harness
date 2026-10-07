# Default configuration

RECOMMENDED_DEFAULT_CONFIG: see observed development and stability evidence below.
仅用1.7b development机制对照及预定重复试验选推荐配置：GATE_V3 coding 0/8，FULL_V3 coding 0/8；repeat-core mean success 0.11/0.17。推荐 GATE_V3；强制 prefer_patch 不默认强制，hash/context patch能力仍可用。这是小样本实用选择，不是统计显著性结论，不使用heldout调参，也不重跑heldout替换成绩。
Observed repeat-core mean Task Success: {'FREE_LOOP': 0.16666666666666666, 'OBSERVATION_FIRST': 0.1111111111111111, 'GATE_V3': 0.1111111111111111, 'FULL_V3': 0.16666666666666666}. GATE_V3 is a guarded coding-workflow recommendation for bounded completion checks, not the empirically highest task-success configuration. FREE_LOOP/Full have higher observed repeat success in this small subset; Full patch preference has insufficient coding evidence. Safety reasons justify the gate; success improvement is NOT VERIFIED. Noncoding workflows can explicitly omit the coding gate.

- Permission: ON for explicit capability boundaries; not an OS sandbox.
- Durable recovery: ON to prevent uncertain side-effect replay.
- Bounded argument retries: ON to bound repeated invalid calls; task-success gain NOT VERIFIED.
- Observation-first: ON as an auditable edit guard with acceptable local implementation cost; success gain NOT VERIFIED; same-response read/edit limitation remains.
- Bounded repository navigation: ON as bounded map/search capabilities, invoked on demand. Auditable path evidence is the reason for accepting bounded schema/output cost; larger metadata cost and single-task negative result retained; superiority NOT VERIFIED. This is a practical cost judgment, not a measured speedup.
- Patch capability: AVAILABLE; force-patch preference OFF by default when evidence insufficient; Full is not presumed best.
- Verification gate: ON for explicit coding workflows to guard completion; does not prove hidden grader success.
- Managed context: ON as hard-budget/pair-integrity protection; semantic evidence retention remains PARTIAL.
- Skills: optional/on-demand; no demonstrated V3 success benefit.
- Models: 1.7b is practical for this CPU budget; neither model is recommended for unsupervised reliable coding.
- Frozen source/CLI defaults and benchmark unchanged. This is an explicit deployment recommendation, not a rewritten benchmark configuration.
