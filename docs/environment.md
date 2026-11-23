# Environment and Resource Plan

## Bootstrap environment

The current target is a CPU-only, deterministic replay of synthetic experience
records and memory queries. It requires Python 3.11 or newer, as declared in
`pyproject.toml`, and the repository's `uv` environment. It requires no GPU,
model weights, hosted inference, or API credentials.

```sh
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
```

The repository's `.python-version` selects Python 3.11. Use the CLI commands
documented in [the README](../README.md) for a replay run.
The bootstrap uses lexical retrieval and an approximate text-token budget; it
does not measure a model tokenizer's actual token usage. Preserve the lockfile
when dependency changes affect it. Record Python, platform, CPU, RAM, elapsed
time, fixture hash, code commit, and run configuration with reported results.

## Environments for future coding runs

The memory harness and the evaluated repositories have different dependencies.
Keep this repository's `.venv` for experiment orchestration and scoring. Build a
separate environment for each original repository at its recorded source commit,
using the original setup recipe and dependency locks where available. Do not
install all evaluated projects into one mutable Python environment.

Prefer a pinned Docker image per repository when the original environment can
be reproduced that way. Record the image digest, base image, repository commit,
dependency lock hash, setup commands, and any local patches. If containers are
unavailable, use an isolated virtual environment per repository and record the
same information. Pin the coding harness separately from the task environment.

Before a paid coding run, smoke-test repository import/build commands and visible
checks in the intended environment. Use evaluator-side reference checks to
validate the environment without exposing their solutions or results to the
agent. An environment that is missing original data or dependencies is not a
failed memory policy.

## Fixed agent and isolation

The primary online experiment will hold the coding model, harness version,
prompts, tool permissions, context limits, and sampling settings fixed. The
condition changes the explicit experience memory. Each round starts a fresh
session and retains the agent's actual preceding code; session resumption is
disabled for that protocol.

Use isolated homes/configuration directories and per-chain memory namespaces.
Disable or declare global persistent memories, automatically loaded notes,
plugins, skills, and instruction files that could transfer experience between
conditions. Keep within-session context and compaction settings identical. Wait
for asynchronous memory writes to finish before starting the next session.
Repository files remain available code context even in the no-memory condition.

Record the backing store and reset procedure for every memory adapter. A reset
must remove persistent records, vectors, caches, and external service namespaces
associated with the chain; clearing only the local prompt is insufficient.

## Resource accounting

The bootstrap consumes CPU time and local storage only. A complete coding-agent
comparison has not yet been profiled. The proposal's one-GPU, at most 12 GB per
GPU and at most four total GPU-hours is an unmeasured planning estimate, not a
resource allocation or a verified budget for every proposed memory system.

Pilot a small chain before committing to a full run. Count inference used by
experience extraction, updating, retrieval, verification, and generation, along
with embedding and service costs. Report total GPU-hours across devices and
runs for measured local inference. Record personal hosted-API credits, provider,
cost, and source separately from a course-pool request; do not invent GPU-hours
for opaque hosted inference.

If the pilot exceeds the available budget, reduce the number of chains, task
size, or history window and preserve a paired comparison. Cached agent-visible
trajectories can support a smaller replay study, provided its claims remain
separate from online coding performance.
