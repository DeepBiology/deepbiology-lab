#!/usr/bin/env python3
"""
DeepBiology Lab — unified Python wrapper for Codex skills.

Called by the agent following SKILL.md instructions.
Accepts a --workflow argument plus workflow-specific parameters,
submits jobs via DeepBiologyClient, and prints JSON results to stdout.

Usage:
    python scripts/query.py --workflow q1 --gene-name CCND1
    python scripts/query.py --workflow resolve-gene --query "cyclin D1"
    python scripts/query.py --workflow status --job-id abc-123
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import re
import time
from typing import Any, Dict, Optional

# ── Config ─────────────────────────────────────────────────────────

DEFAULT_BASE_URL = "https://us-central1-deepbiology-471514.cloudfunctions.net"

# Curated alias map (same as MCP server)
CURATED_ALIASES: Dict[str, str] = {
    "AML1": "RUNX1", "P53": "TP53", "C-MYC": "MYC", "CMYC": "MYC",
    "N-MYC": "MYCN", "NMYC": "MYCN", "L-MYC": "MYCL", "LMYC": "MYCL",
    "BCL-2": "BCL2", "BCL-6": "BCL6", "HER1": "EGFR", "HER2": "ERBB2",
    "ERBB1": "EGFR", "NEU": "ERBB2", "PD-L1": "CD274", "PDL1": "CD274",
    "PD-1": "PDCD1", "PD1": "PDCD1", "CTLA-4": "CTLA4", "CD152": "CTLA4",
    "CD20": "MS4A1", "CD45": "PTPRC", "VEGF": "VEGFA", "PDGF": "PDGFB",
    "TNFA": "TNF", "TNF-ALPHA": "TNF", "IL-2": "IL2", "IL-6": "IL6",
    "IL-10": "IL10", "IFN-GAMMA": "IFNG", "BETA-ACTIN": "ACTB",
    "HIF-1-ALPHA": "HIF1A", "HIF1-ALPHA": "HIF1A", "OCT4": "POU5F1",
    "OCT3/4": "POU5F1", "C-MET": "MET", "HGFR": "MET", "CD246": "ALK",
    "TRKA": "NTRK1", "TRKB": "NTRK2", "TRKC": "NTRK3", "C-RAF": "RAF1",
    "MMAC1": "PTEN", "PKB": "AKT1", "FRAP1": "MTOR", "P16": "CDKN2A",
    "P21": "CDKN1A", "CD95": "FAS", "BCL-XL": "BCL2L1",
    "CASPASE-3": "CASP3", "CASPASE-8": "CASP8", "CASPASE-9": "CASP9",
    "CD135": "FLT3", "C-KIT": "KIT", "CD117": "KIT", "CEBP-ALPHA": "CEBPA",
    "PU.1": "SPI1", "T-BET": "TBX21", "ROR-GAMMA-T": "RORC", "RORGT": "RORC",
    "TTF1": "NKX2-1", "TITF1": "NKX2-1", "BSAP": "PAX5", "IKAROS": "IKZF1",
    "E2A": "TCF3", "E2-2": "TCF4", "PPAR-GAMMA": "PPARG", "TAN1": "NOTCH1",
    "BETA-CATENIN": "CTNNB1", "C-FMS": "CSF1R", "C-SRC": "SRC",
    "TEL": "ETV6", "ETO": "RUNX1T1", "CAN": "NUP214", "EVI1": "MECOM",
    "CD133": "PROM1", "CD90": "THY1", "CD123": "IL3RA", "CD56": "NCAM1",
    "CD326": "EPCAM", "CD227": "MUC1", "CEA": "CEACAM5", "PSA": "KLK3",
    "PSMA": "FOLH1", "NY-ESO-1": "CTAG1B", "MART1": "MLANA", "GP100": "PMEL",
    "CYCLIND1": "CCND1", "CYCLIND2": "CCND2", "CYCLIND3": "CCND3",
    "CYCLINE1": "CCNE1", "CYCLINA2": "CCNA2", "CYCLINB1": "CCNB1",
    "CYCLINH": "CCNH",
}


# ── Helpers ─────────────────────────────────────────────────────────

def _load_api_key() -> str:
    """Load API key from env var or CLI config file."""
    key = os.environ.get("DEEPBIOLOGY_API_KEY", "")
    if key:
        return key
    config_path = os.path.expanduser("~/.config/deepbiology-lab/config.json")
    try:
        with open(config_path) as f:
            cfg = json.load(f)
        key = cfg.get("api_key", "")
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    if not key:
        print(json.dumps({"error": "No API key found. Set DEEPBIOLOGY_API_KEY or run 'deepbiology-lab config --api-key ...'"}))
        sys.exit(1)
    return key


def _load_base_url() -> str:
    url = os.environ.get("DEEPBIOLOGY_BASE_URL", "")
    if url:
        return url
    config_path = os.path.expanduser("~/.config/deepbiology-lab/config.json")
    try:
        with open(config_path) as f:
            cfg = json.load(f)
        url = cfg.get("base_url", "")
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return url or DEFAULT_BASE_URL


def _api_post(path: str, payload: Dict[str, Any], api_key: str, base_url: str) -> Dict[str, Any]:
    import requests
    resp = requests.post(
        f"{base_url}{path}",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def _api_get(path: str, params: Dict[str, str], api_key: str, base_url: str) -> Dict[str, Any]:
    import requests
    resp = requests.get(
        f"{base_url}{path}",
        params=params,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def _call_client(name: str, *args, **kwargs) -> Any:
    """Dynamically import and call DeepBiologyClient methods."""
    try:
        from deepbiology import DeepBiologyClient
    except ImportError:
        print(json.dumps({"error": "deepbiology package not installed. Run: pip install deepbiology-lab"}))
        sys.exit(1)

    api_key = _load_api_key()
    base_url = _load_base_url()
    client = DeepBiologyClient(api_key=api_key, base_url=base_url)
    method = getattr(client, name)
    return method(*args, **kwargs)


# ── Workflow: resolve-gene ─────────────────────────────────────────

def _resolve_gene(query: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]", "", query.upper().strip())
    if not normalized:
        return json.dumps({"matched": False, "canonicalName": None, "resolvedVia": "empty_query"})

    if normalized in CURATED_ALIASES:
        canonical = CURATED_ALIASES[normalized]
        return json.dumps({
            "matched": True, "canonicalName": canonical,
            "query": canonical, "resolvedVia": "curated_alias",
        })

    try:
        url = (
            f"https://mygene.info/v3/query"
            f"?q={urllib.parse.quote(query)}"
            f"&fields=symbol,name,entrezgene"
            f"&species=human&size=1"
        )
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        hit = (data.get("hits") or [None])[0]
        if hit and hit.get("symbol"):
            return json.dumps({
                "matched": True, "canonicalName": hit["symbol"],
                "query": hit["symbol"], "resolvedVia": "mygene_api",
                "mygeneInfo": {"symbol": hit["symbol"], "name": hit.get("name", ""), "entrezgene": str(hit.get("entrezgene", ""))},
            })
    except Exception:
        pass

    return json.dumps({"matched": False, "canonicalName": None, "query": query, "resolvedVia": "not_found"})


# ── Workflow: submit ───────────────────────────────────────────────

WORKFLOW_MAP = {
    "q1": "q1_regulation",
    "q2": "q2_enhancer_importance",
    "q3": "q3_mutation_impact",
    "q4": "q4_enhancer_redesign",
}


def _build_inputs(workflow: str, args: argparse.Namespace) -> Dict[str, Any]:
    gene_name = args.gene_name
    cell_line = args.cell_line or "195"
    mode = args.mode or "medium"
    notes = args.notes or f"Submitted via Codex: {workflow}"

    if workflow == "q1_regulation":
        return {
            "task": "plot_transcription_gradient",
            "gene_name": gene_name,
            "cell_line": cell_line,
            "mode": mode,
            "notes": notes,
            "sequence": f"task=plot_transcription_gradient;gene={gene_name};cell_line={cell_line}",
        }

    if workflow == "q2_enhancer_importance":
        coordinate = args.coordinate or "chr1:207923783-207923857"
        return {
            "task": "mutation",
            "gene_name": gene_name,
            "cell_line": cell_line,
            "coordinate": coordinate,
            "mutatedSeq": "N",
            "loci": coordinate,
            "mode": mode,
            "notes": notes,
            "sequence": f"task=mutation;coordinate={coordinate};mutatedSeq=N;gene={gene_name};cell_line={cell_line}",
        }

    if workflow == "q3_mutation_impact":
        coordinate = args.coordinate
        mutated_seq = args.mutated_seq
        return {
            "task": "mutation",
            "gene_name": gene_name,
            "cell_line": cell_line,
            "coordinate": coordinate,
            "mutatedSeq": mutated_seq,
            "mut": mutated_seq,
            "loci": coordinate,
            "ref": args.ref or "",
            "tf": args.tf or "",
            "mode": mode,
            "notes": notes,
            "sequence": mutated_seq,
        }

    center = args.center or 207923820
    flanking_size = args.flanking_size or 75
    iterations = args.iterations or 250
    return {
        "task": "enhancerOpt",
        "gene_name": gene_name,
        "cell_line": cell_line,
        "center": center,
        "flanking_size": flanking_size,
        "iterations": iterations,
        "mode": mode,
        "notes": notes,
        "sequence": f"task=enhancerOpt;center={center};flanking_size={flanking_size};iterations={iterations};gene={gene_name};cell_line={cell_line}",
    }


def _submit_and_wait(workflow_key: str, inputs: Dict[str, Any]) -> str:
    """Submit job, poll to completion, return clean result."""
    try:
        from deepbiology import DeepBiologyClient
    except ImportError:
        return json.dumps({"error": "deepbiology package not installed. Run: pip install deepbiology-lab"})

    api_key = _load_api_key()
    base_url = _load_base_url()
    client = DeepBiologyClient(api_key=api_key, base_url=base_url)

    # Submit
    job = client.submit_job(workflow=workflow_key, inputs=inputs)
    job_id = job.get("jobId")
    print(json.dumps({"status": "submitted", "jobId": job_id, "submissionId": job.get("submissionId"), "creditCost": job.get("creditCost"), "costUsd": job.get("costUsd")}))
    sys.stdout.flush()

    # Poll
    print(json.dumps({"status": "polling", "jobId": job_id}), file=sys.stderr)
    sys.stderr.flush()
    client.wait_for_job(job_id, poll_seconds=5, timeout_seconds=1800)

    # Result
    raw = client.get_job_result(job_id)
    clean = client.format_clean_result(raw)

    # Download image if available
    image = clean.get("image", {})
    if image.get("url") or (raw.get("result") or {}).get("image", {}).get("base64"):
        output_dir = os.environ.get("DEEPBIOLOGY_OUTPUT_DIR", os.getcwd())
        os.makedirs(output_dir, exist_ok=True)
        image_path = os.path.join(output_dir, f"{job_id}.png")
        try:
            client.download_result_image(job_id, image_path)
            clean["downloadedImage"] = image_path
        except Exception:
            pass

    return json.dumps(clean, indent=2, default=str)


# ── Workflow: status / result ──────────────────────────────────────

def _get_status(job_id: str) -> str:
    try:
        from deepbiology import DeepBiologyClient
    except ImportError:
        return json.dumps({"error": "deepbiology package not installed"})
    api_key = _load_api_key()
    base_url = _load_base_url()
    client = DeepBiologyClient(api_key=api_key, base_url=base_url)
    job = client.get_job(job_id)
    return json.dumps({
        "jobId": job.get("jobId"),
        "status": job.get("status"),
        "submissionId": job.get("submissionId"),
        "createdAt": job.get("createdAt"),
        "updatedAt": job.get("updatedAt"),
        "errorMessage": job.get("errorMessage"),
    }, indent=2)


def _get_result(job_id: str) -> str:
    try:
        from deepbiology import DeepBiologyClient
    except ImportError:
        return json.dumps({"error": "deepbiology package not installed"})
    api_key = _load_api_key()
    base_url = _load_base_url()
    client = DeepBiologyClient(api_key=api_key, base_url=base_url)
    raw = client.get_job_result(job_id)
    clean = client.format_clean_result(raw)
    return json.dumps(clean, indent=2, default=str)


# ── Main ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="DeepBiology Lab — Codex wrapper")
    parser.add_argument("--workflow", required=True,
                        choices=["resolve-gene", "q1", "q2", "q3", "q4", "status", "result"])
    parser.add_argument("--query", help="Gene name/alias for resolve-gene")
    parser.add_argument("--job-id", help="Job ID for status/result workflows")
    parser.add_argument("--gene-name", help="HGNC gene symbol")
    parser.add_argument("--cell-line", default="195")
    parser.add_argument("--mode", default="medium", choices=["fast", "medium", "high"])
    parser.add_argument("--notes", default="")
    parser.add_argument("--coordinate", help="Genomic coordinate (e.g. chr1:207923783-207923857)")
    parser.add_argument("--mutated-seq", help="Mutated DNA sequence (for Q3)")
    parser.add_argument("--ref", default="", help="Reference sequence (for Q3)")
    parser.add_argument("--tf", default="", help="Transcription factor (for Q3)")
    parser.add_argument("--center", type=int, help="Center coordinate (for Q4)")
    parser.add_argument("--flanking-size", type=int, default=75, help="Flanking size in bp (for Q4)")
    parser.add_argument("--iterations", type=int, default=250, help="Optimization iterations (for Q4)")

    args = parser.parse_args()

    if args.workflow == "resolve-gene":
        if not args.query:
            print(json.dumps({"error": "--query is required for resolve-gene"}))
            sys.exit(1)
        print(_resolve_gene(args.query))
        return

    if args.workflow == "status":
        if not args.job_id:
            print(json.dumps({"error": "--job-id is required for status"}))
            sys.exit(1)
        print(_get_status(args.job_id))
        return

    if args.workflow == "result":
        if not args.job_id:
            print(json.dumps({"error": "--job-id is required for result"}))
            sys.exit(1)
        print(_get_result(args.job_id))
        return

    # q1-q4
    if not args.gene_name:
        print(json.dumps({"error": "--gene-name is required"}))
        sys.exit(1)
    workflow_key = WORKFLOW_MAP[args.workflow]
    inputs = _build_inputs(workflow_key, args)
    print(_submit_and_wait(workflow_key, inputs))


if __name__ == "__main__":
    main()
