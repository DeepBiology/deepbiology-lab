---
name: deepbiology-download-result
description: Wait for a DeepBiology Lab job and save its result JSON and optional image to local files. Use when the user asks to download, save, export, or persist the artifacts of a submitted job ID.
---

# Download a result

1. Call `download_job_result` with the exact job ID.
2. Unless the user requests different paths, omit `output_directory` and `run_name` so results are saved under `deepbiology-experiments/run_<jobId>/`.
3. Set `download_image` only when the user asks for the image; omit `image_path` to save it beside the JSON result.
4. Use clean output unless the user explicitly requests the normalized raw API payload.
5. Report `resultFile`, `imageFile`, and `runDirectory` exactly as returned. Files are created on the machine running the local MCP server.
