---
name: deepbiology-q4-enhancer-redesign
description: Submit a Q4 enhancer redesign workflow — AI-driven optimization of an enhancer sequence for a given gene and cell line. TRIGGER when the user asks to design, optimize, or redesign an enhancer, improve regulatory activity, or generate an optimized enhancer sequence. Requires an HGNC gene symbol — use deepbiology-resolve-gene first if needed.
---

## Workflow

1. If the user provides a gene name in natural language, first run `deepbiology-resolve-gene` to get the canonical HGNC symbol
2. If the user provides a cell line name in natural language, first run `deepbiology-resolve-cell-line` to get the canonical form
3. Submit the workflow: `python scripts/query.py --workflow q4 --gene-name <SYMBOL> --center <CENTER> --flanking-size <SIZE> --iterations <N> --cell-line <CELL_LINE>`
3. The script submits the job, polls until completion, and returns the clean result as JSON
4. Present the results to the user:
   - Show the optimized enhancer sequence from `optimizedSequence`
   - Summarize the `means` (performance metrics) comparing original vs. optimized
   - If an enhancer table is present, highlight the key improvements
   - Report `creditCost` and `costUsd` if available

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--gene-name` | Yes | — | Official HGNC gene symbol |
| `--center` | No | 207923820 | Center coordinate for the enhancer region |
| `--flanking-size` | No | 75 | Flanking size in base pairs |
| `--iterations` | No | 250 | Number of optimization iterations |
| `--max-runtime-hours` | No | 24 | Maximum runtime in hours |
| `--cell-line` | No | "195" | Cell line identifier |
| `--mode` | No | "medium" | Analysis mode: "fast", "medium", or "high" |

## Example

```bash
python scripts/query.py --workflow q4 --gene-name CCND1 --center 207923820 --flanking-size 75 --iterations 250 --cell-line 195
```

## Output

The script prints a JSON object with:
- `jobId`, `status` — job tracking info
- `optimizedSequence` — the AI-optimized enhancer DNA sequence
- `means` — performance metrics comparing original vs. optimized
- `enhancerTable` — detailed comparison of enhancer elements
- `fields` — additional result data
- `image` — visualization of the optimization results
- `downloadedImage` — local file path if image was saved
- `notes` — summary text

## Always Do This

- Resolve natural-language gene names first using deepbiology-resolve-gene
- Resolve natural-language cell line names first using deepbiology-resolve-cell-line
- Ask the user if they want to adjust center, flanking size, or iterations
  from the defaults before submitting (especially for genes with known
  well-characterized enhancer regions)
- When presenting the optimized sequence, show it in a code block for easy copying
