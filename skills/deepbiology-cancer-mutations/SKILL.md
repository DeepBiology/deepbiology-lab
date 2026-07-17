---
name: deepbiology-cancer-mutations
description: Query known somatic and clinically relevant mutations for a gene using COSMIC, ClinVar, and CADD data. Use when the user asks about cancer mutations, tumor variants, mutation hotspots, or clinically annotated variants in a gene.
---

# Cancer mutations

1. Resolve a natural-language gene name with `resolve_gene` when necessary.
2. Call the DeepBiology MCP tool `resolve_cancer_mutations` with the HGNC symbol, optional tumor site, and result limit.
3. Separate somatic evidence, clinical interpretation, and prediction scores in the response.
4. State that aggregated annotations are research evidence, not a diagnosis or treatment recommendation.

Do not infer that a variant is causal merely because it appears in COSMIC, ClinVar, or CADD.
