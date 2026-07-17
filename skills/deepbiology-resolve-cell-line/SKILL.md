---
name: deepbiology-resolve-cell-line
description: Resolve a cell-line name to a model output-channel index for a specific DeepBiology model and assay. Use when the user supplies names such as kasumi-1, SK-MEL-28, or K562 or asks which channel represents a cell and assay.
---

# Resolve a cell line

Call `resolve_cell_line` with `cell_name`, `model_id`, and `assay_type`. Default the assay to `RNASeq`, but do not silently change an explicitly requested assay. Report the numeric `cellLineIndex`, matched cell name, model ID, assay, and match type.

If resolution is ambiguous, show the candidates and ask the user to choose. Never resolve a name by normalization alone when a model index is required.
