import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[1]
SYNC_PATH = ROOT / "scripts" / "sync_plugin_skills.py"
SPEC = importlib.util.spec_from_file_location("sync_plugin_skills", SYNC_PATH)
sync_plugin_skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_plugin_skills)


class ExtensionPackagingTests(unittest.TestCase):
    def test_manifests_share_version_and_use_remote_mcp(self):
        gemini = json.loads((ROOT / "gemini-extension.json").read_text())
        qwen = json.loads((ROOT / "qwen-extension.json").read_text())
        codex = json.loads((ROOT / "codex-plugin-python/.codex-plugin/plugin.json").read_text())
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        agy = json.loads((ROOT / "plugin.json").read_text())
        agy_mcp = json.loads((ROOT / "mcp_config.json").read_text())

        self.assertEqual(gemini["version"], codex["version"])
        self.assertEqual(gemini["version"], qwen["version"])
        self.assertEqual(gemini["version"], marketplace["metadata"]["version"])
        self.assertEqual(gemini["name"], qwen["name"])
        self.assertEqual(gemini["name"], agy["name"])
        gemini_server = gemini["mcpServers"]["deepbiology-lab"]
        qwen_server = qwen["mcpServers"]["deepbiology-lab"]
        agy_server = agy_mcp["mcpServers"]["deepbiology-lab"]
        self.assertEqual(gemini_server["httpUrl"], "${DEEPBIOLOGY_MCP_URL}")
        self.assertEqual(qwen_server, gemini_server)
        self.assertEqual(agy_server["serverUrl"], "${DEEPBIOLOGY_MCP_URL}")
        self.assertEqual(
            gemini_server["headers"],
            {"Authorization": "Bearer ${DEEPBIOLOGY_API_KEY}"},
        )
        self.assertEqual(gemini_server["headers"], agy_server["headers"])
        self.assertNotIn("mcpServers", codex)
        self.assertFalse((ROOT / "codex-plugin-python/.mcp.json").exists())
        readme = (ROOT / "README.md").read_text()
        self.assertIn("codex mcp add deepbiology-lab", readme)
        self.assertIn('--url "$DEEPBIOLOGY_MCP_URL"', readme)
        self.assertIn("--bearer-token-env-var DEEPBIOLOGY_API_KEY", readme)
        for server in (gemini_server, agy_server):
            self.assertNotIn("command", server)
            self.assertNotIn("args", server)
            self.assertNotIn("env", server)

        settings = {setting["envVar"]: setting for setting in gemini["settings"]}
        self.assertEqual(set(settings), {"DEEPBIOLOGY_MCP_URL", "DEEPBIOLOGY_API_KEY"})
        self.assertFalse(settings["DEEPBIOLOGY_MCP_URL"]["sensitive"])
        self.assertTrue(settings["DEEPBIOLOGY_API_KEY"]["sensitive"])
        self.assertEqual(qwen["settings"], gemini["settings"])
        self.assertIn("Qwen CLI", qwen["description"])
        self.assertNotIn("Gemini CLI", qwen["description"])

    def test_codex_skills_are_generated_from_canonical_skills(self):
        self.assertTrue(sync_plugin_skills.is_synchronized())
        self.assertEqual(len(list((ROOT / "skills").glob("*/SKILL.md"))), 13)


if __name__ == "__main__":
    unittest.main()
