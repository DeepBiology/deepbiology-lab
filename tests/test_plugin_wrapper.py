import importlib.util
import json
import pathlib
import unittest
from unittest.mock import Mock, patch


PLUGIN_QUERY = pathlib.Path(__file__).parents[1] / "codex-plugin-python" / "scripts" / "query.py"
SPEC = importlib.util.spec_from_file_location("deepbiology_plugin_query", PLUGIN_QUERY)
plugin_query = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plugin_query)


class PluginWrapperTests(unittest.TestCase):
    def test_cell_line_resolution_delegates_to_sdk(self):
        expected = {
            "canonicalName": "KASUMI1",
            "cellLineIndex": 195,
            "modelId": "borzoi_finetune_v1",
            "assayType": "RNASeq",
        }
        with patch("deepbiology.resolve_cell_line", return_value=expected) as resolver:
            result = json.loads(plugin_query._resolve_cell_line(
                "kasumi-1", "borzoi_finetune_v1", "RNASeq"
            ))

        self.assertEqual(result, expected)
        resolver.assert_called_once_with(
            "kasumi-1",
            model_id="borzoi_finetune_v1",
            assay_type="RNASeq",
        )

    def test_variant_resolution_delegates_to_sdk(self):
        with patch("deepbiology.find_variants", return_value={"returned": 1}) as finder:
            result = json.loads(plugin_query._resolve_snps("chr1:1-10", 5, "GRCh38"))

        self.assertEqual(result["returned"], 1)
        finder.assert_called_once_with("chr1:1-10", assembly="GRCh38", limit=5)

    def test_download_result_delegates_to_sdk_with_defaults(self):
        client = Mock()
        client.download_job_result.return_value = {
            "jobId": "job-1",
            "resultFile": "deepbiology-experiments/run_job-1/result_job-1.json",
        }
        with patch("deepbiology.DeepBiologyClient", return_value=client), patch.object(
            plugin_query, "_load_api_key", return_value="test-key"
        ), patch.object(plugin_query, "_load_base_url", return_value="https://example.test"):
            result = json.loads(plugin_query._download_result("job-1"))

        self.assertEqual(result["jobId"], "job-1")
        client.download_job_result.assert_called_once_with(
            "job-1",
            output_directory="deepbiology-experiments",
            run_name=None,
            raw=False,
            download_image=False,
            image_path=None,
            poll_seconds=5,
            timeout_seconds=1800,
        )


if __name__ == "__main__":
    unittest.main()
