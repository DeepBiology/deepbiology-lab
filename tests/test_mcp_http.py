import asyncio
import json
import logging
import os
import re
import threading
import unittest
from unittest.mock import Mock, patch

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.server.auth.middleware.auth_context import get_access_token

from deepbiology import DeepBiologyClient
from deepbiology_lab import mcp_server


class _FakeDeepBiologyClient:
    lock = threading.Lock()
    probes = []
    tool_calls = []
    download_calls = []
    owners = {
        "sentinel-key-a": "owner-a",
        "sentinel-key-b": "owner-b",
        "download-key": "download-owner",
    }

    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

    @classmethod
    def reset(cls):
        with cls.lock:
            cls.probes = []
            cls.tool_calls = []
            cls.download_calls = []

    def get_job(self, job_id):
        owner = self.owners[self.api_key]
        with self.lock:
            self.tool_calls.append((owner, job_id))
        return {"jobId": job_id, "status": owner}

    def wait_for_job(self, job_id, poll_seconds=5, timeout_seconds=1800):
        owner = self.owners[self.api_key]
        with self.lock:
            self.tool_calls.append((owner, "wait:" + job_id))
        return {"jobId": job_id, "status": "completed"}

    def get_job_result(self, job_id):
        owner = self.owners[self.api_key]
        return {
            "jobId": job_id,
            "status": "completed",
            "result": {
                "fields": {"owner": owner},
                "tables": [],
                "image": {"storageSignedUrl": "https://example.test/result.png"},
            },
        }

    format_clean_result = staticmethod(DeepBiologyClient.format_clean_result)

    def download_job_result(self, *args, **kwargs):
        with self.lock:
            self.download_calls.append((args, kwargs))
        raise AssertionError("HTTP mode must not write result files")


async def _fake_validation_request(api_key, base_url, probe_job_id):
    del base_url
    with _FakeDeepBiologyClient.lock:
        _FakeDeepBiologyClient.probes.append((api_key, probe_job_id))
    return "valid" if api_key in _FakeDeepBiologyClient.owners else "invalid"


class McpHttpTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        _FakeDeepBiologyClient.reset()

    @staticmethod
    def _create_app():
        server = mcp_server._create_server("streamable-http")
        return server.streamable_http_app()

    @staticmethod
    async def _call_tool(app, api_key, name, arguments):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
            headers={"Authorization": "Bearer " + api_key},
        ) as http_client:
            async with streamable_http_client(
                "http://testserver/mcp",
                http_client=http_client,
                terminate_on_close=False,
            ) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    return await session.call_tool(name, arguments)

    @staticmethod
    async def _initialize_request(app, authorization=None):
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if authorization is not None:
            headers["Authorization"] = authorization
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        }
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post("/mcp", headers=headers, json=payload)

    async def test_http_authentication_failures_are_sanitized(self):
        with patch.object(mcp_server, "DeepBiologyClient", _FakeDeepBiologyClient), patch.object(
            mcp_server, "_request_api_key_validation", new=_fake_validation_request
        ):
            app = self._create_app()
            async with app.router.lifespan_context(app):
                missing = await self._initialize_request(app)
                wrong_scheme = await self._initialize_request(app, "Basic abc")
                empty = await self._initialize_request(app, "Bearer ")
                with self.assertLogs(level=logging.INFO) as captured:
                    invalid = await self._initialize_request(app, "Bearer invalid-sentinel-key")

        for response in (missing, wrong_scheme, empty, invalid):
            self.assertEqual(response.status_code, 401)
            self.assertIn("Authentication required", response.text)
        self.assertNotIn("invalid-sentinel-key", invalid.text)
        self.assertNotIn("invalid-sentinel-key", "\n".join(captured.output))

    async def test_authentication_backend_unavailable_returns_sanitized_503(self):
        probes = []

        async def unavailable(api_key, base_url, probe_job_id):
            probes.append((api_key, base_url, probe_job_id))
            return "unavailable"

        with patch.object(
            mcp_server, "_request_api_key_validation", new=unavailable
        ), patch.object(
            mcp_server, "_load_base_url", return_value="https://private-backend.example/sentinel"
        ):
            app = self._create_app()
            middleware_names = [middleware.cls.__name__ for middleware in app.user_middleware]
            self.assertEqual(middleware_names[0], "_HttpBoundaryMiddleware")
            self.assertIn("AuthenticationMiddleware", middleware_names[1:])

            async with app.router.lifespan_context(app):
                with self.assertLogs(level=logging.INFO) as captured:
                    response = await self._initialize_request(
                        app, "Bearer unavailable-sentinel-key"
                    )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["retry-after"], "30")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(
            response.json(),
            {
                "error": "authentication_service_unavailable",
                "error_description": "DeepBiology authentication service is temporarily unavailable",
            },
        )
        self.assertEqual(len(probes), 1)
        probe_id = probes[0][2]
        sensitive_values = (
            "unavailable-sentinel-key",
            "https://private-backend.example/sentinel",
            probe_id,
        )
        response_text = response.text
        log_output = "\n".join(captured.output)
        for sensitive_value in sensitive_values:
            self.assertNotIn(sensitive_value, response_text)
            self.assertNotIn(sensitive_value, log_output)

    async def test_backend_validation_statuses_fail_closed(self):
        class FakeAsyncClient:
            status_code = 200
            error = None

            def __init__(self, **kwargs):
                self.headers = kwargs["headers"]

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def get(self, url, params):
                if self.error:
                    raise self.error
                self.request = (url, params)
                return Mock(status_code=self.status_code)

        cases = ((401, "invalid"), (404, "valid"), (200, "valid"), (403, "unavailable"), (500, "unavailable"))
        with patch.object(mcp_server.httpx, "AsyncClient", FakeAsyncClient):
            for status_code, expected in cases:
                FakeAsyncClient.status_code = status_code
                self.assertEqual(
                    await mcp_server._request_api_key_validation(
                        "sentinel-secret", "https://api.example.test", "a" * 64
                    ),
                    expected,
                )

            FakeAsyncClient.error = httpx.ConnectError("backend unavailable")
            self.assertEqual(
                await mcp_server._request_api_key_validation(
                    "sentinel-secret", "https://api.example.test", "b" * 64
                ),
                "unavailable",
            )

    async def test_concurrent_streamable_http_requests_isolate_credentials(self):
        with patch.object(mcp_server, "DeepBiologyClient", _FakeDeepBiologyClient), patch.object(
            mcp_server, "_request_api_key_validation", new=_fake_validation_request
        ):
            app = self._create_app()
            async with app.router.lifespan_context(app):
                with self.assertLogs(level=logging.INFO) as captured:
                    result_a, result_b = await asyncio.gather(
                        self._call_tool(app, "sentinel-key-a", "get_job_status", {"job_id": "job-a"}),
                        self._call_tool(app, "sentinel-key-b", "get_job_status", {"job_id": "job-b"}),
                    )

        payload_a = json.loads(result_a.content[0].text)
        payload_b = json.loads(result_b.content[0].text)
        self.assertEqual(payload_a["status"], "owner-a")
        self.assertEqual(payload_b["status"], "owner-b")
        self.assertCountEqual(
            _FakeDeepBiologyClient.tool_calls,
            [("owner-a", "job-a"), ("owner-b", "job-b")],
        )

        probe_ids = [probe_id for _, probe_id in _FakeDeepBiologyClient.probes]
        self.assertGreaterEqual(len(probe_ids), 2)
        self.assertEqual(len(probe_ids), len(set(probe_ids)))
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", probe_id) for probe_id in probe_ids))
        self.assertGreaterEqual(
            sum(api_key == "sentinel-key-a" for api_key, _ in _FakeDeepBiologyClient.probes), 2
        )
        self.assertGreaterEqual(
            sum(api_key == "sentinel-key-b" for api_key, _ in _FakeDeepBiologyClient.probes), 2
        )

        log_output = "\n".join(captured.output)
        self.assertNotIn("sentinel-key-a", log_output)
        self.assertNotIn("sentinel-key-b", log_output)
        self.assertNotIn("sentinel-key-a", os.environ.values())
        self.assertNotIn("sentinel-key-b", os.environ.values())
        self.assertIsNone(get_access_token())

    async def test_slow_sync_tool_does_not_block_health_or_unrelated_client(self):
        slow_started = threading.Event()
        release_slow = threading.Event()
        original_get_job = _FakeDeepBiologyClient.get_job

        def blocking_get_job(client, job_id):
            if job_id == "slow-job":
                slow_started.set()
                if not release_slow.wait(timeout=10):
                    raise TimeoutError("test did not release slow tool")
            return original_get_job(client, job_id)

        with patch.object(mcp_server, "DeepBiologyClient", _FakeDeepBiologyClient), patch.object(
            mcp_server, "_request_api_key_validation", new=_fake_validation_request
        ), patch.object(_FakeDeepBiologyClient, "get_job", new=blocking_get_job):
            app = self._create_app()
            async with app.router.lifespan_context(app):
                slow_task = asyncio.create_task(
                    self._call_tool(
                        app, "sentinel-key-a", "get_job_status", {"job_id": "slow-job"}
                    )
                )
                try:
                    for _ in range(200):
                        if slow_started.is_set():
                            break
                        await asyncio.sleep(0.01)
                    self.assertTrue(slow_started.is_set())

                    transport = httpx.ASGITransport(app=app)
                    async with httpx.AsyncClient(
                        transport=transport, base_url="http://testserver"
                    ) as client:
                        health = await asyncio.wait_for(client.get("/healthz"), timeout=2)

                    fast_result = await asyncio.wait_for(
                        self._call_tool(
                            app, "sentinel-key-b", "get_job_status", {"job_id": "fast-job"}
                        ),
                        timeout=2,
                    )
                finally:
                    release_slow.set()

                slow_result = await asyncio.wait_for(slow_task, timeout=2)

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json(), {"status": "ok"})
        self.assertEqual(json.loads(fast_result.content[0].text)["status"], "owner-b")
        self.assertEqual(json.loads(slow_result.content[0].text)["status"], "owner-a")
        self.assertCountEqual(
            _FakeDeepBiologyClient.tool_calls,
            [("owner-a", "slow-job"), ("owner-b", "fast-job")],
        )
        self.assertIsNone(get_access_token())

    async def test_http_download_returns_inline_without_filesystem_paths(self):
        with patch.object(mcp_server, "DeepBiologyClient", _FakeDeepBiologyClient), patch.object(
            mcp_server, "_request_api_key_validation", new=_fake_validation_request
        ):
            app = self._create_app()
            async with app.router.lifespan_context(app):
                result = await self._call_tool(
                    app,
                    "download-key",
                    "download_job_result",
                    {"job_id": "job-download"},
                )
                rejected = await self._call_tool(
                    app,
                    "download-key",
                    "download_job_result",
                    {"job_id": "job-download", "output_directory": "/tmp/remote-selected"},
                )

        payload = json.loads(result.content[0].text)
        self.assertEqual(payload["delivery"], "inline")
        self.assertEqual(payload["result"]["fields"]["owner"], "download-owner")
        self.assertEqual(payload["imageUrl"], "https://example.test/result.png")
        self.assertFalse(result.isError)
        self.assertTrue(rejected.isError)
        self.assertIn("cannot select server filesystem paths", rejected.content[0].text)
        self.assertEqual(_FakeDeepBiologyClient.download_calls, [])


if __name__ == "__main__":
    unittest.main()
