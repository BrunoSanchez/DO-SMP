Overview
========

The repository currently provides three core pieces:

* ``SMPRunStub`` for storing reproducible SMP run metadata
* ``SMPAdapter`` and ``GenericSMPAdapter`` for normalizing multiple SMP engines
  behind a shared interface
* a CLI entrypoint that emits a YAML run stub suitable for committing alongside
  reprocessing work

Tracked metadata
----------------

The SMP run stub is designed to capture the main ingredients of a collaborative
run:

* configuration
* software and SMP engine metadata
* input data references
* targets and auxiliary metadata
* user id, timestamps, status, notes, and environment details
* output buckets for light curves, model fits, summary tables, diagnostics, and
  artifacts

Starter template
----------------

The repository includes a starter stub at ``examples/smp-run.stub.yaml``:

.. literalinclude:: ../../examples/smp-run.stub.yaml
   :language: yaml

Build the docs
--------------

Install the docs dependency and build the HTML site from the repository root:

.. code-block:: bash

   python -m pip install -r docs/requirements.txt
   make -C docs html
