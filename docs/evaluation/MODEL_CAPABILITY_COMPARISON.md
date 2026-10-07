# MODEL_CAPABILITY_DIAGNOSTIC — 模型能力与 CPU 时限

非正式 benchmark。8个任务和共同180/360s预算在运行前固定，不替换主评测。Task Success 总体只属于此诊断；其中6项synthetic、2项real另列。

可配对主预算子集 2/8任务 qwen3-1.7b：主预算 AgentTaskSuccess 0/2 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 0；平均轮数 3.00（2/2 observed）；模型工具调用 5；平均耗时 47.25 s（2/2 observed）；外部中断 0；完整 usage 2/2。 宽松预算 AgentTaskSuccess 0/8 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 0；平均轮数 3.25（8/8 observed）；模型工具调用 41；平均耗时 63.92 s（8/8 observed）；外部中断 0；完整 usage 8/8。；timeout转为有响应/其他停止 0/2；失败转成功 0/2。这是诊断子集，不额外改变正式 Task Success 分母。

可配对主预算子集 8/8任务 qwen3-4b：主预算 AgentTaskSuccess 0/8 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 8；平均轮数 1.00（8/8 observed）；模型工具调用 0；平均耗时 60.10 s（8/8 observed）；外部中断 0；完整 usage 0/8。 宽松预算 AgentTaskSuccess 0/8 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 4；平均轮数 2.00（8/8 observed）；模型工具调用 2；平均耗时 242.22 s（8/8 observed）；外部中断 0；完整 usage 4/8。；timeout转为有响应/其他停止 4/8；失败转成功 0/8。这是诊断子集，不额外改变正式 Task Success 分母。

qwen3-1.7b diagnostic synthetic6: AgentTaskSuccess 0/6 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 0；平均轮数 3.33（6/6 observed）；模型工具调用 36；平均耗时 70.18 s（6/6 observed）；外部中断 0；完整 usage 6/6。

qwen3-1.7b diagnostic real2: AgentTaskSuccess 0/2 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 0；平均轮数 3.00（2/2 observed）；模型工具调用 5；平均耗时 45.13 s（2/2 observed）；外部中断 0；完整 usage 2/2。

## qwen3-1.7b

AgentTaskSuccess 0/8 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 0；平均轮数 3.25（8/8 observed）；模型工具调用 41；平均耗时 63.92 s（8/8 observed）；外部中断 0；完整 usage 8/8。
Coding Success 0/4 (0.00%)；Timeout Rate 0/8 (0.00%)；Tool Selection relevance 1.00（capability-category代理，非语义正确率）；Tool Argument Error Rate 1/41 (2.44%)；Tool Calls 41；已观察Tokens 49519/1921（仅已观察部分），完整 usage 8/8。
- v2-dev-01-01 milestones: complete response True; tool calling True; locate False; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [29.445126399999936, 24.973280300000624]; finish reasons ['tool_calls', 'stop']; TTFT UNAVAILABLE; end-to-end reported completion token rates [3.7697240111015535, 3.0832953891122616].

- v2-dev-01-01：FAIL，final_answer，rounds 2，tools 4，54.59s。
- v2-dev-02-01 milestones: complete response True; tool calling True; locate True; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [4.91377250000005, 5.080201300001136]; finish reasons ['tool_calls', 'stop']; TTFT UNAVAILABLE; end-to-end reported completion token rates [7.3263465087159885, 6.102120402196085].

- v2-dev-02-01：FAIL，final_answer，rounds 2，tools 1，10.10s。
- v2-dev-03-01 milestones: complete response True; tool calling True; locate True; read coverage 1.0; edit attempts 2; verification calls 0; success False. Response latency [26.353458300000057, 42.180565199998455, 40.66670560000057]; finish reasons ['tool_calls', 'tool_calls', 'tool_calls']; TTFT UNAVAILABLE; end-to-end reported completion token rates [10.43506308999299, 0.6401052207807066, 1.229507019619492].

- v2-dev-03-01：FAIL，context_limit，rounds 3，tools 9，111.72s。
- v2-dev-04-01 milestones: complete response True; tool calling True; locate True; read coverage 1.0; edit attempts 3; verification calls 1; success False. Response latency [34.391895900000236, 43.85766549999971, 30.32808710000063]; finish reasons ['tool_calls', 'tool_calls', 'tool_calls']; TTFT UNAVAILABLE; end-to-end reported completion token rates [10.322199189955025, 0.5700257803279604, 6.46265619568192].

- v2-dev-04-01：FAIL，max_repair_rounds，rounds 3，tools 9，113.85s。
- v2-dev-05-01 milestones: complete response True; tool calling True; locate True; read coverage 1.0; edit attempts 1; verification calls 1; success False. Response latency [11.900675700000647, 21.56877070000155, 5.1612514999997074]; finish reasons ['tool_calls', 'tool_calls', 'tool_calls']; TTFT UNAVAILABLE; end-to-end reported completion token rates [10.33554758575543, 1.0663565541080349, 3.875029147485088].

- v2-dev-05-01：FAIL，max_repair_rounds，rounds 3，tools 7，43.70s。
- v2-dev-06-01 milestones: complete response True; tool calling True; locate True; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [9.499965399998473, 9.860970499999894, 6.3628924999993615, 10.199569899999915, 10.19983030000003, 10.774139900000591, 29.930699700000332]; finish reasons ['tool_calls', 'tool_calls', 'tool_calls', 'tool_calls', 'tool_calls', 'tool_calls', 'stop']; TTFT UNAVAILABLE; end-to-end reported completion token rates [3.7894874859234524, 4.563445352564485, 8.80102877740047, 5.490427591461525, 5.490287421742677, 5.19763067119603, 1.2361889421515793].

- v2-dev-06-01：FAIL，final_answer，rounds 7，tools 6，87.13s。
- real-nav-1 milestones: complete response True; tool calling True; locate True; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [9.019657200000438, 9.132392700001219]; finish reasons ['tool_calls', 'stop']; TTFT UNAVAILABLE; end-to-end reported completion token rates [2.8825929216022463, 10.183530543970978].

- real-nav-1：FAIL，final_answer，rounds 2，tools 1，18.24s。
- real-bug-1 milestones: complete response True; tool calling True; locate True; read coverage 0.21164021164021163; edit attempts 0; verification calls 0; success False. Response latency [3.8928281999997125, 25.265403600000354, 5.8793523000003916, 36.61442800000077]; finish reasons ['tool_calls', 'tool_calls', 'tool_calls', 'tool_calls']; TTFT UNAVAILABLE; end-to-end reported completion token rates [7.192714027298217, 1.385293524462024, 4.082082306923231, 0.6554793099594372].

- real-bug-1：FAIL，context_limit，rounds 4，tools 4，72.03s。

qwen3-4b diagnostic synthetic6: AgentTaskSuccess 0/6 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 3；平均轮数 2.00（6/6 observed）；模型工具调用 1；平均耗时 243.41 s（6/6 observed）；外部中断 0；完整 usage 3/6。

qwen3-4b diagnostic real2: AgentTaskSuccess 0/2 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 1；平均轮数 2.00（2/2 observed）；模型工具调用 1；平均耗时 238.63 s（2/2 observed）；外部中断 0；完整 usage 1/2。

## qwen3-4b

AgentTaskSuccess 0/8 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 4；平均轮数 2.00（8/8 observed）；模型工具调用 2；平均耗时 242.22 s（8/8 observed）；外部中断 0；完整 usage 4/8。
Coding Success 0/4 (0.00%)；Timeout Rate 4/8 (50.00%)；Tool Selection relevance 1.00（capability-category代理，非语义正确率）；Tool Argument Error Rate 0/2 (0.00%)；Tool Calls 2；已观察Tokens 15574/5848（仅已观察部分），完整 usage 4/8。
- v2-dev-01-01 milestones: complete response True; tool calling False; locate False; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [141.04470039999978]; finish reasons ['length']; TTFT UNAVAILABLE; end-to-end reported completion token rates [3.6300548588353823].

- v2-dev-01-01：FAIL，final_answer，rounds 1，tools 0，141.10s。
- v2-dev-02-01 milestones: complete response True; tool calling False; locate False; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [121.19251639999948]; finish reasons ['length']; TTFT UNAVAILABLE; end-to-end reported completion token rates [4.224683299009395].

- v2-dev-02-01：FAIL，final_answer，rounds 1，tools 0，121.24s。
- v2-dev-03-01 milestones: complete response True; tool calling True; locate True; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [108.56017209999936, 151.24752780000017, 'UNAVAILABLE']; finish reasons ['length', 'tool_calls', 'UNAVAILABLE']; TTFT UNAVAILABLE; end-to-end reported completion token rates [4.716278448125296, 2.5190494386381603, 'UNAVAILABLE'].

- v2-dev-03-01：FAIL，timeout，rounds 3，tools 1，360.05s。
- v2-dev-04-01 milestones: complete response True; tool calling False; locate False; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [111.29333510000015, 144.9091281000001, 'UNAVAILABLE']; finish reasons ['length', 'length', 'UNAVAILABLE']; TTFT UNAVAILABLE; end-to-end reported completion token rates [4.600455180356971, 3.533248779515634, 'UNAVAILABLE'].

- v2-dev-04-01：FAIL，timeout，rounds 3，tools 0，360.06s。
- v2-dev-05-01 milestones: complete response True; tool calling False; locate False; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [109.1711964999995, 140.92087040000024, 'UNAVAILABLE']; finish reasons ['length', 'length', 'UNAVAILABLE']; TTFT UNAVAILABLE; end-to-end reported completion token rates [4.689881730846491, 3.6332446609696722, 'UNAVAILABLE'].

- v2-dev-05-01：FAIL，timeout，rounds 3，tools 0，360.06s。
- v2-dev-06-01 milestones: complete response True; tool calling False; locate False; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [117.92821599999934]; finish reasons ['length']; TTFT UNAVAILABLE; end-to-end reported completion token rates [4.34162423011642].

- v2-dev-06-01：FAIL，final_answer，rounds 1，tools 0，117.98s。
- real-nav-1 milestones: complete response True; tool calling False; locate False; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [117.1565845999994]; finish reasons ['length']; TTFT UNAVAILABLE; end-to-end reported completion token rates [4.37021958047079].

- real-nav-1：FAIL，final_answer，rounds 1，tools 0，117.20s。
- real-bug-1 milestones: complete response True; tool calling True; locate True; read coverage 0.0; edit attempts 0; verification calls 0; success False. Response latency [107.12424139999894, 104.48909950000052, 'UNAVAILABLE']; finish reasons ['length', 'tool_calls', 'UNAVAILABLE']; TTFT UNAVAILABLE; end-to-end reported completion token rates [4.779497089628912, 3.3209205712410057, 'UNAVAILABLE'].

- real-bug-1：FAIL，timeout，rounds 3，tools 1，360.06s。

## Interpretation

更宽预算下能收到响应或成功完成、而相同任务主预算超时，支持 CPU/时限瓶颈的解释。若收到响应后发生参数、导航、编辑或规划失败，说明单纯延长时限不足。若仍超时，两种解释无法充分区分，不能断言模型不会完成任务。诊断不改变任何主分数。reasoning_effort none 是请求参数，不能保证两模型内部生成行为完全相同。

B (CPU/deployment budget) is supported by completed first responses beyond60s; A (intrinsic inability) is NOT PROVEN. Both models still fail the eight diagnostic tasks. A larger timeout is insufficient to establish completion capability. Truncated planning text, context limits, repair limits and the scarcity of executed edits are distinct observations; no practical think/stream profile was implemented and no main result was replaced.
