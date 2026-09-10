# DO-SMP

DESC Orchestrator for Scene Modeling Photometry.

This repository now includes a minimal Python scaffold for reproducible Scene
Modeling Photometry (SMP) runs:

- a structured SMP run stub with metadata for configuration, software, inputs,
  targets, auxiliary information, notes, status, environment, engine metadata,
  timestamps, run hash, and user id
- a lightweight adapter pattern for normalizing different SMP engines behind a
  shared interface
- output tracking for light-curves, model fits, summary tables, diagnostics,
  and generic artifacts
- a checked-in YAML example at
  `/home/runner/work/DO-SMP/DO-SMP/examples/smp-run.stub.yaml`

## Layout

- `/home/runner/work/DO-SMP/DO-SMP/src/do_smp/run_stub.py` - run metadata model
- `/home/runner/work/DO-SMP/DO-SMP/src/do_smp/adapters.py` - adapter interface,
  generic adapter, and registry
- `/home/runner/work/DO-SMP/DO-SMP/src/do_smp/cli.py` - small CLI to emit a run
  stub as YAML
- `/home/runner/work/DO-SMP/DO-SMP/tests/test_run_stub.py` - focused unit tests

## Generate a stub

```bash
cd /home/runner/work/DO-SMP/DO-SMP
PYTHONPATH=src python -m do_smp --user-id your-user-id --engine generic-smp
```

The command prints a YAML stub that can be versioned alongside SMP processing
runs to improve reproducibility and collaboration.
