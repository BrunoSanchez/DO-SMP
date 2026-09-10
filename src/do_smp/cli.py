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
    parser = argparse.ArgumentParser(description="Emit a reproducible SMP run stub.")
    parser.add_argument(
        "--list-engines",
        action="store_true",
        help="List built-in SMP adapters and exit",
    )
    parser.add_argument("--user-id", required=True, help="Collaborator or service user id")
    parser.add_argument(
        "--created-by",
        help="Human-readable creator label; defaults to --user-id",
    )
    parser.add_argument("--engine", default="generic-smp", help="SMP engine name")
    parser.add_argument("--engine-version", default="unknown", help="SMP engine version")
    parser.add_argument(
        "--status",
        default="draft",
        choices=RUN_STATUSES,
        help="Initial run status",
    )
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Optional note to include in the run stub",
    )
    parser.add_argument("--config-uri", help="Configuration file or manifest URI")
    parser.add_argument("--dataset-uri", help="Top-level input dataset URI")
    parser.add_argument(
        "--collection",
        action="append",
        default=[],
        help="Rubin Butler collection reference",
    )
    parser.add_argument(
        "--template",
        action="append",
        default=[],
        help="Template or reference image URI",
    )
    parser.add_argument(
        "--external-catalog",
        action="append",
        default=[],
        help="External catalog reference",
    )
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Target identifier to include in the stub",
    )
    parser.add_argument("--code-repository", help="Source repository URI")
    parser.add_argument("--code-commit", help="Source commit hash")
    parser.add_argument("--code-tag", help="Source tag or release")
    parser.add_argument("--python-version", help="Python runtime version")
    parser.add_argument("--lsst-stack-version", help="LSST stack version")
    parser.add_argument("--registry-uri", help="Run registry location")
    parser.add_argument("--archive-uri", help="Artifact archive location")
    return parser


def build_run_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare execution metadata from a run stub.")
    parser.add_argument("--run-stub", required=True, help="Path to the run stub YAML file")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(argv or [])
    if argv and argv[0] == "run":
        args = build_run_parser().parse_args(argv[1:])
        run_stub_path = Path(args.run_stub)
        if not run_stub_path.exists():
            raise SystemExit(f"Run stub not found: {run_stub_path}")
        sys.stdout.write(f"Prepared execution from {run_stub_path}\n")
        return 0

    args = build_parser().parse_args(argv)
    registry = AdapterRegistry.with_builtin_adapters()
    if args.list_engines:
        sys.stdout.write("\n".join(registry.names()) + "\n")
        return 0

    adapter = registry.get(args.engine)
    adapter.version = args.engine_version
    adapter.engine_version = args.engine_version
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
