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
