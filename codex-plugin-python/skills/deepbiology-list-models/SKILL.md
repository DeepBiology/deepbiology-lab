---
name: deepbiology-list-models
description: List available DeepBiology Lab models and their supported workflows. TRIGGER when the user asks about available models, which model to use, or mentions "CCLE" vs "Borzoi" to help route to the right model catalog.
---

## Workflow

1. Run: `python scripts/query.py --workflow list-models`
2. Parse the JSON output and present the models to the user:
   - `borzoi_finetune_v1` — default production model, 785 cell lines
   - `borzoi_finetune_ccle_v1` — CCLE model, 1019 cancer cell lines

## Model selection guidance

| If the user mentions... | Use model |
|------------------------|-----------|
| "CCLE", "cancer cell lines", "NCI-H1781", "LS513" | `borzoi_finetune_ccle_v1` |
| "Borzoi", "default", or nothing specific | `borzoi_finetune_v1` |

For now, this is informational only — the current submit workflow uses the
default model automatically. Future versions may accept a `--model` parameter.
