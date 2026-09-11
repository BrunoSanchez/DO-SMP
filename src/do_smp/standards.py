"""Normalized standards for SMP requests, Rubin inputs, and outputs."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Mapping


DEFAULT_OUTPUT_CATEGORIES = (
    "light_curves",
    "model_fits",
    "summary_tables",
    "diagnostics",
    "artifacts",
)

RUN_STATUSES = ("draft", "queued", "running", "completed", "failed", "cancelled")
DEFAULT_PIPELINE_TYPE = "Scene Modeling Photometry (SMP)"
DEFAULT_RUNNER_BACKENDS = ("local", "slurm-perlmutter")


def _deep_copy_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return copy.deepcopy(dict(value or {}))


def _deep_copy_sequence(values: list[Any] | None) -> list[Any]:
    return copy.deepcopy(list(values or []))


def _normalize_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "to_dict"):
        return copy.deepcopy(value.to_dict())
    return copy.deepcopy(dict(value))


def _normalize_sequence(values: list[Any]) -> list[Any]:
    normalized: list[Any] = []
    for item in values:
        if hasattr(item, "to_dict"):
            normalized.append(copy.deepcopy(item.to_dict()))
        elif isinstance(item, Mapping):
            normalized.append(copy.deepcopy(dict(item)))
        else:
            normalized.append(copy.deepcopy(item))
    return normalized


def normalize_requested_outputs(requested_outputs: list[str] | None) -> list[str]:
    requested = (
        list(DEFAULT_OUTPUT_CATEGORIES)
        if requested_outputs is None
        else list(requested_outputs)
    )
    unknown = sorted({category for category in requested if category not in DEFAULT_OUTPUT_CATEGORIES})
    if unknown:
        raise ValueError(f"Unsupported output categories: {', '.join(unknown)}")
    return list(dict.fromkeys(requested))


@dataclass
class RubinDataCoordinate:
    """Canonical Rubin/LSST data identifier."""

    instrument: str = "LSSTCam"
    detector: str | int | None = None
    visit: str | int | None = None
    exposure: str | int | None = None
    tract: str | int | None = None
    patch: str | None = None
    band: str | None = None
    skymap: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"instrument": self.instrument}
        for key in ("detector", "visit", "exposure", "tract", "patch", "band", "skymap"):
            value = getattr(self, key)
            if value is not None:
                payload[key] = value
        payload.update(copy.deepcopy(self.extras))
        return payload


@dataclass
class RubinInputBundle:
    """Normalized Rubin/LSST-facing input bundle for an SMP run."""

    butler_collections: list[str] = field(default_factory=list)
    dataset_types: list[str] = field(default_factory=list)
    data_ids: list[RubinDataCoordinate | Mapping[str, Any]] = field(default_factory=list)
    exposures: list[str | int] = field(default_factory=list)
    visits: list[str | int] = field(default_factory=list)
    calibrations: list[str] = field(default_factory=list)
    templates: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    external_catalogs: list[str] = field(default_factory=list)
    dataset_uri: str | None = None
    manifest_uri: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "butler_collections": copy.deepcopy(self.butler_collections),
            "dataset_types": copy.deepcopy(self.dataset_types),
            "data_ids": _normalize_sequence(list(self.data_ids)),
            "exposures": copy.deepcopy(self.exposures),
            "visits": copy.deepcopy(self.visits),
            "calibrations": copy.deepcopy(self.calibrations),
            "templates": copy.deepcopy(self.templates),
            "references": copy.deepcopy(self.references),
            "external_catalogs": copy.deepcopy(self.external_catalogs),
        }
        if self.dataset_uri is not None:
            payload["dataset_uri"] = self.dataset_uri
        if self.manifest_uri is not None:
            payload["manifest_uri"] = self.manifest_uri
        payload.update(copy.deepcopy(self.extras))
        return payload

    def reference_dict(self) -> dict[str, Any]:
        payload = {
            "butler_collections": copy.deepcopy(self.butler_collections),
            "data_ids": _normalize_sequence(list(self.data_ids)),
            "calibrations": copy.deepcopy(self.calibrations),
            "templates": copy.deepcopy(self.templates),
            "external_catalogs": copy.deepcopy(self.external_catalogs),
        }
        if self.dataset_uri is not None:
            payload["dataset_uri"] = self.dataset_uri
        if self.manifest_uri is not None:
            payload["manifest_uri"] = self.manifest_uri
        return payload


@dataclass
class SMPTarget:
    """Normalized transient target descriptor."""

    object_id: str
    name: str | None = None
    ra: float | None = None
    dec: float | None = None
    redshift: float | None = None
    host: str | None = None
    target_class: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {"object_id": self.object_id}
        for key in ("name", "ra", "dec", "redshift", "host", "target_class"):
            value = getattr(self, key)
            if value is not None:
                payload[key] = value
        payload.update(copy.deepcopy(self.extras))
        return payload


@dataclass
class ArtifactRegistry:
    """Normalized archival and registry destinations for an SMP run."""

    run_stub_uri: str | None = None
    registry_uri: str | None = None
    archive_uri: str | None = None
    citation_doi: str | None = None
    analysis_use: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for key in ("run_stub_uri", "registry_uri", "archive_uri", "citation_doi", "analysis_use"):
            value = getattr(self, key)
            if value is not None:
                payload[key] = value
        payload.update(copy.deepcopy(self.extras))
        return payload


@dataclass
class NormalizedOutput:
    """Standard output record shared by all SMP engines."""

    category: str
    uri: str
    format: str
    summary: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "uri": self.uri,
            "format": self.format,
            "summary": copy.deepcopy(self.summary),
            "provenance": copy.deepcopy(self.provenance),
        }
        payload.update(copy.deepcopy(self.extras))
        return payload


@dataclass
class SMPRunRequest:
    """Normalized execution request that every SMP adapter consumes."""

    user_id: str
    created_by: str | None = None
    pipeline_type: str = DEFAULT_PIPELINE_TYPE
    configuration: dict[str, Any] = field(default_factory=dict)
    software: list[dict[str, Any]] = field(default_factory=list)
    input_bundle: RubinInputBundle | Mapping[str, Any] | None = None
    targets: list[SMPTarget | Mapping[str, Any]] = field(default_factory=list)
    auxiliary: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    environment: dict[str, Any] = field(default_factory=dict)
    code_reference: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    archival: ArtifactRegistry | Mapping[str, Any] | None = None
    requested_outputs: list[str] | None = None
    extensions: dict[str, Any] = field(default_factory=dict)
    status: str = "draft"

    def normalized_input_data(self) -> dict[str, Any]:
        if self.input_bundle is None:
            return RubinInputBundle().to_dict()
        return _normalize_mapping(self.input_bundle)

    def normalized_targets(self) -> list[dict[str, Any]]:
        return _normalize_sequence(list(self.targets))

    def normalized_data_reference(self) -> dict[str, Any]:
        if self.input_bundle is None:
            return RubinInputBundle().reference_dict()
        if hasattr(self.input_bundle, "reference_dict"):
            return copy.deepcopy(self.input_bundle.reference_dict())
        payload = _normalize_mapping(self.input_bundle)
        return {
            "butler_collections": copy.deepcopy(payload.get("butler_collections", [])),
            "data_ids": copy.deepcopy(payload.get("data_ids", [])),
            "calibrations": copy.deepcopy(payload.get("calibrations", [])),
            "templates": copy.deepcopy(payload.get("templates", [])),
            "external_catalogs": copy.deepcopy(payload.get("external_catalogs", [])),
            **(
                {"dataset_uri": payload["dataset_uri"]}
                if payload.get("dataset_uri") is not None
                else {}
            ),
            **(
                {"manifest_uri": payload["manifest_uri"]}
                if payload.get("manifest_uri") is not None
                else {}
            ),
        }

    def normalized_target_summary(self) -> dict[str, Any]:
        targets = self.normalized_targets()
        classes = sorted({target.get("target_class") for target in targets if target.get("target_class")})
        redshifts = [
            float(target["redshift"])
            for target in targets
            if target.get("redshift") is not None
        ]
        summary: dict[str, Any] = {"count": len(targets)}
        if classes:
            summary["classes"] = classes
        if redshifts:
            summary["redshift_range"] = {"min": min(redshifts), "max": max(redshifts)}
        return summary

    def normalized_archival(self) -> dict[str, Any]:
        if self.archival is None:
            return ArtifactRegistry().to_dict()
        return _normalize_mapping(self.archival)

    def normalized_requested_outputs(self) -> list[str]:
        return normalize_requested_outputs(self.requested_outputs)

    def to_metadata_dict(self) -> dict[str, Any]:
        return {
            "created_by": self.created_by or self.user_id,
            "pipeline_type": self.pipeline_type,
            "configuration": _deep_copy_mapping(self.configuration),
            "software": _deep_copy_sequence(self.software),
            "input_data": self.normalized_input_data(),
            "targets": self.normalized_targets(),
            "auxiliary": _deep_copy_mapping(self.auxiliary),
            "notes": _deep_copy_sequence(self.notes),
            "environment": _deep_copy_mapping(self.environment),
            "code_reference": _deep_copy_mapping(self.code_reference),
            "data_reference": self.normalized_data_reference(),
            "target_summary": self.normalized_target_summary(),
            "provenance": _deep_copy_mapping(self.provenance),
            "archival": self.normalized_archival(),
            "requested_outputs": self.normalized_requested_outputs(),
            "extensions": _deep_copy_mapping(self.extensions),
        }
