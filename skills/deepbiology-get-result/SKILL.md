---
name: deepbiology-get-result
description: Retrieve and explain the completed result of a DeepBiology Lab job, including fields, tables, sequences, and image metadata. Use when the user requests output from a completed DeepBiology job.
---

# Get a result

1. Call `get_job_status` unless completion was already confirmed in the current context.
2. Call `get_job_result` only after the job is complete.
3. Summarize result fields and tables without dropping genomic coordinates, alleles, model identifiers, or assay types.
4. Report image or sequence artifacts exactly as returned.
5. Include credit and cost fields when present.
