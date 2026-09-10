import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from do_smp import cli
from do_smp.adapters import (
    AdapterRegistry,
    AstroPhotAdapter,
    GenericSMPAdapter,
    Scarlet2Adapter,
    SceneModelingPhotometryAdapter,
    StarredAdapter,
)
from do_smp.run_stub import DEFAULT_OUTPUT_CATEGORIES, SMPRunStub
from do_smp.runners import LocalRunner, SlurmRunner
from do_smp.standards import ArtifactRegistry, RubinDataCoordinate, RubinInputBundle, SMPRunRequest, SMPTarget


class SMPRunStubTest(unittest.TestCase):
    def test_create_stub_tracks_required_sections(self) -> None:
        stub = SMPRunStub.create(
            user_id="desc-user",
            created_by="jdoe (DESC)",
            configuration={"pipeline": "nightly"},
            software=[{"name": "smp-core", "version": "1.2.3"}],
            input_data={"images": ["s3://bucket/exposure.fits"]},
            targets=[{"object_id": "SN2026abc", "target_class": "SN Ia", "redshift": 0.12}],
            auxiliary={"campaign": "reprocessing"},
            notes=["initial import"],
            environment={"container": "ghcr.io/desc/smp:latest"},
            adapter={"name": "do-smp-generic", "version": "0.1.0"},
            engine={"name": "smp-core", "version": "1.2.3"},
            code_reference={"repository": "git@github.com:desc/smp-core.git", "commit": "abc123"},
            data_reference={"butler_collections": ["LSSTCam/runs/DP0.2"]},
            target_summary={"count": 1, "classes": ["SN Ia"]},
            provenance={"reproducible": True},
            archival={"registry_uri": "s3://registry/smp"},
        )

        self.assertEqual(stub.user_id, "desc-user")
        self.assertEqual(stub.created_by, "jdoe (DESC)")
        self.assertEqual(stub.pipeline_type, "Scene Modeling Photometry (SMP)")
        self.assertEqual(stub.status, "draft")
        self.assertTrue(stub.run_id)
        self.assertEqual(len(stub.run_id), 64)
        self.assertEqual(sorted(stub.outputs), sorted(DEFAULT_OUTPUT_CATEGORIES))

    def test_yaml_contains_reproducibility_sections(self) -> None:
        request = SMPRunRequest(
            user_id="desc-user",
            created_by="jdoe (DESC)",
            configuration={"config_uri": "configs/run.yaml"},
            input_bundle=RubinInputBundle(
                butler_collections=["LSSTCam/runs/DP0.2"],
                templates=["templates/ref.fits"],
                manifest_uri="manifests/inputs.json",
            ),
            targets=[SMPTarget(object_id="SN2026abc", redshift=0.11, target_class="SN Ia")],
            auxiliary={"ticket": "DESC-42"},
            notes=["review pending"],
            environment={"python": "3.12"},
            code_reference={"repository": "git@github.com:desc/smp-core.git", "tag": "v2.1.0"},
            provenance={"immutable": True, "rerun_capability": "one-command"},
            archival=ArtifactRegistry(registry_uri="s3://registry/smp", archive_uri="s3://archive/smp"),
        )
        adapter = StarredAdapter(version="0.4.0")
        stub = adapter.build_run_stub_from_request(request)
        stub.add_output(
            "light_curves",
            path="outputs/lightcurve.parquet",
            format="parquet",
            provenance={"engine": "STARRED"},
        )

        yaml_output = stub.to_yaml()

        for section in (
            "run_id:",
            "created_by:",
            "pipeline_type:",
            "configuration:",
            "software:",
            "input_data:",
            "targets:",
            "auxiliary:",
            "environment:",
            "adapter:",
            "engine:",
            "code_reference:",
            "data_reference:",
            "target_summary:",
            "provenance:",
            "archival:",
            "outputs:",
            "light_curves:",
        ):
            self.assertIn(section, yaml_output)

    def test_identical_stable_inputs_keep_same_run_id(self) -> None:
        kwargs = {
            "user_id": "desc-user",
            "created_by": "jdoe (DESC)",
            "configuration": {"config_uri": "configs/run.yaml"},
            "software": [
                {"name": "adapter-b", "version": "2.0.0"},
                {"name": "adapter-a", "version": "1.0.0"},
            ],
            "input_data": {"dataset": "DR1"},
            "targets": [
                {"object_id": "SN2026xyz", "redshift": 0.2},
                {"object_id": "SN2026abc", "redshift": 0.1},
            ],
            "auxiliary": {"ticket": "DESC-42"},
            "notes": ["review pending", "draft"],
            "environment": {"python": "3.12"},
            "adapter": {"name": "do-smp-generic", "version": "0.1.0"},
            "engine": {"name": "smp-core", "version": "1.2.3"},
            "code_reference": {"repository": "git@github.com:desc/smp-core.git", "commit": "abc123"},
            "data_reference": {"butler_collections": ["LSSTCam/runs/DP0.2"]},
            "target_summary": {"count": 2, "redshift_range": {"min": 0.1, "max": 0.2}},
            "provenance": {"immutable": True},
            "archival": {"registry_uri": "s3://registry/smp"},
        }
        reordered_kwargs = {
            **kwargs,
            "software": list(reversed(kwargs["software"])),
            "targets": list(reversed(kwargs["targets"])),
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
            configuration={
                "config:uri": "configs/run:1.yaml",
                " key ": " value ",
                "bool_string": "true",
                "null_string": "null",
            },
            input_data={"inputs": [{"uri": "s3://bucket/file.fits", "tag": "raw:data"}]},
        )

        yaml_output = stub.to_yaml()

        self.assertIn('"config:uri": "configs/run:1.yaml"', yaml_output)
        self.assertIn('" key ": " value "', yaml_output)
        self.assertIn('bool_string: "true"', yaml_output)
        self.assertIn('null_string: "null"', yaml_output)
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
        self.assertTrue(stub.run_id)

    def test_yaml_keeps_finite_floats_numeric(self) -> None:
        stub = SMPRunStub.create(
            user_id="desc-user",
            auxiliary={"seeing": 1.5},
        )

        yaml_output = stub.to_yaml()

        self.assertIn("seeing: 1.5", yaml_output)

    def test_set_status_rejects_unknown_value(self) -> None:
        stub = SMPRunStub.create(user_id="desc-user")

        with self.assertRaises(ValueError):
            stub.set_status("unknown-status")

    def test_create_stub_can_limit_requested_output_categories(self) -> None:
        stub = SMPRunStub.create(
            user_id="desc-user",
            requested_outputs=["light_curves", "diagnostics"],
        )

        self.assertEqual(sorted(stub.outputs), ["diagnostics", "light_curves"])

    def test_create_stub_rejects_unknown_requested_output_categories(self) -> None:
        with self.assertRaises(ValueError):
            SMPRunStub.create(
                user_id="desc-user",
                requested_outputs=["light_curves", "bad-output"],
            )

    def test_adapter_registry_returns_registered_adapter(self) -> None:
        registry = AdapterRegistry.with_builtin_adapters()

        self.assertEqual(
            registry.names(),
            [
                "astrophot",
                "generic-smp",
                "scarlet2",
                "scene-modeling-photometry",
                "starred",
            ],
        )
        self.assertIsInstance(registry.get("astrophot"), AstroPhotAdapter)
        self.assertIn("supported_backends", registry.capabilities()["starred"])

    def test_adapter_registry_create_preserves_generic_adapter_name(self) -> None:
        registry = AdapterRegistry()
        registry.register(GenericSMPAdapter(name="adapter-a", version="1.0.0"))

        adapter = registry.create("adapter-a", version="9.9.9")

        self.assertEqual(adapter.name, "adapter-a")
        self.assertEqual(adapter.version, "9.9.9")

    def test_builtin_adapters_emit_engine_specific_metadata(self) -> None:
        adapters = [
            StarredAdapter(version="1.0.0"),
            AstroPhotAdapter(version="2.0.0"),
            Scarlet2Adapter(version="3.0.0"),
            SceneModelingPhotometryAdapter(version="4.0.0"),
        ]
        request = SMPRunRequest(
            user_id="desc-user",
            input_bundle=RubinInputBundle(
                butler_collections=["LSSTCam/runs/DP0.2"],
                data_ids=[RubinDataCoordinate(visit=101, detector=42, band="i")],
            ),
            targets=[SMPTarget(object_id="SN2026abc", target_class="SN Ia", redshift=0.15)],
            extensions={"do_smp": {"ticket": "DESC-42"}},
        )

        for adapter in adapters:
            with self.subTest(adapter=adapter.name):
                stub = adapter.build_run_stub_from_request(request)
                self.assertEqual(stub.engine["version"], adapter.version)
                self.assertEqual(stub.adapter["name"], adapter.name)
                self.assertEqual(stub.target_summary["count"], 1)
                self.assertEqual(stub.data_reference["butler_collections"], ["LSSTCam/runs/DP0.2"])

    def test_adapter_deduplicates_built_in_software_entries(self) -> None:
        adapter = StarredAdapter(version="2.1.0")
        request = SMPRunRequest(
            user_id="desc-user",
            software=[
                {"name": "starred", "version": "2.1.0", "role": "adapter"},
                {"name": "STARRED", "version": "2.1.0", "role": "smp-engine"},
            ],
        )

        stub = adapter.build_run_stub_from_request(request)

        self.assertEqual(
            stub.software,
            [
                {"name": "starred", "version": "2.1.0", "role": "adapter"},
                {"name": "STARRED", "version": "2.1.0", "role": "smp-engine"},
            ],
        )

    def test_adapter_rejects_unknown_extension_namespace(self) -> None:
        adapter = GenericSMPAdapter()
        request = SMPRunRequest(
            user_id="desc-user",
            extensions={"unexpected.namespace": {"value": 1}},
        )

        with self.assertRaises(ValueError):
            adapter.build_run_stub_from_request(request)

    def test_to_dict_returns_deep_copy(self) -> None:
        stub = SMPRunStub.create(
            user_id="desc-user",
            configuration={"nested": {"bands": ["g", "r"]}},
            provenance={"archive": {"immutable": True}},
        )
        exported = stub.to_dict()
        exported["configuration"]["nested"]["bands"].append("i")
        exported["provenance"]["archive"]["immutable"] = False

        self.assertEqual(stub.configuration["nested"]["bands"], ["g", "r"])
        self.assertTrue(stub.provenance["archive"]["immutable"])

    def test_add_output_rejects_unknown_category(self) -> None:
        stub = SMPRunStub.create(user_id="desc-user")
        before = stub.to_dict()["outputs"]

        with self.assertRaises(ValueError):
            stub.add_output("unknown_category", path="outputs/file.txt")

        self.assertEqual(stub.to_dict()["outputs"], before)

    def test_cli_main_emits_registry_selected_engine_and_metadata(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            exit_code = cli.main(
                [
                    "--user-id",
                    "desc-user",
                    "--created-by",
                    "jdoe (DESC)",
                    "--engine",
                    "starred",
                    "--engine-version",
                    "2.1.0",
                    "--status",
                    "queued",
                    "--config-uri",
                    "configs/run.yaml",
                    "--collection",
                    "LSSTCam/runs/DP0.2",
                    "--target",
                    "SN2026abc",
                    "--note",
                    "first",
                    "--note",
                    "second",
                    "--registry-uri",
                    "s3://registry/smp",
                ]
            )

        output = stdout.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("status: queued", output)
        self.assertIn("created_by: jdoe (DESC)", output)
        self.assertIn("name: STARRED", output)
        self.assertIn('version: "2.1.0"', output)
        self.assertIn("- first", output)
        self.assertIn("- second", output)
        self.assertIn("registry_uri: \"s3://registry/smp\"", output)

    def test_cli_lists_builtin_engines(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            exit_code = cli.main(["--list-engines"])

        self.assertEqual(exit_code, 0)
        self.assertIn("starred", stdout.getvalue())
        self.assertIn("scene-modeling-photometry", stdout.getvalue())

    def test_cli_rejects_unknown_status(self) -> None:
        with self.assertRaises(SystemExit):
            cli.main(["--user-id", "desc-user", "--status", "unknown-status"])

    def test_cli_rejects_unknown_engine(self) -> None:
        with self.assertRaises(SystemExit):
            cli.main(["--user-id", "desc-user", "--engine", "missing-engine"])

    def test_cli_run_subcommand_requires_existing_stub(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            stub_path = Path(tmp_dir) / "run.yaml"
            stub_path.write_text("schema_version: 0.1.0\n", encoding="utf-8")
            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                exit_code = cli.main(["run", "--run-stub", str(stub_path)])

        self.assertEqual(exit_code, 0)
        self.assertIn(str(stub_path), stdout.getvalue())

    def test_local_runner_prepares_command(self) -> None:
        stub = SMPRunStub.create(
            user_id="desc-user",
            engine={"name": "STARRED", "version": "2.1.0"},
        )

        launch = LocalRunner().prepare_launch(stub, run_stub_path="/abs/run.yaml")

        self.assertEqual(launch.backend, "local")
        self.assertEqual(launch.command, ["python", "-m", "do_smp", "run", "--run-stub", "/abs/run.yaml"])
        self.assertEqual(launch.metadata["engine"], "STARRED")

    def test_slurm_runner_renders_perlmutter_job_script(self) -> None:
        stub = SMPRunStub.create(
            user_id="desc-user",
            engine={"name": "Scarlet2", "version": "3.0.0"},
        )

        runner = SlurmRunner(account="desc", qos="debug", partition="cpu")
        launch = runner.prepare_launch(stub, run_stub_path="/abs/run stub.yaml")
        script = launch.metadata["job_script"]

        self.assertEqual(launch.backend, "slurm-perlmutter")
        self.assertEqual(launch.command, ["sbatch"])
        self.assertIn("#SBATCH --account=desc", script)
        self.assertIn("#SBATCH --qos=debug", script)
        self.assertIn("#SBATCH --constraint=cpu", script)
        self.assertIn("NERSC Perlmutter", launch.metadata["site"])
        self.assertIn("srun python -m do_smp run --run-stub '/abs/run stub.yaml'", script)


if __name__ == "__main__":
    unittest.main()
