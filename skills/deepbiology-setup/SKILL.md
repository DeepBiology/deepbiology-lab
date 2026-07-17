---
name: deepbiology-setup
description: Install and configure the DeepBiology SDK, CLI, and local MCP server. Use when DeepBiology tools are unavailable, the MCP executable is missing, authentication fails, or the user asks to configure a Codex, Gemini, or AGY integration.
---

# Set up DeepBiology

Install the package:

```bash
pip install git+https://github.com/DeepBiology/deepbiology-lab.git
```

For CLI and Codex use, store the key with:

```bash
deepbiology-lab config --api-key dbio_your_api_key
```

Gemini extension installation collects `DEEPBIOLOGY_API_KEY` as a sensitive setting. AGY can read the exported environment variable or the shared CLI configuration. Never print, commit, or echo the full key.

Verify installation with `deepbiology-lab --help`, `command -v deepbiology-lab-mcp`, and confirmation that the `list_models` MCP tool is available.
