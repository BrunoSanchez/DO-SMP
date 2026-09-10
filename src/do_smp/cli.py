"""CLI helpers for SMP run stubs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .adapters import AdapterRegistry
from .standards import (
    ArtifactRegistry,
    RubinInputBundle,
    RUN_STATUSES,
    SMPRunRequest,
    SMPTarget,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DO-SMP command line interface.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    stub_parser = subparsers.add_parser("stub", help="Emit a reproducible SMP run stub")
    stub_parser.add_argument(
        "--list-engines",
        action="store_true",
        help="List built-in SMP adapters and exit",
    )
    stub_parser.add_argument("--user-id", help="Collaborator or service user id")
    stub_parser.add_argument(
        "--created-by",
        help="Human-readable creator label; defaults to --user-id",
    )
    stub_parser.add_argument("--engine", default="generic-smp", help="SMP engine name")
    stub_parser.add_argument("--engine-version", default="unknown", help="SMP engine version")
    stub_parser.add_argument(
        "--status",
        default="draft",
        choices=RUN_STATUSES,
        help="Initial run status",
    )
    stub_parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Optional note to include in the run stub",
    )
    stub_parser.add_argument("--config-uri", help="Configuration file or manifest URI")
    stub_parser.add_argument("--dataset-uri", help="Top-level input dataset URI")
    stub_parser.add_argument(
        "--collection",
        action="append",
        default=[],
        help="Rubin Butler collection reference",
    )
    stub_parser.add_argument(
        "--template",
        action="append",
        default=[],
        help="Template or reference image URI",
    )
    stub_parser.add_argument(
        "--external-catalog",
        action="append",
        default=[],
        help="External catalog reference",
    )
    stub_parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Target identifier to include in the stub",
    )
    stub_parser.add_argument("--code-repository", help="Source repository URI")
    stub_parser.add_argument("--code-commit", help="Source commit hash")
    stub_parser.add_argument("--code-tag", help="Source tag or release")
    stub_parser.add_argument("--python-version", help="Python runtime version")
    stub_parser.add_argument("--lsst-stack-version", help="LSST stack version")
    stub_parser.add_argument("--registry-uri", help="Run registry location")
    stub_parser.add_argument("--archive-uri", help="Artifact archive location")

    run_parser = subparsers.add_parser("run", help="Prepare execution metadata from a run stub")
    run_parser.add_argument("--run-stub", required=True, help="Path to the run stub YAML file")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = [] if argv is None else list(argv)
    if not argv or argv[0] not in {"stub", "run"}:
        argv = ["stub", *argv]

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        run_stub_path = Path(args.run_stub)
        if not run_stub_path.exists():
            raise SystemExit(f"Run stub not found: {run_stub_path}")
        sys.stdout.write(f"Prepared execution from {run_stub_path}\n")
        return 0

    registry = AdapterRegistry.with_builtin_adapters()
    if args.list_engines:
        sys.stdout.write("\n".join(registry.names()) + "\n")
        return 0

    if not args.user_id:
        parser.error("--user-id is required unless --list-engines is used")

    try:
        adapter = registry.create(args.engine, version=args.engine_version)
    except KeyError:
        parser.error(f"unknown engine: {args.engine}")
    input_bundle = RubinInputBundle(
        butler_collections=args.collection,
        templates=args.template,
        external_catalogs=args.external_catalog,
        extras=(
            {"dataset_uri": args.dataset_uri}
            if args.dataset_uri
            else {}
        ),
    )
    request = SMPRunRequest(
        user_id=args.user_id,
        created_by=args.created_by,
        configuration=(
            {"config_uri": args.config_uri}
            if args.config_uri
            else {}
        ),
        input_bundle=input_bundle,
        targets=[SMPTarget(object_id=target, name=target) for target in args.target],
        notes=args.note,
        environment={
            key: value
            for key, value in (
                ("python", args.python_version),
                ("lsst_stack", args.lsst_stack_version),
            )
            if value is not None
        },
        code_reference={
            key: value
            for key, value in (
                ("repository", args.code_repository),
                ("commit", args.code_commit),
                ("tag", args.code_tag),
            )
            if value is not None
        },
        archival=ArtifactRegistry(
            registry_uri=args.registry_uri,
            archive_uri=args.archive_uri,
        ),
        status=args.status,
    )
    stub = adapter.build_run_stub_from_request(request)
    sys.stdout.write(stub.to_yaml())
    return 0
