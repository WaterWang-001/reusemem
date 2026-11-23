# Experiment Protocol

## Research questions and status

1. Which memory policy keeps current information without losing useful history
   as a repository evolves?
2. Can a memory-update strategy improve that tradeoff and support correct code
   reuse under a shared resource budget?

The implemented scaffold targets offline deterministic memory probes. These
probes check storage, retrieval, retention, and scoring plumbing; they do not
answer whether a coding agent writes better code. Online coding evaluation and
adapters for named research systems are later stages.

## Experience categories

| Category | What the audit asks | Example of a bounded claim |
| --- | --- | --- |
| `code_understanding` | Does memory preserve reusable functionality and its conditions? | A helper supports list inputs at a particular revision; behavior for generators is unknown. |
| `problem_solving` | Does memory preserve attempts, failures, diagnoses, and decisions? | A truthiness fallback discarded zero; a later explicit `None` check fixed that failure. |
| `validation` | Does memory preserve checks, results, and their scope? | Empty-list and zero-input checks passed at a given revision; Unicode inputs were not checked. |

These are audit dimensions, not an assertion that existing memory systems use
these exact fields. They concern general per-round experience, not interfaces
alone. A policy may preserve current conclusions while losing useful failure
history or overgeneralizing earlier validation.

## Boundaries and invariants

A development task, an agent session, and a persistent workspace are distinct.
One long development task can span fresh sessions; multiple requirements can
also share a session. The planned online protocol fixes a fresh session per
round while retaining the actual code produced by preceding rounds and the
condition's explicit memory. A no-memory condition still retains that code.

Hold the coding model, harness, visible tools, task sequence, context limits,
memory injection cap, and total inference allowance fixed. Namespace stores by
chain and condition. Do not carry experience between independent chains. Retain
within-session context handling consistently, and declare any unavoidable
native harness memory. Historical note files from another condition must not
silently remain in the workspace.

## Bootstrap replay contract

Each JSONL episode contains `chain_id`, `task_id`, `revision`, a list of
`visible_experiences`, and diagnostic `queries`. An experience has an ID,
category, key, content, and provenance; a revision and explicit `supersedes`
links may be supplied. Public queries contain the question and addressing
metadata. Expected answers, expected sources, and stale-source annotations are
evaluator-only fields and must be stripped before a policy sees the query.

The runner writes an episode's visible experiences before issuing that
episode's diagnostic queries. Scores therefore measure memory after observing
the episode, not before-task prediction or coding performance. Each chain gets
an independent store. The fixture includes current, updated, unaffected, and
historical queries; report these subsets and the three categories separately.

The bootstrap shares supplied experience records across policies. It uses
lexical retrieval and explicit fixture keys; no model learns to extract facts
or discover invalidation. Keyed revision can use declared supersession and
revision metadata, which are deliberately easier inputs than raw trajectories.
Delayed evidence from an earlier revision must not become current merely
because it arrived later. These properties make the fixture useful for testing
bookkeeping, not for demonstrating semantic understanding.

The storage cap covers active and archived records together. Retrieval has a
separate cap. The runner's character-based text-token approximation is a budget
proxy, not measured inference tokens. Report both budgets and any record
evictions; a policy that retains history under an unlimited archive has a
different resource allowance.

## Controlled maintenance versus full systems

For a controlled maintenance study, share the writer, experience schema,
retriever, prompts, and budgets and vary the maintenance rule. This isolates
maintenance given the supplied representation.

For a full-system comparison, give each method the same agent-visible trajectory
envelope and keep its native writer, organizer, updater, and retriever. Feeding
every system a pre-extracted three-category summary would remove part of its
method. Record adapter changes and unsupported inputs; distinguish such an
adaptation from a faithful reproduction.

Interface-only disclosure and historical-source disclosure, including the
original L3/L5 conditions, are information-exposure controls. They are not
memory-maintenance policies and should be reported on a separate axis.

## Data and online evaluation stages

1. Validate synthetic records against the small versioned code examples and
   inspect representative probes in all three categories.
2. Obtain authorized raw benchmark tasks, trajectories, and repository
   environments. Audit what each turn exposes before converting it into the
   shared visible-trajectory format.
3. Reproduce a small persistent-code chain with the fixed model and harness.
   Preserve actual preceding submissions rather than substituting reference
   code between turns.
4. Add explicit changed and unchanged conditions. Original mostly additive
   task chains can test cumulative reuse, but do not alone establish that an
   earlier true fact has become obsolete.
5. Use a common prefix and checkpointed branch for a controlled change
   comparison, then assess natural rollouts separately. Include unchanged
   knowledge and explicitly historical queries to detect excessive forgetting.

Memory may observe only source and tool outputs visible to the agent, its
actions, local checks, and visible diffs. Reference solutions, hidden-test
feedback, evaluator result files, reuse targets, and future requirements remain
outside the memory path. Any test-driven memory correction must use visible
checks and count its cost.

## Outcomes and limits

Bootstrap outcomes concern recovery of expected content and sources, retrieval
of annotated stale records, and retention of unaffected or historical evidence.
Inspect raw retrievals alongside aggregate scores. They are not measurements of
executed reuse, duplication, or agent correctness.

Future coding outcomes include held-out functional success, valid reuse of
available implementations, stale-knowledge errors, retained useful experience,
and unnecessary duplication. A static call match alone does not prove valid
reuse; check behavior and, where needed, execution evidence. Reading source is
an observable exploration action, not proof of understanding, and fewer reads
can be a benefit of useful memory.

Report per-chain paired results, subset denominators, uncertainty, and failures
with plausible alternatives such as extraction loss, retrieval miss, budget
eviction, or environment failure. Count all memory operations. Keep measured
coding outcomes, offline memory probes, and planning estimates separate.
