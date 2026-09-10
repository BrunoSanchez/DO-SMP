import io
import unittest
from unittest.mock import patch

from do_smp import cli
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
        self.assertEqual(len(stub.run_id), 64)
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

    def test_identical_stable_inputs_keep_same_run_id(self) -> None:
        kwargs = {
            "user_id": "desc-user",
            "configuration": {"config_uri": "configs/run.yaml"},
            "software": [
                {"name": "adapter-b", "version": "2.0.0"},
                {"name": "adapter-a", "version": "1.0.0"},
            ],
            "input_data": {"dataset": "DR1"},
            "targets": [{"name": "SN2026xyz"}, {"name": "SN2026abc"}],
            "auxiliary": {"ticket": "DESC-42"},
            "notes": ["review pending", "draft"],
            "environment": {"python": "3.12"},
            "engine": {"name": "smp-core", "version": "1.2.3"},
        }
        reordered_kwargs = {
            **kwargs,
            "software": list(reversed(kwargs["software"])),
        }

        with patch(
            "do_smp.run_stub._utc_now",
            side_effect=["2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z"],
        ):
            first = SMPRunStub.create(**kwargs)
            second = SMPRunStub.create(**reordered_kwargs)

        self.assertNotEqual(first.created_at, second.created_at)
        self.assertEqual(first.run_id, second.run_id)

    def test_ordered_note_sequence_changes_run_id(self) -> None:
        kwargs = {
            "user_id": "desc-user",
            "notes": ["first", "second"],
            "software": [{"name": "adapter-a", "version": "1.0.0"}],
        }

        first = SMPRunStub.create(**kwargs)
        second = SMPRunStub.create(**{**kwargs, "notes": ["second", "first"]})

        self.assertNotEqual(first.run_id, second.run_id)

    def test_yaml_quotes_special_keys_and_nested_values(self) -> None:
        stub = SMPRunStub.create(
            user_id="desc-user",
            configuration={"config:uri": "configs/run:1.yaml", " key ": " value "},
            input_data={"inputs": [{"uri": "s3://bucket/file.fits", "tag": "raw:data"}]},
        )

        yaml_output = stub.to_yaml()

        self.assertIn('"config:uri": "configs/run:1.yaml"', yaml_output)
        self.assertIn('" key ": " value "', yaml_output)
        self.assertIn("inputs:\n    -\n      uri: \"s3://bucket/file.fits\"", yaml_output)
        self.assertIn('tag: "raw:data"', yaml_output)

    def test_yaml_quotes_non_finite_floats(self) -> None:
        stub = SMPRunStub.create(
            user_id="desc-user",
            auxiliary={"nan_value": float("nan"), "inf_value": float("inf")},
        )

        yaml_output = stub.to_yaml()

        self.assertIn('nan_value: "nan"', yaml_output)
        self.assertIn('inf_value: "inf"', yaml_output)

    def test_adapter_registry_returns_registered_adapter(self) -> None:
        adapter = GenericSMPAdapter(name="adapter-a", version="1.0.0")
        registry = AdapterRegistry()
        registry.register(adapter)

        self.assertEqual(registry.names(), ["adapter-a"])
        self.assertIs(registry.get("adapter-a"), adapter)

    def test_to_dict_returns_deep_copy(self) -> None:
        stub = SMPRunStub.create(
            user_id="desc-user",
            configuration={"nested": {"bands": ["g", "r"]}},
        )
        exported = stub.to_dict()
        exported["configuration"]["nested"]["bands"].append("i")

        self.assertEqual(stub.configuration["nested"]["bands"], ["g", "r"])

    def test_cli_main_emits_notes_and_engine_metadata(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            exit_code = cli.main(
                [
                    "--user-id",
                    "desc-user",
                    "--engine",
                    "scene-modeler",
                    "--engine-version",
                    "2.1.0",
                    "--status",
                    "queued",
                    "--note",
                    "first",
                    "--note",
                    "second",
                ]
            )

        output = stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("status: queued", output)
        self.assertIn("name: scene-modeler", output)
        self.assertIn("version: 2.1.0", output)
        self.assertIn("- first", output)
        self.assertIn("- second", output)


if __name__ == "__main__":
    unittest.main()
