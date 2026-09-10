"""Reproducible SMP run stub model."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
import re
from typing import Any, Mapping

from .standards import DEFAULT_OUTPUT_CATEGORIES, DEFAULT_PIPELINE_TYPE, RUN_STATUSES

YAML_AMBIGUOUS_STRINGS = {
    "",
    "null",
    "~",
    "true",
    "false",
    "yes",
    "no",
    "on",
    "off",
    "nan",
    "inf",
    "-inf",
    ".nan",
    ".inf",
    "-.inf",
}
VERSION_LIKE_STRING = re.compile(r"^\d+(?:\.\d+)+$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return json.dumps(str(value))
        return str(value)

    text = str(value)
    if (
        text == ""
        or text.strip() != text
        or "\n" in text
        or any(character in text for character in ":#{}[]&*!|>'\"%@`")
        or text.lower() in YAML_AMBIGUOUS_STRINGS
        or VERSION_LIKE_STRING.fullmatch(text) is not None
    ):
        return json.dumps(text)
    return text


def _canonicalize_for_hash(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _canonicalize_for_hash(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, list):
        return [_canonicalize_for_hash(item) for item in value]
    return value


def _sorted_canonical_list(values: list[Any]) -> list[Any]:
    decorated = []
    for item in values:
        canonical_item = _canonicalize_for_hash(item)
        decorated.append(
            (
                json.dumps(canonical_item, sort_keys=True, separators=(",", ":")),
                canonical_item,
            )
        )
    return [canonical_item for _, canonical_item in sorted(decorated, key=lambda pair: pair[0])]


def _normalize_for_export(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _normalize_for_export(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_for_export(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def _normalize_for_hash(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _normalize_for_hash(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_for_hash(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
    return value


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
    created_by: str
    pipeline_type: str
    status: str
    notes: list[str] = field(default_factory=list)
    configuration: dict[str, Any] = field(default_factory=dict)
    software: list[dict[str, Any]] = field(default_factory=list)
    input_data: dict[str, Any] = field(default_factory=dict)
    targets: list[dict[str, Any]] = field(default_factory=list)
    auxiliary: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    adapter: dict[str, Any] = field(default_factory=dict)
    engine: dict[str, Any] = field(default_factory=dict)
    code_reference: dict[str, Any] = field(default_factory=dict)
    data_reference: dict[str, Any] = field(default_factory=dict)
    target_summary: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    archival: dict[str, Any] = field(default_factory=dict)
    extensions: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, list[dict[str, Any]]] = field(
        default_factory=lambda: {category: [] for category in DEFAULT_OUTPUT_CATEGORIES}
    )

    @classmethod
    def create(
        cls,
        *,
        user_id: str,
        created_by: str | None = None,
        pipeline_type: str = DEFAULT_PIPELINE_TYPE,
        configuration: dict[str, Any] | None = None,
        software: list[dict[str, Any]] | None = None,
        input_data: dict[str, Any] | None = None,
        targets: list[dict[str, Any]] | None = None,
        auxiliary: dict[str, Any] | None = None,
        notes: list[str] | None = None,
        environment: dict[str, Any] | None = None,
        adapter: dict[str, Any] | None = None,
        engine: dict[str, Any] | None = None,
        code_reference: dict[str, Any] | None = None,
        data_reference: dict[str, Any] | None = None,
        target_summary: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
        archival: dict[str, Any] | None = None,
        requested_outputs: list[str] | None = None,
        extensions: dict[str, Any] | None = None,
        status: str = "draft",
    ) -> "SMPRunStub":
        if status not in RUN_STATUSES:
            raise ValueError(f"Unsupported status: {status}")

        normalized_requested_outputs = (
            list(DEFAULT_OUTPUT_CATEGORIES)
            if requested_outputs is None
            else list(requested_outputs)
        )
        invalid_requested_outputs = sorted(
            {category for category in normalized_requested_outputs if category not in DEFAULT_OUTPUT_CATEGORIES}
        )
        if invalid_requested_outputs:
            raise ValueError(
                f"Unsupported output categories: {', '.join(invalid_requested_outputs)}"
            )
        normalized_requested_outputs = list(dict.fromkeys(normalized_requested_outputs))
        created_at = _utc_now()
        payload = {
            "schema_version": "0.1.0",
            "user_id": user_id,
            "created_by": created_by or user_id,
            "pipeline_type": pipeline_type,
            "notes": notes or [],
            "configuration": configuration or {},
            "software": _sorted_canonical_list(software or []),
            "input_data": input_data or {},
            "targets": _sorted_canonical_list(targets or []),
            "auxiliary": auxiliary or {},
            "environment": environment or {},
            "adapter": adapter or {},
            "engine": engine or {},
            "code_reference": code_reference or {},
            "data_reference": data_reference or {},
            "target_summary": target_summary or {},
            "provenance": provenance or {},
            "archival": archival or {},
            "requested_outputs": normalized_requested_outputs,
            "extensions": extensions or {},
        }
        run_id = hashlib.sha256(
            json.dumps(
                _canonicalize_for_hash(_normalize_for_hash(payload)),
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()

        return cls(
            schema_version="0.1.0",
            run_id=run_id,
            created_at=created_at,
            updated_at=created_at,
            user_id=user_id,
            created_by=created_by or user_id,
            pipeline_type=pipeline_type,
            status=status,
            notes=copy.deepcopy(notes or []),
            configuration=copy.deepcopy(configuration or {}),
            software=copy.deepcopy(software or []),
            input_data=copy.deepcopy(input_data or {}),
            targets=copy.deepcopy(targets or []),
            auxiliary=copy.deepcopy(auxiliary or {}),
            environment=copy.deepcopy(environment or {}),
            adapter=copy.deepcopy(adapter or {}),
            engine=copy.deepcopy(engine or {}),
            code_reference=copy.deepcopy(code_reference or {}),
            data_reference=copy.deepcopy(data_reference or {}),
            target_summary=copy.deepcopy(target_summary or {}),
            provenance=copy.deepcopy(provenance or {}),
            archival=copy.deepcopy(archival or {}),
            extensions=copy.deepcopy(extensions or {}),
            outputs={category: [] for category in normalized_requested_outputs},
        )

    def add_output(self, category: str, **metadata: Any) -> None:
        if category not in self.outputs:
            raise ValueError(f"Unsupported output category: {category}")
        self.outputs[category].append(dict(metadata))
        self.updated_at = _utc_now()

    def set_status(self, status: str) -> None:
        if status not in RUN_STATUSES:
            raise ValueError(f"Unsupported status: {status}")
        self.status = status
        self.updated_at = _utc_now()

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(
            {
                "schema_version": self.schema_version,
                "run_id": self.run_id,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "user_id": self.user_id,
                "created_by": self.created_by,
                "pipeline_type": self.pipeline_type,
                "status": self.status,
                "notes": self.notes,
                "configuration": self.configuration,
                "software": self.software,
                "input_data": self.input_data,
                "targets": self.targets,
                "auxiliary": self.auxiliary,
                "environment": self.environment,
                "adapter": self.adapter,
                "engine": self.engine,
                "code_reference": self.code_reference,
                "data_reference": self.data_reference,
                "target_summary": self.target_summary,
                "provenance": self.provenance,
                "archival": self.archival,
                "extensions": self.extensions,
                "outputs": {
                    category: items for category, items in self.outputs.items()
                },
            },
        )

    def to_yaml(self) -> str:
        return "\n".join(_to_yaml_lines(_normalize_for_export(self.to_dict()))) + "\n"
