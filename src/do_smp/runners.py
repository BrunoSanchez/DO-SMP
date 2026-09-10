"""Execution backends for SMP run stubs."""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import shlex
from typing import Any

from .run_stub import SMPRunStub


@dataclass
class RunnerLaunch:
    """Runner launch description."""

    backend: str
    command: list[str]
    environment: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "command": copy.deepcopy(self.command),
            "environment": copy.deepcopy(self.environment),
            "metadata": copy.deepcopy(self.metadata),
        }


class SMPRunner(ABC):
    """Execution backend for SMP runs."""

    backend_name: str

    @abstractmethod
    def prepare_launch(self, stub: SMPRunStub, *, run_stub_path: str) -> RunnerLaunch:
        """Prepare a launch description for the supplied run stub."""


class LocalRunner(SMPRunner):
    backend_name = "local"

    def prepare_launch(self, stub: SMPRunStub, *, run_stub_path: str) -> RunnerLaunch:
        return RunnerLaunch(
            backend=self.backend_name,
            command=["python", "-m", "do_smp", "run", "--run-stub", run_stub_path],
            metadata={
                "engine": stub.engine.get("name"),
                "run_id": stub.run_id,
            },
        )


class SlurmRunner(SMPRunner):
    backend_name = "slurm-perlmutter"

    def __init__(
        self,
        *,
        account: str = "m1234",
        qos: str = "regular",
        partition: str = "cpu",
        time_limit: str = "01:00:00",
        nodes: int = 1,
        tasks_per_node: int = 1,
    ) -> None:
        self.account = account
        self.qos = qos
        self.partition = partition
        self.time_limit = time_limit
        self.nodes = nodes
        self.tasks_per_node = tasks_per_node

    def render_job_script(self, stub: SMPRunStub, *, run_stub_path: str) -> str:
        job_name = f"smp-{stub.run_id[:12]}"
        lines = [
            "#!/bin/bash",
            f"#SBATCH --job-name={job_name}",
            f"#SBATCH --account={self.account}",
            f"#SBATCH --qos={self.qos}",
            f"#SBATCH --constraint={self.partition}",
            f"#SBATCH --time={self.time_limit}",
            f"#SBATCH --nodes={self.nodes}",
            f"#SBATCH --ntasks-per-node={self.tasks_per_node}",
            "",
            "set -euo pipefail",
            f"export DO_SMP_RUN_ID={stub.run_id}",
            f"export DO_SMP_ENGINE={stub.engine.get('name', 'unknown')}",
            f"srun python -m do_smp run --run-stub {shlex.quote(run_stub_path)}",
            "",
        ]
        return "\n".join(lines)

    def prepare_launch(self, stub: SMPRunStub, *, run_stub_path: str) -> RunnerLaunch:
        return RunnerLaunch(
            backend=self.backend_name,
            command=["sbatch"],
            metadata={
                "run_id": stub.run_id,
                "job_script": self.render_job_script(stub, run_stub_path=run_stub_path),
                "engine": stub.engine.get("name"),
                "site": "NERSC Perlmutter",
            },
        )
