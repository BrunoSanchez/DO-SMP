"""CLI helpers for SMP run stubs."""

from __future__ import annotations

import argparse
import sys

from .adapters import GenericSMPAdapter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit a reproducible SMP run stub.")
    parser.add_argument("--user-id", required=True, help="Collaborator or service user id")
    parser.add_argument("--engine", default="generic-smp", help="SMP engine name")
    parser.add_argument("--engine-version", default="unknown", help="SMP engine version")
    parser.add_argument("--status", default="draft", help="Initial run status")
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Optional note to include in the run stub",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    adapter = GenericSMPAdapter(name=args.engine, version=args.engine_version)
    stub = adapter.build_run_stub(
        user_id=args.user_id,
        notes=args.note,
        status=args.status,
    )
    sys.stdout.write(stub.to_yaml())
    return 0
