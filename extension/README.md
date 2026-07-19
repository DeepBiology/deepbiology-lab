# DeepBiology agent extensions

The repository root is a Gemini CLI extension, Qwen CLI extension, and native
Antigravity (AGY) plugin. These clients load the canonical `skills/` tree and
connect to a remote Streamable HTTP MCP server.

## Configuration

The manifests use two environment variables and do not contain a hostname or
credential:

```bash
export DEEPBIOLOGY_MCP_URL=https://mcp.example.com/mcp
export DEEPBIOLOGY_API_KEY=dbio_your_api_key
```

`DEEPBIOLOGY_MCP_URL` is the complete endpoint, including `/mcp`. It may be
`http://localhost:8000/mcp` during local HTTP development; production should
use HTTPS. Each client sends the API key as an `Authorization: Bearer` header
on every request.

## Gemini CLI

```bash
gemini extensions install https://github.com/DeepBiology/deepbiology-lab --auto-update
```

Gemini prompts for both `DEEPBIOLOGY_MCP_URL` and `DEEPBIOLOGY_API_KEY` during
installation and stores the API key as a sensitive setting. Configure either
value later with `gemini extensions config deepbiology-lab`.

## Antigravity CLI

```bash
export DEEPBIOLOGY_API_KEY=dbio_your_api_key
export DEEPBIOLOGY_MCP_URL=https://mcp.example.com/mcp
agy plugin install https://github.com/DeepBiology/deepbiology-lab
```

AGY can also import an existing Gemini installation with
`agy plugin import gemini`.

## Qwen CLI

```bash
qwen extensions install https://github.com/DeepBiology/deepbiology-lab
```

Qwen loads `qwen-extension.json`. Configure `DEEPBIOLOGY_MCP_URL` and
`DEEPBIOLOGY_API_KEY` through the extension settings or export them before
starting Qwen.

Remote calls to `download_job_result` return completed JSON and a signed image
URL inline; they never write to the remote server's filesystem. Installing the
Python package and launching `deepbiology-lab-mcp` remains supported for local
stdio development, but is not required by the published remote configurations.

## Development

Run `python scripts/sync_plugin_skills.py` after changing the canonical root
skills. Use `--check` in CI to verify the generated Codex bundle is current.
