# Tools
ToolRegistry registers only explicit BaseTool objects. prepare_call parses an object and validates strict
Pydantic schemas (extra fields/coercion rejected). ToolExecutor applies permission, timeout, error translation.
Seven built-ins: list_dir, read_file, grep (literal, bounded), write_file (atomic replace), edit_file (exact
match count), run_command (three fixed argv templates), run_tests (pytest against contained paths).
run_tests returning nonzero is a successfully executed tool with failing tests; evaluators check exit_code.
Tool errors carry unknown_tool/arguments/permission/timeout/execution categories and can be corrected by the model.
No shell=True. READ is the default capability. Writes and execute require explicit policy grants.

## Built-in contracts

- `list_dir`: contained directory, bounded names; does not recursively read file contents.
- `read_file`: UTF-8, one-based start/end lines, file limit 1 MiB.
- `grep`: literal matching with glob filtering, bounded visited files and matches.
- `write_file`: creates parents inside the workspace and uses temporary-file atomic replacement.
- `edit_file`: exact old/new text and required occurrence count; mismatch leaves the file unchanged.
- `run_command`: only Python version, Git short status and Git diff statistics. Python is the host
  executable. Git is resolved outside the mutable workspace when the tool is constructed, fsmonitor,
  external diff and textconv are disabled, and ancestor repository discovery is bounded.
- `run_tests`: invokes host Python `-m pytest` for contained paths, drains bounded output and cleans
  up its process tree on timeout/cancellation. Tests are executable project code, not safe data.

Local InputModel uses strict mode and forbids extra fields. For example, `{"path": 3}` cannot silently
become the filename `"3"`, and malformed JSON becomes an `arguments` result. MCP parameters are
validated against the remote JSON Schema by jsonschema, with remote references prohibited.

ExecutionResult carries `call_id/name/ok/content/error_type/replayed`. Runner stores it as a JSON
tool message linked to the original tool_call_id. Cached results preserve their original outcome;
an in-doubt side effect produces `recovery_blocked` rather than a new execution.

Tests: `test_complete_tool_flow`, strict-schema cases in `test_tools.py`, Git-shadow tests, actual
delayed-child timeout tests and spawn-cancellation cleanup. Windows cleanup was exercised locally;
the POSIX process-group branch was not executed on this host.


## Built-in contracts

- list_dir: contained directory, bounded names; does not recursively read file contents.
- read_file: UTF-8, one-based start/end lines, file limit 1 MiB.
- grep: literal matching with glob filtering, bounded visited files and matches.
- write_file: creates contained parents and uses temporary-file atomic replacement.
- edit_file: exact old/new text and required occurrence count; mismatch leaves the file unchanged.
- run_command: Python version, Git short status and Git diff statistics only. Python is the host executable. Git is pinned outside the mutable workspace at construction, fsmonitor/external diff/textconv are disabled, and ancestor repository discovery is bounded.
- run_tests: host Python -m pytest for contained paths, bounded output drains and process-tree cleanup on timeout/cancellation. Tests are executable project code, not safe data.

InputModel uses strict mode and forbids extra fields: a numeric path cannot silently become a string. Malformed JSON becomes an arguments result. MCP arguments use jsonschema with remote references prohibited.

ExecutionResult carries call_id/name/ok/content/error_type/replayed. Runner stores it as a JSON tool message linked to tool_call_id. Cached results preserve their outcome; in-doubt side effects produce recovery_blocked.

Tests cover complete_tool_flow, strict schemas, shadow Git executables, delayed-child timeouts and spawn cancellation. Windows cleanup ran locally; POSIX process-group cleanup was not executed here.
