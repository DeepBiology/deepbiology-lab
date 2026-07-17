---
name: deepbiology-q4-enhancer-redesign
description: Submit Q4 AI-assisted enhancer redesign for a gene and cell line. Use when the user asks to optimize, redesign, or generate an enhancer sequence with specified coordinate and runtime constraints.
---

# Q4 enhancer redesign

1. Resolve non-canonical gene names with `resolve_gene`.
2. Confirm center coordinate, flanking size, iteration count, and runtime limit when they materially affect the request.
3. Call `submit_q4_enhancer_redesign` with either `cell_name` or an explicit `cell_line` index.
4. When using `cell_name`, pass `model_id` and `assay_type`; default to `RNASeq`.
5. Return the job ID and retrieve the optimized sequence only after completion.

Describe generated sequences as computational candidates requiring experimental validation.
