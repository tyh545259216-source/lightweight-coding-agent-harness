# Test-driven Verification and Repair

Phase A observed18/18 coding tasks without a successful test run,9 tasks with pytest exit5, and a final answer falsely claiming success even when hidden functional assertions passed. Verification is an optional host policy, disabled by default, for coding tasks requiring actual edits/tests.

Runner tracks successful write/edit revisions. A latest canonical test result verifies only that revision; later changes invalidate it. After a patch exchange, Runner submits run_tests through the same Executor, policy, deadline and execution journal. It never grants EXECUTE itself, writes a repair patch, or executes unregistered functions. The host paths are explicit VerificationPolicy.test_paths.

Nonzero exit status has structured passed/assertion_failure/collection_error/internal_error/usage_error/no_tests categories with bounded stdout/stderr. Test tool success and test success are different. A failing canonical result prompts another bounded model turn; max_repair_rounds caps repair attempts independently of max_iterations and total time. Test-tool errors stop rather than blindly retrying an uncertain execution.

Telemetry: initial_patch_success, repair_rounds, final_test_success, verification_tool_calls; events verification_requested/result, repair_requested, completion_rejected. Permission denials remain denials. A textual plan cannot satisfy required patch+test evidence. Passing weak tests does not establish semantic correctness: independent benchmark graders must still check behavior/API/mutant rejection.

Verification state and observed execution keys persist in the session. Resume reconstructs saved requirements, refuses changed policy, and uses the existing cached/in-doubt rules; it does not replay side effects. The legacy default loop is unchanged when the policy is absent.
