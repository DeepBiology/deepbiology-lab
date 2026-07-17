---
name: deepbiology-q2-enhancer-importance
description: Submit Q2 enhancer-importance analysis at a genomic coordinate for a gene and cell line. Use when the user asks to scan critical enhancer nucleotides or mutation importance in a regulatory region.
---

# Q2 enhancer importance

1. Resolve non-canonical gene names with `resolve_gene`.
2. Confirm the coordinate includes chromosome and interval.
3. Call `submit_q2_enhancer_importance` with the gene and coordinate plus either `cell_name` or an explicit `cell_line` index.
4. When using `cell_name`, pass the intended `model_id` and `assay_type`; default to `RNASeq`.
5. Return the job ID and use `get_job_status` and `get_job_result` for follow-up.
