# Public release checklist

Local preparation only. Remote repository creation, publication, push and remote CI: NOT RUN.

- VERIFIED by final local audit: whitelist export excludes work/model blobs/model files, raw sessions/traces/workspaces, virtual environment, bytecode, pytest/coverage temporary files and runtime caches.
- VERIFIED by final local audit: no forbidden model/private files in current Git index.
- VERIFIED locally: secret and absolute-host-path pattern scans; pattern scanning cannot prove absence of every possible secret.
- VERIFIED locally: tests, statement/branch coverage, lint, format, types, offline and MCP demos.
- PARTIAL: portable installation and Windows/Linux remote CI remain NOT RUN.
- Final audit data: work/public-audit-v3-final.json (private local audit log).
- Public export is an explicit whitelist, not git add-all; no remote package uploaded.
