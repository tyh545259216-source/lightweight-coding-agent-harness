# Security scope

Workspace Guard ≠ OS Sandbox. File tools enforce workspace-relative resolution, permissions and protected paths. `run_tests` and Python execute with host privileges; do not run this project directly on untrusted code. An execute grant is not an operating-system isolation boundary.

MCP servers must be trusted. Their processes can access the host; protocol validation does not sandbox them. Never rely on server hints as permission grants.

Durable recovery blocks uncertain side-effect replay, but does not provide exactly-once semantics for arbitrary external services. Context budgeting and bounded retries limit runtime behavior; they do not prove production security.

Keep credentials out of prompts, repositories and traces. Local outputs live under ignored `work/`, session/trace/cache paths; the release uses an explicit allowlist and secret/path scanning. Pattern scans have false negatives and do not replace manual review.

Do not publish sensitive vulnerability details or credentials. Before public release, configure a private maintainer contact or GitHub private vulnerability reporting; that channel is currently NOT CONFIGURED because the repository has not been created.
