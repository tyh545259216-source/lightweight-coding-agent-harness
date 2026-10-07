# Publication scope and reproducibility

Publish the audited public export/ZIP. Private originals remain in local eval/results
and work, preserved for forensic review. Do not upload the entire local directory.
The public inventory includes source, meaningful tests, examples, skills, docs,
frozen datasets/protocol, measured projections and redacted bad cases. Raw model
messages, sessions, traces, benchmark workspaces, local archives, caches, models
and machine paths are excluded. Hidden grader recipes are public for reproducibility;
models receive only fixture prompts and visible repository files during evaluation.

`python scripts/public_audit.py` checks known credential patterns and absolute
host paths in the declared inventory and reports **locations only**, never matched
secret values. This is a reproducible pattern audit, not an exhaustive secret
scanner or runtime secret redactor. It does not sandbox generated tests.

GitHub Actions runs tests/coverage, Ruff, mypy, offline coding demo, real fixture
MCP demo and public scan on Windows/Linux with Python3.12. It uses
[checkout v7](https://github.com/actions/checkout/releases/tag/v7.0.0) and
[setup-python v6](https://github.com/actions/setup-python/releases/tag/v6.0.0).
Remote CI is configured; local validation does not claim a hosted workflow ran.

For a fresh real evaluation, install an existing supported local model independently,
verify the protocol, and use a new output directory. No model download happens in
this project. `run_experiments_v2.py` recreates the frozen run layout; the collector
requires complete matching raw runs before deriving public records. Existing local
raw evidence is never overwritten. Check dataset/skill/source hashes and actual
provider/config values before comparing metrics.

Public projection rows reference raw record lines and SHA256 trace/record hashes.
They deliberately do not include full raw sessions. Independent observers can
reproduce the benchmark, but cannot verify excluded raw byte contents from hashes
alone without obtaining the original local evidence. Report this audit limitation.

.gitattributes disables automatic line-ending conversion so frozen raw source/task/skill checksums survive Windows/POSIX checkout. Normal text diffs remain available. Do not rewrite heldout files to normalize newlines after freezing.
