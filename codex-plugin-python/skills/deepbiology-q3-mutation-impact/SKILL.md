---
name: deepbiology-q3-mutation-impact
description: Submit a Q3 mutation impact workflow — evaluates the effect of a specific mutated sequence at a given genomic coordinate on gene regulation. TRIGGER when the user asks to assess the impact of a mutation, test a variant sequence, or evaluate how a specific DNA change affects enhancer function. Requires an HGNC gene symbol — use deepbiology-resolve-gene first if needed.
---

## Workflow

1. If the user provides a gene name in natural language, first run `deepbiology-resolve-gene` to get the canonical HGNC symbol
2. Submit the workflow: `python scripts/query.py --workflow q3 --gene-name <SYMBOL> --coordinate <COORD> --mutated-seq <SEQ> --cell-line <CELL_LINE>`
3. The script submits the job, polls until completion, and returns the clean result as JSON
4. Present the results to the user:
   - Compare the mutation's effect on transcription factor binding
   - Highlight key differences from the reference sequence
   - Report `creditCost` and `costUsd` if available

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--gene-name` | Yes | — | Official HGNC gene symbol |
| `--coordinate` | Yes | — | Genomic coordinate of the mutation |
| `--mutated-seq` | Yes | — | The mutated DNA sequence |
| `--cell-line` | No | "195" | Cell line identifier |
| `--ref` | No | "" | Reference sequence (optional) |
| `--tf` | No | "" | Transcription factor to focus on (optional) |
| `--mode` | No | "medium" | Analysis mode: "fast", "medium", or "high" |

## Example

```bash
python scripts/query.py --workflow q3 --gene-name CD34 --coordinate chr1:207923783-207923857 --mutated-seq ATGGCCATGGCCATGGCCATGGCCATGGCC --cell-line 195
```

## Output

The script prints a JSON object with:
- `jobId`, `status` — job tracking info
- `fields` — result data comparing mutation to reference
- `tables` — binding affinity changes and other metrics
- `image` — visualization of mutation impact
- `notes` — summary of findings

## Always Do This

- Resolve natural-language gene names first using deepbiology-resolve-gene
- Ensure the coordinate matches the region where the mutated sequence lies
