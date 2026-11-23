"""Replay factual memory probes, without running a coding agent or an LLM."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from .policies import POLICIES, approximate_text_tokens, make_policy
from .schema import CATEGORIES, QUERY_KINDS, Query, parse_episodes


def _mean(values: list[float | bool]) -> float | None:
    return sum(values) / len(values) if values else None


def _metrics(rows: list[dict]) -> dict:
    stale = [row for row in rows if row["stale_labels_provided"] and row["query_kind"] != "history"]
    history = [row for row in rows if row["query_kind"] == "history" and row["expected_sources"]]
    return {
        "probes": len(rows),
        "exact_match_accuracy": _mean([row["exact_match"] for row in rows]),
        "stale_source_labeled_probes": len(stale),
        "stale_source_use_rate": _mean([row["stale_source_used"] for row in stale]),
        "historical_source_labeled_probes": len(history),
        "historical_source_recall": _mean([row["historical_source_recall"] for row in history]),
        "read_output_approx_text_tokens": sum(row["read_output_approx_text_tokens"] for row in rows),
        "read_latency_ms_mean": _mean([row["read_latency_ms"] for row in rows]),
    }


def _display(value: object, percentage: bool = False) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.1f}%" if percentage else f"{float(value):.3f}"


def _code_provenance() -> dict:
    package = Path(__file__).resolve().parent
    source_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted(package.glob("*.py"))}
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=package,
                                capture_output=True, text=True, timeout=5, check=False)
        commit = result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        commit = None
    return {"git_commit": commit, "package_source_sha256": source_hashes}


def _markdown(summary: dict) -> str:
    lines = [
        "# Factual memory replay diagnostics", "",
        "These are deterministic, supplied-fact probes after each episode's writes. "
        "They are not coding-agent task success, learned-memory performance, or real model token measurements.", "",
        "Text-size accounting uses ceil(characters / 4). Active and archived records share the storage cap. "
        "Latency is local Python bookkeeping only. Expected answers and validity labels are evaluator-only.", "",
        "| Policy | Probes | Exact match | Stale source use | Historical source recall | Read text tokens (approx.) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, item in summary["policies"].items():
        row = item["overall"]
        lines.append(f"| {name} | {row['probes']} | {_display(row['exact_match_accuracy'], True)} "
                     f"| {_display(row['stale_source_use_rate'], True)} "
                     f"| {_display(row['historical_source_recall'], True)} "
                     f"| {row['read_output_approx_text_tokens']} |")
    for name, item in summary["policies"].items():
        lines.extend(["", f"## {name} by experience category", "",
                      "| Category | Probes | Exact match | Stale source use | Historical source recall |",
                      "| --- | ---: | ---: | ---: | ---: |"])
        for category, row in item["by_category"].items():
            lines.append(f"| {category} | {row['probes']} | {_display(row['exact_match_accuracy'], True)} "
                         f"| {_display(row['stale_source_use_rate'], True)} "
                         f"| {_display(row['historical_source_recall'], True)} |")
    for name, item in summary["policies"].items():
        lines.extend(["", f"## {name} by query kind", "",
                      "| Query kind | Probes | Exact match |",
                      "| --- | ---: | ---: |"])
        for kind, row in item["by_query_kind"].items():
            lines.append(f"| {kind} | {row['probes']} | {_display(row['exact_match_accuracy'], True)} |")
    lines.extend(["", "Append-only resolves equal lexical scores by newest insertion, without revising old notes. "
                  "A more lexically similar old note may still rank first. Recent-window returns recent raw "
                  "records. Keyed-revision uses explicit shared keys, revision order, and supersession metadata, "
                  "not inferred semantic validity. These protocol choices explain much of the synthetic result.", ""])
    return "\n".join(lines)


def run_replay(input_path: str | Path, output_dir: str | Path,
               policies: list[str] | tuple[str, ...] | None = None,
               memory_budget: int = 2048, retrieval_budget: int = 512) -> dict:
    """Write traces, probe results, a summary, and a reproducibility manifest.

    Budget units are approximate text tokens, not actual tokenizer tokens.
    The deterministic reader returns the first retrieved record whose explicit
    key and category match the public query. It never sees expected answers.
    Each chain has an independent policy store; every episode is a new session
    boundary, with only that policy's bounded records carried forward.
    """
    source = Path(input_path).resolve()
    destination = Path(output_dir).resolve()
    if source.is_relative_to(destination):
        raise ValueError("input must not be inside the output directory")
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("output directory must be new or empty")
    names = list(POLICIES) if policies is None else list(policies)
    if not names or len(names) != len(set(names)):
        raise ValueError("policies must be nonempty and contain no duplicates")
    # Validate policy names and budget values before creating outputs.
    for name in names:
        make_policy(name, memory_budget, retrieval_budget)
    source_bytes = source.read_bytes()
    code_provenance = _code_provenance()
    episodes = parse_episodes(source_bytes.decode("utf-8"))
    traces, results = [], []
    summary = {"schema": "reusemem-factual-replay-v1", "measurement": "post-write supplied-fact diagnostic",
               "episodes": len(episodes), "chains": len({episode.chain_id for episode in episodes}),
               "policies": {}}
    for name in names:
        stores = {}
        write_ms, input_tokens, action_tokens, peak_tokens = [], 0, 0, 0
        for episode in episodes:
            policy = stores.setdefault(episode.chain_id, make_policy(name, memory_budget, retrieval_budget))
            policy.begin_episode(episode.task_id, episode.revision)
            before = policy.snapshot()
            visible = [record.as_dict() for record in episode.experiences]
            start = perf_counter()
            actions = policy.write(episode.experiences)
            elapsed = (perf_counter() - start) * 1000
            write_ms.append(elapsed)
            input_tokens += approximate_text_tokens(json.dumps(visible, ensure_ascii=False, sort_keys=True))
            action_tokens += approximate_text_tokens(json.dumps(actions, ensure_ascii=False, sort_keys=True))
            after = policy.snapshot()
            peak_tokens = max(peak_tokens, policy.stored_tokens)
            reads = []
            for probe in episode.probes:
                query: Query = probe.query  # Separate public object, no gold fields.
                start = perf_counter()
                retrieved = policy.read(query)
                read_ms = (perf_counter() - start) * 1000
                selected = next((entry for entry in retrieved
                                 if entry.experience.key == query.key
                                 and entry.experience.category == query.category), None)
                answer = selected.experience.content if selected is not None else None
                selected_id = selected.experience.id if selected is not None else None
                retrieved_ids = [entry.experience.id for entry in retrieved]
                read_tokens = sum(entry.approximate_tokens for entry in retrieved)
                reads.append({"query": query.as_dict(), "retrieved": [entry.as_dict() for entry in retrieved],
                              "predicted_content": answer, "selected_source": selected_id,
                              "read_output_approx_text_tokens": read_tokens, "read_latency_ms": read_ms})
                history_recall = (len(set(retrieved_ids) & set(probe.expected_sources)) / len(probe.expected_sources)
                                  if probe.expected_sources and query.query_kind == "history" else None)
                results.append({
                    "policy": name, "chain_id": episode.chain_id, "task_id": episode.task_id,
                    "query_id": query.id, "category": query.category, "query_kind": query.query_kind,
                    "predicted_content": answer, "selected_source": selected_id,
                    "retrieved_sources": retrieved_ids, "acceptable_answers": list(probe.acceptable_answers),
                    "expected_sources": list(probe.expected_sources), "stale_source_ids": list(probe.stale_source_ids),
                    "exact_match": answer in probe.acceptable_answers,
                    "stale_labels_provided": probe.stale_labels_provided,
                    "stale_source_used": selected_id in probe.stale_source_ids,
                    "stale_source_retrieved": bool(set(retrieved_ids) & set(probe.stale_source_ids)),
                    "historical_source_recall": history_recall,
                    "read_output_approx_text_tokens": read_tokens, "read_latency_ms": read_ms,
                })
            traces.append({"policy": name, "chain_id": episode.chain_id, "task_id": episode.task_id,
                           "revision": episode.revision, "probe_timing": "after_episode_write",
                           "memory_before": before, "visible_writes": visible, "update_actions": actions,
                           "memory_after": after, "reads": reads, "write_latency_ms": elapsed})
        rows = [row for row in results if row["policy"] == name]
        summary["policies"][name] = {
            "overall": _metrics(rows),
            "by_category": {category: _metrics([row for row in rows if row["category"] == category])
                            for category in CATEGORIES},
            "by_query_kind": {kind: _metrics([row for row in rows if row["query_kind"] == kind])
                              for kind in QUERY_KINDS},
            "accounting": {"write_input_approx_text_tokens": input_tokens,
                           "update_trace_approx_text_tokens": action_tokens,
                           "peak_stored_approx_text_tokens": peak_tokens,
                           "final_stored_approx_text_tokens_by_chain": {chain: store.stored_tokens
                                                                       for chain, store in stores.items()},
                           "write_latency_ms_total": sum(write_ms), "write_latency_ms_mean": _mean(write_ms)},
        }
    manifest = {
        "schema": "reusemem-replay-manifest-v1", "created_at": datetime.now(timezone.utc).isoformat(),
        "input_path": str(source), "input_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "code": code_provenance,
        "config": {"policies": names, "memory_budget": memory_budget, "retrieval_budget": retrieval_budget,
                   "budget_unit": "approx_text_tokens", "token_heuristic": "ceil(unicode_characters / 4)",
                   "archive_shares_storage_budget": True, "probe_timing": "after_episode_write"},
        "limitations": ["No coding agent or model is called.", "Facts and shared metadata are supplied by the input.",
                        "Keyed decoding is not open-ended question answering.",
                        "Local bookkeeping latency is not inference latency."],
    }
    destination.mkdir(parents=True, exist_ok=True)
    for filename, data in (("manifest.json", manifest), ("results.json", results), ("summary.json", summary)):
        with (destination / filename).open("x", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
    with (destination / "traces.jsonl").open("x", encoding="utf-8") as handle:
        for trace in traces:
            handle.write(json.dumps(trace, ensure_ascii=False, allow_nan=False) + "\n")
    (destination / "summary.md").write_text(_markdown(summary), encoding="utf-8")
    return summary
