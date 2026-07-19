# DeepBiology Lab on Alibaba Cloud — Proof of Deployment

## Overview

This repository demonstrates the use of **Alibaba Cloud** services for AI-powered genomics research. The DeepBiology Lab MCP server is deployed on an **Alibaba Cloud ECS (Elastic Compute Service)** virtual machine, providing genomics workflows via the Model Context Protocol (MCP).

## Alibaba Cloud Service Details

| Property | Value |
|---|---|
| **Service** | Alibaba Cloud ECS (Elastic Compute Service) |
| **Endpoint** | `https://47.89.181.155/mcp` |
| **IP Address** | `47.89.181.155` (Alibaba Cloud CN region) |
| **Protocol** | Model Context Protocol (MCP) over Streamable HTTP |
| **API Format** | JSON-RPC 2.0 |
| **Authentication** | Bearer token (API key) |
| **Server** | deepbiology-lab v1.28.1 |

## Architecture

```
User (curl / Qwen CLI / Gemini CLI)
        │
        │ HTTPS + JSON-RPC 2.0
        ▼
┌─────────────────────────────────┐
│  Alibaba Cloud ECS Instance      │
│  https://47.89.181.155/mcp       │
│                                 │
│  DeepBiology Lab MCP Server     │
│  - Q1: Transcription Regulation │
│  - Q2: Enhancer Importance      │
│  - Q3: Mutation Impact          │
│  - Q4: Enhancer Redesign        │
│  - Gene/Cell Line Resolution    │
│  - Variant Annotation           │
└─────────────────────────────────┘
        │
        ▼
  DeepBiology Lab Backend Services
```

## Available MCP Tools (15 tools)

| Tool | Description |
|---|---|
| `submit_q1_regulation` | Plot transcription gradient for a gene in a cell line |
| `submit_q2_enhancer_importance` | Scan enhancer nucleotide importance at a coordinate |
| `submit_q3_mutation_impact` | Test impact of a specific DNA sequence mutation |
| `submit_q4_enhancer_redesign` | AI-driven enhancer sequence optimization |
| `get_job_status` | Check status of a submitted job |
| `get_job_result` | Retrieve completed job results |
| `download_job_result` | Download job results with artifacts |
| `resolve_gene` | Resolve gene aliases to HGNC symbols |
| `resolve_cell_line` | Resolve cell line names to model channel indices |
| `find_variants` | Find known variants in a genomic region |
| `annotate_variant` | Annotate a dbSNP rsID with Ensembl VEP |
| `resolve_cancer_mutations` | Query cancer mutations via COSMIC/ClinVar |
| `list_models` | List available DeepBiology models |

## Quick Start

### Prerequisites

```bash
# Install required tools
sudo apt-get install -y curl jq

# Set your API key
export DEEPBIOLOGY_API_KEY="dbio_your_api_key_here"
```

### Run the Demo

```bash
chmod +x deepbiology_q1_cd34_kasumi1.sh
./deepbiology_q1_cd34_kasumi1.sh
```

### Manual API Calls

#### 1. Initialize MCP Session

```bash
curl -s https://47.89.181.155/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $DEEPBIOLOGY_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "curl-client", "version": "1.0.0"}
    }
  }' | jq .
```

#### 2. Submit Q1 Regulation Analysis (CD34 in Kasumi-1)

```bash
curl -s https://47.89.181.155/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $DEEPBIOLOGY_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "submit_q1_regulation",
      "arguments": {
        "gene_name": "CD34",
        "cell_line": "195",
        "cell_name": "Kasumi-1",
        "model_id": "borzoi_finetune_v1",
        "assay_type": "RNASeq",
        "mode": "medium",
        "top_n": 3,
        "check_overlap": true,
        "notes": "CD34 regulation in Kasumi-1 cells"
      }
    }
  }' | jq .
```

#### 3. Check Job Status

```bash
curl -s https://47.89.181.155/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $DEEPBIOLOGY_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get_job_status",
      "arguments": {"job_id": "YOUR_JOB_ID"}
    }
  }' | jq .
```

#### 4. Retrieve Results

```bash
curl -s https://47.89.181.155/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $DEEPBIOLOGY_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "get_job_result",
      "arguments": {"job_id": "YOUR_JOB_ID"}
    }
  }' | jq .
```

## Scientific Context

### CD34 Gene
CD34 is a cell surface glycoprotein expressed on hematopoietic stem and progenitor cells. It is a key marker in acute myeloid leukemia (AML) research and is used for identifying and isolating leukemic stem cells.

### Kasumi-1 Cell Line
Kasumi-1 is a well-characterized AML cell line derived from a patient with acute lymphoblastic leukemia (ALL) with t(8;21) translocation. It is widely used as a model system for studying AML biology and gene regulation.

### Q1 Transcription Gradient Analysis
The Q1 workflow uses the Borzoi deep learning model (finetuned v1) to predict how transcription factor binding and enhancer activity change across genomic coordinates near the CD34 gene. This helps identify:
- Key enhancer regions regulating CD34 expression
- Transcription factor binding sites
- Regulatory elements that may be dysregulated in AML

## Files

| File | Description |
|---|---|
| `deepbiology_q1_cd34_kasumi1.sh` | Complete bash script demonstrating the full Q1 workflow |
| `deepbiology_alibaba_cloud_demo.md` | This documentation file |

## Verification

To verify the Alibaba Cloud deployment:

```bash
# Check server response
curl -s https://47.89.181.155/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $DEEPBIOLOGY_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"verify","version":"1.0"}}}' | jq '.result.serverInfo'
```

Expected output:
```json
{
  "name": "deepbiology-lab",
  "version": "1.28.1"
}
```

## License

MIT License
