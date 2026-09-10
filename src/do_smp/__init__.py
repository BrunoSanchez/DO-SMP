"""Minimal SMP orchestration scaffold."""

from .adapters import AdapterRegistry, GenericSMPAdapter, SMPAdapter
from .run_stub import SMPRunStub

__all__ = [
    "AdapterRegistry",
    "GenericSMPAdapter",
    "SMPAdapter",
    "SMPRunStub",
]
