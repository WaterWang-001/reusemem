# Baselines and Comparison Boundaries

## Bootstrap policies

The deterministic replay uses a shared set of visible experience records. It
has no LLM writer, embeddings, or coding-agent execution.

| Policy ID | Operation | Interpretation |
| --- | --- | --- |
| `no_memory` | Return no explicit experience memory. | Lower control; earlier code would still persist in an online experiment. |
| `append_only` | Append records subject to the storage cap and retrieve by lexical relevance. | Simple bounded retrieval control; not a research-system reproduction. |
| `recent_window` | Keep a bounded window of recent records. | Recency control; no LLM compression or rolling summary. |
| `keyed_revision` | Track explicit shared keys, revision order, and supersession; retain historical records within the joint cap. | Controlled revision baseline using supplied metadata; not Mem0 or a learned ReuseMem strategy. |

The runner probes memory after each episode's writes. It uses a character-based
text-token estimate and exposes addressing metadata such as keys. Consequently,
success shows that a storage/retrieval rule works for these supplied records;
it does not establish that the rule can infer keys, conflicts, or applicability
from a coding trajectory. In particular, newer arrival is not necessarily a
newer repository revision.

The revision control conservatively archives newly arriving observations scoped
to an older revision, even if a newer same-key record has been evicted. It does
not automatically promote such delayed observations to current advice. Earlier
unaffected active notes are retained normally; this rule does not infer which
code changes invalidate them.

## Planned full-system baselines

These methods are not implemented by the bootstrap policies above. Pin the
paper version, repository commit, prompts, models, configuration, and adapter
deviations before reporting a method under its research name.

| Planned method | Mechanism to preserve | Adaptation to audit |
| --- | --- | --- |
| Rolling summary | LLM rewrites a bounded summary of accumulated visible experience. | Summary prompts, update frequency, lost failure context, and validation scope. |
| Mem0, text memory | Extract candidate facts and decide add/update/delete/no-op against retrieved memories. | Coding-specific applicability, failed attempts, source revisions, and supersession behavior. |
| SimpleMem, text core | Structured compression, online synthesis, and intent-aware retrieval. | Whether compressed experience preserves conditions and historical checks; do not substitute a later Omni/EvolveMem variant silently. |
| ReasoningBank, without MaTTS | Distill and retrieve task-solving experience from visible trajectories. | Treatment of failures and evolving code; no test-time scaling or extra trajectory sampling in the core comparison. |

Primary references for implementation planning are
[Mem0](https://arxiv.org/abs/2504.19413) and its
[repository](https://github.com/mem0ai/mem0),
[SimpleMem](https://arxiv.org/abs/2601.02553) and its
[repository](https://github.com/aiming-lab/SimpleMem), and
[ReasoningBank](https://arxiv.org/abs/2509.25140). A paper's update mechanism
does not itself guarantee that repository changes invalidate the correct claim
or that retained test evidence remains applicable.

## Two complementary comparisons

**Controlled maintenance comparison.** Share the writer and record format, then
hold retrieval and budgets fixed while varying append, recency, summarization,
or revision behavior. This asks what maintenance contributes after extraction.

**Full-system comparison.** Supply the same visible actions and observations to
each complete system and preserve its own extraction and retrieval machinery.
This asks what experience the system actually preserves and uses. Audit the
three categories after the run rather than requiring all systems to emit an
identical enriched schema beforehand.

Do not attribute a shared writer's failure to a full system that was not allowed
to use its writer. Conversely, do not attribute a full system's advantage solely
to maintenance when extraction, retrieval, and prompts also differ.

## Controls and reporting

Keep model, harness, task/code history, visible evidence, and injected context
budget fixed. Count extraction, update, retrieval, verification, and embedding
costs. Disable or declare native persistent memory so it cannot silently supply
a second store. Use separate namespaces and reset procedures for every chain
and condition.

L3 interface exposure and L5 historical source exposure control what information
the agent can access; they do not specify how experience is maintained. If used,
cross them with a small policy subset and label the axes separately. Report
whether historical note files are removed or replaced, rather than leaving the
original note channel alongside a new memory store.

For a first paid pilot, implement rolling summary and one native revision-capable
text system before expanding to all planned methods. Keep the deterministic
policies as debugging controls. Any reduction in method count should preserve
one useful retention/update contrast and a paired task set.
