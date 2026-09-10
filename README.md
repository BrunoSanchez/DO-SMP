# DO-SMP

DESC Orchestrator for Scene Modeling Photometry.

This repository now includes a minimal Python scaffold for reproducible Scene
Modeling Photometry (SMP) runs:

- a structured SMP run stub with metadata for configuration, software, inputs,
  Rubin/LSST data references, targets, auxiliary information, notes, status,
  environment, engine metadata, timestamps, run hash, and user identity
- a lightweight adapter pattern for normalizing different SMP engines behind a
  shared interface
- built-in adapter placeholders for STARRED, AstroPhot, Scarlet2, and
  SceneModelingPhotometry
- runner abstractions for local execution and Slurm job preparation on NERSC
  Perlmutter
- output tracking for light-curves, model fits, summary tables, diagnostics,
  and generic artifacts, plus provenance and archival metadata
- a checked-in YAML starter template with placeholders at
  `examples/smp-run.stub.yaml` and engine-specific stubs under `examples/`

## Layout

- `src/do_smp/run_stub.py` - run metadata model
- `src/do_smp/standards.py` - normalized Rubin inputs, targets, outputs, and
  run request models
- `src/do_smp/adapters.py` - adapter interface, engine adapters, and registry
- `src/do_smp/runners.py` - local and Slurm runner abstractions
- `src/do_smp/cli.py` - CLI to emit a run stub as YAML
- `tests/test_run_stub.py` - focused unit tests

## Generate a stub

```bash
cd <repo-root>
PYTHONPATH=src python -m do_smp --user-id your-user-id --engine generic-smp --engine-version 0.1.0
```

The command prints a YAML stub that can be versioned alongside SMP processing
runs to improve reproducibility and collaboration.

List the built-in engines:

```bash
PYTHONPATH=src python -m do_smp --list-engines
```

Generate a STARRED-flavored stub with Rubin and archival metadata:

```bash
PYTHONPATH=src python -m do_smp \
  --user-id your-user-id \
  --created-by "jdoe (DESC)" \
  --engine starred \
  --engine-version 0.4.0 \
  --config-uri configs/starred.yaml \
  --collection LSSTCam/runs/DP0.2 \
  --target SN2026abc \
  --registry-uri registry/starred.json
```

## Included engines and runners

Built-in adapters are provided for:

- `generic-smp`
- `starred`
- `astrophot`
- `scarlet2`
- `scene-modeling-photometry`

Execution backends currently include:

- `LocalRunner` for local orchestration metadata
- `SlurmRunner` for Slurm job generation targeting NERSC Perlmutter

## Documentation

Basic Sphinx documentation is available under `docs/`.

```bash
python -m pip install -r docs/requirements.txt
make -C docs html
```

The rendered HTML entrypoint is `docs/build/html/index.html`.
