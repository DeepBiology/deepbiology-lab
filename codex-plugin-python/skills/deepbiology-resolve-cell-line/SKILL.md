---
name: deepbiology-resolve-cell-line
description: Resolve a cell line name to its canonical identifier by normalizing hyphens, spaces, and casing. TRIGGER when the user provides a cell line name in natural language (e.g. "kasumi-1", "SK-MEL-28", "K562") and you need the canonical form before submitting a DeepBiology Lab workflow. Always use this before submitting workflows to ensure cell line names match the expected format.
---

## Workflow

1. Run the resolver: `python scripts/query.py --workflow resolve-cell-line --query "<user's cell line>"`
2. Parse the JSON output. The `canonicalName` is the resolved form.
3. Use the `canonicalName` value as the cell line in subsequent workflow calls.

## How it works

Cell line resolution is simple — it strips all non-alphanumeric characters
(hyphens, spaces, dots, underscores) and uppercases. No lookup table needed.

| User says | Canonical form |
|-----------|---------------|
| "kasumi-1" | KASUMI1 |
| "Kasumi 1" | KASUMI1 |
| "SK-MEL-28" | SKMEL28 |
| "NCI-H1781" | NCIH1781 |
| "ls-513" | LS513 |
| "K562" | K562 |

## Always Do This

- Always resolve cell line names before submitting workflows
- The `--cell-line` parameter on submit_* workflows expects the canonical (stripped, uppercased) form
- Run this skill even when the cell line looks like it's already canonical — it's cheap and prevents mismatches
