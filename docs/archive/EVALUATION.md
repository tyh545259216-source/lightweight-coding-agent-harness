# Evaluation
The suite contains 54 versioned tasks: six in each of nine categories, 36 development and 18 held-out.
Task files are frozen after construction; scripts and expected answers are never supplied to real models.
Each run creates a fresh small repository, retains JSONL trace/record, and uses deterministic independent
functional graders. Bug fixes are checked by hidden assertions; test generation must pass correct code
and reject a behavior-changing mutant. Multi-tool tasks require the complete ordered tool chain.
Fault injection and recovery checkpoints are synthetic and explicitly labeled. Safety grades observe outside
sentinels/protected files and actual denied or refused actions. Recovering ambiguous side effects safely
counts as success even when stopped for human reconciliation.

FakeProvider results are SCRIPTED HARNESS REGRESSION, not LLM task-solving ability. Fake tokens are unavailable.
Real benchmark uses local qwen3:1.7b, temperature=0, bounded rounds/latency; failures remain failures.
Five variants share the original loop/security and toggle context, skill discovery/activation and recovery.
When recovery is disabled, recovery checkpoint tasks are unsupported and counted failed; this is a feature
coverage comparison, not a claim that baseline fails ordinary coding. A single model/run is descriptive,
not statistically conclusive; both splits reported, no held-out optimization or test edits after results.
All metric values must come from generated records. Connection failure gives NOT RUN, not invented scores.

## 实测样本和指标口径
完整脚本回归为 54×5；真实 Full 为54，真实五配置消融为固定9类代表任务（development 第一例）。
参见 eval/PROTOCOL.md；不能把9例消融标成54例，也不能声称留出集消融或多模型结论。
UNSUPPORTED 计入 task success 的功能覆盖分母，但不进入实际运行 latency/round/tool/error 均值。
Token 只累加 provider 观测到的计数，响应超时而未返回的 token 不补算；Fake 为 unavailable/null。
Recovery fixture 的 prefix 是 synthetic，真实模型 rounds/tokens 只记录 continuation；rehydrated tool
outcomes 和 cached replay 可进入工具统计，应结合 seeded_checkpoint 字段解释。
安全指标仅观察本套件 sentinel/protected files，不能代表未知攻击的完整 OS 隔离能力。
初始无效 grader 记录与中断 pilot 永久保留并从最终报告排除。derived summary-v2 修正不实际运行
任务的均值分母，保持所有 raw records 原样。
