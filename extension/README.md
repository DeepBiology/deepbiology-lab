# DeepBiology agent extensions

The repository root is both a Gemini CLI extension and a native Antigravity
(AGY) plugin. Both clients load the canonical `skills/` tree and start the
`deepbiology-lab-mcp` executable supplied by the Python package.

## Prerequisite

Install the local SDK, CLI, and MCP executable:

```bash
pip install git+https://github.com/DeepBiology/deepbiology-lab.git
```

## Gemini CLI

```bash
gemini extensions install https://github.com/DeepBiology/deepbiology-lab --auto-update
```

Gemini prompts for `DEEPBIOLOGY_API_KEY` during installation. Configure it
later with `gemini extensions config deepbiology-lab`.

## Antigravity CLI

```bash
export DEEPBIOLOGY_API_KEY=dbio_your_api_key
agy plugin install https://github.com/DeepBiology/deepbiology-lab
```

AGY can also import an existing Gemini installation with
`agy plugin import gemini`.

Both clients can save a completed job's JSON result and optional image through
the `deepbiology-download-result` skill. Unless the user requests another
location, artifacts are written under
`deepbiology-experiments/run_<jobId>/` on the machine running the MCP server.

## Development

Run `python scripts/sync_plugin_skills.py` after changing the canonical root
skills. Use `--check` in CI to verify the generated Codex bundle is current.
