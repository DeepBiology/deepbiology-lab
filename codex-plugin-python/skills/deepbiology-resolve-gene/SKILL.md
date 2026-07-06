---
name: deepbiology-resolve-gene
description: Resolve a gene name, alias, or description to its official HGNC symbol using a curated alias map and the mygene.info public API. TRIGGER when the user provides a gene in natural language (e.g. "cyclin D1", "p53", "HER2") and you need the canonical symbol before submitting a DeepBiology Lab workflow. Also use this when you need to expand the alias map with new entries.
---

## Workflow

1. Run the resolver: `python scripts/query.py --workflow resolve-gene --query "<user's gene reference>"`
2. Parse the JSON output. The `resolvedVia` field tells you how it was resolved:
   - `"curated_alias"` — matched from a built-in alias map
   - `"mygene_api"` — resolved via the mygene.info public API
   - `"not_found"` — could not be resolved
3. If matched, use the `canonicalName` value as the gene symbol in subsequent workflow calls
4. If not found, ask the user for the official HGNC symbol and suggest alternatives

## Expanding the alias map

The curated alias map is defined at the top of `scripts/query.py` in the `CURATED_ALIASES` dictionary. To add a new alias:

1. Open `scripts/query.py`
2. Add a new entry: `"MYALIAS": "CANONICAL_SYMBOL",`
3. Save the file
4. The new alias is available immediately on the next invocation

## Examples

| User says | Resolves to | via |
|-----------|-------------|-----|
| "cyclin D1" | CCND1 | curated_alias |
| "HER2" | ERBB2 | curated_alias |
| "p53" | TP53 | curated_alias |
| "BRCA1" | BRCA1 | mygene_api (exact) |
| "a gene that regulates cholesterol" | (varies) | mygene_api |

## Always Do This

- Always resolve gene names before submitting workflows — the API requires official HGNC symbols
- If the user's description is ambiguous, resolve the most likely gene and confirm with the user
