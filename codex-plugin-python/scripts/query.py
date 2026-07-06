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


# ── Workflow: resolve-cell-line ────────────────────────────────────

def _resolve_cell_line(query: str) -> str:
    canonical = re.sub(r"[^a-zA-Z0-9]", "", query.strip()).upper()
    return json.dumps({
        "matched": bool(canonical),
        "canonicalName": canonical if canonical else None,
        "original": query,
        "resolvedVia": "normalization",
    })


# ── Workflow: resolve-snps ────────────────────────────────────────

ENSEMBL_BASE = "https://rest.ensembl.org"


def _resolve_snps(region: str, max_results: int = 50) -> str:
    """Query Ensembl REST API for variants in a region."""
    import json as _json
    import urllib.request, urllib.error

    region_clean = region.replace("chr", "").replace("CHR", "").strip()
    url = f"{ENSEMBL_BASE}/overlap/region/human/{region_clean}?feature=variation"
    if max_results > 0:
        url += f";size={min(max_results, 200)}"

    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read())
    except Exception as e:
        return _json.dumps({"error": f"Failed to query Ensembl: {str(e)}", "region": region})

    results = []
    for v in data:
        results.append({
            "rsid": v.get("id"),
            "chromosome": v.get("seq_region_name"),
            "start": v.get("start"),
            "end": v.get("end"),
            "alleles": v.get("allele_string"),
            "variant_class": v.get("variant_class", ""),
            "clinical_significance": v.get("clinical_significance", []),
        })

    return _json.dumps({
        "region": region,
        "genome_build": "hg38",
        "count": len(results),
        "variants": results,
    }, indent=2)


def _resolve_snp_impact(rsid: str) -> str:
    """Query Ensembl VEP for a specific rsID."""
    import json as _json
    import urllib.request, urllib.error

    rsid = rsid.strip()
    if not rsid.startswith("rs"):
        rsid = f"rs{rsid}"

    url = f"{ENSEMBL_BASE}/vep/human/id/{rsid}"
    try:
        req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read())
    except Exception as e:
        return _json.dumps({"error": f"Failed to query Ensembl VEP: {str(e)}", "rsid": rsid})

    result = {"rsid": rsid, "genes": []}
    for item in data:
        result["location"] = f"{item.get('seq_region_name')}:{item.get('start')}"
        result["allele_string"] = item.get("allele_string", "")
        result["most_severe_consequence"] = item.get("most_severe_consequence", "")
        for tc in item.get("transcript_consequences", []):
            result["genes"].append({
                "gene_symbol": tc.get("gene_symbol", ""),
                "gene_id": tc.get("gene_id", ""),
                "impact": tc.get("impact", ""),
                "consequence_terms": tc.get("consequence_terms", []),
                "biotype": tc.get("biotype", ""),
            })
        for ic in item.get("intergenic_consequences", []):
            result["genes"].append({
                "gene_symbol": ic.get("gene_symbol", ""),
                "impact": "INTERGENIC",
                "consequence_terms": ["intergenic_variant"],
                "distance": ic.get("distance", ""),
            })

    return _json.dumps(result, indent=2)


# ── Workflow: resolve-cancer-mutations ────────────────────────────

def _resolve_cancer_mutations(gene_name: str, tumor_site: str = "", max_results: int = 20) -> str:
    """Query myvariant.info for somatic/cancer mutations in a gene."""
    import json as _json
    import urllib.request, urllib.parse

    query = urllib.parse.quote(gene_name)
    fields = "cosmic,cadd,clinvar,dbsnp"
    url = f"https://myvariant.info/v1/query?q={query}&fields={fields}&species=human&size={min(max_results, 100)}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read())
    except Exception as e:
        return _json.dumps({"error": f"Failed: {str(e)}", "gene": gene_name})

    results = []
    for hit in data.get("hits", []):
        cosmic = hit.get("cosmic") or {}
        cadd = hit.get("cadd") or {}
        dbsnp = hit.get("dbsnp") or {}
        clinvar = hit.get("clinvar") or {}
        if tumor_site:
            site = (cosmic.get("tumor_site") or "").lower()
            if tumor_site.lower() not in site:
                continue
        results.append({
            "variant": hit.get("_id", ""),
            "rsid": dbsnp.get("rsid", ""),
            "cosmic_id": cosmic.get("cosmic_id", ""),
            "tumor_site": cosmic.get("tumor_site", ""),
            "mut_freq": cosmic.get("mut_freq"),
            "cadd_phred": cadd.get("phred"),
            "clinical_significance": clinvar.get("clinical_significance", ""),
        })

    return _json.dumps({
        "gene": gene_name,
        "tumor_site_filter": tumor_site or "none",
        "total_matches": data.get("total", 0),
        "returned": len(results),
        "mutations": results,
    }, indent=2)


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
        chip_seq_factor = getattr(args, "chip_seq_factor", "SRR3082397")
        check_overlap = getattr(args, "check_overlap", True)
        top_n = getattr(args, "top_n", 3)
        return {
            "task": "plot_transcription_gradient",
            "gene_name": gene_name,
            "cell_line": cell_line,
            "chip_seq_factor": chip_seq_factor,
            "check_overlap": check_overlap,
            "top_n": top_n,
            "mode": mode,
            "notes": notes,
            "sequence": f"task=plot_transcription_gradient;gene={gene_name};cell_line={cell_line};chip_seq_factor={chip_seq_factor};top_n={top_n};check_overlap={str(check_overlap).lower()}",
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
    max_runtime_hours = getattr(args, "max_runtime_hours", 24)
    return {
        "task": "enhancerOpt",
        "gene_name": gene_name,
        "cell_line": cell_line,
        "center": center,
        "flanking_size": flanking_size,
        "iterations": iterations,
        "max_runtime_hours": max_runtime_hours,
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
                        choices=["resolve-gene", "resolve-cell-line", "resolve-snps", "resolve-snp-impact", "resolve-cancer-mutations", "list-models", "q1", "q2", "q3", "q4", "status", "result"])
    parser.add_argument("--query", help="Gene name/alias for resolve-gene; or cell line for resolve-cell-line")
    parser.add_argument("--region", help="Genomic region (e.g. chr1:207923720-207923920) for resolve-snps")
    parser.add_argument("--rsid", help="dbSNP rsID (e.g. rs1053802528) for resolve-snp-impact")
    parser.add_argument("--tumor-site", default="", help="Tumor site filter for resolve-cancer-mutations (e.g. lung, breast, pancreas)")
    parser.add_argument("--max-results", type=int, default=50, help="Max results (for resolve-snps or resolve-cancer-mutations)")
    parser.add_argument("--job-id", help="Job ID for status/result workflows")
    parser.add_argument("--gene-name", help="HGNC gene symbol")
    parser.add_argument("--cell-line", default="195")
    parser.add_argument("--mode", default="medium", choices=["fast", "medium", "high"])
    parser.add_argument("--notes", default="")
    parser.add_argument("--coordinate", help="Genomic coordinate (e.g. chr1:207923783-207923857)")
    parser.add_argument("--mutated-seq", help="Mutated DNA sequence (for Q3)")
    parser.add_argument("--ref", default="", help="Reference sequence (for Q3)")
    parser.add_argument("--tf", default="", help="Transcription factor (for Q3)")
    parser.add_argument("--chip-seq-factor", default="SRR3082397", help="ChIP-seq factor for peak overlap (for Q1)")
    parser.add_argument("--check-overlap", type=bool, default=True, help="Filter by ChIP-seq peak overlap (for Q1)")
    parser.add_argument("--top-n", type=int, default=3, help="Number of top enhancer candidates (for Q1)")
    parser.add_argument("--center", type=int, help="Center coordinate (for Q4)")
    parser.add_argument("--flanking-size", type=int, default=75, help="Flanking size in bp (for Q4)")
    parser.add_argument("--iterations", type=int, default=250, help="Optimization iterations (for Q4)")
    parser.add_argument("--max-runtime-hours", type=int, default=24, help="Maximum runtime in hours (for Q4)")

    args = parser.parse_args()

    if args.workflow == "resolve-gene":
        if not args.query:
            print(json.dumps({"error": "--query is required for resolve-gene"}))
            sys.exit(1)
        print(_resolve_gene(args.query))
        return

    if args.workflow == "resolve-cell-line":
        if not args.query:
            print(json.dumps({"error": "--query is required for resolve-cell-line"}))
            sys.exit(1)
        print(_resolve_cell_line(args.query))
        return

    if args.workflow == "list-models":
        models = [
            {
                "id": "borzoi_finetune_v1",
                "name": "Borzoi Fine-tune v1",
                "description": "Production model trained on ChIP-seq, Gro-seq, and RNA-seq data",
                "supportedWorkflows": ["q1_regulation", "q2_enhancer_importance", "q3_mutation_impact", "q4_enhancer_redesign"],
                "catalog": "samplefile_w_anno_for_chipseq_with6cols.csv",
                "cellLines": "785 cell lines from ChIP-seq/Gro-seq/RNA-seq experiments",
            },
            {
                "id": "borzoi_finetune_ccle_v1",
                "name": "Borzoi Fine-tune CCLE v1",
                "description": "CCLE-trained model covering 1019 cancer cell lines",
                "supportedWorkflows": ["q1_regulation", "q2_enhancer_importance", "q3_mutation_impact", "q4_enhancer_redesign"],
                "catalog": "samplefile_annotated_ccle_new.csv",
                "cellLines": "1019 cancer cell lines from CCLE",
            },
        ]
        print(json.dumps(models, indent=2))
        return

    if args.workflow == "resolve-cancer-mutations":
        if not args.gene_name:
            print(json.dumps({"error": "--gene-name is required for resolve-cancer-mutations"}))
            sys.exit(1)
        print(_resolve_cancer_mutations(args.gene_name, args.tumor_site or "", args.max_results or 20))
        return

    if args.workflow == "resolve-snps":
        if not args.region:
            print(json.dumps({"error": "--region is required for resolve-snps"}))
            sys.exit(1)
        print(_resolve_snps(args.region, args.max_results or 50))
        return

    if args.workflow == "resolve-snp-impact":
        if not args.rsid:
            print(json.dumps({"error": "--rsid is required for resolve-snp-impact"}))
            sys.exit(1)
        print(_resolve_snp_impact(args.rsid))
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
