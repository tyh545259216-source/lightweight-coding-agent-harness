# Evaluation evidence

The project separates AgentTaskSuccess, ModelCodingSuccess and HarnessMechanismSuccess. No combined real/synthetic success rate is reported.

- Real-repository tasks: qwen3:1.7b **0/8**; qwen3:4b **0/8**, with severe fixed-budget first-response latency on CPU.
- Wider-budget diagnostic: **0/8 per model**. 1.7b made41 tools/no timeout;4b made2 tools/four timeouts. Neither demonstrated reliable autonomous coding.
- Six-task stability:72 completed outcomes plus one separately retained external interruption. Coding success0/36.
- Independent1.7b standalone development/heldout/context/skills groups were NOT RUN under the final closeout scope; the120-record development mechanism comparison is a different experiment.

[Final V3 report](FINAL_REPORT_V3.md) · [Real repository](REAL_REPO_EVAL.md) · [Stability](STABILITY_ANALYSIS.md) · [Model comparison](MODEL_COMPARISON.md) · [Mechanisms](V3_MECHANISM_ANALYSIS.md) · [Default rationale](DEFAULT_CONFIGURATION.md) · [Historical ablation](ABLATION.md).

Raw traces/sessions/private workspaces are excluded. Safe numeric projections are under [eval/public/v3](../../eval/public/v3). The [evaluation philosophy](../EVALUATION_PHILOSOPHY.md) explains why runtime enforcement and model intelligence need separate evidence.
