# Behavior optimization V3

V2 observations and graders remain frozen at baseline a0f6759.

## Observation-first (L)

Explicit task policy marks coding tasks; prose classification is not silently imposed.
The optional controller consumes only successful executor results. Directory listings
and searches locate paths; actual reads provide source evidence. Existing-file edits
require inspection, location and a read of that target. New files require an inspected
parent and relevant existing source. Model claims and failed tools are not evidence.
Policy feedback identifies missing evidence and permits at most the configured replans.
Audit/free-loop mode measures violations without enforcing. Non-coding tasks do not
require the coding workflow. No task ID/file-name answers are embedded in the guard.
All effects still enter the same executor schema, permissions and journal. Saved policy
and workspace must match on resume; dropped policy is refused. The trace records
policy_violation/evidence_collected and statistics record replanning_count. This guard
is a workflow constraint, not proof that a read was understood or an edit is correct.

Real comparison is pending until the V3 experiment protocol is frozen. Scripted tests
verify runtime mechanics only, never model intelligence.

## Repository navigation (M)

V3 tools are explicitly enabled with builtin_registry(..., navigation_v2=True).
Legacy tool output stays available for V2 reproduction. V3 read_file returns
path/start_line/end_line/total_lines/has_more/full-file sha256/content. Default200-line
chunks and400-line maximum require continuation. Invalid ranges disclose total lines.
repository_map scans at most2000 files, returning at most300 metadata rows; Python
AST symbols are top-level only. symbol_search uses literal name matching, no regex
or vector retrieval. Protected directories, directory links and credential files
are excluded. No whole-source repository dump. With complete-read policy enabled,
partial header reads cannot authorize an existing-file edit; ranges accumulate only
at the same observed revision. The guard still cannot prove semantic understanding.

## Structured errors and model retries (N)

Every executor failure has error_type/tool/invalid_field/received/expected/retryable/
hint; path and range failures additionally expose bounded confirmed candidates or
legal line ranges. Long received values are bounded. Permission failures never grant
retry authority. The model submits corrected arguments explicitly; the host does not
choose a candidate or auto-execute a retry. Identical invalid fingerprints allow at
most configured retries, and total attempts remain bounded by the runner iteration/
time caps. Recovered_argument_errors counts a successful corrected tool call after
an observed retryable error; repeated_invalid_calls counts repeated failed validation.
Saved repair state/policy survives resume. Uncertain side-effect execution retains
its V2 reconciliation rule, regardless of a retry hint.

## Preconditioned patching (O)

apply_patch requires an observed full-file sha256, one exact old/context match and
a different replacement. Stale/context-mismatch/no-op patches reject without writing.
Atomic replacement preserves existing file permissions; success reports actual changed
line count, bounded unified diff and new hash. Optional preview_only computes a diff
without dirtying verification (WRITE grant remains required by the declared schema).
This is one-file exact-context patching, not a general multi-file patch interpreter.
Prefer-patch policy can reject whole-file/legacy edits of existing files; creating a
new test file remains possible via write_file after observation. API preservation is
verified by task checks, not an editor hardcoded-name restriction. Existing TOCTOU,
hardlink and trusted-host execution limitations remain; no sandbox claim is added.

## Task-specific completion gate (P)

A host policy specifies changed targets and whether independent checks exist. Status
is VERIFIED_SUCCESS/VERIFIED_FAILURE/UNVERIFIED, separate from model prose. Success
requires actual target byte changes, current observed canonical test pass, and current
independent pass when required. A no-op rewrite or stale test snapshot cannot succeed.
The host-only independent_check tool uses the same executor/EXECUTE permission/journal;
it is absent from model definitions and model-origin calls are refused. Checks can
validate behavior/API/mutants without hardcoding names in the editor. Failed independent
checks enter the same bounded repair budget; execution failures stop without uncertain
replay. Canonical failure projection retains failed tests, exception/assertion evidence
and a bounded relevant summary; raw diagnostics stay local. Saved requirements and
initial/tested/independent file hashes must survive resume unchanged. Snapshot hashes
are local consistency checks, not protection against concurrent hostile filesystem
mutation or proof beyond test scope.

P validation exposed a V2 runtime test hazard: same-size source edits within a timestamp
window could reuse stale Python bytecode. V3 canonical pytest now uses a fresh private
pycache prefix and disables bytecode writes. A fixed-size/fixed-mtime regression proves
that fresh source is tested. This runtime fix does not change frozen V2 scores or its
grader. Completion change comparison normalizes CRLF/LF so line-ending-only rewrites
are not counted as substantive target changes; patch revision hashes remain exact bytes.

## Optional compact/full skills (Q)

Same three names and unchanged metadata descriptions. SKILL.md bodies now contain only
steps/constraints; original V2 full bodies are retained in references/FULL.md and at
baseline commit. NO_SKILL omits the loader/catalog/tool in V3 evaluation.
SELECTED_SKILL_COMPACT and SELECTED_SKILL_FULL route on identical lexical metadata;
full mode or explicit detail=full activation loads the one requested full reference.
Other references/scripts are never eagerly injected/executed. Saved active detail
survives resume. V3 default has no automatic skill loading; comparisons remain optional.
Token/cost conclusions will use model-reported outcomes, not body length as token metrics.
V2 source/skill-hash reproduction requires the frozen baseline checkout.

## Context V3 and inspection (R)

V2 naive/managed results remain unchanged in docs/ABLATION.md. MANAGED_V3 adds priority
for the latest source-read exchange, repository map/symbol exchange and failed canonical
test exchange, retaining their complete tool call/result groups. Skills/latest task/
recent groups stay pinned. Structured source/diff/failure leaves are bounded and source
truncation is marked explicitly. Repeated host policy feedback retains its latest rule.
If pinned evidence cannot fit, stop instead of silently dropping it. This guarantees
client projection integrity, not the model's semantic retention or server tokenization.
Opt-in inspection records actual retained messages, dropped group descriptions, summary,
byte proxy estimate, pinned indexes and reasons in private traces; it is silent on the
terminal. Inspection indexes refer to projected groups after skill injection.

For larger modules, a task policy can require the relevant function span instead of
whole-file reads. Exact edit/patch context must occur in actually observed bounded
chunks; unobserved sections cannot be authorized by reading an unrelated header.
Whole-file mode remains configurable and tested. This avoids forcing an entire large
module into the prompt just to modify one observed function.
