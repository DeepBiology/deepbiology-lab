import json
import logging
import os
import unittest
from unittest.mock import Mock, patch

from deepbiology import DeepBiologyClient
from deepbiology_lab import mcp_server


class McpServerTests(unittest.TestCase):
    def test_default_transport_remains_stdio(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(mcp_server.server, "run") as run:
            mcp_server.main()

        run.assert_called_once_with(transport="stdio")

    def test_port_precedence(self):
        with patch.dict(os.environ, {"PORT": "9100", "MCP_PORT": "9200"}, clear=True):
            self.assertEqual(mcp_server._http_port(), 9100)
        with patch.dict(os.environ, {"MCP_PORT": "9200"}, clear=True):
            self.assertEqual(mcp_server._http_port(), 9200)
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(mcp_server._http_port(), 8000)

    def test_http_server_uses_required_streamable_settings(self):
        http_server = mcp_server._create_server(
            "streamable-http", host="192.0.2.10", port=9100
        )

        self.assertEqual(http_server.settings.host, "192.0.2.10")
        self.assertEqual(http_server.settings.port, 9100)
        self.assertEqual(http_server.settings.streamable_http_path, "/mcp")
        self.assertTrue(http_server.settings.stateless_http)
        self.assertTrue(http_server.settings.json_response)

    def test_tool_schemas_preserve_public_parameters(self):
        tools = mcp_server.server._tool_manager.list_tools()
        self.assertEqual(len(tools), 15)
        for tool in tools:
            parameters = tool.parameters.get("properties", {})
            self.assertNotIn("api_key", parameters)
            self.assertNotIn("authorization", parameters)
            self.assertNotIn("ctx", parameters)
            self.assertIsNone(tool.context_kwarg)

    def test_http_adapters_preserve_complete_tool_schemas(self):
        http_server = mcp_server._create_server("streamable-http")
        stdio_tools = {
            tool.name: tool for tool in mcp_server.server._tool_manager.list_tools()
        }
        http_tools = {
            tool.name: tool for tool in http_server._tool_manager.list_tools()
        }

        self.assertEqual(set(http_tools), set(stdio_tools))
        for name, stdio_tool in stdio_tools.items():
            http_tool = http_tools[name]
            self.assertEqual(http_tool.title, stdio_tool.title)
            self.assertEqual(http_tool.description, stdio_tool.description)
            self.assertEqual(http_tool.parameters, stdio_tool.parameters)
            self.assertEqual(
                http_tool.fn_metadata.output_schema,
                stdio_tool.fn_metadata.output_schema,
            )
            self.assertEqual(http_tool.context_kwarg, stdio_tool.context_kwarg)
            self.assertEqual(http_tool.annotations, stdio_tool.annotations)
            self.assertEqual(http_tool.icons, stdio_tool.icons)
            self.assertEqual(http_tool.meta, stdio_tool.meta)
            self.assertFalse(stdio_tool.is_async)
            self.assertTrue(http_tool.is_async)

    def test_stdio_client_still_uses_local_config(self):
        config = mcp_server._Config(api_key="local-key", base_url="https://example.test")
        with patch.object(mcp_server, "get_access_token", return_value=None), patch.object(
            mcp_server, "_load_config", return_value=config
        ), patch.object(mcp_server, "DeepBiologyClient", wraps=DeepBiologyClient) as client_type:
            client = mcp_server._get_client()

        client_type.assert_called_once_with(api_key="local-key", base_url="https://example.test")
        self.assertEqual(client.api_key, "local-key")

    def test_stdio_config_file_fallback_remains_unchanged(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            mcp_server, "get_access_token", return_value=None
        ), patch.object(
            mcp_server,
            "load_config",
            return_value={"api_key": "file-key", "base_url": "https://file.example.test"},
        ):
            client = mcp_server._get_client()

        self.assertEqual(client.api_key, "file-key")
        self.assertEqual(client.base_url, "https://file.example.test")
        self.assertTrue(
            all(not tool.is_async for tool in mcp_server.server._tool_manager.list_tools())
        )

    def test_secret_bearing_objects_have_redacted_representations(self):
        token = mcp_server._RedactedAccessToken(token="sentinel-secret", client_id="fingerprint", scopes=[])
        client = DeepBiologyClient(api_key="sentinel-secret", base_url="https://example.test")

        self.assertNotIn("sentinel-secret", repr(token))
        self.assertNotIn("sentinel-secret", str(token))
        self.assertNotIn("sentinel-secret", repr(client))

        record = logging.LogRecord(
            "test", logging.ERROR, __file__, 1,
            "Authorization: Bearer sentinel-secret dbio_another-secret", (), None
        )
        mcp_server._SecretRedactionFilter().filter(record)
        self.assertNotIn("sentinel-secret", record.getMessage())
        self.assertNotIn("dbio_another-secret", record.getMessage())

    def test_cell_line_resolution_delegates_to_sdk_with_model_and_assay(self):
        expected = {
            "canonicalName": "KASUMI1",
            "cellLineIndex": 195,
            "modelId": "borzoi_finetune_v1",
            "assayType": "RNASeq",
        }
        with patch.object(mcp_server, "sdk_resolve_cell_line", return_value=expected) as resolver:
            result = json.loads(mcp_server.resolve_cell_line(
                "kasumi-1", "borzoi_finetune_v1", "RNASeq"
            ))

        self.assertEqual(result, expected)
        resolver.assert_called_once_with(
            "kasumi-1",
            model_id="borzoi_finetune_v1",
            assay_type="RNASeq",
        )

    def test_variant_tools_delegate_to_sdk(self):
        with patch.object(mcp_server, "sdk_find_variants", return_value={"returned": 1}) as finder:
            region = json.loads(mcp_server.find_variants("chr1:1-10", "GRCh38", 5))
        with patch.object(mcp_server, "sdk_annotate_variant", return_value={"variantId": "rs1"}) as annotator:
            impact = json.loads(mcp_server.annotate_variant("rs1", "GRCh38"))

        self.assertEqual(region["returned"], 1)
        self.assertEqual(impact["variantId"], "rs1")
        finder.assert_called_once_with("chr1:1-10", assembly="GRCh38", limit=5)
        annotator.assert_called_once_with("rs1", assembly="GRCh38")

    def test_q1_resolves_named_cell_before_submission(self):
        resolution = {"cellLineIndex": 195, "assayType": "RNASeq"}
        with patch.object(mcp_server, "sdk_resolve_cell_line", return_value=resolution), patch.object(
            mcp_server, "_submit", return_value='{"jobId":"job-1"}'
        ) as submit:
            result = json.loads(mcp_server.submit_q1_regulation(
                "CD34", cell_name="kasumi-1", model_id="borzoi_finetune_v1"
            ))

        self.assertEqual(result["jobId"], "job-1")
        inputs = submit.call_args.args[1]
        self.assertEqual(inputs["cell_line"], "195")
        self.assertEqual(submit.call_args.args[2], resolution)

    def test_download_job_result_uses_cli_defaults(self):
        client = Mock()
        client.download_job_result.return_value = {
            "jobId": "job-1",
            "runDirectory": "deepbiology-experiments/run_job-1",
            "resultFile": "deepbiology-experiments/run_job-1/result_job-1.json",
            "imageFile": None,
            "raw": False,
            "result": {"jobId": "job-1"},
        }
        with patch.object(mcp_server, "_get_client", return_value=client):
            result = json.loads(mcp_server.download_job_result("job-1"))

        self.assertEqual(result["resultFile"], "deepbiology-experiments/run_job-1/result_job-1.json")
        self.assertNotIn("result", result)
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
