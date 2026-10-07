# Security and recovery
PermissionPolicy grants independent READ/WRITE/EXECUTE/DANGEROUS capabilities. Default READ only.
A missing capability requires an async human approval callback or explicit policy grant. Denied access
is a structured tool error. Workspace.resolve rejects traversal, drive-relative paths, resolved escapes,
symlinks/junctions pointing outside, and protected .git/.venv/.sessions/.traces/.harness internals.

File reads/writes are bounded; edits require exact counts and use fsynced atomic replacement. Commands
use fixed argv templates, never a shell. EXECUTE runs trusted pytest code, which can access the host:
this harness is NOT an OS sandbox. Same-user concurrent symlink swaps (TOCTOU), hardlinks, hostile tests,
network isolation, secret redaction and containerization are outside the present security guarantee.

SessionStore.lease holds a platform advisory lock released by the OS after a crash. One runner writes
one session. ToolExecutor journals execution_started before effects and execution_completed after success.
Key = turn_id:iteration:call_id; argument fingerprints reject key collisions. Cached completion returns
recorded result. Started/uncertain side effects block automatic replay, including timeout/cancellation and any error after execution started. Error class alone cannot prove that no effect occurred.
Read-only calls can retry safely. No claim of exactly-once transactions across filesystem and JSONL.
Runner.resume finishes missing results and resumes with the remaining round budget. RecoveryBlocked
requires inspecting actual files plus journal; no automatic destructive reconciliation tool is provided.

CLI also protects explicitly configured session/trace files and session lock files, even with custom names. Library hosts should pass these through Workspace(protected_files=...).

run_command pins Git to an absolute executable outside the mutable workspace, disables external diff/textconv/fsmonitor, and sets a discovery ceiling. Repository-local git.bat cannot shadow the allowlisted command.
