# 重新学习本项目的路线

先在全新 `work/demo-new` 运行 `mini-harness demo`，再看 JSON 中的 messages 和 stats。
建议用两到三天逐层阅读，跟一个调用走到底，比一次通读所有文件更容易理解。

## 1. 概念与入口

概念：Harness 是模型周围的运行设施。模型建议工具调用，Python 程序负责实际执行。
代码文件：src/mini_harness/cli.py、providers/base.py、agent/result.py。
核心函数：main → execute；Message/ToolCall/ModelResponse/AgentResult。
调用顺序：解析命令 → Workspace/Registry/Policy/Session/Provider → AgentRunner。
示例：无工具 FakeProvider script 只返回 content，runner 一轮给出 final_answer。
先读 tests/test_runner.py 的 test_loop(0)，在模型返回处加断点观察数据结构。

## 2. Runner 调用链

概念：每轮必须有上限；失败不是无限重试。tool error 可让模型纠错，provider error 则停止。
代码文件：agent/runner.py、agent/state.py、agent/stopping.py、providers/fake.py。
核心函数：run/resume/_drive，Provider.complete，FakeProvider.complete。
调用顺序：user message → Context.prepare → provider request → response → final 或工具执行 → 下一轮。
示例：test_loop(3) 的三次工具响应后出现最终文本；max_iterations 测试展示耗尽轮数。
找出 asyncio.timeout 的模型和整任务两个层次；取消会记录 cancelled。

## 3. Tool Calling 调用链

概念：工具名称不是任意 Python 函数名，只有已注册实例可调用。参数先验证，效果后执行。
代码文件：tools/base.py、registry.py、executor.py、result.py、tools/builtin/*.py。
核心函数：BaseTool.definition/validate/execute；register/get_definitions/prepare_call；ToolExecutor.execute。
调用顺序：Pydantic model_json_schema → Provider tools 字段 → ToolCall → JSON object → strict Pydantic
→ PermissionPolicy → tool.execute → ExecutionResult → role=tool、关联 tool_call_id。
示例：read_file 的 path=3 被拒绝；edit_file 的 old 匹配数不对就不写文件。
运行 tests/test_tools.py::test_complete_tool_flow，观察修改和 run_tests exit_code。

## 4. Context 调用链

概念：持久会话完整；working context 有限；summary 是有损投影。调用和结果不能分离。
代码文件：context/budget.py、compaction.py、manager.py。
核心函数：estimate_messages、summarize、message_groups、ContextManager.prepare。
调用顺序：复制原始 Message → 截断 tool content → 按交换分组 → 固定 system/最新任务/最新组
→ 删除旧组并生成摘要 → 检查预算 → provider 请求。
示例：test_compaction_atomic 检查原始 history 没被改、工具配对还有效；pinned overflow 直接停止。
注意这里的 estimated input 是保守字节代理，不是真实 tokenizer 计数；实际 usage 来自 Provider。

## 5. Skills 调用链

概念：Skill 是方法文本；不能因为文本写了命令就绕过工具权限。
代码文件：skills/models.py、discovery.py、loader.py，根目录 skills/*/SKILL.md。
核心函数：read_header → discover_skills → SkillLoader.catalog → activate → ActivateSkill.execute。
调用顺序：读前置 name/description → catalog 加入指令 → 模型选择 activate_skill → 延迟加载正文
→ 后续模型按方法选择工具。正文在 tool result 中，权限仍由 Executor 判定。
示例：test_activation_via_agent_registry；修改尚未激活的正文可看到 activation 才读取新内容。
references/scripts/assets 不自动执行或全部读入；完整 YAML 也未实现。

## 6. MCP 调用链

概念：MCP 是外部能力传输协议。外部工具也应经过同样的 schema/permission/journal/timeout。
代码文件：mcp/client.py，examples/mcp_server.py、mcp_demo.py。
核心函数：connect → request(initialize) → register_tools → MCPTool.definition/validate/execute。
调用顺序：stdio subprocess → legacy handshake → tools/list/pagination → MCPTool 注册
→ AgentRunner/Executor → JSON Schema → host grant → tools/call → JSON-RPC result。
示例：python examples/mcp_demo.py；tests/test_mcp.py 的 slow/malformed/rpc-error 验证失败处理。
思考为什么 default DANGEROUS，为什么不能相信 server readOnlyHint，以及超时后为何关闭连接。

## 7. Permission 调用链

概念：代码 guardrail 不依赖模型“听话”；但 workspace path guard 不是 OS 沙箱。
代码文件：security/permissions.py、workspace.py，filesystem.py、shell.py。
核心函数：PermissionPolicy.check；Workspace.resolve；atomic_write；run_process。
调用顺序：schema → capability policy → 工具内部 resolved containment → 文件或固定 argv → bounded result。
示例：READ 默认可读不可写；../、absolute escape、Windows junction、.git/config 均被拦截。
审批 callback 只是显式授权入口，CLI 当前使用 grant flags，没有通用交互审批 UI。
run_tests 能执行仓库 Python 代码；只有可信仓库才能授予 EXECUTE。TOCTOU/hardlink 未完整隔离。

## 8. Session / Recovery 调用链

概念：对副作用，未知状态必须停。成功工具执行与消息记录之间也可能崩溃。
代码文件：session/store.py、recovery.py、tools/executor.py、agent/runner.py。
核心函数：SessionStore.append/load/lease；plan_recovery；ToolExecutor._execute；AgentRunner.resume。
调用顺序：lease → turn_started/assistant record → execution_started fsync → 副作用
→ execution_completed fsync → tool message → terminal。
恢复顺序：load → 找最新 turn 和 iteration → 配出 pending calls → 原 execution key/fingerprint
→ 完成记录复用；uncertain write 停止；safe read 可重试 → 剩余轮数 → final。
示例：tests/test_process_recovery.py 真正让子进程 os._exit，在 uncertain 和 committed 两个窗口终止。
观察 OS 自动释放 lease，而 durable intent/result 仍存在。修改 counter 后恢复也不会覆盖人类修改。

## 9. Trace 与评测

概念：final_answer 只是协议终止，不代表任务成功；独立 grader 必须检查结果。
代码文件：tracing/recorder.py、evaluation/tasks.py、fixtures.py、oracle.py、graders.py、evaluator.py、metrics.py。
核心函数：TraceRecorder.record；fixture_for/materialize；run_task/grade/evaluate/aggregate。
调用顺序：固定任务 → 新 workspace → provider/variant → runner → 独立判分 → JSONL → summary。
示例：weak-tests 测试中 assert True 能通过正确程序，却抓不到 mutant，因此失败。
先读 scripted regression 的 trace，再读真实模型失败 trace，定位 model/tool arguments/execution/context/final answer。

## 推荐练习

为新的本地工具定义 InputModel 和 BaseTool，注册并验证未知字段/权限拒绝；不要添加任意 shell。
构造一个 latest tool exchange 超预算的任务，解释为何宁可停止也不能拆分工具结果。
人为中断一次真实副作用调用，说明为何 JSONL+fsync 不等于跨文件系统事务。
只在 development tasks 上改进提示或工作流，冻结 held-out。每个效果论点都引用真实记录。
