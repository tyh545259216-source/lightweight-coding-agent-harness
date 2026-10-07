# 面试问题与基于实际实现的答案

不要背诵不存在的能力；先运行对应测试和查看当前 FINAL_REPORT 的真实数字。

## 1. 什么是 Agent Harness？

围绕模型请求实现循环、工具执行、上下文、权限、持久化和观测的运行设施。本项目的编排入口是 AgentRunner。

## 2. 核心实现有没有直接调用 Agent 框架？

没有。loop/registry/context/recovery 是本仓库代码；Pydantic/httpx/jsonschema 提供基础通用能力。

## 3. Agent Loop 怎么实现？

_drive 在有限 iteration 中请求 Provider；有 tool_calls 就逐个执行并追加结果，否则非空文本作为 final_answer。

## 4. Tool Call 谁真正执行？

模型只提供名字和参数；ToolExecutor 查 Registry、验证 schema、检查权限后调用 BaseTool.execute。

## 5. 为什么不能无限循环？

max_iterations 限制轮数，model_timeout/task_timeout 限制耗时，工具有自己的 timeout，并能记录停止原因。

## 6. Tool Schema 怎么生成？

本地 InputModel.model_json_schema 生成；MCP 工具沿用服务端 inputSchema，再用 jsonschema 验证。

## 7. 为什么 strict=True / extra=forbid？

拒绝模型参数类型隐式转换和拼错字段；错误返回 arguments 类型，模型可以纠正后继续。

## 8. Malformed tool arguments 怎么处理？

prepare_call 解析字符串 JSON，要求对象并验证 Pydantic。坏 JSON/类型/缺字段返回结构化 arguments error。

## 9. Tool error 与 Provider error 区别？

tool error 是消息数据，下一轮可修复；ProviderError 终止任务，避免不受控网络重试。

## 10. 空模型响应怎么办？

没有调用也没有可见文本时停止为 empty_response，不凭空补答案。

## 11. 如何支持 cancellation？

asyncio cancellation 被 runner 记录为 cancelled；工具执行意图保留。命令创建用 shield 避免丢失进程句柄，随后终止进程。

## 12. Context Window 满了怎么办？

截断工具输出、按完整调用组移除历史、生成有损摘要；固定的最新任务/交换仍超预算就 context_limit。

## 13. 为什么工具调用和结果不能拆开？

Provider 需要正确关联 tool_call_id；孤儿结果或未完成调用会破坏对话协议，message_groups 会检查。

## 14. Token 统计是精确的吗？

Context 的 UTF-8 字节估计是保守代理；Usage 中 provider 来源才是服务端报告的 token。FakeProvider 不编造 token。

## 15. Session 与 Context 有什么区别？

Session 是完整 durable history；Context 是每轮 bounded projection。Summary 是丢信息的短文本，不替代原始会话。

## 16. Summary 怎么生成？

compaction.summarize 从旧消息提取角色、工具名和文本片段，加上有损警告，限制字符长度；未使用摘要 LLM。

## 17. Skill 是文本还是代码？

本项目 Skill 正文是 Markdown instructions。目录可包含 scripts，但加载器不会自动运行脚本。

## 18. Skill 和 Tool 有什么区别？

Skill 告诉模型怎样做，Tool 是可执行的代码能力；激活 Skill 不授予 WRITE/EXECUTE 权限。

## 19. 如何避免全部 Skill 进入 Context？

discovery 只读 frontmatter；catalog 只含名称描述，activate_skill 才调用 SkillLoader.activate 读正文。

## 20. MCP 和 Tool 有什么区别？

MCP 是外部工具的发现/调用协议；MCPTool 是适配器，执行仍走同一个 Registry/Executor。

## 21. 支持全部 MCP 功能吗？

不支持。实现的是 legacy 2025-06-18 stdio tools primitive；HTTP、资源、OAuth、现代版本协商未实现。

## 22. 为什么外部工具默认 DANGEROUS？

客户端不能把服务端声明当成授权。只有 host 配置可将可信工具明确分类为 READ 等权限。

## 23. 为什么需要 Permission？

工具能力可以改文件、执行代码、访问数据。能力级别必须在 Python 层检查，而不是任由模型决定。

## 24. 为什么不能只用 Prompt 限制工具？

提示可能被忽略或注入。路径解析、policy 和命令 whitelist 在实际执行前拒绝越权。

## 25. 如何防止 workspace escape？

拒绝 .. 和 drive-relative 路径，resolve 后检查 relative_to(root)，拦截 symlink/junction 外指与受保护目录。

## 26. 这些 guardrail 是安全沙箱吗？

不是。pytest 代码可访问主机，TOCTOU/hardlink/网络隔离未覆盖；需要可信 workspace 和显式 EXECUTE grant。

## 27. 为什么 edit_file 用 exact match？

明确 expected_count，匹配数异常就不写；减少定位含糊导致的大面积错误修改，成功后原子替换。

## 28. 是否提供任意 run_command？

没有，只提供 python --version、git status --short、git diff --stat 三种 argv 模板，无 shell=True。

## 29. 恢复如何避免重复副作用？

执行前 durable intent，成功后 durable completion；同 key/fingerprint 命中 completion 就复用结果。uncertain side effect 停止。

## 30. 为什么不承诺 exactly-once？

文件写入和 JSONL 提交不是单一事务。崩溃可能发生在效果后、记录前；项目用保守停止避免自动重复。

## 31. 如何处理多进程恢复竞争？

SessionStore.lease 持有 OS advisory lock，同一 session 只允许一个 runner；进程死亡后由 OS 释放。

## 32. 恢复怎样找到待执行调用？

plan_recovery 找最新 turn 的 assistant 与已记录 tool IDs，恢复原 iteration/key，再完成缺失结果并继续剩余轮数。

## 33. JSONL 写到一半怎么办？

只忽略/修复未换行的最后一条记录；完整记录或中间损坏抛 SessionCorruptError，不能默默跳过。

## 34. 怎么验证真的崩溃恢复？

crash_worker 子进程在副作用后或 completion 后 os._exit；集成测试重新打开会话验证阻断/复用与锁释放。

## 35. Tracing 能定位哪些失败？

事件带 turn_id、iteration、model、layer；区分 model、tool selection/arguments/execution、context、final answer，并记录真实延迟。

## 36. Final answer 是任务成功吗？

不是。final_answer 只是模型停止调用工具；独立 functional grader 才判断代码/答案是否正确。

## 37. Benchmark 怎么设计？

54 个固定小仓库任务，9 类各6，开发36/留出18；每次新workspace，保留trace和独立判分，不把oracle传给真实模型。

## 38. 为什么测试生成需要 mutant？

只通过原实现可能是 assert True；必须在正确实现通过且在行为变异上出现测试失败，证明测试检查了目标行为。

## 39. 为什么要 Ablation？

保持loop/tools/permissions一致，仅切换Context/Skills/Recovery，观察各功能的覆盖和开销；结果不能脱离样本及模型配置解释。

## 40. FakeProvider 成功率说明什么？

说明预设轨迹能通过 runtime 和 graders，不说明模型会选择正确工具。真实模型结果必须单独报告。

## 41. Recovery baseline 失败意味着模型弱吗？

不意味着。该配置不提供恢复，checkpoint任务记为UNSUPPORTED。应把feature coverage和普通任务成功率分开看。

## 42. 当前主要扩展方向有哪些？

真实仓库更多任务、精确tokenizer、SQLite日志、OS/container隔离、现代MCP、更多模型与重复测量；这些当前未实现。

