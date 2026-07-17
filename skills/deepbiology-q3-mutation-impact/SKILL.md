---
name: deepbiology-q3-mutation-impact
description: Submit Q3 mutation-impact analysis for a mutated DNA sequence at a genomic coordinate. Use when the user asks how a specified sequence change may affect gene regulation or enhancer function.
---

# Q3 mutation impact

1. Resolve non-canonical gene names with `resolve_gene`.
2. Require the genomic coordinate and mutated DNA sequence; do not guess either.
3. Call `submit_q3_mutation_impact` with the gene, coordinate, mutated sequence, and either `cell_name` or an explicit `cell_line` index.
4. When using `cell_name`, pass `model_id` and `assay_type`; default to `RNASeq`.
5. Preserve optional reference sequence and transcription-factor inputs when supplied.
6. Return the job ID and track it with the status and result tools.
