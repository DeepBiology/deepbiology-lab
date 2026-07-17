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
    def test_manifests_share_version_and_mcp_command(self):
        gemini = json.loads((ROOT / "gemini-extension.json").read_text())
        codex = json.loads((ROOT / "codex-plugin-python/.codex-plugin/plugin.json").read_text())
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
        agy = json.loads((ROOT / "plugin.json").read_text())
        agy_mcp = json.loads((ROOT / "mcp_config.json").read_text())

        self.assertEqual(gemini["version"], codex["version"])
        self.assertEqual(gemini["version"], marketplace["metadata"]["version"])
        self.assertEqual(gemini["name"], agy["name"])
        self.assertEqual(
            gemini["mcpServers"]["deepbiology-lab"]["command"],
            agy_mcp["mcpServers"]["deepbiology-lab"]["command"],
        )

    def test_codex_skills_are_generated_from_canonical_skills(self):
        self.assertTrue(sync_plugin_skills.is_synchronized())
        self.assertEqual(len(list((ROOT / "skills").glob("*/SKILL.md"))), 13)


if __name__ == "__main__":
    unittest.main()
