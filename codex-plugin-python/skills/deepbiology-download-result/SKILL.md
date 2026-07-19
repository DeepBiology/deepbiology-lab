---
name: deepbiology-download-result
description: Wait for a DeepBiology Lab job and retrieve its result inline or save it with a local MCP server. Use when the user asks to download, save, export, or persist the artifacts of a submitted job ID.
---

# Download a result

1. Call `download_job_result` with the exact job ID.
2. With a remote HTTP server, omit `output_directory`, `run_name`, `image_path`, and `download_image`; the tool returns the result and signed image URL inline and cannot write files for the client.
3. With a local stdio server, omit `output_directory` and `run_name` unless the user requests different paths. Set `download_image` only when requested and omit `image_path` to save it beside the JSON result under `deepbiology-experiments/run_<jobId>/`.
4. Use clean output unless the user explicitly requests the normalized raw API payload.
5. For remote delivery, report the inline `result` and `imageUrl`. For local delivery, report `resultFile`, `imageFile`, and `runDirectory` exactly as returned.
