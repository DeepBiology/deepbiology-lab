---
name: deepbiology-setup
description: Configure the DeepBiology SDK, CLI, remote MCP service, or optional local MCP server. Use when DeepBiology tools are unavailable, an MCP endpoint is missing, authentication fails, or the user asks to configure a Qwen, Gemini, AGY, or Codex integration.
---

# Set up DeepBiology

Install the package for CLI, SDK, or local stdio use:

```bash
pip install git+https://github.com/DeepBiology/deepbiology-lab.git
```

For local CLI and stdio use, store the key with:

```bash
deepbiology-lab config --api-key dbio_your_api_key
```

The published Qwen, Gemini, and AGY manifests use `DEEPBIOLOGY_MCP_URL` as the complete Streamable HTTP endpoint and send `DEEPBIOLOGY_API_KEY` as a Bearer credential. Qwen and Gemini expose extension settings, and AGY reads the exported variables. Use `http://localhost:8000/mcp` for local HTTP development or the deployment's `https://<hostname>/mcp` endpoint in production. Never print, commit, or echo the full key.

Codex does not expand `DEEPBIOLOGY_MCP_URL` inside a plugin MCP manifest, so its plugin ships the shared skills and users register the remote MCP server separately after exporting both variables:

```bash
export DEEPBIOLOGY_MCP_URL=https://your-mcp-host.example/mcp
export DEEPBIOLOGY_API_KEY=dbio_your_api_key
codex plugin marketplace add DeepBiology/deepbiology-lab
codex plugin add deepbiology@deepbiology-marketplace
codex mcp add deepbiology-lab \
  --url "$DEEPBIOLOGY_MCP_URL" \
  --bearer-token-env-var DEEPBIOLOGY_API_KEY
```

Verify remote configuration by starting a new agent thread and confirming that the `list_models` MCP tool is available. For optional local stdio use, also verify `deepbiology-lab --help` and `command -v deepbiology-lab-mcp`.
