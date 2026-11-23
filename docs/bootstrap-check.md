# Bootstrap Verification Record

Date: 2026-11-23. Scope: CPU-only protocol checks, with no model or API calls.

## Environment

- macOS on arm64; Python 3.11.15; uv 0.10.8.
- pytest 8.4.2 and Ruff 0.17.6 from the committed lockfile.
- No GPU or Docker was required for these checks.

## Checks completed

| Check | Outcome |
| --- | --- |
| Local behavioral and example tests | 18 passed |
| Ruff | Passed |
| Bundled demo | Completed all four policies on 3 chains / 12 tasks / 22 probes per policy |
| External evaluation snapshot availability | Required code entry points found |
| External snapshot's six synthetic scoring test modules | 96 passed |

Reproduce the local checks using the [quick start](../README.md#quick-start).
Use `scripts/check_external_eval.py` with an external snapshot root to repeat
the last check; the snapshot is not included in this repository.

## Interpretation

The checks establish that the initial replay, information boundaries, budget
accounting, and synthetic code examples run in the prepared environment. They
do not establish performance of a coding agent or any named paper method.
The external tests check scoring machinery with synthetic fixtures; they do not
reproduce original benchmark results or validate repository runtime environments.

A small-budget review found an eviction edge case: delayed older evidence could
become active once a newer same-key note had been evicted. The revision control
now conservatively archives newly arriving older-revision evidence, and a
regression test covers this sequence. This is explicit metadata handling, not
learned invalidation of a development claim.

Each generated run stores input/source hashes, configuration, Git revision,
environment metadata, and inspectable read/write traces. Generated outputs stay
outside version control. The next experiment adds actual trajectory extraction
and a fixed coding harness before measuring downstream task success or reuse.
