---
name: deepbiology-setup
description: Configure the DeepBiology SDK, CLI, remote MCP service, or optional local MCP server. Use when DeepBiology tools are unavailable, an MCP endpoint is missing, authentication fails, or the user asks to configure a Codex, Gemini, or AGY integration.
---

# Set up DeepBiology

Install the package for CLI, SDK, or local stdio use:

```bash
pip install git+https://github.com/DeepBiology/deepbiology-lab.git
```

For CLI and Codex use, store the key with:

```bash
deepbiology-lab config --api-key dbio_your_api_key
```

The published Gemini and AGY manifests use `DEEPBIOLOGY_MCP_URL` as the complete Streamable HTTP endpoint and send `DEEPBIOLOGY_API_KEY` in an `Authorization: Bearer` header. Gemini installation collects both settings and marks the API key sensitive. For AGY, export both variables before starting the client. Use `http://localhost:8000/mcp` for local HTTP development or the deployment's `https://<hostname>/mcp` endpoint in production. Never print, commit, or echo the full key.

Verify remote configuration by confirming that the `list_models` MCP tool is available. For optional local stdio use, also verify `deepbiology-lab --help` and `command -v deepbiology-lab-mcp`.
