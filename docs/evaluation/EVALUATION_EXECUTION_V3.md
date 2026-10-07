# V3 evaluation execution amendment

Frozen benchmark protocol, prompts, tools, graders and existing results remain unchanged. This amendment changes execution and interpretation only, following the user instruction of 2026-10-06.

## Fixed-budget feasibility stop

QWEN3_4B_FIXED_BUDGET: DEPLOYMENT-INFEASIBLE UNDER CURRENT CPU BUDGET.

Development: 48/50 first-response timeouts (96%), one external interruption and one host recovery safety result. Heldout: 39 first-response timeouts and one host safety result. Real repositories: eight first-response timeouts. Ablation: 39 retained records (33 first-response timeouts, four other stops, two recovery results). One additional interrupted ablation artifact is retained without inventing a model result. The older execution chain had already run heldout before this amendment; those results are preserved and disclosed. Remaining 4b main experiments are not run, not scored as failures.

A requested response with no complete model_received event is MODEL_RESPONSE_TIMEOUT / DEPLOYMENT_BUDGET_TIMEOUT. It is not evidence of planning, navigation or coding inability. Non-streaming transport cannot reveal whether the server was still generating tokens. External interruptions are excluded from model-failure denominators. Recovery fixture success is HarnessSafetySuccess, not ModelCodingSuccess.

## Bounded execution

scripts/run_v3_batch.py executes at most five tasks per process, defaults to three. Diagnostic batches use two tasks. It validates all frozen hashes before running. --resume skips completed attempts, including failures. --task-filter and --start-from restrict execution without changing task selection. Each attempt gets an intent record and a separate fresh workspace. The result is atomically persisted and fsynced immediately after the task. An existing intent without a completed record is annotated as an interruption and never replayed. An exclusive local lock prevents simultaneous batches; stale locks require process and artifact audit before being archived. No automatic lock deletion or uncertain side-effect replay occurs.

The model service was unavailable before the first diagnostic fixture/inference. The preflight event is retained separately. A fresh isolated-preflight-recovery run directory is used for the diagnostic; it is not a retry of an executed model task. No old workspace is reused.

## Capability diagnostic

The same eight tasks declared in protocol_v3_diagnostic.json are used for both models, with model timeout 180 seconds and task timeout 360 seconds, ten rounds, temperature zero and 512 output tokens. This is not a formal benchmark and never replaces the main data.

## Observational transport

scripts/v3_observed_provider.py preserves the original non-streaming request and parsed model response. It records request start/end, first HTTP body chunk, complete tool-call response, response latency, observed usage and wire reasoning metadata. HTTP body chunks are not model tokens: TTFT and pure generation tokens/second remain UNAVAILABLE. Provider-reported completion tokens divided by response latency are explicitly an end-to-end rate. Missing token usage is never replaced with zero. reasoning_effort=none and /no_think are requests, not proof that reasoning was disabled; no native think parameter is added to the frozen payload.

No model downloads, remote repository creation, publication or push are authorized.

Instrumentation format2 distinguishes completed responses from partial HTTP bodies. Earlier format1 observations are retained unchanged: their response_timeout_observation field used PARTIAL_HTTP_BODY_RECEIVED whenever any body was seen, including COMPLETE rows. Interpret status=COMPLETE and response_body_end as complete reception, not a partially generated call. This metadata label correction changes no request or model response.
