# Design decisions

1. 自己实现 orchestration：AgentRunner 负责有界循环；Provider 只做传输，Executor 负责可执行边界。
   没有复制 nanobot、LangGraph、LangChain、OpenAI Agents SDK 源码；它们也不是运行依赖。
2. Pydantic 负责统一数据模型、本地参数验证及 JSON Schema；jsonschema 负责 MCP 外部 Schema。
   这是基础库能力，不能称为自研 Schema 验证器。
3. 所有工具顺序执行，便于确定日志顺序、处理副作用和解释恢复。当前没有 parallel tool execution。
4. 本地命令使用 argv whitelist，没有通用 shell。pytest 仍会执行任意仓库代码，所以 EXECUTE 是信任授权。
5. Context 使用保守 UTF-8 字节估计而非精确 tokenizer；受保护的最新交换过大就停止，不能拆开调用/结果。
   历史摘要是 bounded extractive text，便宜可测，但会丢信息；不是 LLM 摘要模型。
6. JSONL fsync 易读可恢复；现在 append/load 会扫描文件，长会话有 O(n²) 总写入开销。
   面试可讨论 SQLite/WAL，但本项目未实现它，不应写成已有能力。
7. 存储与工具效果不能原子提交，因此拒绝重放 uncertain side effects，不承诺 exactly-once。
   OS lease 处理多进程竞争；只允许一个 runner 持有同一个 session。
8. Skills 用简单 scalar frontmatter parser，避免额外 YAML 依赖；不是完整 YAML 语法。
9. MCP 固定 legacy 2025-06-18 stdio，支持 initialize/tools discovery/call；其他协议版本显式拒绝。
   host grants 优先，永不信任 readOnlyHint。启动外部 server 也需要用户信任。
10. 评测使用小型确定性仓库、hidden assertions/mutant rejection；fakes 是 runtime regression。
    任务难度与真实大仓库仍有差距，不能拿本套件替代 SWE-bench 或生产效果。
11. OpenAI-compatible 默认通用不发送 reasoning_effort；本地 Ollama CLI/evaluator 明确设置 none。
    初始 `/no_think` 验收产生长思考输出，provider-probe.json 记录 none 的实际效果。
12. 工具/会话记录可能含源码或敏感参数，目前未实现自动脱敏、加密存储或日志轮转。

## References

只参考协议说明与通用机制，没有引入框架核心代码：
- Ollama Chat Completions compatibility: https://docs.ollama.com/api/openai-compatibility
- Ollama reasoning control discussion: https://github.com/ollama/ollama/issues/14820
- MCP lifecycle: https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle
- MCP stdio transport: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
- MCP tools: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- Pydantic models/schema: https://docs.pydantic.dev/latest/concepts/models/
- asyncio timeout/subprocess: https://docs.python.org/3.12/library/asyncio-task.html

这些来源解释兼容接口，不证明本仓库效果；效果只能由本地保存的测试和实测记录支持。


## Final safety and provenance choices

CLI 将自定义 session/trace 及 lock 文件列为 protected files。Git 固定为 workspace 外部可执行文件，禁用 fsmonitor/external diff/textconv，限制上级仓库发现。这些 guardrail 不能阻止获授权的 pytest 代码访问进程权限允许的位置。

最终评测 manifest 记录任务文件哈希、源代码哈希和模型参数。最终五配置消融从同一版代码重新运行；先前 Full-54 在最后安全加固前启动，作为独立实测，不充当最终消融 Full 对照。
