import asyncio
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from deepbiology_lab import mcp_server


class McpExecutorLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancelled_waiter_does_not_report_late_worker_exception(self):
        executor = ThreadPoolExecutor(max_workers=1)
        worker_started = threading.Event()
        release_worker = threading.Event()
        loop_errors = []
        loop = asyncio.get_running_loop()
        previous_handler = loop.get_exception_handler()
        loop.set_exception_handler(lambda _loop, context: loop_errors.append(context))

        def fail_after_release():
            worker_started.set()
            release_worker.wait(timeout=2)
            raise RuntimeError("late worker sentinel")

        adapted = mcp_server._http_tool_adapter(fail_after_release, executor)
        task = asyncio.create_task(adapted())
        try:
            for _ in range(200):
                if worker_started.is_set():
                    break
                await asyncio.sleep(0.01)
            self.assertTrue(worker_started.is_set())

            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

            release_worker.set()
            executor.shutdown(wait=True)
            await asyncio.sleep(0)
            self.assertEqual(loop_errors, [])
        finally:
            release_worker.set()
            executor.shutdown(wait=True)
            loop.set_exception_handler(previous_handler)

    async def test_executor_shutdown_waits_for_running_work_then_completes(self):
        executor = ThreadPoolExecutor(max_workers=1)
        worker_started = threading.Event()
        release_worker = threading.Event()
        shutdown_finished = threading.Event()

        def blocked_work():
            worker_started.set()
            release_worker.wait(timeout=2)
            return "completed"

        adapted = mcp_server._http_tool_adapter(blocked_work, executor)
        task = asyncio.create_task(adapted())
        for _ in range(200):
            if worker_started.is_set():
                break
            await asyncio.sleep(0.01)
        self.assertTrue(worker_started.is_set())

        def shut_down_executor():
            executor.shutdown(wait=True)
            shutdown_finished.set()

        shutdown_thread = threading.Thread(target=shut_down_executor)
        shutdown_thread.start()
        time.sleep(0.05)
        self.assertFalse(shutdown_finished.is_set())

        release_worker.set()
        self.assertEqual(await asyncio.wait_for(task, timeout=1), "completed")
        shutdown_thread.join(timeout=1)
        self.assertFalse(shutdown_thread.is_alive())
        self.assertTrue(shutdown_finished.is_set())

    async def test_production_asgi_shutdown_closes_executor_after_abandoned_work(self):
        server = mcp_server._create_server("streamable-http")
        app = server.streamable_http_app()
        incoming = asyncio.Queue()
        outgoing = asyncio.Queue()

        async def receive():
            return await incoming.get()

        async def send(message):
            await outgoing.put(message)

        scope = {
            "type": "lifespan",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "state": {},
        }
        app_task = asyncio.create_task(app(scope, receive, send))
        await incoming.put({"type": "lifespan.startup"})
        self.assertEqual(
            (await asyncio.wait_for(outgoing.get(), timeout=1))["type"],
            "lifespan.startup.complete",
        )

        worker_started = threading.Event()
        release_worker = threading.Event()

        def abandoned_work():
            worker_started.set()
            release_worker.wait(timeout=2)

        adapted = mcp_server._http_tool_adapter(
            abandoned_work,
            server.tool_executor,
        )
        request_task = asyncio.create_task(adapted())
        for _ in range(200):
            if worker_started.is_set():
                break
            await asyncio.sleep(0.01)
        self.assertTrue(worker_started.is_set())
        request_task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await request_task

        release_timer = threading.Timer(0.1, release_worker.set)
        release_timer.start()
        started_shutdown = time.monotonic()
        await incoming.put({"type": "lifespan.shutdown"})
        self.assertEqual(
            (await asyncio.wait_for(outgoing.get(), timeout=1))["type"],
            "lifespan.shutdown.complete",
        )
        await asyncio.wait_for(app_task, timeout=1)
        elapsed = time.monotonic() - started_shutdown
        release_timer.join(timeout=1)

        self.assertGreaterEqual(elapsed, 0.08)
        self.assertLess(elapsed, 1)


if __name__ == "__main__":
    unittest.main()
