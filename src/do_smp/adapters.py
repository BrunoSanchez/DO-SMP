"""Adapter abstractions for SMP engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from .run_stub import SMPRunStub


class SMPAdapter(ABC):
    """Common adapter interface for different SMP engines."""

    name: str
    version: str

    @abstractmethod
    def build_run_stub(
        self,
        *,
        user_id: str,
        configuration: Mapping[str, Any] | None = None,
        input_data: Mapping[str, Any] | None = None,
        targets: list[Mapping[str, Any]] | None = None,
        auxiliary: Mapping[str, Any] | None = None,
        notes: list[str] | None = None,
        environment: Mapping[str, Any] | None = None,
        status: str = "draft",
    ) -> SMPRunStub:
        """Return a normalized SMP run stub for this engine."""


class GenericSMPAdapter(SMPAdapter):
    """Default adapter for engines that only need normalized metadata."""

    def __init__(self, name: str = "generic-smp", version: str = "unknown") -> None:
        self.name = name
        self.version = version

    def build_run_stub(
        self,
        *,
        user_id: str,
        configuration: Mapping[str, Any] | None = None,
        input_data: Mapping[str, Any] | None = None,
        targets: list[Mapping[str, Any]] | None = None,
        auxiliary: Mapping[str, Any] | None = None,
        notes: list[str] | None = None,
        environment: Mapping[str, Any] | None = None,
        status: str = "draft",
    ) -> SMPRunStub:
        return SMPRunStub.create(
            user_id=user_id,
            configuration=dict(configuration or {}),
            software=[
                {
                    "name": self.name,
                    "version": self.version,
                    "role": "smp-engine",
                }
            ],
            input_data=dict(input_data or {}),
            targets=[dict(target) for target in (targets or [])],
            auxiliary=dict(auxiliary or {}),
            notes=list(notes or []),
            environment=dict(environment or {}),
            engine={"name": self.name, "version": self.version},
            status=status,
        )


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
