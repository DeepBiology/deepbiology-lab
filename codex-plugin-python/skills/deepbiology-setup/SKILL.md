---
name: deepbiology-setup
description: Install the deepbiology-lab Python package and configure the API key so DeepBiology Lab skills can submit genomics workflows. TRIGGER when asked to set up, configure, initialize, or authenticate DeepBiology Lab, or when another skill reports a missing API key or package error.
---

## Workflow

1. Check if the `deepbiology` package is installed: `python -c "import deepbiology; print('ok')"`
2. If not installed, install it: `pip install deepbiology-lab`
3. Check if the API key is configured by running: `python scripts/query.py --workflow status --job-id test 2>&1`
   - If it returns an error about a missing API key, prompt the user for their API key
4. Once the user provides their API key, configure it:
   - Set the `DEEPBIOLOGY_API_KEY` environment variable in the agent's environment
   - Or run: `deepbiology-lab config --api-key <key>`
5. Verify it works by submitting a quick test

## Variables

- `DEEPBIOLOGY_API_KEY` — the API key for authenticating with DeepBiology Lab
- `DEEPBIOLOGY_BASE_URL` — optional override for the API base URL
- `DEEPBIOLOGY_OUTPUT_DIR` — optional directory for downloaded results (defaults to current directory)
