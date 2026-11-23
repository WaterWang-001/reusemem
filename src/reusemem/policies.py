"""Deterministic diagnostic policies, with no LLM or embedding dependency.

KeyedRevision uses visible, explicit keys/revision labels. It is a controlled
update baseline, not an implementation of Mem0 or the proposed ReuseMem method.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Iterable

from .schema import Experience, Query


def approximate_text_tokens(text: str) -> int:
    """ceil(characters / 4), a text-size heuristic, never model token usage."""
    return math.ceil(len(text) / 4)


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass
class MemoryEntry:
    experience: Experience
    sequence: int
    task_order: int
    revision_order: int
    status: str = "active"

    def as_dict(self) -> dict:
        return {**self.experience.as_dict(), "status": self.status}

    @property
    def approximate_tokens(self) -> int:
        return approximate_text_tokens(_json_text(self.as_dict()))


class MemoryPolicy:
    name = "base"

    def __init__(self, memory_budget: int = 2048, retrieval_budget: int = 512):
        for label, value in (("memory_budget", memory_budget), ("retrieval_budget", retrieval_budget)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{label} must be a positive integer")
        self.memory_budget = memory_budget
        self.retrieval_budget = retrieval_budget
        self.entries: list[MemoryEntry] = []
        self.task_order: dict[str, int] = {}
        self.revision_order: dict[str, int] = {}
        self.current_task = ""
        self.current_revision = ""
        self._sequence = 0

    def begin_episode(self, task_id: str, revision: str) -> None:
        if task_id in self.task_order:
            raise ValueError(f"task {task_id!r} already ingested")
        self.task_order[task_id] = len(self.task_order)
        self.revision_order.setdefault(revision, len(self.revision_order))
        self.current_task, self.current_revision = task_id, revision

    def snapshot(self) -> dict:
        return {
            "records": [entry.as_dict() for entry in self.entries],
            "stored_approx_text_tokens": self.stored_tokens,
            "active_records": sum(entry.status == "active" for entry in self.entries),
            "historical_records": sum(entry.status == "historical" for entry in self.entries),
        }

    @property
    def stored_tokens(self) -> int:
        # Historical records share this budget; they are not a free archive.
        return sum(entry.approximate_tokens for entry in self.entries)

    def _entry(self, record: Experience) -> MemoryEntry:
        if record.task_id != self.current_task:
            raise ValueError("record belongs to a different ingestion episode")
        revision = record.revision or self.current_revision
        if revision not in self.revision_order:
            raise ValueError(f"unseen record revision {revision!r}")
        self._sequence += 1
        return MemoryEntry(record, self._sequence, self.task_order[self.current_task],
                           self.revision_order[revision])

    def _trim(self) -> list[dict]:
        actions = []
        while self.stored_tokens > self.memory_budget:
            removed = self.entries.pop(0)
            actions.append({"action": "evict", "id": removed.experience.id, "reason": "storage_budget"})
        return actions

    def write(self, records: Iterable[Experience]) -> list[dict]:
        actions = []
        for record in records:
            self.entries.append(self._entry(record))
            actions.append({"action": "append", "id": record.id})
            actions.extend(self._trim())
        return actions

    def _eligible(self, query: Query) -> list[MemoryEntry]:
        if query.at_revision is not None and query.at_revision not in self.revision_order:
            raise ValueError(f"unseen requested revision {query.at_revision!r}")
        if query.as_of_task is not None and query.as_of_task not in self.task_order:
            raise ValueError(f"unseen requested task {query.as_of_task!r}")
        return [entry for entry in self.entries
                if (query.at_revision is None or entry.revision_order <= self.revision_order[query.at_revision])
                and (query.as_of_task is None or entry.task_order <= self.task_order[query.as_of_task])]

    def _bounded(self, entries: Iterable[MemoryEntry]) -> tuple[MemoryEntry, ...]:
        selected = []
        used = 0
        for entry in entries:
            cost = entry.approximate_tokens
            if used + cost <= self.retrieval_budget:
                selected.append(entry)
                used += cost
        return tuple(selected)

    def read(self, query: Query) -> tuple[MemoryEntry, ...]:
        raise NotImplementedError


class NoMemory(MemoryPolicy):
    name = "no_memory"

    def write(self, records: Iterable[Experience]) -> list[dict]:
        return [{"action": "ignore", "id": record.id} for record in records]

    def read(self, query: Query) -> tuple[MemoryEntry, ...]:
        return ()


class AppendOnly(MemoryPolicy):
    """Append immutable notes; FIFO eviction at capacity; lexical retrieval.

    Equal relevance is resolved by newest insertion. Old records remain in the
    store and may outrank newer ones when their lexical match is stronger.
    """
    name = "append_only"

    @staticmethod
    def _score(entry: MemoryEntry, query: Query) -> int:
        record = entry.experience
        if record.key != query.key or record.category != query.category:
            return 0
        query_words = set(re.findall(r"\w+", query.question.casefold()))
        note_words = set(re.findall(r"\w+", record.content.casefold()))
        return 1 + len(query_words & note_words)

    def read(self, query: Query) -> tuple[MemoryEntry, ...]:
        ranked = sorted(self._eligible(query), key=lambda e: (-self._score(e, query), -e.sequence))
        return self._bounded(entry for entry in ranked if self._score(entry, query) > 0)


class RecentWindow(MemoryPolicy):
    """Expose recent raw records, not a model-generated rolling summary."""
    name = "recent_window"

    def read(self, query: Query) -> tuple[MemoryEntry, ...]:
        return self._bounded(sorted(self._eligible(query), key=lambda e: -e.sequence))


class KeyedRevision(MemoryPolicy):
    """Explicit-key and declared-revision update with a bounded history archive.

    Revision order is the order in which episode revision labels first appear,
    not lexical order or record-arrival order. Older evidence arriving late is
    historical. These are supplied metadata, not inferred code validity.
    """
    name = "keyed_revision"

    def _trim(self) -> list[dict]:
        actions = []
        while self.stored_tokens > self.memory_budget:
            # Prioritize current notes, then keep as much dated history as fits.
            candidate = min(self.entries, key=lambda e: (e.status != "historical", e.sequence))
            self.entries.remove(candidate)
            actions.append({"action": "evict", "id": candidate.experience.id, "reason": "storage_budget"})
        return actions

    def write(self, records: Iterable[Experience]) -> list[dict]:
        actions = []
        for record in records:
            incoming = self._entry(record)
            previous = [entry for entry in self.entries
                        if entry.status == "active" and entry.experience.category == record.category
                        and entry.experience.key == record.key]
            if previous and max(entry.revision_order for entry in previous) > incoming.revision_order:
                incoming.status = "historical"
                actions.append({"action": "archive_incoming", "id": record.id, "reason": "older_declared_revision"})
            else:
                for entry in self.entries:
                    same_key = (entry.experience.key == record.key
                                and entry.experience.category == record.category)
                    if entry.status == "active" and (same_key or entry.experience.id in record.supersedes):
                        entry.status = "historical"
                        actions.append({"action": "archive", "id": entry.experience.id, "by": record.id})
                actions.append({"action": "activate", "id": record.id})
            self.entries.append(incoming)
            actions.extend(self._trim())
        return actions

    def read(self, query: Query) -> tuple[MemoryEntry, ...]:
        candidates = [entry for entry in self._eligible(query)
                      if entry.experience.key == query.key and entry.experience.category == query.category]
        if query.query_kind != "history":
            candidates = [entry for entry in candidates if entry.status == "active"]
        return self._bounded(sorted(candidates, key=lambda e: (-e.revision_order, -e.sequence)))


POLICIES = {policy.name: policy for policy in (NoMemory, AppendOnly, RecentWindow, KeyedRevision)}


def make_policy(name: str, memory_budget: int = 2048, retrieval_budget: int = 512) -> MemoryPolicy:
    if name not in POLICIES:
        raise ValueError(f"unknown policy {name!r}; choose from {', '.join(POLICIES)}")
    return POLICIES[name](memory_budget, retrieval_budget)
