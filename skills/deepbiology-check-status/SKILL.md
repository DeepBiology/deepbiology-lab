---
name: deepbiology-check-status
description: Check the processing status of a submitted DeepBiology Lab job. Use when the user asks whether a workflow is complete, requests progress, or provides a DeepBiology job ID for status tracking.
---

# Check job status

Call `get_job_status` with the exact job ID. Report the status, timestamps, and any error message. If the job is complete, offer or proceed to `get_job_result` when the user requested the result. Do not invent progress percentages.
