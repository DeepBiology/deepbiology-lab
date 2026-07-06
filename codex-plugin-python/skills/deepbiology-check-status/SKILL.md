---
name: deepbiology-check-status
description: Check the current processing status of a previously submitted DeepBiology Lab job. TRIGGER when the user asks about a job's progress, wants to know if a workflow completed, or when following up on a previous submission from the same session. Use this before deepbiology-get-result to ensure the job is done.
---

## Workflow

1. Run: `python scripts/query.py --workflow status --job-id <JOB_ID>`
2. Parse the JSON output:
   - `"submitted"` or `"processing"` — job is still running, tell the user to wait
   - `"completed"` — job is done, offer to retrieve the result with deepbiology-get-result
   - `"failed"` — job failed, show the `errorMessage`
   - `"cancelled"` — job was cancelled

## Parameters

| Parameter | Required |
|-----------|----------|
| `--job-id` | Yes |

## Example

```bash
python scripts/query.py --workflow status --job-id abc-123-def
```

## Always Do This

- After a submit_* workflow, use this skill to track progress before offering results
- If the job is still processing, tell the user and offer to check again later
