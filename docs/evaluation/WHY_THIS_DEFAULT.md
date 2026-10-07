# Recommended local default


仅用1.7b development机制对照及预定重复试验选推荐配置：GATE_V3 coding 0/8，FULL_V3 coding 0/8；repeat-core mean success 0.11/0.17。推荐 GATE_V3；强制 prefer_patch 不默认强制，hash/context patch能力仍可用。这是小样本实用选择，不是统计显著性结论，不使用heldout调参，也不重跑heldout替换成绩。
推荐轻量可靠性配置：明确 coding flag/targets；observation-first；bounded navigation；结构化错误+2次相同无效参数重试上限；有 hash/context 的 patch；当前代码对应的 canonical verification + 可配置独立检查；MANAGED_V3；durable journal/recovery；显式权限。Skills optional/on-demand，默认不注入所有正文。这个推荐包含安全/可审计理由，并非宣称 Full 提高所有任务分数。

API/业务独立 verifier 必须由应用提供；CLI 的仅 canonical 模式不能冒充独立隐藏评测。Tool execute 不等于 OS sandbox。详见 WHY_THIS_DEFAULT.md。


证据判断：安全保护可因阻止不可审计/未验证写入而保留，不能被包装成模型 Task Success 提升。Skills 默认 optional/on-demand；只有可靠的同任务效果或成本收益才支持自动注入。所有机制具体结果和对照混杂见 FINAL_REPORT_V3 的 E–K。
