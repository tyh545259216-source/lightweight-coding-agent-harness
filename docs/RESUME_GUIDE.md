# Résumé guide

**Lightweight Coding Agent Harness｜个人项目**

定位：轻量级 Coding Agent Harness（自研 Agent Runtime）。技术栈：Python、asyncio、Pydantic、Structured Tool Calling、Ollama、MCP、Skills、pytest。

推荐三条：

- 自研轻量级 Agent Runtime，实现异步 AgentRunner、Provider 抽象、严格 schema 的 Tool Registry 与统一 Executor，串联本地工具及限定 stdio MCP 工具执行链。
- 实现上下文预算与完整 tool-call/result 分组、显式权限和 workspace guard、持久化 journal/session 与恢复策略，对不确定副作用阻止盲目重放，并加入可观察编辑与验证护栏。
- 建立 trace 驱动的分层评测与失败分析，分别统计 AgentTaskSuccess 与 HarnessMechanismSuccess；V3 通过 235 项自动化测试，核心运行时语句/分支覆盖率为 93.21%/83.20%，保留双模型真实仓库与诊断均 0/8 的负结果及 CPU 时限限制。

上述235/覆盖率对应冻结V3验收；RC重新安装验收见 [RC报告](../GITHUB_RELEASE_CANDIDATE.md)。只描述真实实现和明确范围。

不要宣称：显著提升 Coding 成功率、高可靠自主 Coding、production-grade sandbox、full MCP platform、强模型优越性。Tutorial 成功不进入 benchmark；第三方模型与 Ollama 不属于自研实现。
