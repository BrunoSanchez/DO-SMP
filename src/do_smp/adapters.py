"""Adapter abstractions for SMP engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
import copy
from typing import Any, Mapping

from .run_stub import SMPRunStub
from .standards import (
    DEFAULT_OUTPUT_CATEGORIES,
    DEFAULT_RUNNER_BACKENDS,
    SMPRunRequest,
)


class SMPAdapter(ABC):
    """Common adapter interface for different SMP engines."""

    name: str
    version: str
    engine_name: str
    engine_version: str
    extension_namespace: str = "do_smp.generic"
    supported_backends: tuple[str, ...] = DEFAULT_RUNNER_BACKENDS

    def build_run_stub(
        self,
        *,
        user_id: str,
        created_by: str | None = None,
        pipeline_type: str = "Scene Modeling Photometry (SMP)",
        configuration: Mapping[str, Any] | None = None,
        software: list[Mapping[str, Any]] | None = None,
        input_data: Mapping[str, Any] | None = None,
        targets: list[Mapping[str, Any]] | None = None,
        auxiliary: Mapping[str, Any] | None = None,
        notes: list[str] | None = None,
        environment: Mapping[str, Any] | None = None,
        code_reference: Mapping[str, Any] | None = None,
        provenance: Mapping[str, Any] | None = None,
        archival: Mapping[str, Any] | None = None,
        requested_outputs: list[str] | None = None,
        extensions: Mapping[str, Any] | None = None,
        status: str = "draft",
    ) -> SMPRunStub:
        """Return a normalized SMP run stub for this engine."""

        return self.build_run_stub_from_request(
            SMPRunRequest(
                user_id=user_id,
                created_by=created_by,
                pipeline_type=pipeline_type,
                configuration=dict(configuration or {}),
                software=[dict(item) for item in (software or [])],
                input_bundle=dict(input_data or {}),
                targets=[dict(target) for target in (targets or [])],
                auxiliary=dict(auxiliary or {}),
                notes=list(notes or []),
                environment=dict(environment or {}),
                code_reference=dict(code_reference or {}),
                provenance=dict(provenance or {}),
                archival=dict(archival or {}),
                requested_outputs=list(requested_outputs or DEFAULT_OUTPUT_CATEGORIES),
                extensions=dict(extensions or {}),
                status=status,
            )
        )

    @abstractmethod
    def build_run_stub_from_request(self, request: SMPRunRequest) -> SMPRunStub:
        """Return a normalized SMP run stub for this engine from a shared request."""

    def capabilities(self) -> dict[str, Any]:
        return {
            "adapter": {"name": self.name, "version": self.version},
            "engine": {"name": self.engine_name, "version": self.engine_version},
            "supported_backends": list(self.supported_backends),
            "supported_outputs": list(DEFAULT_OUTPUT_CATEGORIES),
            "extension_namespace": self.extension_namespace,
        }

    def validate_request(self, request: SMPRunRequest) -> None:
        unknown_namespaces = [
            namespace
            for namespace in request.extensions
            if namespace not in ("do_smp", self.extension_namespace)
        ]
        if unknown_namespaces:
            raise ValueError(
                f"{self.name} does not support extension namespaces: {', '.join(sorted(unknown_namespaces))}"
            )

    def _build_normalized_stub(self, request: SMPRunRequest) -> SMPRunStub:
        self.validate_request(request)
        metadata = request.to_metadata_dict()
        adapter_metadata = {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities(),
        }
        engine_metadata = {
            "name": self.engine_name,
            "version": self.engine_version,
        }
        software = metadata["software"] + [
            {
                "name": self.name,
                "version": self.version,
                "role": "adapter",
            },
            {
                "name": self.engine_name,
                "version": self.engine_version,
                "role": "smp-engine",
            },
        ]
        deduplicated_software: list[dict[str, Any]] = []
        seen_indices: dict[tuple[Any, Any, Any], int] = {}
        for record in software:
            key = (record.get("name"), record.get("version"), record.get("role"))
            if key in seen_indices:
                deduplicated_software[seen_indices[key]] = copy.deepcopy(record)
                continue
            seen_indices[key] = len(deduplicated_software)
            deduplicated_software.append(copy.deepcopy(record))
        return SMPRunStub.create(
            user_id=request.user_id,
            created_by=metadata["created_by"],
            pipeline_type=metadata["pipeline_type"],
            configuration=metadata["configuration"],
            software=deduplicated_software,
            input_data=metadata["input_data"],
            targets=metadata["targets"],
            auxiliary=metadata["auxiliary"],
            notes=metadata["notes"],
            environment=metadata["environment"],
            adapter=adapter_metadata,
            engine=engine_metadata,
            code_reference=metadata["code_reference"],
            data_reference=metadata["data_reference"],
            target_summary=metadata["target_summary"],
            provenance=metadata["provenance"],
            archival=metadata["archival"],
            requested_outputs=metadata["requested_outputs"],
            extensions=metadata["extensions"],
            status=request.status,
        )


class GenericSMPAdapter(SMPAdapter):
    """Default adapter for engines that only need normalized metadata."""

    def __init__(self, name: str = "generic-smp", version: str = "unknown") -> None:
        self.name = name
        self.version = version
        self.engine_name = name
        self.engine_version = version
        self.extension_namespace = f"engine.{name.replace('-', '_')}"

    def build_run_stub_from_request(self, request: SMPRunRequest) -> SMPRunStub:
        return self._build_normalized_stub(request)


class StarredAdapter(GenericSMPAdapter):
    def __init__(self, version: str = "unknown") -> None:
        super().__init__(name="starred", version=version)
        self.engine_name = "STARRED"
        self.extension_namespace = "engine.starred"


class AstroPhotAdapter(GenericSMPAdapter):
    def __init__(self, version: str = "unknown") -> None:
        super().__init__(name="astrophot", version=version)
        self.engine_name = "AstroPhot"
        self.extension_namespace = "engine.astrophot"


class Scarlet2Adapter(GenericSMPAdapter):
    def __init__(self, version: str = "unknown") -> None:
        super().__init__(name="scarlet2", version=version)
        self.engine_name = "Scarlet2"
        self.extension_namespace = "engine.scarlet2"


class SceneModelingPhotometryAdapter(GenericSMPAdapter):
    def __init__(self, version: str = "unknown") -> None:
        super().__init__(name="scene-modeling-photometry", version=version)
        self.engine_name = "SceneModelingPhotometry"
        self.extension_namespace = "engine.scene_modeling_photometry"


class AdapterRegistry:
    """In-memory registry for available SMP adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, SMPAdapter] = {}

    def register(self, adapter: SMPAdapter) -> None:
        self._adapters[adapter.name] = adapter

    def get(self, name: str) -> SMPAdapter:
        try:
            return self._adapters[name]
        except KeyError as exc:
            raise KeyError(f"Unknown SMP adapter: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._adapters)

    def capabilities(self) -> dict[str, dict[str, Any]]:
        return {name: adapter.capabilities() for name, adapter in sorted(self._adapters.items())}

    def create(self, name: str, *, version: str = "unknown") -> SMPAdapter:
        prototype = self.get(name)
        return type(prototype)(version=version)

    @classmethod
    def with_builtin_adapters(cls) -> "AdapterRegistry":
        registry = cls()
        for adapter in (
            GenericSMPAdapter(),
            StarredAdapter(),
            AstroPhotAdapter(),
            Scarlet2Adapter(),
            SceneModelingPhotometryAdapter(),
        ):
            registry.register(adapter)
        return registry
