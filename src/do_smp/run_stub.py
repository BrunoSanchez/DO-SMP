"""Reproducible SMP run stub model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping


DEFAULT_OUTPUT_CATEGORIES = (
    "light_curves",
    "model_fits",
    "summary_tables",
    "diagnostics",
    "artifacts",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)

    text = str(value)
    if (
        text == ""
        or text.strip() != text
        or "\n" in text
        or any(character in text for character in ":#{}[]&*!|>'\"%@`")
        or text.lower() in {"null", "true", "false", "yes", "no"}
    ):
        return json.dumps(text)
    return text


def _normalize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (dict(record) for record in records),
        key=lambda record: json.dumps(record, sort_keys=True, separators=(",", ":")),
    )


def _to_yaml_lines(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent

    if isinstance(value, Mapping):
        if not value:
            return [prefix + "{}"]

        lines: list[str] = []
        for key, item in value.items():
            rendered_key = _normalize_scalar(str(key))
            if isinstance(item, (Mapping, list)):
                if not item:
                    empty = "{}" if isinstance(item, Mapping) else "[]"
                    lines.append(f"{prefix}{rendered_key}: {empty}")
                else:
                    lines.append(f"{prefix}{rendered_key}:")
                    lines.extend(_to_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}{rendered_key}: {_normalize_scalar(item)}")
        return lines

    if isinstance(value, list):
        if not value:
            return [prefix + "[]"]

        lines = []
        for item in value:
            if isinstance(item, (Mapping, list)):
                if not item:
                    empty = "{}" if isinstance(item, Mapping) else "[]"
                    lines.append(f"{prefix}- {empty}")
                else:
                    lines.append(f"{prefix}-")
                    lines.extend(_to_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_normalize_scalar(item)}")
        return lines

    return [prefix + _normalize_scalar(value)]


@dataclass
class SMPRunStub:
    """Normalized SMP run description used for reproducibility."""

    schema_version: str
    run_id: str
    created_at: str
    updated_at: str
    user_id: str
    status: str
    notes: list[str] = field(default_factory=list)
    configuration: dict[str, Any] = field(default_factory=dict)
    software: list[dict[str, Any]] = field(default_factory=list)
    input_data: dict[str, Any] = field(default_factory=dict)
    targets: list[dict[str, Any]] = field(default_factory=list)
    auxiliary: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    engine: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: {category: [] for category in DEFAULT_OUTPUT_CATEGORIES}
    )

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        configuration: dict[str, Any] | None = None,
        software: list[dict[str, Any]] | None = None,
        input_data: dict[str, Any] | None = None,
        targets: list[dict[str, Any]] | None = None,
        auxiliary: dict[str, Any] | None = None,
        notes: list[str] | None = None,
        environment: dict[str, Any] | None = None,
        engine: dict[str, Any] | None = None,
        status: str = "draft",
    ) -> "SMPRunStub":
        created_at = _utc_now()
        payload = {
            "schema_version": "0.1.0",
            "user_id": user_id,
            "status": status,
            "notes": sorted(notes or []),
            "configuration": configuration or {},
            "software": _normalize_records(software or []),
            "input_data": input_data or {},
            "targets": _normalize_records(targets or []),
            "auxiliary": auxiliary or {},
            "environment": environment or {},
            "engine": engine or {},
        }
        run_id = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:12]

        return cls(
            schema_version="0.1.0",
            run_id=run_id,
            created_at=created_at,
            updated_at=created_at,
            user_id=user_id,
            status=status,
            notes=list(notes or []),
            configuration=dict(configuration or {}),
            software=[dict(component) for component in (software or [])],
            input_data=dict(input_data or {}),
            targets=[dict(target) for target in (targets or [])],
            auxiliary=dict(auxiliary or {}),
            environment=dict(environment or {}),
            engine=dict(engine or {}),
        )

    def add_output(self, category: str, **metadata: Any) -> None:
        if category not in self.outputs:
            raise ValueError(f"Unsupported output category: {category}")
        self.outputs[category].append(dict(metadata))
        self.updated_at = _utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_id": self.user_id,
            "status": self.status,
            "notes": list(self.notes),
            "configuration": dict(self.configuration),
            "software": [dict(component) for component in self.software],
            "input_data": dict(self.input_data),
            "targets": [dict(target) for target in self.targets],
            "auxiliary": dict(self.auxiliary),
            "environment": dict(self.environment),
            "engine": dict(self.engine),
            "outputs": {
                category: [dict(item) for item in items]
                for category, items in self.outputs.items()
            },
        }

    def to_yaml(self) -> str:
        return "\n".join(_to_yaml_lines(self.to_dict())) + "\n"
