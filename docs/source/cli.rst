CLI examples
============

The CLI emits a YAML SMP run stub to standard output.

Minimal example
---------------

.. code-block:: bash

   PYTHONPATH=src python -m do_smp \
     --user-id your-user-id \
     --engine generic-smp \
     --engine-version 0.1.0

List the built-in engines
-------------------------

.. code-block:: bash

   PYTHONPATH=src python -m do_smp \
     --user-id your-user-id \
     --list-engines

Add notes and an explicit status
--------------------------------

.. code-block:: bash

   PYTHONPATH=src python -m do_smp \
     --user-id analyst-42 \
     --engine scene-modeler \
     --engine-version 2.1.0 \
     --status queued \
     --note "DESC reprocessing batch 12" \
     --note "validation pending"

Rubin-aware STARRED example
---------------------------

.. code-block:: bash

   PYTHONPATH=src python -m do_smp \
     --user-id analyst-42 \
     --created-by "jdoe (DESC)" \
     --engine starred \
     --engine-version 2.1.0 \
     --config-uri configs/starred.yaml \
     --collection LSSTCam/runs/DP0.2 \
     --target SN2026abc \
     --registry-uri registry/starred.json

Write a stub to a file
----------------------

.. code-block:: bash

   PYTHONPATH=src python -m do_smp \
     --user-id analyst-42 \
     --engine generic-smp \
     --engine-version 0.1.0 \
     > smp-run.yaml

Supported status values
-----------------------

The CLI currently accepts these normalized run lifecycle values:

* ``draft``
* ``queued``
* ``running``
* ``completed``
* ``failed``
* ``cancelled``

The emitted stub also includes normalized adapter metadata, Rubin/LSST input
references, provenance details, and archival destinations.
