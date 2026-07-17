import contextlib
import io
import unittest
from unittest.mock import Mock, patch

from deepbiology_lab import cli


class CliTests(unittest.TestCase):
    def test_run_defaults_to_rnaseq_and_submits_resolved_index(self):
        args = cli.build_parser().parse_args([
            "run",
            "q1",
            "--api-key",
            "test-key",
            "--cell-name",
            "kasumi-1",
        ])
        client = Mock()
        client.submit_job.return_value = {"jobId": "job-1"}
        resolution = {
            "cellLineIndex": 195,
            "assayType": "RNASeq",
            "modelId": "borzoi_finetune_v1",
        }

        with patch.object(cli, "load_config", return_value={}), patch.object(
            cli, "resolve_cell_line", return_value=resolution
        ) as resolver, patch.object(cli, "DeepBiologyClient", return_value=client), contextlib.redirect_stdout(
            io.StringIO()
        ), contextlib.redirect_stderr(io.StringIO()):
            status = cli.cmd_run(args)

        self.assertEqual(status, 0)
        resolver.assert_called_once_with("kasumi-1", "borzoi_finetune_v1", "RNASeq")
        submitted_inputs = client.submit_job.call_args.kwargs["inputs"]
        self.assertEqual(submitted_inputs["cell_line"], "195")

    def test_resolve_parser_defaults_assay_to_rnaseq(self):
        args = cli.build_parser().parse_args(["resolve", "KASUMI1"])
        self.assertEqual(args.assay_type, "RNASeq")

    def test_snp_subcommands_parse(self):
        region = cli.build_parser().parse_args(["snps", "region", "chr1:1-10"])
        impact = cli.build_parser().parse_args(["snps", "impact", "rs1"])
        self.assertEqual(region.max_results, 50)
        self.assertEqual(impact.assembly, "GRCh38")

    def test_download_uses_shared_default_layout(self):
        args = cli.build_parser().parse_args(["download", "job-1", "--api-key", "test-key"])
        client = Mock()
        client.download_job_result.return_value = {
            "resultFile": "deepbiology-experiments/run_job-1/result_job-1.json",
            "imageFile": None,
            "result": {"jobId": "job-1"},
        }

        with patch.object(cli, "load_config", return_value={}), patch.object(
            cli, "DeepBiologyClient", return_value=client
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            status = cli.cmd_download(args)

        self.assertEqual(status, 0)
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
