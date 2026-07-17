---
name: deepbiology-q1-regulation
description: Submit Q1 transcription-regulation analysis for a gene and cell line. Use when the user asks to plot a transcription gradient or study regulation across genomic coordinates.
---

# Q1 regulation

1. Resolve non-canonical gene names with `resolve_gene`.
2. Call `submit_q1_regulation` with the HGNC symbol and either `cell_name` or an explicit `cell_line` index.
3. When using `cell_name`, pass `model_id` and `assay_type`; default the assay to `RNASeq`.
4. Keep `check_overlap=true` with the default `SRR3082397` only for relevant AML analyses. Use `check_overlap=false` for unrelated cell types unless the user supplies an appropriate factor.
5. Return the job ID and submission metadata. Use the status and result skills for follow-up.

Preserve explicit numeric indices for backward compatibility; a supplied cell name takes precedence.
