---
name: deepbiology-resolve-snps
description: Query known SNPs within a genomic coordinate range (hg38) and look up a specific SNP's predicted impact on nearby genes. TRIGGER when the user asks about SNPs in a region, wants to find variants near a gene, or wants to know the functional impact of a specific rsID on gene expression.
---

## Workflow: Find SNPs in a region

1. Run: `python scripts/query.py --workflow resolve-snps --region <COORD>`
2. Parse the JSON output — it returns a list of variants with rsID, position, and alleles
3. Present the results to the user, highlighting notable variants (e.g. those with clinical significance)

## Workflow: Look up SNP impact

1. Run: `python scripts/query.py --workflow resolve-snp-impact --rsid <RS_ID>`
2. Parse the JSON output — it returns:
   - The variant location and most severe consequence
   - For transcript consequences: gene symbol, impact severity, consequence terms
   - For intergenic variants: nearest gene symbol and distance
3. Present the findings to the user

## Chaining the two workflows

These two skills are designed to be used together. For example:

> User: "Are there any SNPs within chr1:207923720-207923920 under hg38?"

→ Run `deepbiology-resolve-snps` with the region

> User: "What is the impact of SNP rs1053802528 on the expression of its closest gene?"

→ Run `deepbiology-resolve-snp-impact` with the rsID

## Parameters

### resolve-snps

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--region` | Yes | — | Genomic region (e.g. `chr1:207923720-207923920`) |
| `--max-results` | No | 50 | Maximum number of results (max 200) |

### resolve-snp-impact

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--rsid` | Yes | dbSNP rsID (e.g. `rs1053802528`) |

## Examples

```bash
python scripts/query.py --workflow resolve-snps --region chr1:207923720-207923920
python scripts/query.py --workflow resolve-snp-impact --rsid rs1053802528
```

## Output

### resolve-snps returns
- `count` — number of variants found
- `variants[]` — array with rsid, chromosome, start, end, alleles, variant_class, clinical_significance
- Uses the Ensembl REST API (hg38/GRCh38)

### resolve-snp-impact returns
- `location` — genomic position
- `most_severe_consequence` — e.g. "intron_variant", "missense_variant"
- `genes[]` — array with gene_symbol, impact (HIGH/MODERATE/LOW/MODIFIER), consequence_terms, biotype
- Uses the Ensembl VEP API
