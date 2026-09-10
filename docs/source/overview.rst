Overview
========

The repository currently provides three core pieces:

* ``SMPRunStub`` for storing reproducible SMP run metadata
* ``SMPRunRequest`` plus normalized Rubin input and target models for a shared
  SMP execution contract
* ``SMPAdapter`` and built-in adapters for STARRED, AstroPhot, Scarlet2, and
  SceneModelingPhotometry behind a shared interface
* ``LocalRunner`` and ``SlurmRunner`` for backend-specific launch metadata
* a CLI entrypoint that emits a YAML run stub suitable for committing alongside
  reprocessing work

Tracked metadata
----------------

The SMP run stub is designed to capture the main ingredients of a collaborative
run:

* configuration
* software, adapter, and SMP engine metadata
* Rubin/LSST input data references
* targets and auxiliary metadata
* user id, creator label, timestamps, status, notes, and environment details
* code reference, data reference, target summary, provenance, and archival
  registry metadata
* output buckets for light curves, model fits, summary tables, diagnostics, and
  artifacts

Starter template
----------------

The repository includes a starter stub at ``examples/smp-run.stub.yaml``:

.. literalinclude:: ../../examples/smp-run.stub.yaml
   :language: yaml

Engine-specific placeholders are also included:

* ``examples/starred.stub.yaml``
* ``examples/astrophot.stub.yaml``
* ``examples/scarlet2.stub.yaml``
* ``examples/scene-modeling-photometry.stub.yaml``

Build the docs
--------------

Install the docs dependency and build the HTML site from the repository root:

.. code-block:: bash

   python -m pip install -r docs/requirements.txt
   make -C docs html
