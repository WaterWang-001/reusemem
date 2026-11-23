"""Check synthetic data integrity and ground its notes in executable snapshots."""

import importlib.util
import json
from collections import Counter
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = PROJECT_ROOT / "examples"
DATA_PATH = EXAMPLES / "synthetic-chains.jsonl"


@pytest.fixture(scope="module")
def episodes() -> list[dict]:
    return [json.loads(line) for line in DATA_PATH.read_text().splitlines() if line.strip()]


def load_snapshot(revision: str, module_name: str) -> ModuleType:
    source = EXAMPLES / "toy_repo" / revision / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(f"toy_{revision}_{module_name}", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def experience_index(episodes: list[dict]) -> dict[str, dict]:
    return {
        experience["id"]: experience
        for episode in episodes
        for experience in episode["visible_experiences"]
    }


def test_synthetic_chains_cover_the_intended_probe_types(episodes: list[dict]) -> None:
    counts = Counter(episode["chain_id"] for episode in episodes)
    assert len(counts) == 3
    assert set(counts.values()) == {4}
    assert all(chain_id.startswith("synthetic-") for chain_id in counts)
    for chain_id in counts:
        chain = [episode for episode in episodes if episode["chain_id"] == chain_id]
        assert {query["query_kind"] for row in chain for query in row["queries"]} == {
            "current", "updated", "unaffected", "history"
        }
        assert {
            note["category"] for row in chain for note in row["visible_experiences"]
        } == {"code_understanding", "problem_solving", "validation"}


def test_expected_answers_use_only_previously_visible_experiences(episodes: list[dict]) -> None:
    seen: dict[str, dict[str, dict]] = {}
    task_ids: set[tuple[str, str]] = set()
    query_ids: set[tuple[str, str]] = set()
    experience_ids: set[str] = set()
    for episode in episodes:
        chain_id = episode["chain_id"]
        task_key = (chain_id, episode["task_id"])
        assert task_key not in task_ids
        task_ids.add(task_key)
        available = seen.setdefault(chain_id, {})
        for note in episode["visible_experiences"]:
            assert note["id"] not in experience_ids
            experience_ids.add(note["id"])
            assert note["task_id"] == episode["task_id"]
            assert not ({"expected_content", "acceptable_answers", "queries"} & note.keys())
            for superseded_id in note.get("supersedes", []):
                assert superseded_id in available
                assert available[superseded_id]["key"] == note["key"]
            available[note["id"]] = note
        for query in episode["queries"]:
            query_key = (chain_id, query["id"])
            assert query_key not in query_ids
            query_ids.add(query_key)
            sources = query["expected_sources"]
            assert sources
            assert all(source_id in available for source_id in sources)
            for source_id in sources:
                source = available[source_id]
                assert source["content"] == query["expected_content"]
                assert source["key"] == query["key"]
                assert source["category"] == query["category"]
            for source_id in query.get("stale_source_ids", []):
                assert source_id in available
                assert available[source_id]["key"] == query["key"]
                assert source_id not in sources
            if query["query_kind"] == "history":
                assert all(available[s]["revision"] == query["at_revision"] for s in sources)


def test_batch_notes_are_grounded_in_the_utility_addition(episodes: list[dict]) -> None:
    old = load_snapshot("r1", "batching")
    new = load_snapshot("r2", "batching")
    notes = experience_index(episodes)
    assert not hasattr(old, "batch_process")
    assert "no batch_process helper exists" in notes["batch-r1-utility"]["content"]
    assert new.batch_process([3, -1, 2]) == [6, -2, 4]
    assert "batching.batch_process(values)" in notes["batch-r2-utility"]["content"]
    assert old.process_item(0) == new.process_item(0) == 0
    assert new.batch_process([]) == []
    assert new.batch_process([0, 2]) == [0, 4]
    failed_attempt = [new.process_item(value) for value in [0, 2] if value]
    assert failed_attempt == [4]
    assert failed_attempt != new.batch_process([0, 2])


def test_timeout_notes_are_grounded_in_the_fix_and_preserved_conventions(
    episodes: list[dict],
) -> None:
    old = load_snapshot("r1", "config")
    new = load_snapshot("r2", "config")
    notes = experience_index(episodes)
    assert old.resolve_timeout("0") == 30
    assert new.resolve_timeout("0") == 0
    assert new.resolve_timeout("bad") == 30
    assert new.resolve_timeout(" 5 ") == 5
    for snapshot in [old, new]:
        assert snapshot.parse_timeout(" 5 ") == 5
        assert snapshot.parse_timeout("0") == 0
        for invalid in ["bad", "", "-1"]:
            assert snapshot.parse_timeout(invalid) is None
    assert notes["config-r2-zero"]["supersedes"] == ["config-r1-zero"]
    assert "explicit is None" in notes["config-r2-zero"]["content"]


def test_delayed_observation_is_scoped_to_the_old_revision(episodes: list[dict]) -> None:
    delayed_task = next(row for row in episodes if row["task_id"] == "config-04")
    note = delayed_task["visible_experiences"][0]
    assert delayed_task["revision"] == "r2"
    assert note["revision"] == "r1"
    assert "supersedes" not in note
    assert note["content"] == experience_index(episodes)["config-r1-zero"]["content"]
    current_probe = next(
        query for query in delayed_task["queries"] if query["id"] == "config-delayed-evidence"
    )
    assert current_probe["expected_sources"] == ["config-r2-zero"]
    assert note["id"] in current_probe["stale_source_ids"]


def test_identifier_notes_are_grounded_in_full_string_validation(episodes: list[dict]) -> None:
    old = load_snapshot("r1", "identifiers")
    new = load_snapshot("r2", "identifiers")
    notes = experience_index(episodes)
    assert old.is_valid_identifier("task!") is True
    assert new.is_valid_identifier("task!") is False
    assert "re.fullmatch" in notes["identifier-r2-matching"]["content"]
    assert old.IDENTIFIER_PATTERN == new.IDENTIFIER_PATTERN
    for snapshot in [old, new]:
        assert snapshot.is_valid_identifier("_task2") is True
        assert snapshot.is_valid_identifier("2task") is False
        assert snapshot.is_valid_identifier("") is False
