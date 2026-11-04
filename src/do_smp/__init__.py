"""Minimal SMP orchestration scaffold."""

from .adapters import (
    AdapterRegistry,
    AstroPhotAdapter,
    GenericSMPAdapter,
    SMPAdapter,
    Scarlet2Adapter,
    SceneModelingPhotometryAdapter,
    StarredAdapter,
)
from .run_stub import SMPRunStub
from .runners import LocalRunner, RunnerLaunch, SlurmRunner, SMPRunner
from .standards import (
    ArtifactRegistry,
    DEFAULT_OUTPUT_CATEGORIES,
    DEFAULT_PIPELINE_TYPE,
    RUN_STATUSES,
    RubinDataCoordinate,
    RubinInputBundle,
    SMPRunRequest,
    SMPTarget,
)

__all__ = [
    "AdapterRegistry",
    "AstroPhotAdapter",
    "ArtifactRegistry",
    "DEFAULT_OUTPUT_CATEGORIES",
    "DEFAULT_PIPELINE_TYPE",
    "GenericSMPAdapter",
    "LocalRunner",
    "RUN_STATUSES",
    "RubinDataCoordinate",
    "RubinInputBundle",
    "RunnerLaunch",
    "SMPAdapter",
    "SMPRunner",
    "SMPRunRequest",
    "SMPTarget",
    "SMPRunStub",
    "Scarlet2Adapter",
    "SceneModelingPhotometryAdapter",
    "SlurmRunner",
    "StarredAdapter",
]
