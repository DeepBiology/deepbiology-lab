# deepbiology-lab

Python client, CLI, MCP server, and Codex plugin for DeepBiology Lab.

## Quick install

**One-liner:**

```bash
curl -fsSL https://raw.githubusercontent.com/DeepBiology/deepbiology-lab/main/scripts/install.sh | sh
```

**Or with pip directly:**

```bash
pip install git+https://github.com/DeepBiology/deepbiology-lab.git
```

**Local development:**

```bash
git clone https://github.com/DeepBiology/deepbiology-lab.git
cd deepbiology-lab
pip install -e .
```

## Configure your API key

```bash
deepbiology-lab config --api-key dbio_your_api_key_here
```

Optional:

```bash
deepbiology-lab config --base-url https://us-central1-deepbiology-471514.cloudfunctions.net
deepbiology-lab config --show
```

Config is stored at:

```bash
~/.config/deepbiology-lab/config.json
```

## Run workflows

### Q1

```bash
deepbiology-lab run q1 --gene-name CD34 --cell-line 195 --download-image --image-path cd34.png
```

By default the CLI prints the clean website-style JSON result. Use `--raw` to print the normalized raw API payload instead.

```bash
deepbiology-lab run q1 --gene-name CD34 --cell-line 195 --raw
```

### Q2

```bash
deepbiology-lab run q2 --gene-name CD34 --cell-line 195 --coordinate chr1:207923783-207923857
```

### Q3

```bash
deepbiology-lab run q3 --gene-name CD34 --cell-line 195 --coordinate chr1:207923783-207923857 --mutated-seq ATGGCCATGGCCATGGCCATGGCCATGGCC
```

### Q4

```bash
deepbiology-lab run q4 --gene-name CD34 --cell-line 195 --center 207923820 --flanking-size 75 --iterations 250 --download-image --image-path redesign.png
```

## Python usage

```python
from deepbiology import DeepBiologyClient

client = DeepBiologyClient(
    api_key="dbio_your_api_key_here",
    base_url="https://us-central1-deepbiology-471514.cloudfunctions.net",
)

job = client.submit_job("q1_regulation", {
    "task": "plot_transcription_gradient",
    "gene_name": "CD34",
    "cell_line": "195",
})

result = client.get_clean_result(job["jobId"])
print(result)
```

## MCP Server

The package includes an [MCP](https://modelcontextprotocol.io) (Model Context Protocol) server
that exposes DeepBiology Lab workflows as tools for LLM chatboxes — Claude Desktop,
VS Code Copilot Chat, Cursor, and any other MCP-compatible client.

### Tools

| Tool | Description |
|------|-------------|
| `resolve_gene` | Resolve a gene name/alias to canonical HGNC symbol (e.g. "cyclin D1" → `CCND1`) |
| `submit_q1_regulation` | Submit Q1 — plot transcription gradient |
| `submit_q2_enhancer_importance` | Submit Q2 — mutation importance scan |
| `submit_q3_mutation_impact` | Submit Q3 — test a specific mutated sequence |
| `submit_q4_enhancer_redesign` | Submit Q4 — AI-driven enhancer optimization |
| `get_job_status` | Check a job's current processing status |
| `get_job_result` | Retrieve completed result with data fields, tables, and image URL |

### Usage

```bash
# Set your API key (or use the shared CLI config from ~/.config/deepbiology-lab/config.json)
export DEEPBIOLOGY_API_KEY=dbio_your_api_key_here

# Start the MCP server over stdio
deepbiology-lab-mcp
```

### Configuration

The server checks these sources in order:

1. **Environment variables:** `DEEPBIOLOGY_API_KEY`, `DEEPBIOLOGY_BASE_URL`
2. **CLI config file:** `~/.config/deepbiology-lab/config.json`

### Adding to an MCP client

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "deepbiology-lab": {
      "command": "deepbiology-lab-mcp",
      "env": {
        "DEEPBIOLOGY_API_KEY": "dbio_your_api_key_here"
      }
    }
  }
}
```

**VS Code Copilot** (`.vscode/mcp.json` or global settings):

```json
{
  "servers": {
    "deepbiology-lab": {
      "command": "deepbiology-lab-mcp",
      "env": {
        "DEEPBIOLOGY_API_KEY": "dbio_your_api_key_here"
      }
    }
  }
}
```

**Cursor:**

```json
{
  "mcpServers": {
    "deepbiology-lab": {
      "command": "deepbiology-lab-mcp",
      "env": {
        "DEEPBIOLOGY_API_KEY": "dbio_your_api_key_here"
      }
    }
  }
}

```

## Codex Plugin

This package also ships a [Codex](https://openai.com/codex/) plugin (boltz-compatible pattern)
that gives Codex agents the ability to submit and track DeepBiology Lab workflows via skills.

The plugin source is in the `codex-plugin/` directory of this repo.

### Skills

| Skill | What it does |
|-------|-------------|
| `deepbiology-setup` | Install the CLI package and configure API key |
| `deepbiology-resolve-gene` | Resolve gene names/aliases to HGNC symbols |
| `deepbiology-q1-regulation` | Submit Q1 — transcription gradient analysis |
| `deepbiology-q2-enhancer-importance` | Submit Q2 — enhancer mutation importance scan |
| `deepbiology-q3-mutation-impact` | Submit Q3 — mutated sequence impact evaluation |
| `deepbiology-q4-enhancer-redesign` | Submit Q4 — AI-driven enhancer optimization |
| `deepbiology-check-status` | Check the status of a submitted job |
| `deepbiology-get-result` | Retrieve completed job results |

### How to install

```bash
# Add the marketplace (from the git repo)
codex plugin marketplace add DeepBiology/deepbiology-lab
codex plugin add deepbiology@deepbiology-marketplace

# Set your API key
export DEEPBIOLOGY_API_KEY=dbio_your_api_key_here

# Now describe what you want in natural language —
# Codex will pick the right skill automatically
```

### Local development

```bash
# Point Codex at the local plugin directory
codex --plugin-dir ./codex-plugin-python
```

### Architecture

Each skill (`SKILL.md`) instructs the Codex agent to call a shared Python wrapper
script (`scripts/query.py`) that handles submission, polling, result formatting,
and image downloads via the `DeepBiologyClient`.

```mermaid
flowchart LR
    A[User prompt] --> B[Codex agent]
    B --> C{Which skill?}
    C --> D[SKILL.md instructions]
    D --> E[python scripts/query.py]
    E --> F[DeepBiologyClient]
    F --> G[DeepBiology API]
```

### Expanding the plugin

To add a new skill:
1. Create a new directory under `codex-plugin-python/skills/` with a `SKILL.md`
2. Add the workflow logic to `codex-plugin-python/scripts/query.py` (if a new workflow type)
3. Register the skill in the plugin manifest
4. That's it — Codex picks it up on next load

To add a new alias to the gene resolver:
1. Edit `CURATED_ALIASES` in `codex-plugin-python/scripts/query.py`
2. Add a new line: `"ALIAS": "CANONICAL_SYMBOL",`

## Notes

- Package name: `deepbiology-lab`
- Console scripts: `deepbiology-lab` (CLI), `deepbiology-lab-mcp` (MCP server)
- Codex plugin: `codex-plugin/` directory (install via `codex plugin marketplace add DeepBiology/deepbiology-lab`)
- Importable Python client remains available as `deepbiology`
