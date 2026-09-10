import unittest

from do_smp.adapters import AdapterRegistry, GenericSMPAdapter
from do_smp.run_stub import DEFAULT_OUTPUT_CATEGORIES, SMPRunStub


class SMPRunStubTest(unittest.TestCase):
    def test_create_stub_tracks_required_sections(self) -> None:
        stub = SMPRunStub.create(
            user_id="desc-user",
            configuration={"pipeline": "nightly"},
            software=[{"name": "smp-core", "version": "1.2.3"}],
            input_data={"images": ["s3://bucket/exposure.fits"]},
            targets=[{"name": "SN2026abc", "band": "i"}],
            auxiliary={"campaign": "reprocessing"},
            notes=["initial import"],
            environment={"container": "ghcr.io/desc/smp:latest"},
            engine={"name": "smp-core", "version": "1.2.3"},
        )

        self.assertEqual(stub.user_id, "desc-user")
        self.assertEqual(stub.status, "draft")
        self.assertTrue(stub.run_id)
        self.assertEqual(sorted(stub.outputs), sorted(DEFAULT_OUTPUT_CATEGORIES))

    def test_yaml_contains_reproducibility_sections(self) -> None:
        adapter = GenericSMPAdapter(name="scene-modeler", version="0.4.0")
        stub = adapter.build_run_stub(
            user_id="desc-user",
            configuration={"config_uri": "configs/run.yaml"},
            input_data={"dataset": "DR1"},
            targets=[{"name": "SN2026abc"}],
            auxiliary={"ticket": "DESC-42"},
            notes=["review pending"],
            environment={"python": "3.12"},
        )
        stub.add_output("light_curves", path="outputs/lightcurve.parquet", format="parquet")

        yaml_output = stub.to_yaml()

        for section in (
            "run_id:",
            "user_id:",
            "configuration:",
            "software:",
            "input_data:",
            "targets:",
            "auxiliary:",
            "environment:",
            "engine:",
            "outputs:",
            "light_curves:",
        ):
            self.assertIn(section, yaml_output)

    def test_adapter_registry_returns_registered_adapter(self) -> None:
        adapter = GenericSMPAdapter(name="adapter-a", version="1.0.0")
        registry = AdapterRegistry()
        registry.register(adapter)

        self.assertEqual(registry.names(), ["adapter-a"])
        self.assertIs(registry.get("adapter-a"), adapter)


if __name__ == "__main__":
    unittest.main()
