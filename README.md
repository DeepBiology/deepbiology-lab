# deepbiology-lab

Python client and CLI for DeepBiology Lab.

## Install

### Local development

```bash
cd python_client
pip install -e .
```

### From GitHub (after pushing repo)

```bash
pip install git+https://github.com/<org>/<repo>.git#subdirectory=python_client
```

## Configure your API key

```bash
deepbiology-lab config --api-key dbio_your_api_key_here
```

Optional:

```bash
deepbiology-lab config --base-url https://us-central1-deepbiology-471514.cloudfunctions.net
deepbiology-lab config --show
```

Config is stored at:

```bash
~/.config/deepbiology-lab/config.json
```

## Run workflows

### Q1

```bash
deepbiology-lab run q1 --gene-name CD34 --cell-line 195 --download-image --image-path cd34.png
```

By default the CLI prints the clean website-style JSON result. Use `--raw` to print the normalized raw API payload instead.

```bash
deepbiology-lab run q1 --gene-name CD34 --cell-line 195 --raw
```

### Q2

```bash
deepbiology-lab run q2 --gene-name CD34 --cell-line 195 --coordinate chr1:207923783-207923857
```

### Q3

```bash
deepbiology-lab run q3 --gene-name CD34 --cell-line 195 --coordinate chr1:207923783-207923857 --mutated-seq ATGGCCATGGCCATGGCCATGGCCATGGCC
```

### Q4

```bash
deepbiology-lab run q4 --gene-name CD34 --cell-line 195 --center 207923820 --flanking-size 75 --iterations 250 --download-image --image-path redesign.png
```

## Python usage

```python
from deepbiology import DeepBiologyClient

client = DeepBiologyClient(
    api_key="dbio_your_api_key_here",
    base_url="https://us-central1-deepbiology-471514.cloudfunctions.net",
)

job = client.submit_job("q1_regulation", {
    "task": "plot_transcription_gradient",
    "gene_name": "CD34",
    "cell_line": "195",
})

result = client.get_clean_result(job["jobId"])
print(result)
```

## Notes

- Package name: `deepbiology-lab`
- Console script: `deepbiology-lab`
- Importable Python client remains available as `deepbiology`
