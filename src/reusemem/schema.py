"""Strict visible-memory inputs and evaluator-only factual probes.

One JSONL line describes a session boundary. Probes are run after that line's
visible experiences have been ingested. They measure availability of supplied
facts, not the performance of a coding agent or a learned memory writer.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

CATEGORIES = ("code_understanding", "problem_solving", "validation")
QUERY_KINDS = ("current", "updated", "unaffected", "history")


def _text(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    return value


def _optional_text(data: dict[str, Any], field: str) -> str | None:
    return _text(data, field) if data.get(field) is not None else None


def _strings(data: dict[str, Any], field: str) -> tuple[str, ...]:
    value = data.get(field, [])
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError(f"{field} must be a list of nonempty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} contains duplicates")
    return tuple(value)


@dataclass(frozen=True)
class Experience:
    id: str
    task_id: str
    category: str
    key: str
    content: str
    revision: str | None = None
    supersedes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["supersedes"] = list(self.supersedes)
        return data


@dataclass(frozen=True)
class Query:
    """Only these public fields are passed to a memory policy."""

    id: str
    key: str
    question: str
    category: str
    query_kind: str = "current"
    at_revision: str | None = None
    as_of_task: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Probe:
    """Expected answers and validity labels stay in the evaluator."""

    query: Query
    acceptable_answers: tuple[str, ...]
    expected_sources: tuple[str, ...] = ()
    stale_source_ids: tuple[str, ...] = ()
    stale_labels_provided: bool = False


@dataclass(frozen=True)
class Episode:
    chain_id: str
    task_id: str
    revision: str
    experiences: tuple[Experience, ...]
    probes: tuple[Probe, ...]


def parse_episodes(text: str) -> tuple[Episode, ...]:
    episodes = []
    seen_tasks: dict[str, set[str]] = {}
    seen_records: dict[str, set[str]] = {}
    seen_queries: dict[str, set[str]] = {}
    seen_revisions: dict[str, set[str]] = {}
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                raise ValueError("episode must be a JSON object")
            chain = _text(data, "chain_id")
            task = _text(data, "task_id")
            revision = _text(data, "revision")
            task_ids = seen_tasks.setdefault(chain, set())
            record_ids = seen_records.setdefault(chain, set())
            query_ids = seen_queries.setdefault(chain, set())
            revisions = seen_revisions.setdefault(chain, set())
            if task in task_ids:
                raise ValueError(f"duplicate task_id {task!r} in chain {chain!r}")
            task_ids.add(task)
            revisions.add(revision)
            raw_experiences = data.get("visible_experiences")
            raw_queries = data.get("queries")
            if not isinstance(raw_experiences, list) or not isinstance(raw_queries, list):
                raise ValueError("visible_experiences and queries must be lists")
            experiences = []
            for item in raw_experiences:
                if not isinstance(item, dict):
                    raise ValueError("experience must be an object")
                # A closed schema prevents accidentally forwarding gold fields.
                allowed = {"id", "task_id", "category", "key", "content", "revision", "supersedes"}
                if set(item) - allowed:
                    raise ValueError(f"unexpected visible experience fields: {sorted(set(item) - allowed)}")
                record = Experience(
                    id=_text(item, "id"), task_id=_text(item, "task_id"),
                    category=_text(item, "category"), key=_text(item, "key"),
                    content=_text(item, "content"),
                    revision=_optional_text(item, "revision") or revision,
                    supersedes=_strings(item, "supersedes"),
                )
                if record.task_id != task:
                    raise ValueError("experience task_id must name its ingestion episode")
                if record.category not in CATEGORIES:
                    raise ValueError(f"unknown experience category {record.category!r}")
                if record.id in record_ids:
                    raise ValueError(f"duplicate experience id {record.id!r}")
                if record.revision not in revisions:
                    raise ValueError(f"experience refers to an unseen revision {record.revision!r}")
                if any(old not in record_ids for old in record.supersedes):
                    raise ValueError("supersedes must name previously ingested experiences in this chain")
                record_ids.add(record.id)
                experiences.append(record)
            probes = []
            for item in raw_queries:
                if not isinstance(item, dict):
                    raise ValueError("query must be an object")
                query = Query(
                    id=_text(item, "id"), key=_text(item, "key"),
                    question=_text(item, "question"), category=_text(item, "category"),
                    query_kind=item.get("query_kind", "current"),
                    at_revision=_optional_text(item, "at_revision"),
                    as_of_task=_optional_text(item, "as_of_task"),
                )
                if query.category not in CATEGORIES or query.query_kind not in QUERY_KINDS:
                    raise ValueError("query has an unknown category or query_kind")
                if query.id in query_ids:
                    raise ValueError(f"duplicate query id {query.id!r}")
                query_ids.add(query.id)
                if query.at_revision is not None and query.at_revision not in revisions:
                    raise ValueError("query refers to an unseen revision")
                if query.as_of_task is not None and query.as_of_task not in task_ids:
                    raise ValueError("query refers to an unseen task")
                if query.query_kind == "history" and not (query.at_revision or query.as_of_task):
                    raise ValueError("history probes need at_revision or as_of_task")
                if query.query_kind != "history" and (query.at_revision or query.as_of_task):
                    raise ValueError("only history probes may request an earlier revision or task")
                if "expected_content" in item and "acceptable_answers" in item:
                    raise ValueError("specify expected_content or acceptable_answers, not both")
                answers = ((_text(item, "expected_content"),) if "expected_content" in item
                           else _strings(item, "acceptable_answers"))
                if not answers:
                    raise ValueError("every probe needs a nonempty expected answer")
                expected = _strings(item, "expected_sources")
                stale = _strings(item, "stale_source_ids")
                if any(source not in record_ids for source in (*expected, *stale)):
                    raise ValueError("source labels must name ingested experiences in this chain")
                if set(expected) & set(stale):
                    raise ValueError("a source cannot be both expected and stale for one query")
                probes.append(Probe(query, answers, expected, stale, "stale_source_ids" in item))
            episodes.append(Episode(chain, task, revision, tuple(experiences), tuple(probes)))
        except (ValueError, TypeError, KeyError) as exc:
            raise ValueError(f"JSONL line {line_no}: {exc}") from exc
    if not episodes:
        raise ValueError("input contains no episodes")
    return tuple(episodes)


def load_episodes(path: str | Path) -> tuple[Episode, ...]:
    return parse_episodes(Path(path).read_text(encoding="utf-8"))
