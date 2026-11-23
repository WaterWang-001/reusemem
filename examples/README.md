# Synthetic memory replay examples

`synthetic-chains.jsonl` contains three hand-written development chains, each
with four tasks. These are small, inspectable protocol checks, not a benchmark
release or experiments on the original coding dataset. They exercise memory
retrieval without running an LLM coding agent.

Each JSONL row provides the observations available after one task in
`visible_experiences`. The separate `queries` field contains evaluation probes
and their expected answers. Only the former may be passed to a memory writer.
Every policy receives the same experience keys, revision labels, and update
links. The examples therefore evaluate policies under structured metadata;
they do not measure automatic key extraction or contradiction discovery.

| Chain | Repository change | Knowledge that should survive |
| --- | --- | --- |
| `synthetic-batch-helper` | A reusable batch utility is added. | Zero is valid; existing validation results remain useful. |
| `synthetic-timeout-fix` | Explicit `None` checking fixes a zero-value fallback bug. | Parser conventions and invalid-input checks remain useful. |
| `synthetic-identifier-fix` | Full matching replaces buggy prefix matching. | Naming conventions and empty-input checks remain useful. |

Each chain has current, updated, unaffected, and historical probes. A historical
probe uses `at_revision` to request an earlier repository state. The timeout
chain also delivers an old observation after the fix: its task runs at `r2`,
but that observation remains explicitly scoped to `r1`. Arrival order should
not make it the current fact. No example requires deciding between two
unresolved contradictory observations of the same revision.

The executable snapshots in `toy_repo/r1/` and `toy_repo/r2/` ground the notes
in actual Python behavior. `tests/test_examples.py` imports both snapshots and
checks the utility addition, the zero-value fix, and the identifier fix. It
also checks that expected answers refer only to observations already visible
at each probe. The snapshots contain intentional bugs in `r1`.

From the project root, run the replay with the CLI documented in the main
README, and validate the examples with:

```sh
uv run pytest tests/test_examples.py
```
