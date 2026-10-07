# V2 interview additions

1. **Why analyze failures before changing prompts?** V1 traces showed planning-only completion, poor edits and invalid arguments. Context loss was not an observed primary cause; context reliability therefore cannot be claimed as the explanation for coding failures.
2. **Why does tool ok differ from test success?** A pytest process can execute normally but return1 for assertion failure or5 for no collected tests. Verification parses exit/status explicitly.
3. **What does a passing canonical suite prove?** Only that the configured collected tests passed on that revision. Test-generation stubs can pass while detecting no bug; the independent grader requires mutant rejection.
4. **How is repair bounded?** Maximum model repair rounds, normal iteration/model/task limits, and explicit repair-limit stop. Each accepted write/edit invalidates previous test success.
5. **How does recovery avoid weakening verification?** Persist policy/revision/outcome and restore it on resume; changed test requirements are refused. Completed test results are cached; uncertain side effects are not replayed.
6. **Why preserve call/result pairs?** Transport expects one correlated result per assistant call. Dropping half an exchange can break the protocol or misrepresent execution.
7. **Why are state/summary messages advisory?** They contain extracted tool data, which is untrusted. Promoting stdout to privileged system instructions would worsen prompt-injection risk.
8. **Are token budgets exact?** No. Serialized UTF-8 bytes are a conservative proxy. Actual provider usage is reported separately and may be partial after timeouts.
9. **What does skill selection accuracy mean?** Exact active-name-set agreement with expected Skills-case metadata labels. Lexical routing is transparent rules, not an LLM intelligence result; all-loaded over-selection can have0 accuracy.
10. **What is the tool selection metric's weakness?** Category-relevant capabilities can be selected with wrong paths/arguments or in the wrong sequence. Read argument/error/ordered-chain metrics and bad cases separately.
11. **Why does a recovery-disabled variant score unsupported?** It lacks the capability required by the checkpoint fixture. The overall denominator measures capability coverage, while executed counts/observed cost remain separate.
12. **Why are V1/V2 scores not directly comparable?** V2 changes tasks, prompts, stricter API/evidence/mutant grading and modules. Only within-V2 paired comparisons hold the protocol fixed.
13. **Why not add HTTP MCP merely for the resume?** Current MCP changes protocol metadata and message semantics as well as transport. A POST wrapper would not establish compatibility; scope stays explicit legacy stdio.
14. **What does the public audit guarantee?** Known secret/host-path patterns are checked in a declared export inventory. It is not exhaustive detection, arbitrary runtime redaction or an OS sandbox.
15. **What remains weak?** Small-model planning, argument/path selection, correct edits and meaningful tests, plus CPU deadlines. A reliable stop/result ledger does not imply a reliable autonomous coding model.
16. **What can an interviewer reproduce offline?** Tests, scripted actual coding tools, real MCP subprocess integration, strict schemas/permissions/recovery and grader integrity. Real intelligence scores require the local model and frozen protocol.
