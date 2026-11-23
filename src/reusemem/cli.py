"""Command-line entry points for the offline experiment scaffold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from reusemem.doctor import inspect_environment

POLICIES = ("no_memory", "append_only", "recent_window", "keyed_revision")


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _demo_input() -> Path:
    relative = Path("examples/synthetic-chains.jsonl")
    for root in (Path.cwd(), Path(__file__).resolve().parents[2]):
        candidate = root / relative
        if candidate.is_file():
            return candidate
    raise ValueError("demo fixtures not found; run inside the repository or use replay --input PATH")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ReuseMem: inspectable experience-memory experiments")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor", help="inspect the local environment without model calls")
    doctor.add_argument("--external-eval-root", type=Path)
    doctor.add_argument("--benchmark-root", type=Path)
    doctor.add_argument("--trajectories-root", type=Path)
    for name, help_text in (
        ("demo", "run bundled synthetic memory probes (CPU, no API key)"),
        ("replay", "run controlled memory probes from a JSONL episode file"),
    ):
        command = commands.add_parser(name, help=help_text)
        if name == "replay":
            command.add_argument("--input", required=True, type=Path)
        command.add_argument("--output", required=True, type=Path)
        command.add_argument("--policies", nargs="+", choices=POLICIES, default=list(POLICIES))
        command.add_argument("--memory-budget", type=_positive_int, default=2048)
        command.add_argument("--retrieval-budget", type=_positive_int, default=512)
    args = parser.parse_args(argv)
    if args.command == "doctor":
        report = inspect_environment(
            args.external_eval_root, args.benchmark_root, args.trajectories_root
        )
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1
    try:
        from reusemem.replay import run_replay

        input_path = (args.input if args.command == "replay" else _demo_input()).resolve()
        output = args.output.expanduser().resolve()
        if output == input_path or output in input_path.parents:
            raise ValueError("output directory must not contain the input episode file")
        if output.exists() and (not output.is_dir() or any(output.iterdir())):
            raise ValueError("output must be a new or empty directory; previous results are preserved")
        if not input_path.is_file():
            raise ValueError(f"input file not found: {input_path}")
        run_replay(
            input_path=input_path,
            output_dir=output,
            policies=args.policies,
            memory_budget=args.memory_budget,
            retrieval_budget=args.retrieval_budget,
        )
        (output / "environment.json").write_text(
            json.dumps(inspect_environment(), indent=2) + "\n", encoding="utf-8"
        )
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Synthetic memory-probe results: {output / 'summary.md'}")
    print("These scores measure deterministic retrieval, not coding-agent performance.")
    return 0
