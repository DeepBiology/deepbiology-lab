import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

from deepbiology import DeepBiologyClient


class ClientDownloadTests(unittest.TestCase):
    def test_download_job_result_uses_cli_default_layout(self):
        client = DeepBiologyClient(api_key="test-key", base_url="https://example.test")
        normalized = {
            "jobId": "job-1",
            "status": "completed",
            "result": {"fields": {"summary": "done"}},
        }

        with tempfile.TemporaryDirectory() as temporary_directory, patch.object(
            client, "wait_for_job"
        ) as wait_for_job, patch.object(
            client, "get_job_result", return_value=normalized
        ):
            downloaded = client.download_job_result(
                "job-1", output_directory=temporary_directory
            )

            expected_run_directory = pathlib.Path(temporary_directory) / "run_job-1"
            expected_result_file = expected_run_directory / "result_job-1.json"
            self.assertEqual(downloaded["runDirectory"], str(expected_run_directory))
            self.assertEqual(downloaded["resultFile"], str(expected_result_file))
            self.assertIsNone(downloaded["imageFile"])
            self.assertTrue(expected_result_file.is_file())
            self.assertEqual(
                json.loads(expected_result_file.read_text(encoding="utf-8"))["jobId"],
                "job-1",
            )
            wait_for_job.assert_called_once_with(
                "job-1", poll_seconds=5, timeout_seconds=1800
            )

    def test_download_job_result_places_image_beside_json_by_default(self):
        client = DeepBiologyClient(api_key="test-key", base_url="https://example.test")
        normalized = {"jobId": "job-2", "status": "completed", "result": {}}

        with tempfile.TemporaryDirectory() as temporary_directory, patch.object(
            client, "wait_for_job"
        ), patch.object(client, "get_job_result", return_value=normalized), patch.object(
            client, "download_result_image", side_effect=lambda _job_id, path: path
        ) as download_image:
            downloaded = client.download_job_result(
                "job-2",
                output_directory=temporary_directory,
                download_image=True,
            )

        expected_image = pathlib.Path(temporary_directory) / "run_job-2" / "result_job-2.png"
        self.assertEqual(downloaded["imageFile"], str(expected_image))
        download_image.assert_called_once_with("job-2", str(expected_image))


if __name__ == "__main__":
    unittest.main()
