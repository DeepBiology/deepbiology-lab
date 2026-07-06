---
name: deepbiology-q2-enhancer-importance
description: Submit a Q2 enhancer importance workflow — scans mutation importance at a given genomic coordinate for a gene and cell line. TRIGGER when the user asks to scan for important enhancer positions, find critical nucleotides, or assess mutation importance in a regulatory region. Requires an HGNC gene symbol — use deepbiology-resolve-gene first if needed.
---

## Workflow

1. If the user provides a gene name in natural language, first run `deepbiology-resolve-gene` to get the canonical HGNC symbol
2. If the user provides a cell line name in natural language, first run `deepbiology-resolve-cell-line` to get the canonical form
3. Submit the workflow: `python scripts/query.py --workflow q2 --gene-name <SYMBOL> --coordinate <COORD> --cell-line <CELL_LINE>`
3. The script submits the job, polls until completion, and returns the clean result as JSON
4. Present the results to the user:
   - Highlight which positions show the most important regulatory effects
   - Summarize any tables showing position-by-position importance scores
   - Report `creditCost` and `costUsd` if available

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--gene-name` | Yes | — | Official HGNC gene symbol |
| `--coordinate` | No | "chr1:207923783-207923857" | Genomic coordinate |
| `--cell-line` | No | "195" | Cell line identifier |
| `--mode` | No | "medium" | Analysis mode: "fast", "medium", or "high" |

## Example

```bash
python scripts/query.py --workflow q2 --gene-name MYC --coordinate chr8:128750000-128760000 --cell-line 195
```

## Output

The script prints a JSON object with:
- `jobId`, `status` — job tracking info
- `fields` — result data including position-level importance scores
- `tables` — structured data tables
- `image` — result image showing importance landscape
- `notes` — summary text

## Always Do This

- Resolve natural-language gene names first using deepbiology-resolve-gene
- Resolve natural-language cell line names first using deepbiology-resolve-cell-line
- Use a reasonable coordinate range for the gene's known enhancer region
