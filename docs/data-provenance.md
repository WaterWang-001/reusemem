# Data Provenance and Access Boundaries

## Original bootstrap fixtures

The small JSONL chains and versioned Python examples under `examples/` are
original synthetic material for this repository. They exercise added helpers,
bug fixes, unaffected knowledge, delayed older evidence, and historical queries.
They are not an extract of a private benchmark or a reproduced coding-agent
trajectory.

Visible records are authored observations, not model-generated memories.
Expected answers and source annotations are evaluation labels. Keep these
labels out of memory-policy inputs and do not claim that supplied revision or
supersession metadata was inferred by a model. Record a fixture hash in each
run so later changes to examples do not silently change the comparison.

## External user-provided bundle

The reference bundle is located outside this repository:

```text
/Users/sizhewang/Downloads/codeflow-eval-v5-575d84a/
```

Treat this path as read-only. Its README identifies a code snapshot from branch
`evalkit`, commit `575d84a559174241823a0e184395be54a1da8bb2`; the bundle is not a
Git checkout with full history. It supplies construction/evaluation code,
manifests, and small numeric audit artifacts, but does not supply a `LICENSE`,
the complete raw benchmark, raw agent trajectories, or ready-to-run original
repository environments.

This scaffold references the bundle externally and contains no copied bundle
code, manuscripts, raw task data, or trajectories. Record externally reported
statistics as reported results, not as fresh ReuseMem reproductions. Record the
provenance and applicable license of any external components added later.

## What is still required for benchmark experiments

Before connecting original tasks, locate and record:

- Raw task chains and their task order, repository identities, and revision
  commits.
- The agent-visible trajectories and historical code artifacts needed for
  replay, with a documented redaction and visibility policy.
- Original dependency recipes, lockfiles, datasets, and container images or
  equivalent reproducible environment specifications.
- Evaluation-only tests, reference artifacts, and reuse annotations under a
  separate access boundary.
- Applicable licenses and access restrictions for each asset class.

Keep external asset locations in local configuration rather than embedding
private data in source control. For each experiment, record source URI or local
reference, access date, checksum, original commit, conversion code commit,
filtering, exclusions, and the final selected chain IDs. Publish only artifacts
whose release is authorized.

## Conversion and contamination audit

The visible experience envelope may contain the task already presented to the
agent, its actions, source it actually saw, visible diffs, and local check
outputs. Reference solutions, hidden tests and their feedback, future task
requirements, gold reuse targets, and evaluator result files belong only to the
scorer. Check the conversion path for accidental imports of these fields.

Audit the existing historical-note channel before adding another memory store.
In the primary comparison, replace or remove that channel consistently across
conditions so it does not bypass the selected policy. Persistent actual code is
part of the environment and remains available even when explicit memory is
absent. Record snapshots and hashes to verify the intended boundaries.

Mostly additive original chains can support a study of accumulated reuse.
Claims about obsolete knowledge additionally require inspected changes that
invalidate previously applicable conclusions, alongside unchanged controls and
useful-history queries. Label synthetic interventions and their construction
separately from naturally occurring changes in the original data.
