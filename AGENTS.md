# ReuseMem Repository Guidelines

## Scope and current status

This private repository studies experience memory for coding agents in evolving
repositories. Use one fixed coding model and harness in the primary comparison:
each development round starts a fresh agent session, while the agent's actual
code and the condition's explicit experience store persist within a task chain.
Task boundaries, session boundaries, and persistence boundaries are separate
experimental choices; do not use these terms interchangeably.

The bootstrap experiment is an offline, deterministic memory replay on original
synthetic fixtures. It does not execute a coding agent or reproduce the original
benchmark. Do not describe its memory-probe scores as coding success or valid
code reuse. Named research systems remain planned until adapters and their
validation are present.

## Organization and development

- Write source, comments, and repository documentation in English.
- Keep the Python environment in this repository separate from each evaluated
  project's dependencies. Use `uv sync` and `uv run` for the harness environment.
- Put reusable implementation in `src/reusemem/`, focused behavioral tests in
  `tests/`, original small fixtures in `examples/`, and protocols in `docs/`.
- Follow the configured Python version and lint rules. For semantic changes,
  test information boundaries, policy behavior, and budget enforcement rather
  than duplicating implementation details in tests.
- Keep generated run outputs, credentials, caches, unpublished papers, raw
  benchmark data, and private trajectories out of version control.

## Experimental integrity

- Audit `code_understanding`, `problem_solving`, and `validation` separately.
  A remembered test result must retain its scope; a previous successful check
  does not establish correctness after arbitrary code changes.
- Never pass hidden tests, reference solutions, expected memory answers,
  validity labels, or future task requirements to a writer or memory policy.
- Isolate memory by chain and condition. Declare built-in memory, global agent
  instructions, plugins, session resumption, and compaction settings.
- Distinguish a controlled maintenance experiment with a shared writer from a
  full-system comparison that preserves each method's native writer.
- Explicit fixture keys and supersession metadata are provided inputs, not
  learned invalidation. Lexical retrieval is not a reproduction of an embedding
  retriever. Recent-window retention is not an LLM rolling summary.
- Record method and environment versions, seeds, budgets, visible inputs, and
  all memory-related costs. Distinguish measurements from planning estimates.

## External materials

The user-provided evaluation bundle remains an external, read-only provenance
source for this scaffold. Keep the new implementation independent and record
provenance and applicable licenses when adding external components.
See [data provenance](docs/data-provenance.md) before connecting benchmark assets,
and follow the
[experiment protocol](docs/experiment-protocol.md) before reporting results.
