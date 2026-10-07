# REAL_REPO_EVAL — V3 local results

MIT dbader/schedule，pinned commit82a43db1b938d8fdf60103bd41f329e06c8d3651。9个来源文件经 hash 校验；license/attribution保留。8个task recipes：2导航、2理解、3注入缺陷修复、1测试添加。不是历史issues，不运行完整上游测试suite。

Grader：实际读源码证据/答案关键词，或固定contract suite+API signature/protected hashes；测试生成还检查original通过/mutant失败。用 test_contract_v3.py/test_candidate_v3.py canonical scope；不得修改contract/pytest配置。

## qwen3-1.7b

AgentTaskSuccess 0/8 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 1；平均轮数 2.62（8/8 observed）；模型工具调用 36；平均耗时 46.72 s（8/8 observed）；外部中断 0；完整 usage 7/8。

### real-bug-1

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: The scheduled-job tag filter returns the wrong subset. Inspect the repository, restore get_jobs(tag) so only jobs bearing that tag are returned, preserve the public API and verify actual tests. Existing contract tests are read-only.
Actual: FAIL；context_limit；rounds 4，tools 4，latency 78.39s。
State: context_limit; repair rounds 0; classification COMPLETED.
Tests/grader: {"stop_reason": "context_limit", "protected_contracts_preserved": true}

### real-bug-2

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Cancelling one scheduled job unexpectedly removes other jobs. Inspect and repair cancellation, preserve the public API, and keep cancellation of an absent job harmless. Verify actual tests; existing contract tests are read-only.
Actual: FAIL；context_limit；rounds 3，tools 9，latency 58.48s。
State: context_limit; repair rounds 0; classification COMPLETED.
Tests/grader: {"stop_reason": "context_limit", "protected_contracts_preserved": true}

### real-bug-3

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: A job is being marked overdue at the exact cancellation deadline. Restore the strict overdue boundary: equality remains eligible, only a later time is overdue, and no configured deadline means not overdue. Preserve APIs and verify tests. Contract tests are read-only.
Actual: FAIL；timeout；rounds 4，tools 7，latency 120.06s。
State: timeout; repair rounds 0; classification TASK_TIMEOUT.
Tests/grader: {"stop_reason": "timeout", "protected_contracts_preserved": true}

### real-nav-1

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Locate Scheduler.get_jobs in this repository. Explain how it filters by tag and what happens when tag is omitted. Cite the actual source path and observed implementation.
Actual: FAIL；final_answer；rounds 2，tools 1，latency 16.10s。
State: final_answer; repair rounds 0; classification COMPLETED.
Tests/grader: {"required_file_evidence": false, "answer_matches": true, "boundary_matches": true, "protected_contracts_preserved": true}

### real-nav-2

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Locate Scheduler.get_next_run and explain the return value when there are no scheduled jobs, including the source path and observed method.
Actual: FAIL；final_answer；rounds 2，tools 2，latency 14.09s。
State: final_answer; repair rounds 0; classification COMPLETED.
Tests/grader: {"required_file_evidence": false, "answer_matches": false, "boundary_matches": true, "protected_contracts_preserved": true}

### real-tests-1

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Add collected, deterministic regression tests in test_candidate_v3.py for Job.should_run before, exactly at, and after next_run. Freeze/mock the clock; equality must be ready. Import the actual package and preserve production source and existing contract tests. Run real tests and report observed results.
Actual: FAIL；context_limit；rounds 1，tools 10，latency 40.52s。
State: context_limit; repair rounds 0; classification COMPLETED.
Tests/grader: {"stop_reason": "context_limit", "protected_contracts_preserved": true}

### real-understanding-1

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Explain Job.should_run using repository evidence. Is equality with next_run considered ready to run? Cite the implementation path and method.
Actual: FAIL；final_answer；rounds 3，tools 2，latency 26.06s。
State: final_answer; repair rounds 0; classification COMPLETED.
Tests/grader: {"required_file_evidence": false, "answer_matches": false, "boundary_matches": false, "protected_contracts_preserved": true}

### real-understanding-2

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Explain Scheduler.cancel_job behavior when the requested job is not scheduled. Cite observed implementation path, method and the exception it handles.
Actual: FAIL；final_answer；rounds 2，tools 1，latency 20.05s。
State: final_answer; repair rounds 0; classification COMPLETED.
Tests/grader: {"required_file_evidence": false, "answer_matches": false, "boundary_matches": true, "protected_contracts_preserved": true}

## qwen3-4b

AgentTaskSuccess 0/8 (0.00%)；HarnessMechanismSuccess N/A（没有可观察机会）；timeout 8；平均轮数 1.00（8/8 observed）；模型工具调用 0；平均耗时 60.11 s（8/8 observed）；外部中断 0；完整 usage 0/8。

### real-nav-1

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Locate Scheduler.get_jobs in this repository. Explain how it filters by tag and what happens when tag is omitted. Cite the actual source path and observed implementation.
Actual: FAIL；timeout；rounds 1，tools 0，latency 60.07s。
State: timeout; repair rounds 0; classification MODEL_RESPONSE_TIMEOUT.
Tests/grader: {"stop_reason": "timeout", "protected_contracts_preserved": true}

### real-nav-2

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Locate Scheduler.get_next_run and explain the return value when there are no scheduled jobs, including the source path and observed method.
Actual: FAIL；timeout；rounds 1，tools 0，latency 60.15s。
State: timeout; repair rounds 0; classification MODEL_RESPONSE_TIMEOUT.
Tests/grader: {"stop_reason": "timeout", "protected_contracts_preserved": true}

### real-understanding-1

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Explain Job.should_run using repository evidence. Is equality with next_run considered ready to run? Cite the implementation path and method.
Actual: FAIL；timeout；rounds 1，tools 0，latency 60.15s。
State: timeout; repair rounds 0; classification MODEL_RESPONSE_TIMEOUT.
Tests/grader: {"stop_reason": "timeout", "protected_contracts_preserved": true}

### real-understanding-2

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Explain Scheduler.cancel_job behavior when the requested job is not scheduled. Cite observed implementation path, method and the exception it handles.
Actual: FAIL；timeout；rounds 1，tools 0，latency 60.13s。
State: timeout; repair rounds 0; classification MODEL_RESPONSE_TIMEOUT.
Tests/grader: {"stop_reason": "timeout", "protected_contracts_preserved": true}

### real-bug-1

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: The scheduled-job tag filter returns the wrong subset. Inspect the repository, restore get_jobs(tag) so only jobs bearing that tag are returned, preserve the public API and verify actual tests. Existing contract tests are read-only.
Actual: FAIL；timeout；rounds 1，tools 0，latency 60.11s。
State: timeout; repair rounds 0; classification MODEL_RESPONSE_TIMEOUT.
Tests/grader: {"stop_reason": "timeout", "protected_contracts_preserved": true}

### real-bug-2

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Cancelling one scheduled job unexpectedly removes other jobs. Inspect and repair cancellation, preserve the public API, and keep cancellation of an absent job harmless. Verify actual tests; existing contract tests are read-only.
Actual: FAIL；timeout；rounds 1，tools 0，latency 60.10s。
State: timeout; repair rounds 0; classification MODEL_RESPONSE_TIMEOUT.
Tests/grader: {"stop_reason": "timeout", "protected_contracts_preserved": true}

### real-bug-3

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: A job is being marked overdue at the exact cancellation deadline. Restore the strict overdue boundary: equality remains eligible, only a later time is overdue, and no configured deadline means not overdue. Preserve APIs and verify tests. Contract tests are read-only.
Actual: FAIL；timeout；rounds 1，tools 0，latency 60.11s。
State: timeout; repair rounds 0; classification MODEL_RESPONSE_TIMEOUT.
Tests/grader: {"stop_reason": "timeout", "protected_contracts_preserved": true}

### real-tests-1

Repository/source: https://github.com/dbader/schedule; pinned commit 82a43db1b938d8fdf60103bd41f329e06c8d3651; license MIT.
Expected: Add collected, deterministic regression tests in test_candidate_v3.py for Job.should_run before, exactly at, and after next_run. Freeze/mock the clock; equality must be ready. Import the actual package and preserve production source and existing contract tests. Run real tests and report observed results.
Actual: FAIL；timeout；rounds 1，tools 0，latency 60.10s。
State: timeout; repair rounds 0; classification MODEL_RESPONSE_TIMEOUT.
Tests/grader: {"stop_reason": "timeout", "protected_contracts_preserved": true}
