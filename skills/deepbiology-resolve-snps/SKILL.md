---
name: deepbiology-resolve-snps
description: Find known variants in a genomic region or annotate a dbSNP rsID with Ensembl VEP. Use when the user asks about SNPs near a coordinate or gene, regional variants, or predicted transcript and regulatory consequences of an rsID.
---

# Resolve variants

For a region, call `find_variants` with a `chr:start-end` interval, assembly, and limit. For an rsID, call `annotate_variant` with the rsID and assembly. Default to `GRCh38` only when the user has not specified a build.

Keep genomic mappings separate from transcript, regulatory-feature, and intergenic consequences. Distinguish overlap from proximity and predicted consequence from experimentally demonstrated regulatory effect.
