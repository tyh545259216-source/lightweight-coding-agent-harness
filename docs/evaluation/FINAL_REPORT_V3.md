# FINAL_REPORT_V3

Status definitions: IMPLEMENTED = present code; VERIFIED = direct matching evidence; PARTIAL = limited evidence/scope; NOT VERIFIED = unproved; NOT IMPLEMENTED = absent; NOT RUN = omitted execution. No frozen benchmark input or existing result was modified.

## 1. Executive Summary

235 local tests; core statement 93.21%/branch 83.20%; whole statement 89.02%/branch 77.61%. Repeat72/72; mechanism120; real8/model; diagnostic8/model. Negative coding outcomes retained. Latest authorized closeout: only remaining 32/72 repeated attempts were run. Original frozen plans remain unchanged. qwen3:1.7b standalone development50, heldout40, context60 and skills15 are NOT RUN. Development mechanism comparison120 is complete and separately reported; it does not substitute for the missing Full development benchmark. Existing4b development/heldout results are retained; unmatched incomplete model comparison cannot establish superiority.

## 2. Project Positioning

Explainable, independently implemented and testable coding-agent harness. Research/learning project; model intelligence and runtime safeguards are evaluated separately.

## 3. Final Architecture

IMPLEMENTED / VERIFIED（本地测试）：Runner 仍编排原有循环；Provider 仅传输；Executor 统一 schema、权限、journal 和 evidence。新增 observation-first、结构化错误与重试记账、范围读取/repository_map/symbol_search、预条件 apply_patch、完成验证、compact/full skill、MANAGED_V3 上下文。没有引入 agent framework、Multi-Agent、WebUI、RAG 或 OS sandbox。

V2 frozen fixtures、grader、heldout 和记录不变；V3 通过 adapter 使用它们。V2 legacy Multi-tool grader 要求 edit_file 有序链，故该类别保留 edit_file，不能声称它被 patch 对照覆盖。

## 4. V2 → V3 Changes

IMPLEMENTED / VERIFIED（本地测试）：Runner 仍编排原有循环；Provider 仅传输；Executor 统一 schema、权限、journal 和 evidence。新增 observation-first、结构化错误与重试记账、范围读取/repository_map/symbol_search、预条件 apply_patch、完成验证、compact/full skill、MANAGED_V3 上下文。没有引入 agent framework、Multi-Agent、WebUI、RAG 或 OS sandbox。

V2 frozen fixtures、grader、heldout 和记录不变；V3 通过 adapter 使用它们。V2 legacy Multi-tool grader 要求 edit_file 有序链，故该类别保留 edit_file，不能声称它被 patch 对照覆盖。

## 5. Implemented / Verified / Partial / Not Implemented

IMPLEMENTED: V3 runtime mechanisms. VERIFIED: local contract/regression tests and observed outcomes. PARTIAL: model-driven mechanism effectiveness, task data and portability. NOT VERIFIED: reliable autonomous coding, broad generalization, statistical significance. NOT IMPLEMENTED: OS sandbox, full modern MCP feature set, practical thinking-profile experiment. Remote CI NOT RUN.

## 6. Unit & Integration Tests

先前验收：228 passed，whole statement 88.72%。最终验收：235 tests，0 skipped；pytest、Ruff、format、mypy、offline demo、MCP demo 状态均为 VERIFIED（本地）。FakeProvider 测试只证明脚本化 harness 回归，不证明模型智能。没有为覆盖率补充无行为价值的测试。

## 7. Coverage

严格 core runtime（排除 evaluation 和两个 CLI）：statement 93.21%，branch 83.20%。
与 V2 相同过滤口径（排除 evaluation 和 cli.py，包含新增 behavior_cli.py）：statement 92.96%，branch 82.28%。
Whole-project：statement 89.02%，branch 77.61%，语句+分支合并 86.24%。分支覆盖率来自 --cov-branch，未把合并覆盖率当作独立 branch coverage。

## 8. Synthetic Development Benchmark

Latest authorized closeout: only remaining 32/72 repeated attempts were run. Original frozen plans remain unchanged. qwen3:1.7b standalone development50, heldout40, context60 and skills15 are NOT RUN. Development mechanism comparison120 is complete and separately reported; it does not substitute for the missing Full development benchmark. Existing4b development/heldout results are retained; unmatched incomplete model comparison cannot establish superiority.

Development50 与 frozen heldout40 分开。机制 ablation/context/skills/repeats 不混入正式 Full success 分母。Coding 指 Bug Fix/Test Generation/Multi-tool，含 Skills 中的 coding 任务；不要用安全/恢复成功代替 coding success。Recovery checkpoint前缀由host fixture生成；其中安全阻止不确定重放的成功不需要新的模型响应。工具计数可能包含这一前缀，不等同全部由模型新生成。

- qwen3-1.7b development：AgentTaskSuccess N/A（没有可观察机会）；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 0；平均轮数 N/A（0/0 observed）；模型工具调用 0；平均耗时 N/A s（0/0 observed）；外部中断 0；完整 usage 0/0。 Coding N/A（没有可观察机会）。

- qwen3-1.7b heldout：AgentTaskSuccess N/A（没有可观察机会）；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 0；平均轮数 N/A（0/0 observed）；模型工具调用 0；平均耗时 N/A s（0/0 observed）；外部中断 0；完整 usage 0/0。 Coding N/A（没有可观察机会）。

- qwen3-4b development：AgentTaskSuccess 0/40 (0.00%)；HarnessMechanismSuccess 1/9 (11.11%)；timeout 48；平均轮数 0.98（49/50 observed）；模型工具调用 4；平均耗时 58.87 s（49/50 observed）；外部中断 1；完整 usage 0/50。 Coding 0/19 (0.00%)。

- qwen3-4b heldout：AgentTaskSuccess 0/32 (0.00%)；HarnessMechanismSuccess 1/8 (12.50%)；timeout 39；平均轮数 0.97（40/40 observed）；模型工具调用 3；平均耗时 58.60 s（40/40 observed）；外部中断 0；完整 usage 0/40。 Coding 0/15 (0.00%)。

## 9. Held-out Benchmark

Latest authorized closeout: only remaining 32/72 repeated attempts were run. Original frozen plans remain unchanged. qwen3:1.7b standalone development50, heldout40, context60 and skills15 are NOT RUN. Development mechanism comparison120 is complete and separately reported; it does not substitute for the missing Full development benchmark. Existing4b development/heldout results are retained; unmatched incomplete model comparison cannot establish superiority.

## 10. Real Repository Evaluation

两模型各8项，独立于 synthetic 分数；MIT dbader/schedule pinned commit82a43db1b938d8fdf60103bd41f329e06c8d3651。使用明确披露的 curated contract tests，不声称完整上游 suite 或历史 bug。详细逐项结果见 REAL_REPO_EVAL.md。

- qwen3-1.7b：AgentTaskSuccess 0/8 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 1；平均轮数 2.62（8/8 observed）；模型工具调用 36；平均耗时 46.72 s（8/8 observed）；外部中断 0；完整 usage 7/8。

- qwen3-4b：AgentTaskSuccess 0/8 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 8；平均轮数 1.00（8/8 observed）；模型工具调用 0；平均耗时 60.11 s（8/8 observed）；外部中断 0；完整 usage 0/8。

See REAL_REPO_EVAL.md. Never aggregate these with synthetic success.

## 11. qwen3:1.7b vs qwen3:4b

### Model comparison

Fixed-budget and wider-budget diagnostic remain separate. CPU deployment budget incompatibility is not a ranking of model intelligence.
两模型主协议一致：max rounds10、model timeout60s、task timeout120s、output512、temperature0、reasoning_effort none；相同 task IDs、variant、prompt/system、工具定义和 grader。CPU 顺序运行，模型批次顺序/cold cache/共享机器负载是限制。外部turn中断的未完成case单独标INTERRUPTED，单独记录并从模型失败分母排除，不伪装成模型timeout、不给出未观察到的latency，也不重放其已完成写入；外部中断不计为模型失败。Model rounds 包含已发出但未完成的请求；报告 latency 是 runner+外层grader实际耗时，120s限额约束 agent runtime，外层固定grader可能使记录总耗时超过120s。没有因4b较慢放宽主评测。
独立8任务，两模型相同180s模型/360s任务预算，10轮和工具/prompt/grader保持一致；transport190s防止客户端先于180s截断。非正式 benchmark，绝不替换主记录。见 docs/MODEL_CAPABILITY_COMPARISON.md。

qwen3-1.7b: AgentTaskSuccess 0/8 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 0；平均轮数 3.25（8/8 observed）；模型工具调用 41；平均耗时 63.92 s（8/8 observed）；外部中断 0；完整 usage 8/8。

qwen3-4b: AgentTaskSuccess 0/8 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 4；平均轮数 2.00（8/8 observed）；模型工具调用 2；平均耗时 242.22 s（8/8 observed）；外部中断 0；完整 usage 4/8。

4b is severely response-latency constrained in this CPU deployment. Wider 180s model/360s task diagnostic shows speed is not the whole observed problem: complete responses and two tools still produced zero successes, but does not isolate intrinsic inability. 1.7b entered the loop more often (41 tools) without diagnostic task success. Neither model demonstrated reliable autonomous coding on these eight tasks. No claim that 4b is less intelligent or that CPU explains every failure is supported.

### Saved per-case diagnostic observations

- qwen3:1.7b / real-bug-1: success False, stop context_limit, rounds 4, model tools 4, latency 72.03s. Complete first transport response latency 3.8928281999997125; complete tool call latencies [3.8928281999997125, 25.265403600000354, 5.8793523000003916, 36.61442800000077]; location observed True, read coverage 0.21164021164021163, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:1.7b / real-nav-1: success False, stop final_answer, rounds 2, model tools 1, latency 18.24s. Complete first transport response latency 9.019657200000438; complete tool call latencies [9.019657200000438]; location observed True, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:1.7b / v2-dev-01-01: success False, stop final_answer, rounds 2, model tools 4, latency 54.59s. Complete first transport response latency 29.445126399999936; complete tool call latencies [29.445126399999936]; location observed False, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:1.7b / v2-dev-02-01: success False, stop final_answer, rounds 2, model tools 1, latency 10.10s. Complete first transport response latency 4.91377250000005; complete tool call latencies [4.91377250000005]; location observed True, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:1.7b / v2-dev-03-01: success False, stop context_limit, rounds 3, model tools 9, latency 111.72s. Complete first transport response latency 26.353458300000057; complete tool call latencies [26.353458300000057, 42.180565199998455, 40.66670560000057]; location observed True, read coverage 1.0, edit attempts 2, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:1.7b / v2-dev-04-01: success False, stop max_repair_rounds, rounds 3, model tools 9, latency 113.85s. Complete first transport response latency 34.391895900000236; complete tool call latencies [34.391895900000236, 43.85766549999971, 30.32808710000063]; location observed True, read coverage 1.0, edit attempts 3, verification calls 1. TTFT/generation TPS UNAVAILABLE.
- qwen3:1.7b / v2-dev-05-01: success False, stop max_repair_rounds, rounds 3, model tools 7, latency 43.70s. Complete first transport response latency 11.900675700000647; complete tool call latencies [11.900675700000647, 21.56877070000155, 5.1612514999997074]; location observed True, read coverage 1.0, edit attempts 1, verification calls 1. TTFT/generation TPS UNAVAILABLE.
- qwen3:1.7b / v2-dev-06-01: success False, stop final_answer, rounds 7, model tools 6, latency 87.13s. Complete first transport response latency 9.499965399998473; complete tool call latencies [9.499965399998473, 9.860970499999894, 6.3628924999993615, 10.199569899999915, 10.19983030000003, 10.774139900000591]; location observed True, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:4b / real-bug-1: success False, stop timeout, rounds 3, model tools 1, latency 360.06s. Complete first transport response latency 107.12424139999894; complete tool call latencies [104.48909950000052]; location observed True, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:4b / real-nav-1: success False, stop final_answer, rounds 1, model tools 0, latency 117.20s. Complete first transport response latency 117.1565845999994; complete tool call latencies []; location observed False, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:4b / v2-dev-01-01: success False, stop final_answer, rounds 1, model tools 0, latency 141.10s. Complete first transport response latency 141.04470039999978; complete tool call latencies []; location observed False, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:4b / v2-dev-02-01: success False, stop final_answer, rounds 1, model tools 0, latency 121.24s. Complete first transport response latency 121.19251639999948; complete tool call latencies []; location observed False, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:4b / v2-dev-03-01: success False, stop timeout, rounds 3, model tools 1, latency 360.05s. Complete first transport response latency 108.56017209999936; complete tool call latencies [151.24752780000017]; location observed True, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:4b / v2-dev-04-01: success False, stop timeout, rounds 3, model tools 0, latency 360.06s. Complete first transport response latency 111.29333510000015; complete tool call latencies []; location observed False, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:4b / v2-dev-05-01: success False, stop timeout, rounds 3, model tools 0, latency 360.06s. Complete first transport response latency 109.1711964999995; complete tool call latencies []; location observed False, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.
- qwen3:4b / v2-dev-06-01: success False, stop final_answer, rounds 1, model tools 0, latency 117.98s. Complete first transport response latency 117.92821599999934; complete tool call latencies []; location observed False, read coverage 0.0, edit attempts 0, verification calls 0. TTFT/generation TPS UNAVAILABLE.

## 12. Fixed-budget Deployment Analysis

两模型主协议一致：max rounds10、model timeout60s、task timeout120s、output512、temperature0、reasoning_effort none；相同 task IDs、variant、prompt/system、工具定义和 grader。CPU 顺序运行，模型批次顺序/cold cache/共享机器负载是限制。外部turn中断的未完成case单独标INTERRUPTED，单独记录并从模型失败分母排除，不伪装成模型timeout、不给出未观察到的latency，也不重放其已完成写入；外部中断不计为模型失败。Model rounds 包含已发出但未完成的请求；报告 latency 是 runner+外层grader实际耗时，120s限额约束 agent runtime，外层固定grader可能使记录总耗时超过120s。没有因4b较慢放宽主评测。

逐个 timeout 的 trace、最后状态、轮数、工具数、延迟、可观察 usage 和停滞阶段写入 eval/public/v3/timeout_annotations.jsonl；私有完整 traces 保留。MODEL_INFERENCE 表示请求已发出但未收到完整响应；非流式传输不能确认服务器已经生成多少内容或 intrinsic inability。无效循环另记 invalid_loop_observed，不把等待生成混成无效工具循环。

- qwen3-1.7b：timeout 16；stages {'MODEL_INFERENCE': 16}；有重复无效调用证据 0。

- qwen3-4b：timeout 128；stages {'MODEL_INFERENCE': 128}；有重复无效调用证据 0。

Three evidence levels: Model / AgentTaskSuccess, ModelCodingSuccess and timeout classification; Harness behavior / attempted and executed edits, confirmed invalid paths, argument repair episodes, no-op and premature completion; Runtime / journal recovery, permissions, context budgeting, token cost, rounds and latency. Host recovery safety success is HarnessMechanismSuccess, not ModelCodingSuccess. Zero opportunities are UNAVAILABLE rather than evidence of improved behavior.

4b main feasibility stop leaves unrun context, skills and repeats as NOT VERIFIED. Diagnostic observations are separate. reasoning_effort=none and /no_think did not guarantee absence of planning-like output. No native think parameter or streaming change was introduced. finish_reason=length signals budget-truncated output; receiving such text is not successful tool calling. Pure generation tokens/s and TTFT are UNAVAILABLE; observed completion tokens divided by response time is an end-to-end rate only.

## 13. Capability Diagnostic

独立8任务，两模型相同180s模型/360s任务预算，10轮和工具/prompt/grader保持一致；transport190s防止客户端先于180s截断。非正式 benchmark，绝不替换主记录。见 docs/MODEL_CAPABILITY_COMPARISON.md。

## 14. Failure Taxonomy

用户引用的 PLANNING 41.67%、EDIT_QUALITY 25% 来自此前54条 Full trace 中36条失败（较早 V1 证据，被用于 V2/V3 设计），不是 frozen V2 development50 的同任务配对统计。V3 按相同13类 taxonomy 标注已完成记录；1.7b standalone FULL_V3 development50 NOT RUN，机制子集另列；不同数据/预算下不能把比例差当因果改善。MODEL_INFERENCE 等是停滞阶段，PROVIDER 等是失败 taxonomy，二者独立。

qwen3-1.7b：。

qwen3-4b：DEPLOYMENT_BUDGET_TIMEOUT 48/48 (100.00%)。

1.7b Full standalone development is NOT RUN; use the separately labeled mechanism-comparison failure distribution below. No causal V2 percentage-reduction claim is established.

FULL_V3 development mechanism subset failure taxonomy (20 selected tasks, not full50): {'FILE_NAVIGATION': 3, 'PLANNING': 2, 'CONTEXT_LOSS': 3, 'PROVIDER': 3, 'EDIT_QUALITY': 2, 'OTHER': 1}. Same label set retained; deployment timeouts remain separate.

## 15. Observation-first Analysis

该配对仅改变 observation enforce。区分所有尝试与执行成功的写操作；被拒绝的工具调用仍保留。没有调用机会时指标为 N/A，不能宣称策略训练了模型。保护检查发生在工具执行时，同一模型响应可同时提出read和edit，若read先执行成功，后续edit可能被允许；因此另列提案产生时尚无read_file结果的计数，不把执行顺序当作模型已经观察源码的证明。attempt edit-before-read/premature-final的统计仅针对coding tasks，不把恢复fixture前缀写入混进去。

- qwen3-1.7b / FREE_LOOP：AgentTaskSuccess 1/16 (6.25%)；HarnessMechanismSuccess 4/4 (100.00%)；timeout 3；平均轮数 2.45（20/20 observed）；模型工具调用 83；平均耗时 39.49 s（20/20 observed）；外部中断 0；完整 usage 14/20。 edit-before-read attempts 0/18 (0.00%)；confirmed invalid paths 12/74 (16.22%)；premature finals 1/3 (33.33%)。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate 0/18 (0.00%); context-limit avoidance 12/16 (75.00%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 4; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 15358; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 6; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/3；validation error calls 14；recovered episodes 3；unrecovered tool episodes 9。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 2/83 (2.41%); all validated schema/range/path error rate 14/83 (16.87%)；Recovered Argument Episode Rate 3/12 (25.00%)；Repeated Invalid Call Rate 2/14 (14.29%)（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 13/18; executed coding edits before any read 0/4；observation denied edits 0；verified success 0；read coverage 0.56；correct file location 4/6 (66.67%)；first valid file hit 2/6 (33.33%)；已观察输入/输出 token 73561/3726（仅已观察部分）（完整 usage 14/20）。

- qwen3-1.7b / OBSERVATION_FIRST：AgentTaskSuccess 1/16 (6.25%)；HarnessMechanismSuccess 4/4 (100.00%)；timeout 2；平均轮数 2.50（20/20 observed）；模型工具调用 83；平均耗时 39.98 s（20/20 observed）；外部中断 0；完整 usage 15/20。 edit-before-read attempts 0/15 (0.00%)；confirmed invalid paths 8/74 (10.81%)；premature finals 1/4 (25.00%)。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate 0/15 (0.00%); context-limit avoidance 11/16 (68.75%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 5; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 14585; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 6; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/3；validation error calls 12；recovered episodes 2；unrecovered tool episodes 9。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 4/83 (4.82%); all validated schema/range/path error rate 12/83 (14.46%)；Recovered Argument Episode Rate 2/11 (18.18%)；Repeated Invalid Call Rate 1/12 (8.33%)（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 12/15; executed coding edits before any read 0/4；observation denied edits 9；verified success 0；read coverage 0.56；correct file location 4/6 (66.67%)；first valid file hit 2/6 (33.33%)；已观察输入/输出 token 76462/4086（仅已观察部分）（完整 usage 15/20）。

- qwen3-4b / FREE_LOOP: PARTIAL retained evidence (20 records); no complete4b mechanism comparison claim.

- qwen3-4b / FREE_LOOP：AgentTaskSuccess 0/16 (0.00%)；HarnessMechanismSuccess 1/4 (25.00%)；timeout 17；平均轮数 0.85（20/20 observed）；模型工具调用 2；平均耗时 51.08 s（20/20 observed）；外部中断 0；完整 usage 0/20。 edit-before-read attempts N/A（没有可观察机会）；confirmed invalid paths 0/2 (0.00%)；premature finals N/A（没有可观察机会）。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate N/A（没有可观察机会）; context-limit avoidance 14/16 (87.50%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 2; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 6469; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 0; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/0；validation error calls 0；recovered episodes 0；unrecovered tool episodes 0。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 0/2 (0.00%); all validated schema/range/path error rate 0/2 (0.00%)；Recovered Argument Episode Rate N/A（没有可观察机会）；Repeated Invalid Call Rate N/A（没有可观察机会）（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 0/0; executed coding edits before any read 0/0；observation denied edits 0；verified success 0；read coverage 0.00；correct file location 0/6 (0.00%)；first valid file hit 0/6 (0.00%)；已观察输入/输出 token N/A（未收到 provider usage）（完整 usage 0/20）。

- qwen3-4b / OBSERVATION_FIRST: PARTIAL retained evidence (19 records); no complete4b mechanism comparison claim.

- qwen3-4b / OBSERVATION_FIRST：AgentTaskSuccess 0/15 (0.00%)；HarnessMechanismSuccess 1/4 (25.00%)；timeout 16；平均轮数 0.84（19/19 observed）；模型工具调用 2；平均耗时 50.61 s（19/19 observed）；外部中断 0；完整 usage 0/19。 edit-before-read attempts N/A（没有可观察机会）；confirmed invalid paths 0/2 (0.00%)；premature finals N/A（没有可观察机会）。
  Verification completion rate 0/7 (0.00%); detected no-op rejection rate N/A（没有可观察机会）; context-limit avoidance 13/15 (86.67%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 2; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 6477; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 0; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/0；validation error calls 0；recovered episodes 0；unrecovered tool episodes 0。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 0/2 (0.00%); all validated schema/range/path error rate 0/2 (0.00%)；Recovered Argument Episode Rate N/A（没有可观察机会）；Repeated Invalid Call Rate N/A（没有可观察机会）（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 0/0; executed coding edits before any read 0/0；observation denied edits 0；verified success 0；read coverage 0.00；correct file location 0/6 (0.00%)；first valid file hit 0/6 (0.00%)；已观察输入/输出 token N/A（未收到 provider usage）（完整 usage 0/19）。

See docs/V3_MECHANISM_ANALYSIS.md for additional model-origin trace counts, valid-path lower bounds, read-continuation metadata limits, request-state retention and coding full-file-write observations.

## 16. Navigation Analysis

该配对同时改变 read metadata 和 navigation 工具组合，不单独隔离某一个工具。旧read_file没有V3范围metadata，read coverage标N/A而不把缺失metadata当成0读取。Guessed-path 仅指确认不存在的路径，不声称知道模型意图。

- qwen3-1.7b / LEGACY_NAVIGATION：AgentTaskSuccess 2/16 (12.50%)；HarnessMechanismSuccess 4/4 (100.00%)；timeout 0；平均轮数 2.70（20/20 observed）；模型工具调用 72；平均耗时 35.55 s（20/20 observed）；外部中断 0；完整 usage 17/20。 edit-before-read attempts 0/12 (0.00%)；confirmed invalid paths 13/64 (20.31%)；premature finals 1/6 (16.67%)。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate 0/12 (0.00%); context-limit avoidance 13/16 (81.25%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 3; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 14463; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 2; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/6；validation error calls 14；recovered episodes 1；unrecovered tool episodes 8。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 1/72 (1.39%); all validated schema/range/path error rate 14/72 (19.44%)；Recovered Argument Episode Rate 1/9 (11.11%)；Repeated Invalid Call Rate 4/14 (28.57%)（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 10/12; executed coding edits before any read 0/7；observation denied edits 0；verified success 0；read coverage N/A；correct file location 4/6 (66.67%)；first valid file hit 3/6 (50.00%)；已观察输入/输出 token 73051/4430（仅已观察部分）（完整 usage 17/20）。

- qwen3-1.7b / FREE_LOOP：AgentTaskSuccess 1/16 (6.25%)；HarnessMechanismSuccess 4/4 (100.00%)；timeout 3；平均轮数 2.45（20/20 observed）；模型工具调用 83；平均耗时 39.49 s（20/20 observed）；外部中断 0；完整 usage 14/20。 edit-before-read attempts 0/18 (0.00%)；confirmed invalid paths 12/74 (16.22%)；premature finals 1/3 (33.33%)。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate 0/18 (0.00%); context-limit avoidance 12/16 (75.00%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 4; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 15358; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 6; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/3；validation error calls 14；recovered episodes 3；unrecovered tool episodes 9。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 2/83 (2.41%); all validated schema/range/path error rate 14/83 (16.87%)；Recovered Argument Episode Rate 3/12 (25.00%)；Repeated Invalid Call Rate 2/14 (14.29%)（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 13/18; executed coding edits before any read 0/4；observation denied edits 0；verified success 0；read coverage 0.56；correct file location 4/6 (66.67%)；first valid file hit 2/6 (33.33%)；已观察输入/输出 token 73561/3726（仅已观察部分）（完整 usage 14/20）。

- qwen3-4b / LEGACY_NAVIGATION: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-4b / FREE_LOOP: PARTIAL retained evidence (20 records); no complete4b mechanism comparison claim.

- qwen3-4b / FREE_LOOP：AgentTaskSuccess 0/16 (0.00%)；HarnessMechanismSuccess 1/4 (25.00%)；timeout 17；平均轮数 0.85（20/20 observed）；模型工具调用 2；平均耗时 51.08 s（20/20 observed）；外部中断 0；完整 usage 0/20。 edit-before-read attempts N/A（没有可观察机会）；confirmed invalid paths 0/2 (0.00%)；premature finals N/A（没有可观察机会）。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate N/A（没有可观察机会）; context-limit avoidance 14/16 (87.50%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 2; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 6469; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 0; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/0；validation error calls 0；recovered episodes 0；unrecovered tool episodes 0。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 0/2 (0.00%); all validated schema/range/path error rate 0/2 (0.00%)；Recovered Argument Episode Rate N/A（没有可观察机会）；Repeated Invalid Call Rate N/A（没有可观察机会）（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 0/0; executed coding edits before any read 0/0；observation denied edits 0；verified success 0；read coverage 0.00；correct file location 0/6 (0.00%)；first valid file hit 0/6 (0.00%)；已观察输入/输出 token N/A（未收到 provider usage）（完整 usage 0/20）。

See docs/V3_MECHANISM_ANALYSIS.md for additional model-origin trace counts, valid-path lower bounds, read-continuation metadata limits, request-state retention and coding full-file-write observations.

## 17. Tool Argument Repair

两个 V3 组都提供结构化错误，因此这里只隔离重试限额，不单独证明 structured feedback 比旧文本错误更好。恢复按成功纠正的错误 episode 统计，不把错误调用数与 episode 数混用。

- qwen3-1.7b / NO_ARGUMENT_REPAIR：AgentTaskSuccess 1/16 (6.25%)；HarnessMechanismSuccess 4/4 (100.00%)；timeout 0；平均轮数 2.40（20/20 observed）；模型工具调用 88；平均耗时 37.60 s（20/20 observed）；外部中断 0；完整 usage 17/20。 edit-before-read attempts 0/20 (0.00%)；confirmed invalid paths 16/79 (20.25%)；premature finals 1/6 (16.67%)。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate 0/20 (0.00%); context-limit avoidance 12/16 (75.00%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 4; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 15358; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 6; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/6；validation error calls 19；recovered episodes 3；unrecovered tool episodes 12。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 3/88 (3.41%); all validated schema/range/path error rate 19/88 (21.59%)；Recovered Argument Episode Rate 3/15 (20.00%)；Repeated Invalid Call Rate 3/19 (15.79%)（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 16/20; executed coding edits before any read 0/6；observation denied edits 0；verified success 0；read coverage 0.56；correct file location 4/6 (66.67%)；first valid file hit 2/6 (33.33%)；已观察输入/输出 token 80226/3930（仅已观察部分）（完整 usage 17/20）。

- qwen3-1.7b / FREE_LOOP：AgentTaskSuccess 1/16 (6.25%)；HarnessMechanismSuccess 4/4 (100.00%)；timeout 3；平均轮数 2.45（20/20 observed）；模型工具调用 83；平均耗时 39.49 s（20/20 observed）；外部中断 0；完整 usage 14/20。 edit-before-read attempts 0/18 (0.00%)；confirmed invalid paths 12/74 (16.22%)；premature finals 1/3 (33.33%)。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate 0/18 (0.00%); context-limit avoidance 12/16 (75.00%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 4; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 15358; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 6; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/3；validation error calls 14；recovered episodes 3；unrecovered tool episodes 9。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 2/83 (2.41%); all validated schema/range/path error rate 14/83 (16.87%)；Recovered Argument Episode Rate 3/12 (25.00%)；Repeated Invalid Call Rate 2/14 (14.29%)（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 13/18; executed coding edits before any read 0/4；observation denied edits 0；verified success 0；read coverage 0.56；correct file location 4/6 (66.67%)；first valid file hit 2/6 (33.33%)；已观察输入/输出 token 73561/3726（仅已观察部分）（完整 usage 14/20）。

- qwen3-4b / NO_ARGUMENT_REPAIR: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-4b / FREE_LOOP: PARTIAL retained evidence (20 records); no complete4b mechanism comparison claim.

- qwen3-4b / FREE_LOOP：AgentTaskSuccess 0/16 (0.00%)；HarnessMechanismSuccess 1/4 (25.00%)；timeout 17；平均轮数 0.85（20/20 observed）；模型工具调用 2；平均耗时 51.08 s（20/20 observed）；外部中断 0；完整 usage 0/20。 edit-before-read attempts N/A（没有可观察机会）；confirmed invalid paths 0/2 (0.00%)；premature finals N/A（没有可观察机会）。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate N/A（没有可观察机会）; context-limit avoidance 14/16 (87.50%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 2; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 6469; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 0; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/0；validation error calls 0；recovered episodes 0；unrecovered tool episodes 0。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 0/2 (0.00%); all validated schema/range/path error rate 0/2 (0.00%)；Recovered Argument Episode Rate N/A（没有可观察机会）；Repeated Invalid Call Rate N/A（没有可观察机会）（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 0/0; executed coding edits before any read 0/0；observation denied edits 0；verified success 0；read coverage 0.00；correct file location 0/6 (0.00%)；first valid file hit 0/6 (0.00%)；已观察输入/输出 token N/A（未收到 provider usage）（完整 usage 0/20）。

See docs/V3_MECHANISM_ANALYSIS.md for additional model-origin trace counts, valid-path lower bounds, read-continuation metadata limits, request-state retention and coding full-file-write observations.

## 18. Patch Editing

该配对主要改变 prefer_patch；Multi-tool 是 frozen grader 例外。No-op/stale 拒绝是机制保护；signature violation 是可观察破坏代理，不代表所有 destructive edits。

- qwen3-1.7b / GATE_V3：AgentTaskSuccess 2/16 (12.50%)；HarnessMechanismSuccess 4/4 (100.00%)；timeout 4；平均轮数 3.05（20/20 observed）；模型工具调用 88；平均耗时 55.65 s（20/20 observed）；外部中断 0；完整 usage 15/20。 edit-before-read attempts 0/18 (0.00%)；confirmed invalid paths 17/81 (20.99%)；premature finals 0/2 (0.00%)。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate 0/18 (0.00%); context-limit avoidance 13/16 (81.25%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 3; compacted rounds 7; dropped exchange groups 134; max observed byte proxy 15109; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 0; permission denials 6; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/0；validation error calls 19；recovered episodes 1；unrecovered tool episodes 10。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 2/88 (2.27%); all validated schema/range/path error rate 19/88 (21.59%)；Recovered Argument Episode Rate 1/11 (9.09%)；Repeated Invalid Call Rate 5/19 (26.32%)（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 12/18; executed coding edits before any read 0/3；observation denied edits 10；verified success 0；read coverage 0.62；correct file location 4/6 (66.67%)；first valid file hit 2/6 (33.33%)；已观察输入/输出 token 104810/4389（仅已观察部分）（完整 usage 15/20）。

- qwen3-1.7b / FULL_V3：AgentTaskSuccess 2/16 (12.50%)；HarnessMechanismSuccess 4/4 (100.00%)；timeout 3；平均轮数 2.95（20/20 observed）；模型工具调用 87；平均耗时 58.46 s（20/20 observed）；外部中断 0；完整 usage 16/20。 edit-before-read attempts 1/15 (6.67%)；confirmed invalid paths 14/78 (17.95%)；premature finals 3/3 (100.00%)。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate 0/15 (0.00%); context-limit avoidance 13/16 (81.25%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 3; compacted rounds 7; dropped exchange groups 135; max observed byte proxy 15236; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 0; permission denials 2; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/1；no-op拒绝 0；stale拒绝 0；signature violations 0/0；validation error calls 16；recovered episodes 2；unrecovered tool episodes 10。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 2/87 (2.30%); all validated schema/range/path error rate 16/87 (18.39%)；Recovered Argument Episode Rate 2/12 (16.67%)；Repeated Invalid Call Rate 3/16 (18.75%)（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 11/15; executed coding edits before any read 0/3；observation denied edits 7；verified success 0；read coverage 0.56；correct file location 4/6 (66.67%)；first valid file hit 2/6 (33.33%)；已观察输入/输出 token 103088/4103（仅已观察部分）（完整 usage 16/20）。

- qwen3-4b / GATE_V3: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-4b / FULL_V3: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

See docs/V3_MECHANISM_ANALYSIS.md for additional model-origin trace counts, valid-path lower bounds, read-continuation metadata limits, request-state retention and coding full-file-write observations.

## 19. Verification / Repair

GATE_V3 相对 OBSERVATION_FIRST 还改变 context，故 success 差不能归因于 gate 单一因素。真实 completed/拒绝 final/独立检查结果可观察；测试证明 passing invocation 不等于 verified completion。

- qwen3-1.7b / OBSERVATION_FIRST：AgentTaskSuccess 1/16 (6.25%)；HarnessMechanismSuccess 4/4 (100.00%)；timeout 2；平均轮数 2.50（20/20 observed）；模型工具调用 83；平均耗时 39.98 s（20/20 observed）；外部中断 0；完整 usage 15/20。 edit-before-read attempts 0/15 (0.00%)；confirmed invalid paths 8/74 (10.81%)；premature finals 1/4 (25.00%)。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate 0/15 (0.00%); context-limit avoidance 11/16 (68.75%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 5; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 14585; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 6; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/3；validation error calls 12；recovered episodes 2；unrecovered tool episodes 9。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 4/83 (4.82%); all validated schema/range/path error rate 12/83 (14.46%)；Recovered Argument Episode Rate 2/11 (18.18%)；Repeated Invalid Call Rate 1/12 (8.33%)（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 12/15; executed coding edits before any read 0/4；observation denied edits 9；verified success 0；read coverage 0.56；correct file location 4/6 (66.67%)；first valid file hit 2/6 (33.33%)；已观察输入/输出 token 76462/4086（仅已观察部分）（完整 usage 15/20）。

- qwen3-1.7b / GATE_V3：AgentTaskSuccess 2/16 (12.50%)；HarnessMechanismSuccess 4/4 (100.00%)；timeout 4；平均轮数 3.05（20/20 observed）；模型工具调用 88；平均耗时 55.65 s（20/20 observed）；外部中断 0；完整 usage 15/20。 edit-before-read attempts 0/18 (0.00%)；confirmed invalid paths 17/81 (20.99%)；premature finals 0/2 (0.00%)。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate 0/18 (0.00%); context-limit avoidance 13/16 (81.25%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 3; compacted rounds 7; dropped exchange groups 134; max observed byte proxy 15109; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 0; permission denials 6; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/0；validation error calls 19；recovered episodes 1；unrecovered tool episodes 10。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 2/88 (2.27%); all validated schema/range/path error rate 19/88 (21.59%)；Recovered Argument Episode Rate 1/11 (9.09%)；Repeated Invalid Call Rate 5/19 (26.32%)（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 12/18; executed coding edits before any read 0/3；observation denied edits 10；verified success 0；read coverage 0.62；correct file location 4/6 (66.67%)；first valid file hit 2/6 (33.33%)；已观察输入/输出 token 104810/4389（仅已观察部分）（完整 usage 15/20）。

- qwen3-1.7b / FULL_V3：AgentTaskSuccess 2/16 (12.50%)；HarnessMechanismSuccess 4/4 (100.00%)；timeout 3；平均轮数 2.95（20/20 observed）；模型工具调用 87；平均耗时 58.46 s（20/20 observed）；外部中断 0；完整 usage 16/20。 edit-before-read attempts 1/15 (6.67%)；confirmed invalid paths 14/78 (17.95%)；premature finals 3/3 (100.00%)。
  Verification completion rate 0/8 (0.00%); detected no-op rejection rate 0/15 (0.00%); context-limit avoidance 13/16 (81.25%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 3; compacted rounds 7; dropped exchange groups 135; max observed byte proxy 15236; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 0; permission denials 2; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/1；no-op拒绝 0；stale拒绝 0；signature violations 0/0；validation error calls 16；recovered episodes 2；unrecovered tool episodes 10。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 2/87 (2.30%); all validated schema/range/path error rate 16/87 (18.39%)；Recovered Argument Episode Rate 2/12 (16.67%)；Repeated Invalid Call Rate 3/16 (18.75%)（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 11/15; executed coding edits before any read 0/3；observation denied edits 7；verified success 0；read coverage 0.56；correct file location 4/6 (66.67%)；first valid file hit 2/6 (33.33%)；已观察输入/输出 token 103088/4103（仅已观察部分）（完整 usage 16/20）。

- qwen3-4b / OBSERVATION_FIRST: PARTIAL retained evidence (19 records); no complete4b mechanism comparison claim.

- qwen3-4b / OBSERVATION_FIRST：AgentTaskSuccess 0/15 (0.00%)；HarnessMechanismSuccess 1/4 (25.00%)；timeout 16；平均轮数 0.84（19/19 observed）；模型工具调用 2；平均耗时 50.61 s（19/19 observed）；外部中断 0；完整 usage 0/19。 edit-before-read attempts N/A（没有可观察机会）；confirmed invalid paths 0/2 (0.00%)；premature finals N/A（没有可观察机会）。
  Verification completion rate 0/7 (0.00%); detected no-op rejection rate N/A（没有可观察机会）; context-limit avoidance 13/15 (86.67%) (model-task scope, not semantic retention). No-op metric only counts detected edit/patch rejections, not all unchanged write_file proposals.
  Runtime evidence: context_limit 2; compacted rounds 0; dropped exchange groups 0; max observed byte proxy 6477; orphan tool messages 0; incomplete call pairs 0; before-request hard-budget refusals 2; permission denials 0; safe replay blocks 1. Byte proxy is not tokenizer usage; budget stopping is a safety observation, not coding success.
  patch 0/0；no-op拒绝 0；stale拒绝 0；signature violations 0/0；validation error calls 0；recovered episodes 0；unrecovered tool episodes 0。
  Unknown Tool Calls 0; schema/range Tool Argument Error Rate 0/2 (0.00%); all validated schema/range/path error rate 0/2 (0.00%)；Recovered Argument Episode Rate N/A（没有可观察机会）；Repeated Invalid Call Rate N/A（没有可观察机会）（分母分别是模型工具调用、错误episodes、已确认validation错误调用）。
  coding edit proposals before any prior read_file result 0/0; executed coding edits before any read 0/0；observation denied edits 0；verified success 0；read coverage 0.00；correct file location 0/6 (0.00%)；first valid file hit 0/6 (0.00%)；已观察输入/输出 token N/A（未收到 provider usage）（完整 usage 0/19）。

- qwen3-4b / GATE_V3: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-4b / FULL_V3: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

See docs/V3_MECHANISM_ANALYSIS.md for additional model-origin trace counts, valid-path lower bounds, read-continuation metadata limits, request-state retention and coding full-file-write observations.

## 20. Context Management

相同任务/工具/模型预算，比较上下文投影。字节代理不是模型 token 数；pinning 不保证语义理解，超过硬预算安全停止。

- qwen3-1.7b / NAIVE: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-1.7b / MANAGED_V2: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-1.7b / MANAGED_V3: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-4b / NAIVE: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-4b / MANAGED_V2: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-4b / MANAGED_V3: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

Independent V3 context contrast NOT RUN. Managed-context behavior within mechanism comparison is observable but confounded.

See docs/V3_MECHANISM_ANALYSIS.md for additional model-origin trace counts, valid-path lower bounds, read-continuation metadata limits, request-state retention and coding full-file-write observations.

## 21. Skills

同一组5个 Skills 任务；相同三个 skill，full 只增加所选正文。Optional/on-demand 是默认候选，不把预加载或 skill routing 当作模型 coding intelligence。

- qwen3-1.7b / FREE_LOOP: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-1.7b / SELECTED_SKILL_COMPACT: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-1.7b / SELECTED_SKILL_FULL: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-4b / FREE_LOOP: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-4b / SELECTED_SKILL_COMPACT: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

- qwen3-4b / SELECTED_SKILL_FULL: NOT VERIFIED / NOT RUN after the authorized deployment feasibility stop; no zero score is assigned.

Independent V3 Skills contrast NOT RUN; optional/on-demand recommended.

See docs/V3_MECHANISM_ANALYSIS.md for additional model-origin trace counts, valid-path lower bounds, read-continuation metadata limits, request-state retention and coding full-file-write observations.

## 22. Recovery / Permission

Permission denial and uncertain-side-effect replay blocking are HarnessMechanismSuccess, not ModelCodingSuccess. Tools execute with host privileges; no OS sandbox. Category-level safety grader passes alone do not prove every safeguard was exercised.

## 23. Stability / Repeated Runs

### Stability analysis

VERIFIED: 72 prespecified attempts, six unchanged tasks, four configurations, three runs each. AgentTaskSuccess is separate from HarnessMechanismSuccess. No Permission/Recovery tasks occur in this six-task subset. Repeated outcomes are not replacements for official main results. One additional FULL_V3 repeat-2/v2-dev-05-01 attempt was externally interrupted and permanently retained outside these 72 completed outcomes; it is not a model failure. Its scheduled run was executed once in a fresh isolated fixture, without replay of the uncertain old workspace. Total attempts including that interruption: 73.

### FREE_LOOP

Per-run successes: [1, 1, 1]; rates: [0.16666666666666666, 0.16666666666666666, 0.16666666666666666]. Mean Task Success 0.1667; min/max 0.1667/0.1667. Coding Success 0/9 (0.00%).
Timeouts 1; context_limit 6; repair_exhausted 0; empty_response 0. Mean model rounds 3.222; mean model tool calls 6.222; mean latency 52.322s.
Provider usage observed records 18/18; complete 17/18; partial 1/18. Observed prompt/completion sums 96541/5056; missing usage is UNAVAILABLE, never zero. Partial sums are lower bounds, not comparable total task token costs.

### OBSERVATION_FIRST

Per-run successes: [1, 0, 1]; rates: [0.16666666666666666, 0.0, 0.16666666666666666]. Mean Task Success 0.1111; min/max 0.0000/0.1667. Coding Success 0/9 (0.00%).
Timeouts 0; context_limit 4; repair_exhausted 0; empty_response 0. Mean model rounds 3.500; mean model tool calls 6.389; mean latency 48.349s.
Provider usage observed records 18/18; complete 18/18; partial 0/18. Observed prompt/completion sums 110987/4920; missing usage is UNAVAILABLE, never zero. Partial sums are lower bounds, not comparable total task token costs.

### GATE_V3

Per-run successes: [0, 1, 1]; rates: [0.0, 0.16666666666666666, 0.16666666666666666]. Mean Task Success 0.1111; min/max 0.0000/0.1667. Coding Success 0/9 (0.00%).
Timeouts 1; context_limit 4; repair_exhausted 3; empty_response 1. Mean model rounds 2.944; mean model tool calls 5.500; mean latency 57.061s.
Provider usage observed records 18/18; complete 17/18; partial 1/18. Observed prompt/completion sums 93614/3893; missing usage is UNAVAILABLE, never zero. Partial sums are lower bounds, not comparable total task token costs.

### FULL_V3

Per-run successes: [1, 1, 1]; rates: [0.16666666666666666, 0.16666666666666666, 0.16666666666666666]. Mean Task Success 0.1667; min/max 0.1667/0.1667. Coding Success 0/9 (0.00%).
Timeouts 1; context_limit 6; repair_exhausted 2; empty_response 0. Mean model rounds 2.944; mean model tool calls 6.000; mean latency 60.008s.
Provider usage observed records 18/18; complete 17/18; partial 1/18. Observed prompt/completion sums 91858/4324; missing usage is UNAVAILABLE, never zero. Partial sums are lower bounds, not comparable total task token costs.

### Fixed-task stability

- v2-dev-01-01: 0/12 (0.00%); per-configuration successes {'FREE_LOOP': 0, 'OBSERVATION_FIRST': 0, 'GATE_V3': 0, 'FULL_V3': 0}; stop states {'final_answer': 12}.
- v2-dev-02-01: 0/12 (0.00%); per-configuration successes {'FREE_LOOP': 0, 'OBSERVATION_FIRST': 0, 'GATE_V3': 0, 'FULL_V3': 0}; stop states {'final_answer': 12}.
- v2-dev-03-01: 0/12 (0.00%); per-configuration successes {'FREE_LOOP': 0, 'OBSERVATION_FIRST': 0, 'GATE_V3': 0, 'FULL_V3': 0}; stop states {'context_limit': 12}.
- v2-dev-04-01: 0/12 (0.00%); per-configuration successes {'FREE_LOOP': 0, 'OBSERVATION_FIRST': 0, 'GATE_V3': 0, 'FULL_V3': 0}; stop states {'context_limit': 6, 'final_answer': 4, 'empty_response': 1, 'max_repair_rounds': 1}.
- v2-dev-05-01: 0/12 (0.00%); per-configuration successes {'FREE_LOOP': 0, 'OBSERVATION_FIRST': 0, 'GATE_V3': 0, 'FULL_V3': 0}; stop states {'timeout': 3, 'final_answer': 3, 'context_limit': 2, 'max_repair_rounds': 4}.
- v2-dev-06-01: 10/12 (83.33%); per-configuration successes {'FREE_LOOP': 3, 'OBSERVATION_FIRST': 2, 'GATE_V3': 2, 'FULL_V3': 3}; stop states {'final_answer': 12}.

## 24. Recommended Default Configuration

### Default configuration

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

## 25. Known Limitations

PARTIAL：非编码的理解/导航任务没有强制完成证据门，独立grader仍要求实际读取与正确答案；taxonomy是优先级规则的可审计标签，非盲评专家归因，多个原因可以共存。小型合成数据、单一真实仓库/8个自定义任务、CPU资源与模型批次/cold cache混杂、非流式 token/生成状态观测不完整、多个机制对比存在已披露混杂。没有真实模型效果证据的机制标为 NOT VERIFIED（效果）；代码和机制回归可为 IMPLEMENTED/VERIFIED（测试）。

NOT IMPLEMENTED：OS sandbox、Multi-Agent、WebUI、RAG、大型 planner；这些是明确排除范围。执行 pytest/Python 代码具备宿主进程权限，workspace 文件工具护栏不是 OS 隔离；protected hashes 能检查篡改，不能阻止所有宿主副作用。更大模型不自动代表更好 coding。诊断仍超时不能证明模型不会完成；诊断变快也不自动证明主实验工具/agent正确。

Latest authorized closeout: only remaining 32/72 repeated attempts were run. Original frozen plans remain unchanged. qwen3:1.7b standalone development50, heldout40, context60 and skills15 are NOT RUN. Development mechanism comparison120 is complete and separately reported; it does not substitute for the missing Full development benchmark. Existing4b development/heldout results are retained; unmatched incomplete model comparison cannot establish superiority.

## 26. Public Release Audit

### Public release checklist

Local preparation only. Remote repository creation, publication, push and remote CI: NOT RUN.

- VERIFIED by final local audit: whitelist export excludes work/model blobs/model files, raw sessions/traces/workspaces, virtual environment, bytecode, pytest/coverage temporary files and runtime caches.
- VERIFIED by final local audit: no forbidden model/private files in current Git index.
- VERIFIED locally: secret and absolute-host-path pattern scans; pattern scanning cannot prove absence of every possible secret.
- VERIFIED locally: tests, statement/branch coverage, lint, format, types, offline and MCP demos.
- PARTIAL: portable installation and Windows/Linux remote CI remain NOT RUN.
- Final audit data: work/public-audit-v3-final.json (private local audit log).
- Public export is an explicit whitelist, not git add-all; no remote package uploaded.

## 27. Reproduction Commands

`python scripts/run_v3_batch.py --model qwen3:1.7b --group repeat-core --resume --batch-size 5`

Completed cases are skipped; no old workspace replay. `python -m pytest --basetemp=work/pytest-local --cov=mini_harness --cov-branch`; `python -m ruff check src tests examples`; `python -m ruff format --check src tests examples`; `python -m mypy src/mini_harness`. Models must already be locally available; no downloads performed.

## 28. GitHub Readiness

- VERIFIED：本地测试/覆盖率/Ruff/mypy/demos；冻结主协议及真实失败留存；Git index 模型/私有数据扫描；显式 public export whitelist。
- VERIFIED：模型 blobs、gguf、raw sessions/traces/private workspaces、.venv、__pycache__、coverage/cache 被忽略且不进入 public inventory。
- NOT VERIFIED：远程 Windows/Linux CI、公开 GitHub 可复现执行。
- 明确跳过：创建远程仓库、push、发布；用户禁止这些操作，不能标为已完成。

本地证据位置：eval/results/v3、eval/results/v3-batched、eval/results/validation-v3-final；安全公开数值投影：eval/public/v3。原始证据不被删除或改写。

Local audit-ready; remote CI and publication NOT RUN. No GitHub creation/push.

## 29. Resume-safe Claims

Safe resume means durable per-case results, exact completion-key skipping and fresh isolated fixtures for explicitly allowed interrupted attempts. It does not mean replaying uncertain effects. Resume-safe résumé claims: independently implemented strict-schema runtime, permission/journaling/recovery, observation and verification guards, local regression suite and honest measured CPU model evaluations. Report actual numbers and limitations.

## 30. Claims That Must NOT Be Made

Do not claim reliable autonomous coding, significantly improved coding success, production-grade sandbox, modern full MCP support, strong-model coding superiority, successful real-repository coding, fully completed V3 synthetic benchmark, or remote CI verification. FakeProvider regressions do not prove model intelligence.
