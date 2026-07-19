#!/usr/bin/env python3
"""Validate cross-client manifests and canonical skill packaging."""

from __future__ import annotations

import json
import re
from pathlib import Path

from sync_plugin_skills import ROOT, is_synchronized


SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SKILL_NAME = re.compile(r"^[a-z0-9-]{1,64}$")
MCP_URL_REFERENCE = "${DEEPBIOLOGY_MCP_URL}"
AUTHORIZATION_REFERENCE = "Bearer ${DEEPBIOLOGY_API_KEY}"


def _json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError("{} has invalid YAML frontmatter".format(path))
    values = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def main() -> int:
    gemini = _json(ROOT / "gemini-extension.json")
    qwen = _json(ROOT / "qwen-extension.json")
    agy = _json(ROOT / "plugin.json")
    agy_mcp = _json(ROOT / "mcp_config.json")
    codex = _json(ROOT / "codex-plugin-python" / ".codex-plugin" / "plugin.json")
    codex_mcp = _json(ROOT / "codex-plugin-python" / ".mcp.json")
    marketplace = _json(ROOT / ".claude-plugin" / "marketplace.json")

    versions = {
        gemini["version"],
        qwen["version"],
        codex["version"],
        marketplace["metadata"]["version"],
    }
    assert len(versions) == 1 and SEMVER.fullmatch(next(iter(versions))), versions
    assert gemini["name"] == qwen["name"] == agy["name"] == "deepbiology-lab"
    gemini_server = gemini["mcpServers"]["deepbiology-lab"]
    qwen_server = qwen["mcpServers"]["deepbiology-lab"]
    agy_server = agy_mcp["mcpServers"]["deepbiology-lab"]
    assert gemini_server == {
        "httpUrl": MCP_URL_REFERENCE,
        "headers": {"Authorization": AUTHORIZATION_REFERENCE},
        "timeout": 1800000,
    }, gemini_server
    assert qwen_server == gemini_server, qwen_server
    assert agy_server == {
        "serverUrl": MCP_URL_REFERENCE,
        "headers": {"Authorization": AUTHORIZATION_REFERENCE},
    }, agy_server
    gemini_settings = {setting["envVar"]: setting for setting in gemini["settings"]}
    assert set(gemini_settings) == {"DEEPBIOLOGY_MCP_URL", "DEEPBIOLOGY_API_KEY"}
    assert gemini_settings["DEEPBIOLOGY_MCP_URL"]["sensitive"] is False
    assert gemini_settings["DEEPBIOLOGY_API_KEY"]["sensitive"] is True
    assert qwen["settings"] == gemini["settings"]
    assert codex["mcpServers"] == "./.mcp.json"
    assert codex_mcp["mcpServers"]["deepbiology-lab"] == {
        "type": "http",
        "url": "${DEEPBIOLOGY_MCP_URL}",
        "bearer_token_env_var": "DEEPBIOLOGY_API_KEY",
    }

    skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
    assert len(skill_files) == 13, "expected 13 canonical skills"
    for skill_file in skill_files:
        metadata = _frontmatter(skill_file)
        directory_name = skill_file.parent.name
        assert metadata.get("name") == directory_name, skill_file
        assert SKILL_NAME.fullmatch(directory_name), directory_name
        assert metadata.get("description"), skill_file

    assert is_synchronized(), "Codex skills differ from canonical skills"
    print("Validated Gemini, Qwen, AGY, Codex, marketplace, and 13 shared skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
