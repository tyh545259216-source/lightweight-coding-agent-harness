# Tutorial walkthrough

Tutorial / Demonstration only. Not part of benchmark scores.

```sh
python examples/tutorial_demo.py
python examples/tutorial_demo.py --demo navigation
python examples/tutorial_ollama.py --model qwen3:1.7b
```

## Actual offline results

Both scripted FakeProvider tutorials were executed successfully with real tools and pytest: seven total tool calls, seven model/script rounds, VERIFIED_SUCCESS, protected tests unchanged. These are deterministic runtime demonstrations, not successful autonomous coding by an LLM.

Bugfix: list_dir → grep → read implementation → read read-only tests → SHA/context apply_patch → run_tests → final gate / host verification. Navigation uses repository_map → symbol_search before the same read/patch/test flow. Each dependent call is a separate response. The patch precondition uses the exact UTF-8 source bytes, preserving Windows line endings.

Fixtures live under [examples/tutorials](../examples/tutorials), independent of benchmark datasets and oracles. They intentionally contain one tiny bug each; the runner copies them into a fresh ignored workspace. Test files and pytest configuration are read-only to file tools; final byte hashes check preservation. Host Python still has host privileges, so this is not an OS sandbox.

The redacted JSON samples are actual **offline scripted** event projections: [bugfix](../examples/tutorials/bugfix_trace_redacted.json), [navigation](../examples/tutorials/navigation_trace_redacted.json). They contain tool names/outcomes, not raw prompts, sessions or personal paths.

## Live tutorial status

Real Ollama generation: **NOT RUN for this RC**. Live behavior is model-dependent / best effort, with one attempt and bounded rounds/time. No new model is downloaded. A deliberately unavailable local endpoint was tested: the command returned a concise setup hint and exit2, without a traceback.

During offline tutorial development, import wiring, read-only-versus-hidden protection and CRLF SHA wiring errors were corrected in the example harness. Failed private attempts remain retained. Runtime, benchmark fixtures, graders and V3 results were not changed.
