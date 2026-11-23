# ReuseMem

**Updating Agent Memory for Code Reuse in Evolving Repositories**

ReuseMem studies how coding agents accumulate, revise, and reuse development
experience across tasks in the same repository. The central question is:
**Which memory policy keeps current information without losing useful history?**

We examine three kinds of experience:

- **Code understanding and use:** reusable functionality, preconditions, and conventions.
- **Problem solving:** failure observations, attempted fixes, explanations, and lessons.
- **Validation:** useful checks, edge cases, observed outcomes, and their scope.

The intended coding experiment fixes the model and harness, starts a fresh
conversation for each task, and preserves the agent's actual earlier code.
External experience memory is the experimental variable. Native harnesses are
not being ranked.

## Current status

This first version is an **offline experiment scaffold**. It provides executable,
synthetic memory probes and a small Python repository with two revisions. It does
not yet execute a coding agent or reproduce a published memory system.

| Component | Status |
| --- | --- |
| Three experience categories; separate visible records and evaluation labels | Implemented |
| No memory, append-only retrieval, recent-record window, keyed revision | Implemented deterministic controls |
| Current, updated, unaffected, and historical memory probes | Implemented |
| Per-chain isolation, bounded storage/retrieval, inspectable traces | Implemented |
| Mem0, SimpleMem, ReasoningBank, LLM rolling summaries | Planned integrations |
| External multi-round coding benchmark and agent execution | Requires separate data and integration |

The keyed-revision control receives explicit keys and supersession metadata
available to every policy. It does not discover obsolescence from code changes,
and it is neither Mem0 nor the proposed ReuseMem method. The recent-record window
does not generate a summary. These distinctions keep the initial experiment
inspectable.

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run from
this repository:

```bash
uv sync --locked
uv run --locked reusemem doctor
uv run --locked reusemem demo --output outputs/demo
uv run --locked pytest
uv run --locked ruff check .
```

Python 3.11+ is required; `.python-version` selects 3.11. The package has no
runtime dependencies. The lockfile pins pytest and Ruff; the build backend is
version-pinned in `pyproject.toml`. Initial installation can require network access; the
installed demo and tests require no API key, model download, GPU, or Docker.

The demo writes its report to `outputs/demo/summary.md`. Use a new output
directory for each invocation; the CLI refuses to overwrite an existing run.
Generated results are ignored by Git.

## Run a controlled comparison

```bash
uv run --locked reusemem replay \
  --input examples/synthetic-chains.jsonl \
  --output outputs/small-budget \
  --policies no_memory append_only recent_window keyed_revision \
  --memory-budget 512 \
  --retrieval-budget 192
```

Budgets use a documented character-based token approximation, not a model
tokenizer or measured API usage. Archived history counts toward storage.

The input contains three short synthetic chains, each with four tasks. Every
episode separates `visible_experiences` from `queries` and their expected
answers. The replay writes the visible records, then issues diagnostic memory
queries. It selects a record deterministically and compares its content with
evaluation-only answers. These are **post-write memory probes**, not measurements
of a coding agent's next-task success.

Outputs include:

- `summary.md` and `summary.json`: results overall and by experience category.
- `results.json`: individual query outcomes and denominators.
- `traces.jsonl`: memory before/after writes, retrievals, and selected records.
- `manifest.json`: input and implementation hashes, Git revision, and configuration.
- `environment.json`: interpreter, platform, and package versions.

Scores describe this synthetic fixture and this deterministic reader. A memory
policy ranking here is not evidence of better coding performance. The executable
toy repository tests check the factual anchors used by the examples.

See [the example format](examples/README.md) for the schema and supported probes.

## External evaluation environment

Keep the existing evaluation code, raw benchmark, trajectories, and pinned source
repositories outside this Git repository. Check availability without importing or
executing external code:

```bash
uv run --locked reusemem doctor \
  --external-eval-root /path/to/codeflow-eval-v5-575d84a
```

If the raw inputs are available, check them separately:

```bash
uv run --locked reusemem doctor \
  --external-eval-root /path/to/codeflow-eval-v5-575d84a \
  --benchmark-root /path/to/Codeflow-v2-1028 \
  --trajectories-root /path/to/trajectories
```

These are availability checks, not a validation of dataset identity or coverage.
The external snapshot does not include the full benchmark or original
trajectories. Offline rescoring of old trajectories cannot establish how a new
memory policy changes agent behavior; that requires new coding rollouts.

The snapshot's synthetic scoring tests can be run with the same environment:

```bash
uv run --locked python scripts/check_external_eval.py \
  --root /path/to/codeflow-eval-v5-575d84a
```

The wrapper imports the external snapshot and runs its tests in a subprocess;
it does not copy code or data into this repository. Bytecode and pytest cache
writes to the external input are disabled.

## Experiment plan and documentation

- [Environment](docs/environment.md): lightweight local setup and separate coding environments.
- [Protocol](docs/experiment-protocol.md): state boundaries, fair comparisons, and evaluation.
- [Baselines](docs/baselines.md): implemented controls and planned paper methods.
- [Data provenance](docs/data-provenance.md): synthetic examples and external input boundaries.
- [Bootstrap checks](docs/bootstrap-check.md): completed checks and their interpretation.

The next implementation stage connects a fixed coding harness to each memory
system's own write and retrieval pipeline. First inspect the three experience
categories on shared histories, then run complete development chains. All
memory-side inference costs must be recorded. Hidden tests, reference solutions,
and reuse-target labels remain evaluation-only.
