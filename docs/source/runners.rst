Runners
=======

DO-SMP separates engine adapters from execution backends.

Available backends
------------------

* ``LocalRunner`` prepares a local launch description for a validated run stub
* ``SlurmRunner`` prepares a Slurm job payload for NERSC Perlmutter

Perlmutter / Slurm workflow
---------------------------

The Slurm runner emits a job script with:

* Slurm resource directives
* exported SMP run metadata such as the run id and engine name
* an ``srun`` command that references the normalized run stub

This keeps Slurm-specific details in the runner layer instead of in each engine
adapter.
