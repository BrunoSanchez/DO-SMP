Contributor guide
=================

Adding a new engine adapter
---------------------------

To add another SMP implementation:

* subclass ``SMPAdapter`` or ``GenericSMPAdapter``
* declare engine metadata and an extension namespace
* consume the shared ``SMPRunRequest`` contract
* emit the normalized ``SMPRunStub`` output categories
* add contract tests alongside the existing adapter tests

Design rules
------------

* keep Rubin/LSST input normalization in the shared standards layer
* keep engine-specific knobs under namespaced ``extensions``
* keep execution backend details in runners, not adapters
* preserve provenance and archival metadata needed for reproducibility
