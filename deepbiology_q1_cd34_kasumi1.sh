#!/bin/bash
# =============================================================================
# DeepBiology Lab Q1: Transcription Regulation Analysis
# Gene: CD34 | Cell Line: Kasumi-1 (Acute Myeloid Leukemia)
#
# This script demonstrates the use of Alibaba Cloud services via the
# DeepBiology Lab MCP server deployed on an Alibaba Cloud virtual machine.
#
# Alibaba Cloud MCP Endpoint: https://47.89.181.155/mcp
#   - IP 47.89.181.155 is an Alibaba Cloud ECS instance
#   - Service: DeepBiology Lab - AI-powered genomics workflows
#   - Protocol: Model Context Protocol (MCP) over Streamable HTTP / JSON-RPC 2.0
#   - Authentication: Bearer token (API key)
#
# Workflow: Q1 - Transcription Gradient Analysis
#   Plots predicted transcription gradient for the CD34 gene across genomic
#   coordinates in Kasumi-1 cells, identifying enhancer regions that regulate
#   CD34 expression in acute myeloid leukemia.
#
# Usage:
#   export DEEPBIOLOGY_API_KEY="dbio_your_api_key_here"
#   chmod +x deepbiology_q1_cd34_kasumi1.sh
#   ./deepbiology_q1_cd34_kasumi1.sh
#
# Prerequisites:
#   - DEEPBIOLOGY_API_KEY environment variable must be set
#   - curl and jq must be installed
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration - Alibaba Cloud DeepBiology MCP Server
# ---------------------------------------------------------------------------
MCP_URL="https://47.89.181.155/mcp"
API_KEY="${DEEPBIOLOGY_API_KEY:?Error: DEEPBIOLOGY_API_KEY environment variable is not set}"

# Write curl header file to avoid exposing the bearer token in process lists
HEADER_FILE=$(mktemp /tmp/deepbiology_headers.XXXXXX)
trap 'rm -f "$HEADER_FILE"' EXIT
cat > "$HEADER_FILE" <<EOF
Content-Type: application/json
Accept: application/json
Authorization: Bearer ${API_KEY}
EOF

# Q1 workflow parameters
GENE_NAME="CD34"
CELL_LINE="195"        # Kasumi-1 cell line index in borzoi_finetune_v1 model
CELL_NAME="Kasumi-1"
MODEL_ID="borzoi_finetune_v1"
ASSAY_TYPE="RNASeq"
MODE="medium"
TOP_N=3
NOTES="Q1 transcription regulation analysis for CD34 in Kasumi-1 cells - Global AI Hackathon"

# Polling configuration
POLL_INTERVAL=10      # seconds between status checks
MAX_POLLS=180         # max polling attempts (30 minutes total)

# ---------------------------------------------------------------------------
# Helper: validate MCP JSON-RPC response and extract .result.content[0].text
# Prints the extracted text to stdout. Exits on errors or isError responses.
# ---------------------------------------------------------------------------
mcp_extract_text() {
  local response="$1"
  local label="$2"

  # Check for JSON-RPC error
  local rpc_error
  rpc_error=$(echo "$response" | jq -r '.error.message // empty')
  if [ -n "$rpc_error" ]; then
    echo "  ERROR: MCP error during ${label}: ${rpc_error}" >&2
    exit 1
  fi

  # Check for tool-level isError (lives on .result, not inside .content)
  local is_error
  is_error=$(echo "$response" | jq -r '.result.isError // false')
  if [ "$is_error" = "true" ]; then
    local err_text
    err_text=$(echo "$response" | jq -r '.result.content[0].text // "(no message)"')
    echo "  ERROR: Tool error during ${label}: ${err_text}" >&2
    exit 1
  fi

  local text
  text=$(echo "$response" | jq -r '.result.content[0].text // empty')
  if [ -z "$text" ]; then
    echo "  ERROR: Empty response during ${label}" >&2
    exit 1
  fi

  echo "$text"
}

echo "============================================================"
echo "  DeepBiology Lab Q1 - CD34 Regulation in Kasumi-1 Cells"
echo "  Alibaba Cloud MCP Server: ${MCP_URL}"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# Step 1: MCP Initialize - Establish connection with Alibaba Cloud MCP server
# ---------------------------------------------------------------------------
echo "[Step 1/5] Initializing MCP session with Alibaba Cloud server..."

INIT_RESPONSE=$(curl -s "${MCP_URL}" \
  -H "@${HEADER_FILE}" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "deepbiology-curl-client",
        "version": "1.0.0"
      }
    }
  }')

SERVER_INFO=$(echo "$INIT_RESPONSE" | jq -r '.result.serverInfo.name // empty')
SERVER_VERSION=$(echo "$INIT_RESPONSE" | jq -r '.result.serverInfo.version // empty')

if [ -z "$SERVER_INFO" ]; then
  echo "  ERROR: MCP initialization failed"
  echo "  Response: ${INIT_RESPONSE}"
  exit 1
fi

echo "  Connected to: ${SERVER_INFO} v${SERVER_VERSION}"
echo "  Protocol: $(echo "$INIT_RESPONSE" | jq -r '.result.protocolVersion')"
echo "  MCP session initialized successfully."
echo ""

# ---------------------------------------------------------------------------
# Step 2: List Available Tools (verify Alibaba Cloud service capabilities)
# ---------------------------------------------------------------------------
echo "[Step 2/5] Listing available tools on Alibaba Cloud MCP server..."

TOOLS_RESPONSE=$(curl -s "${MCP_URL}" \
  -H "@${HEADER_FILE}" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }')

TOOL_COUNT=$(echo "$TOOLS_RESPONSE" | jq '.result.tools | length')
echo "  Available tools: ${TOOL_COUNT}"
echo "$TOOLS_RESPONSE" | jq -r '.result.tools[].name' | sed 's/^/    - /'

if [ "$TOOL_COUNT" -ne 15 ]; then
  echo "  ERROR: Expected 15 tools, got ${TOOL_COUNT}. Aborting."
  exit 1
fi
echo ""

# ---------------------------------------------------------------------------
# Step 3: Submit Q1 Regulation Analysis Job
# Submits transcription gradient analysis for CD34 in Kasumi-1 cells
# ---------------------------------------------------------------------------
echo "[Step 3/5] Submitting Q1 regulation analysis job..."
echo "  Gene: ${GENE_NAME}"
echo "  Cell Line: ${CELL_NAME} (index: ${CELL_LINE})"
echo "  Model: ${MODEL_ID}"
echo "  Assay: ${ASSAY_TYPE}"
echo ""

SUBMIT_RESPONSE=$(curl -s "${MCP_URL}" \
  -H "@${HEADER_FILE}" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": 3,
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"submit_q1_regulation\",
      \"arguments\": {
        \"gene_name\": \"${GENE_NAME}\",
        \"cell_line\": \"${CELL_LINE}\",
        \"cell_name\": \"${CELL_NAME}\",
        \"model_id\": \"${MODEL_ID}\",
        \"assay_type\": \"${ASSAY_TYPE}\",
        \"mode\": \"${MODE}\",
        \"top_n\": ${TOP_N},
        \"check_overlap\": true,
        \"notes\": \"${NOTES}\"
      }
    }
  }")

# Extract and validate job details
JOB_TEXT=$(mcp_extract_text "$SUBMIT_RESPONSE" "job submission")
JOB_ID=$(echo "$JOB_TEXT" | jq -r '.jobId')
JOB_STATUS=$(echo "$JOB_TEXT" | jq -r '.status')
CREDIT_COST=$(echo "$JOB_TEXT" | jq -r '.creditCost')
TASK=$(echo "$JOB_TEXT" | jq -r '.task')

if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
  echo "  ERROR: Job submission did not return a valid job ID."
  exit 1
fi

echo "  Job ID: ${JOB_ID}"
echo "  Status: ${JOB_STATUS}"
echo "  Task: ${TASK}"
echo "  Credit Cost: ${CREDIT_COST}"

# Show cell line resolution details
echo ""
echo "  Cell Line Resolution:"
echo "$JOB_TEXT" | jq -r '.cellLineResolution | "    Input: \(.inputCellName) -> Canonical: \(.canonicalName) (index: \(.cellLineIndex), match: \(.matchType))"'

echo ""
echo "  Job submitted to Alibaba Cloud successfully!"
echo ""

# ---------------------------------------------------------------------------
# Step 4: Poll Job Status until completion
# ---------------------------------------------------------------------------
echo "[Step 4/5] Polling job status on Alibaba Cloud (interval: ${POLL_INTERVAL}s)..."
echo ""

POLL_COUNT=0
CURRENT_STATUS="${JOB_STATUS}"

while [ "$CURRENT_STATUS" != "completed" ] && \
      [ "$CURRENT_STATUS" != "failed" ] && \
      [ "$CURRENT_STATUS" != "cancelled" ] && \
      [ "$POLL_COUNT" -lt "$MAX_POLLS" ]; do
  POLL_COUNT=$((POLL_COUNT + 1))

  STATUS_RESPONSE=$(curl -s "${MCP_URL}" \
    -H "@${HEADER_FILE}" \
    -d "{
      \"jsonrpc\": \"2.0\",
      \"id\": $((10 + POLL_COUNT)),
      \"method\": \"tools/call\",
      \"params\": {
        \"name\": \"get_job_status\",
        \"arguments\": {
          \"job_id\": \"${JOB_ID}\"
        }
      }
    }")

  STATUS_TEXT=$(mcp_extract_text "$STATUS_RESPONSE" "status poll ${POLL_COUNT}")
  CURRENT_STATUS=$(echo "$STATUS_TEXT" | jq -r '.status')

  ELAPSED=$((POLL_COUNT * POLL_INTERVAL))
  printf "  Poll %3d (%4ds): Status = %s\n" "$POLL_COUNT" "$ELAPSED" "$CURRENT_STATUS"

  if [ "$CURRENT_STATUS" = "completed" ] || [ "$CURRENT_STATUS" = "failed" ] || [ "$CURRENT_STATUS" = "cancelled" ]; then
    break
  fi

  sleep "$POLL_INTERVAL"
done

echo ""

if [ "$CURRENT_STATUS" = "failed" ]; then
  echo "  ERROR: Job failed on Alibaba Cloud server."
  exit 1
elif [ "$CURRENT_STATUS" = "cancelled" ]; then
  echo "  ERROR: Job was cancelled on Alibaba Cloud server."
  exit 1
elif [ "$POLL_COUNT" -ge "$MAX_POLLS" ]; then
  echo "  WARNING: Job timed out after $((MAX_POLLS * POLL_INTERVAL)) seconds."
  echo "  Current status: ${CURRENT_STATUS}"
  exit 1
elif [ "$CURRENT_STATUS" != "completed" ]; then
  echo "  ERROR: Job ended in unexpected status: ${CURRENT_STATUS}"
  exit 1
fi

echo "  Job completed on Alibaba Cloud after $((POLL_COUNT * POLL_INTERVAL)) seconds!"
echo ""

# ---------------------------------------------------------------------------
# Step 5: Retrieve Job Results from Alibaba Cloud
# ---------------------------------------------------------------------------
echo "[Step 5/5] Retrieving results from Alibaba Cloud..."
echo ""

RESULT_RESPONSE=$(curl -s "${MCP_URL}" \
  -H "@${HEADER_FILE}" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": 100,
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"get_job_result\",
      \"arguments\": {
        \"job_id\": \"${JOB_ID}\"
      }
    }
  }")

# Extract and validate the result
RESULT_TEXT=$(mcp_extract_text "$RESULT_RESPONSE" "result retrieval")

echo "============================================================"
echo "  Q1 RESULTS: CD34 Transcription Regulation in Kasumi-1"
echo "  (from Alibaba Cloud MCP Server)"
echo "============================================================"
echo ""

# Pretty-print the full result
echo "$RESULT_TEXT" | jq .

echo ""
echo "============================================================"
echo "  Analysis Complete!"
echo "  Alibaba Cloud MCP Server: ${MCP_URL}"
echo "  Server: ${SERVER_INFO} v${SERVER_VERSION}"
echo "  Job ID: ${JOB_ID}"
echo "  Gene: ${GENE_NAME} | Cell Line: ${CELL_NAME}"
echo "  Task: ${TASK}"
echo "============================================================"
