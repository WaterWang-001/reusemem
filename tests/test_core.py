"""Protocol and accounting checks, not assertions of real agent performance."""
import dataclasses
import json

import pytest

from reusemem.policies import AppendOnly, KeyedRevision, RecentWindow
from reusemem.replay import run_replay
from reusemem.schema import Experience, Query, load_episodes, parse_episodes


def experience(identifier, task, content, revision="r1", key="parser", supersedes=()):
    return Experience(identifier, task, "code_understanding", key, content, revision, supersedes)


def query(kind="current", at_revision=None):
    return Query("q", "parser", "What is known?", "code_understanding", kind, at_revision)


def test_revisions_retain_history_and_ignore_late_old_evidence():
    policy = KeyedRevision(1000, 1000)
    policy.begin_episode("t1", "r1")
    policy.write([experience("old", "t1", "The parser rejects empty input.")])
    policy.begin_episode("t2", "r2")
    policy.write([experience("new", "t2", "The parser accepts empty input.", "r2", supersedes=("old",))])
    policy.begin_episode("t3", "r2")
    policy.write([experience("late-old", "t3", "The parser rejects empty input.")])
    assert policy.read(query())[0].experience.id == "new"
    assert policy.read(query("history", "r1"))[0].experience.id == "late-old"
    assert {entry.experience.id for entry in policy.entries if entry.status == "historical"} == {"old", "late-old"}


def test_current_and_historical_records_share_storage_budget():
    policy = KeyedRevision(120, 120)
    policy.begin_episode("t1", "r1")
    policy.write([experience("old", "t1", "A" * 100)])
    policy.begin_episode("t2", "r2")
    policy.write([experience("new", "t2", "B" * 100, "r2")])
    assert policy.stored_tokens <= 120
    assert policy.snapshot()["historical_records"] == 0
    assert policy.read(query())[0].experience.id == "new"
    assert policy.read(query("history", "r1")) == ()


def test_delayed_old_evidence_stays_historical_after_newer_note_is_evicted():
    policy = KeyedRevision(100, 100)
    policy.begin_episode("t1", "r1")
    policy.write([experience("old", "t1", "Rejects empty input.")])
    policy.begin_episode("t2", "r2")
    policy.write([experience("new", "t2", "Accepts empty input.", "r2", supersedes=("old",))])
    policy.write([
        experience("other-a", "t2", "Unrelated observation A.", "r2", key="other-a"),
        experience("other-b", "t2", "Unrelated observation B.", "r2", key="other-b"),
    ])
    assert all(entry.experience.key != "parser" for entry in policy.entries)
    policy.begin_episode("t3", "r2")
    policy.write([experience("late-old", "t3", "Rejects empty input.", "r1")])
    assert policy.stored_tokens <= 100
    assert policy.read(query()) == ()


def test_retrieval_cap_does_not_partially_expose_an_oversize_note():
    policy = AppendOnly(1000, 10)
    policy.begin_episode("t1", "r1")
    policy.write([experience("old", "t1", "not visible under a ten-token response cap")])
    assert policy.read(query()) == ()
    assert policy.entries  # Stored, but not returned for free.


def test_recent_window_is_recent_raw_content_not_query_based_summary():
    policy = RecentWindow(1000, 80)
    policy.begin_episode("t1", "r1")
    policy.write([experience("parser", "t1", "old fact", key="parser"),
                  experience("other", "t1", "new fact", key="different")])
    assert policy.read(query())[0].experience.id == "other"


def test_append_only_uses_newest_tie_break_without_erasing_old_notes():
    policy = AppendOnly(1000, 1000)
    policy.begin_episode("t1", "r1")
    policy.write([experience("old", "t1", "old fact")])
    policy.begin_episode("t2", "r2")
    policy.write([experience("new", "t2", "new fact", "r2")])
    assert [entry.experience.id for entry in policy.read(query())] == ["new", "old"]


def _episode(chain, content, expected=None):
    return {"chain_id": chain, "task_id": "t1", "revision": "r1",
            "visible_experiences": [{"id": "e1", "task_id": "t1", "category": "code_understanding",
                                     "key": "parser", "content": content}],
            "queries": [{"id": "q1", "key": "parser", "question": "What is known?",
                         "category": "code_understanding", "expected_content": expected or content,
                         "expected_sources": ["e1"], "stale_source_ids": []}]}


def test_chain_isolation_and_hidden_labels_do_not_enter_memory(tmp_path):
    first = _episode("one", "first content", "HIDDEN_EXPECTED_ANSWER")
    second = _episode("two", "second content")
    source = tmp_path / "input.jsonl"
    source.write_text("\n".join(json.dumps(x) for x in [first, second]))
    output = tmp_path / "run"
    summary = run_replay(source, output, policies=["keyed_revision"])
    results = json.loads((output / "results.json").read_text())
    assert [row["predicted_content"] for row in results] == ["first content", "second content"]
    assert summary["policies"]["keyed_revision"]["overall"]["exact_match_accuracy"] == 0.5
    assert summary["policies"]["keyed_revision"]["by_query_kind"]["current"]["probes"] == 2
    traces = (output / "traces.jsonl").read_text()
    assert "HIDDEN_EXPECTED_ANSWER" not in traces
    assert "expected_content" not in dataclasses.asdict(load_episodes(source)[0].probes[0].query)
    assert json.loads((output / "manifest.json").read_text())["config"]["archive_shares_storage_budget"]
    with pytest.raises(FileExistsError):
        run_replay(source, output)


def test_unknown_fields_cannot_smuggle_answers_into_experiences():
    item = _episode("one", "visible")
    item["visible_experiences"][0]["expected_content"] = "hidden"
    with pytest.raises(ValueError, match="unexpected visible experience fields"):
        parse_episodes(json.dumps(item))


def test_history_query_requires_explicit_scope_and_cannot_look_ahead():
    item = _episode("one", "visible")
    item["queries"][0]["query_kind"] = "history"
    with pytest.raises(ValueError, match="history probes need"):
        parse_episodes(json.dumps(item))
    item["queries"][0]["at_revision"] = "future"
    with pytest.raises(ValueError, match="unseen revision"):
        parse_episodes(json.dumps(item))
