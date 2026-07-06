---
name: deepbiology-q1-regulation
description: Submit a Q1 transcription regulation workflow — plots the transcription gradient for a gene across genomic coordinates in a given cell line. TRIGGER when the user asks to analyze gene regulation, plot transcription, or study how a gene's transcription varies across a region. Requires an HGNC gene symbol — use the deepbiology-resolve-gene skill first if the user provides a name in natural language.
---

## Workflow

1. If the user provides a gene name in natural language (e.g. "cyclin D1"), first run `deepbiology-resolve-gene` to get the canonical HGNC symbol
2. Submit the workflow: `python scripts/query.py --workflow q1 --gene-name <SYMBOL> --cell-line <CELL_LINE>`
3. The script submits the job, polls until completion, and returns the clean result as JSON
4. Present the results to the user:
   - Summarize the key findings from the `fields` and `notes`
   - If an image was downloaded, mention the file path
   - Report `creditCost` and `costUsd` if available

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--gene-name` | Yes | — | Official HGNC gene symbol (e.g. CCND1, CD34, MYC) |
| `--cell-line` | No | "195" | Cell line identifier |
| `--mode` | No | "medium" | Analysis mode: "fast", "medium", or "high" |
| `--notes` | No | "" | Optional description |

## Example

```bash
python scripts/query.py --workflow q1 --gene-name CCND1 --cell-line 195
```

## Output

The script prints a JSON object with:
- `jobId`, `status`, `submissionId` — job tracking info
- `fields` — result data fields from the analysis
- `tables` — data tables
- `image` — result image URL and metadata
- `downloadedImage` — local path if the image was downloaded
- `notes` — summary text
- `creditCost`, `costUsd` — pricing info

## Always Do This

- Resolve natural-language gene names first using deepbiology-resolve-gene
- Default to cell line "195" unless the user specifies otherwise
