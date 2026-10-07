# Evaluation philosophy

The project evaluates runtime mechanics and model outcomes separately.

- **Tool Call Success ≠ Task Success.** A successful grep/read invocation can still inspect the wrong file. In the diagnostic, 1.7b made 41 tool calls and completed zero of eight tasks.
- **HarnessMechanismSuccess ≠ AgentTaskSuccess.** Blocking an uncertain recovery side effect is a runtime safety success; no coding accomplishment is implied.
- **Test Pass ≠ Correct Generated Test.** The frozen test-generation grader checks that candidates pass the original implementation and reject a mutant. A vacuous passing test is insufficient.
- **Safety Refusal ≠ Coding Success.** Permission denial or context-budget refusal can be correct enforcement while leaving the user task incomplete.
- **Entering Tool Loop ≠ Completing Coding.** The wider diagnostic gave 4b two tool calls and zero successes. More time enabled some responses, but did not establish coding reliability.

Fixed-budget response timeout means deployment-budget incompatibility when no executable decision arrives. It is not proof of low model intelligence. Wider-budget diagnostic results never replace official results. Real-repository and synthetic outcomes are reported separately; external interruptions are retained outside model-failure denominators.

Tutorials demonstrate control flow. Scripted FakeProvider behavior and tiny selected examples are never added to benchmark success rates. Failed cases, unrun groups and negative comparisons remain disclosed in [the V3 report](evaluation/FINAL_REPORT_V3.md).
