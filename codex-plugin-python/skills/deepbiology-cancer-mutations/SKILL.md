---
name: deepbiology-cancer-mutations
description: Query known somatic/cancer mutations for a gene using data aggregated from COSMIC, ClinVar, and CADD via myvariant.info. TRIGGER when the user asks about cancer mutations, somatic variants, tumor mutations, or known clinically relevant mutations in a gene.
---

## Workflow

1. Run: `python scripts/query.py --workflow resolve-cancer-mutations --gene-name <GENE> [--tumor-site <SITE>]`
2. Parse the JSON output — it returns mutations with COSMIC IDs, tumor sites, CADD scores, and clinical significance
3. Present the findings to the user:
   - Highlight mutations with high CADD scores (≥20 indicates deleterious)
   - Note COSMIC IDs for well-known cancer mutations
   - Filter by tumor site if relevant

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--gene-name` | Yes | — | HGNC gene symbol (e.g. TP53, KRAS, BRAF, EGFR) |
| `--tumor-site` | No | all | Filter by tumor site (e.g. "lung", "breast", "pancreas", "skin", "large_intestine") |
| `--max-results` | No | 20 | Maximum number of results |

## Examples

```bash
# All TP53 cancer mutations
python scripts/query.py --workflow resolve-cancer-mutations --gene-name TP53

# BRAF mutations found in lung cancer
python scripts/query.py --workflow resolve-cancer-mutations --gene-name BRAF --tumor-site lung

# KRAS mutations in pancreatic cancer
python scripts/query.py --workflow resolve-cancer-mutations --gene-name KRAS --tumor-site pancreas
```

## Output

- `gene` — the queried gene
- `total_matches` — total variants found in myvariant.info
- `returned` — number returned (limited by max-results)
- `mutations[]` — array with:
  - `variant` — genomic position (HGVS format)
  - `rsid` — dbSNP ID if available
  - `cosmic_id` — COSMIC identifier (e.g. COSM44505)
  - `tumor_site` — COSMIC tumor site annotation
  - `mut_freq` — mutation frequency in COSMIC
  - `cadd_phred` — CADD Phred score (≥20 = likely deleterious)
  - `clinical_significance` — ClinVar annotation if available

## Data source

Uses [myvariant.info](https://myvariant.info) which aggregates:
- **COSMIC** — Catalogue of Somatic Mutations in Cancer
- **ClinVar** — clinical significance annotations
- **CADD** — Combined Annotation Dependent Depletion (deleteriousness scores)

## Always Do This

- Use a gene that you've already resolved with deepbiology-resolve-gene if the user provides a natural language name
- Highlight high CADD scores (≥20) as potentially clinically significant
- For more comprehensive cancer mutation data, full COSMIC access requires a license
