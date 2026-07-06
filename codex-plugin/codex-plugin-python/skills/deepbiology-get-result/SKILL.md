---
name: deepbiology-get-result
description: Retrieve the completed result of a DeepBiology Lab job, including data fields, tables, and image URL. TRIGGER when the user wants the final output of a completed job. Use deepbiology-check-status first to confirm the job has finished.
---

## Workflow

1. First check the job status with `deepbiology-check-status` to confirm it's completed
2. If completed, retrieve the result: `python scripts/query.py --workflow result --job-id <JOB_ID>`
3. Parse the JSON output and present the findings:
   - Summarize the `fields` and `notes`
   - Show any `tables` in a readable format
   - If `image.url` exists, mention it to the user
   - Report `creditCost` and `costUsd` if available

## Parameters

| Parameter | Required |
|-----------|----------|
| `--job-id` | Yes |

## Example

```bash
python scripts/query.py --workflow result --job-id abc-123-def
```

## Output

The script prints a JSON object with:
- `jobId`, `status` — job info
- `question`, `task` — what was requested
- `fields` — result data key-value pairs
- `tables` — structured data tables
- `image` — result image with URL and metadata
- `notes` — summary text
- `creditCost`, `costUsd` — job pricing

## Always Do This

- Always confirm the job is completed (deepbiology-check-status) before retrieving results
- Parse the returned JSON and present a human-readable summary to the user
- Do not print raw JSON to the user — interpret the data
