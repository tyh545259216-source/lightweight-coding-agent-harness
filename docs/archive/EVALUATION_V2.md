# Benchmark v2 protocol

V1's54 tasks/results stay unchanged. V2 has50 development and40 heldout cases
(10 categories,5/4 each), with SHA256 frozen in eval/tasks/v2/manifest.json.
Heldout coding APIs differ from development; safety, recovery, and synthetic
context recipes remain structurally correlated. This small deterministic suite
is not a broad industry benchmark. Never tune prompts/rules from heldout scores.

A shared evaluator materializes a fresh workspace per task/variant, uses the
same runner/executor and records raw traces, grades and provider usage. Fixture
hidden checks and reference patches are never sent to real providers. They are
used only by independent graders and privileged FakeProvider regression.

Grading: read tasks require all specified actual read paths plus answer evidence;
fixes preserve AST function parameters/defaults, pass independent behavior checks,
produce collected regression tests that pass the candidate and reject a buggy
mutant, and observe passing agent tests. Test generation must preserve production
source and reject the mutant. Multi-tool additionally requires an ordered successful
chain. Permission tasks use outside/protected sentinels and refusal evidence.
Recovery seeds a disclosed checkpoint prefix; disabled recovery is UNSUPPORTED.
Actual process-crash recovery is separately tested in integration tests.

Metrics: task success includes unsupported cases in the denominator (capability
coverage), with executed counts reported separately. Bug-fix success includes
Skills tasks whose effective kind is Bug Fix. Tool selection accuracy is a declared
category-relevant capability fraction over **model-origin calls**, not optimal
planning accuracy. Argument/tool error rates use all attempted executions;
host verification calls are counted separately in raw stats. Skill accuracy uses
exact selected-name-set agreement on Skills cases only. Input/output token totals
include only provider-reported observations; absent usage is null, never zero.
Latency is agent time on observed runs, excluding independent grading. Token totals cover completed responses only: requests ending in timeout/cancellation may consume unreported tokens. Published derivatives count complete/partial usage and unobserved response rounds.

Experimental resource policy: qwen3:1.7b, temperature0, max output512,
reasoning_effort none,10 model rounds,60s model timeout,120s task timeout,
UTF-8 byte-proxy context16384 with1024 reserve, tool output5000 chars,
canonical verification paths ['.'], maximum2 repair rounds. NoCompaction is also
subject to the same input cap. Synthetic Context Stress may therefore stop before
any model call; its null token usage must be distinguished from cost savings.

Six ablations: baseline (raw context), context (managed), verification, skills
(metadata-selected), recovery, full (all enhancements). Three context and skill
comparisons isolate their toggles; all use identical tasks/configuration. Preserve
failed experiments. Real model success never derives from FakeProvider scores.

Commands: `python -m mini_harness.evaluation.evaluator --dataset v2 --provider
ollama --variants full --split development --model-timeout 60 --task-timeout 120
--output eval/results/v2-development`; use a new output directory for every run.
