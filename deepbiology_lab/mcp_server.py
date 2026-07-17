"""
MCP (Model Context Protocol) server for DeepBiology Lab.

Exposes DeepBiology Lab workflows as MCP tools so LLM chatboxes
(Claude Desktop, VS Code Copilot, Cursor, etc.) can submit and
track research questions.

Usage:
    DEEPBIOLOGY_API_KEY=dbio_... deepbiology-lab-mcp

    # or using the shared CLI config:
    deepbiology-lab-mcp

Configuration (priority order):
    1. Environment variables: DEEPBIOLOGY_API_KEY, DEEPBIOLOGY_BASE_URL
    2. ~/.config/deepbiology-lab/config.json (same as CLI)
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Dict, Optional
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from deepbiology import (
    DEFAULT_ASSAY_TYPE,
    DEFAULT_MODEL_ID,
    DeepBiologyClient,
    annotate_variant as sdk_annotate_variant,
    find_variants as sdk_find_variants,
    list_models as sdk_list_models,
    resolve_cell_line as sdk_resolve_cell_line,
)
from deepbiology_lab.config import DEFAULT_BASE_URL, load_config

# ── MCP Server ─────────────────────────────────────────────────────

server = FastMCP("deepbiology-lab")


# ── Config Loading ─────────────────────────────────────────────────

@dataclass
class _Config:
    api_key: str
    base_url: str


def _load_config() -> _Config:
    """Load config from env vars first, then fall back to CLI config file."""
    api_key = os.environ.get("DEEPBIOLOGY_API_KEY") or ""
    base_url = os.environ.get("DEEPBIOLOGY_BASE_URL") or ""

    if not api_key:
        try:
            cfg = load_config()
            api_key = cfg.get("api_key") or ""
            base_url = base_url or cfg.get("base_url") or ""
        except Exception:
            pass

    if not api_key:
        raise RuntimeError(
            "No API key found. Set DEEPBIOLOGY_API_KEY environment variable "
            "or run 'deepbiology-lab config --api-key ...' first."
        )

    return _Config(
        api_key=api_key,
        base_url=base_url or DEFAULT_BASE_URL,
    )


def _get_client() -> DeepBiologyClient:
    cfg = _load_config()
    return DeepBiologyClient(api_key=cfg.api_key, base_url=cfg.base_url)


# ── Tool: resolve_gene ────────────────────────────────────────────

CURATED_ALIASES: Dict[str, str] = {
    # Common clinical / previous symbols
    "AML1": "RUNX1",
    "P53": "TP53",
    "C-MYC": "MYC",
    "CMYC": "MYC",
    "N-MYC": "MYCN",
    "NMYC": "MYCN",
    "L-MYC": "MYCL",
    "LMYC": "MYCL",
    "BCL-2": "BCL2",
    "BCL-6": "BCL6",
    "HER1": "EGFR",
    "HER2": "ERBB2",
    "ERBB1": "EGFR",
    "NEU": "ERBB2",
    "PD-L1": "CD274",
    "PDL1": "CD274",
    "PD-1": "PDCD1",
    "PD1": "PDCD1",
    "CTLA-4": "CTLA4",
    "CD152": "CTLA4",
    "CD20": "MS4A1",
    "CD45": "PTPRC",
    "VEGF": "VEGFA",
    "PDGF": "PDGFB",
    "TNFA": "TNF",
    "TNF-ALPHA": "TNF",
    "IL-2": "IL2",
    "IL-6": "IL6",
    "IL-10": "IL10",
    "IFN-GAMMA": "IFNG",
    "BETA-ACTIN": "ACTB",
    "HIF-1-ALPHA": "HIF1A",
    "HIF1-ALPHA": "HIF1A",
    "OCT4": "POU5F1",
    "OCT3/4": "POU5F1",
    "C-MET": "MET",
    "HGFR": "MET",
    "CD246": "ALK",
    "TRKA": "NTRK1",
    "TRKB": "NTRK2",
    "TRKC": "NTRK3",
    "C-RAF": "RAF1",
    "MMAC1": "PTEN",
    "PKB": "AKT1",
    "FRAP1": "MTOR",
    "P16": "CDKN2A",
    "P21": "CDKN1A",
    "CD95": "FAS",
    "BCL-XL": "BCL2L1",
    "CASPASE-3": "CASP3",
    "CASPASE-8": "CASP8",
    "CASPASE-9": "CASP9",
    "CD135": "FLT3",
    "C-KIT": "KIT",
    "CD117": "KIT",
    "CEBP-ALPHA": "CEBPA",
    "PU.1": "SPI1",
    "T-BET": "TBX21",
    "ROR-GAMMA-T": "RORC",
    "RORGT": "RORC",
    "TTF1": "NKX2-1",
    "TITF1": "NKX2-1",
    "BSAP": "PAX5",
    "IKAROS": "IKZF1",
    "E2A": "TCF3",
    "E2-2": "TCF4",
    "PPAR-GAMMA": "PPARG",
    "TAN1": "NOTCH1",
    "BETA-CATENIN": "CTNNB1",
    "C-FMS": "CSF1R",
    "C-SRC": "SRC",
    "TEL": "ETV6",
    "ETO": "RUNX1T1",
    "CAN": "NUP214",
    "EVI1": "MECOM",
    "CD133": "PROM1",
    "CD90": "THY1",
    "CD123": "IL3RA",
    "CD56": "NCAM1",
    "CD326": "EPCAM",
    "CD227": "MUC1",
    "CEA": "CEACAM5",
    "PSA": "KLK3",
    "PSMA": "FOLH1",
    "NY-ESO-1": "CTAG1B",
    "MART1": "MLANA",
    "GP100": "PMEL",
    "CYCLIND1": "CCND1",
    "CYCLIND2": "CCND2",
    "CYCLIND3": "CCND3",
    "CYCLINE1": "CCNE1",
    "CYCLINA2": "CCNA2",
    "CYCLINB1": "CCNB1",
    "CYCLINH": "CCNH",
}


@server.tool(description="Resolve a gene name, alias, or description to its official HGNC symbol")
def resolve_gene(query: str) -> str:
    """
    Resolve a gene reference to its canonical HGNC gene symbol.

    Tries, in order:
      1. A curated alias map (common clinical names like "HER2" -> "ERBB2")
      2. The mygene.info public API (covers ~all human genes)

    Args:
        query: Gene name, alias, or description (e.g. "cyclin D1", "HER2", "p53", "BRCA1")

    Returns:
        JSON object with matched status, canonical symbol, and resolution method.
    """
    import re

    normalized = re.sub(r"[^A-Z0-9]", "", query.upper().strip())

    if not normalized:
        return json.dumps({"matched": False, "canonicalName": None, "resolvedVia": "empty_query"})

    # 1. Curated alias map
    if normalized in CURATED_ALIASES:
        canonical = CURATED_ALIASES[normalized]
        return json.dumps({
            "matched": True,
            "canonicalName": canonical,
            "query": canonical,
            "resolvedVia": "curated_alias",
        })

    # 2. mygene.info API
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
            canonical = hit["symbol"]
            return json.dumps({
                "matched": True,
                "canonicalName": canonical,
                "query": canonical,
                "resolvedVia": "mygene_api",
                "mygeneInfo": {
                    "symbol": canonical,
                    "name": hit.get("name", ""),
                    "entrezgene": str(hit.get("entrezgene", "")),
                },
            })
    except Exception:
        pass

    return json.dumps({
        "matched": False,
        "canonicalName": None,
        "query": query,
        "resolvedVia": "not_found",
    })


# ── Tool: resolve_cell_line ───────────────────────────────────────

@server.tool(description="Resolve a cell-line name to the output-channel index for a DeepBiology model and assay")
def resolve_cell_line(
    cell_name: str,
    model_id: str = DEFAULT_MODEL_ID,
    assay_type: str = DEFAULT_ASSAY_TYPE,
) -> str:
    """
    Resolve a cell line against a model metadata catalog. Resolution is
    model- and assay-specific; RNASeq is the default assay.

    Args:
        cell_name: Cell line name (e.g. "kasumi-1", "SK-MEL-28", "K562")
        model_id: DeepBiology model catalog identifier
        assay_type: Assay represented by the requested output channel

    Returns:
        JSON with canonical name, matched catalog row, and numeric channel.
    """
    return json.dumps(
        sdk_resolve_cell_line(
            cell_name,
            model_id=model_id,
            assay_type=assay_type,
        ),
        indent=2,
    )


# ── Tools: variants ───────────────────────────────────────────────

@server.tool(description="Find known Ensembl variants within a GRCh38/hg38 or GRCh37/hg19 genomic region")
def find_variants(
    region: str,
    assembly: str = "GRCh38",
    limit: int = 50,
) -> str:
    """Query regional variants through the shared DeepBiology SDK."""
    return json.dumps(
        sdk_find_variants(region, assembly=assembly, limit=limit),
        indent=2,
    )


@server.tool(description="Annotate a dbSNP rsID with Ensembl VEP transcript, regulatory, and intergenic consequences")
def annotate_variant(variant_id: str, assembly: str = "GRCh38") -> str:
    """Run Ensembl VEP annotation through the shared DeepBiology SDK."""
    return json.dumps(
        sdk_annotate_variant(variant_id, assembly=assembly),
        indent=2,
    )


@server.tool(description="Deprecated alias for find_variants; query known variants in a genomic region")
def resolve_snps(
    region: str,
    genome_build: str = "hg38",
    max_results: int = 50,
) -> str:
    """Compatibility alias retained for existing MCP clients."""
    return find_variants(region=region, assembly=genome_build, limit=max_results)


@server.tool(description="Deprecated alias for annotate_variant; annotate an rsID with Ensembl VEP")
def resolve_snp_impact(rsid: str, genome_build: str = "hg38") -> str:
    """Compatibility alias retained for existing MCP clients."""
    return annotate_variant(variant_id=rsid, assembly=genome_build)


# ── Tool: resolve_cancer_mutations ────────────────────────────────

@server.tool(description="Query known cancer (somatic) mutations for a gene via myvariant.info (COSMIC + ClinVar + CADD)")
def resolve_cancer_mutations(
    gene_name: str,
    tumor_site: str = "",
    max_results: int = 20,
) -> str:
    """
    Query known somatic/cancer mutations for a gene using myvariant.info,
    which aggregates data from COSMIC, ClinVar, and CADD.

    Args:
        gene_name: HGNC gene symbol (e.g. "TP53", "KRAS", "BRAF", "EGFR")
        tumor_site: Optional tumor site filter (e.g. "lung", "breast", "pancreas", "AML")
        max_results: Maximum number of results (default 20, max 100)

    Returns:
        JSON array of mutations with COSMIC IDs, tumor sites, CADD scores, and clinical significance.
    """
    import json as _json
    import urllib.request
    import urllib.parse

    query = urllib.parse.quote(gene_name)
    fields = "cosmic,cadd,clinvar,dbsnp,dbnsfp"
    url = (
        f"https://myvariant.info/v1/query"
        f"?q={query}&fields={fields}&species=human"
        f"&size={min(max_results, 100)}"
    )

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read())
    except Exception as e:
        return _json.dumps({"error": f"Failed to query myvariant.info: {str(e)}", "gene": gene_name})

    results = []
    for hit in data.get("hits", []):
        cosmic = hit.get("cosmic") or {}
        cadd = hit.get("cadd") or {}
        dbsnp = hit.get("dbsnp") or {}
        clinvar = hit.get("clinvar") or {}

        # Filter by tumor site if specified
        if tumor_site:
            site = (cosmic.get("tumor_site") or "").lower()
            if tumor_site.lower() not in site:
                continue

        entry = {
            "variant": hit.get("_id", ""),
            "rsid": dbsnp.get("rsid", ""),
            "cosmic_id": cosmic.get("cosmic_id", ""),
            "tumor_site": cosmic.get("tumor_site", ""),
            "mut_freq": cosmic.get("mut_freq"),
            "cadd_phred": cadd.get("phred"),
            "cadd_score": cadd.get("consscore"),
        }

        if clinvar:
            entry["clinical_significance"] = clinvar.get("clinical_significance", "")

        results.append(entry)

    return _json.dumps({
        "gene": gene_name,
        "tumor_site_filter": tumor_site or "none",
        "total_matches": data.get("total", 0),
        "returned": len(results),
        "mutations": results,
    }, indent=2)


# ── Shared: Resolve channels + submit ─────────────────────────────

def _resolve_workflow_cell(
    cell_line: str,
    cell_name: str,
    model_id: str,
    assay_type: str,
) -> tuple[str, Optional[Dict[str, Any]]]:
    """Resolve a named cell or preserve an explicit output-channel index."""
    if not cell_name:
        return str(cell_line), None
    resolution = sdk_resolve_cell_line(
        cell_name,
        model_id=model_id,
        assay_type=assay_type,
    )
    return str(resolution["cellLineIndex"]), resolution


def _submit(
    workflow_key: str,
    inputs: Dict[str, Any],
    cell_line_resolution: Optional[Dict[str, Any]] = None,
) -> str:
    client = _get_client()
    job = client.submit_job(workflow=workflow_key, inputs=inputs)
    response = {
        "jobId": job.get("jobId"),
        "status": job.get("status", "submitted"),
        "submissionId": job.get("submissionId"),
        "creditCost": job.get("creditCost"),
        "costUsd": job.get("costUsd"),
        "createdAt": job.get("createdAt"),
        "question": workflow_key,
        "task": inputs.get("task"),
        "message": "Job submitted successfully. Use get_job_status and get_job_result to track progress.",
    }
    if cell_line_resolution:
        response["cellLineResolution"] = cell_line_resolution
    return json.dumps(response, indent=2)


# ── Tool: submit_q1_regulation ────────────────────────────────────

@server.tool(description="Submit Q1: Plot transcription gradient for a gene across a cell line")
def submit_q1_regulation(
    gene_name: str,
    cell_line: str = "195",
    cell_name: str = "",
    model_id: str = DEFAULT_MODEL_ID,
    assay_type: str = DEFAULT_ASSAY_TYPE,
    mode: str = "medium",
    chip_seq_factor: str = "SRR3082397",
    check_overlap: bool = True,
    top_n: int = 3,
    notes: str = "",
) -> str:
    """
    Submit a Q1 (regulation) workflow — plots transcription gradient
    for a gene across genomic coordinates in a given cell line.

    The `chip_seq_factor` and `check_overlap` parameters control enhancer
    candidate filtering. `check_overlap=True` (default) limits results to
    enhancers that overlap with ChIP-seq peaks for the given factor.
    The default factor SRR3082397 is specific to AML cells — set
    `check_overlap=False` for non-AML cell lines.

    Args:
        gene_name: Official HGNC gene symbol (e.g. "CD34", "CCND1", "MYC")
        cell_line: Explicit output-channel index (default "195")
        cell_name: Cell-line name to resolve instead of using cell_line
        model_id: Model catalog used for cell-name resolution
        assay_type: Assay used for cell-name resolution (default RNASeq)
        mode: Analysis mode ("fast", "medium", or "high")
        chip_seq_factor: ChIP-seq factor for peak overlap filtering (default "SRR3082397"; AML-specific)
        check_overlap: Filter enhancers by ChIP-seq peak overlap (default True; set False for non-AML cells)
        top_n: Number of top enhancer candidates to return (default 3)
        notes: Optional notes or description

    Returns:
        JSON with job ID for tracking.
    """
    resolved_cell_line, resolution = _resolve_workflow_cell(
        cell_line, cell_name, model_id, assay_type
    )
    sequence = (
        f"task=plot_transcription_gradient;gene={gene_name};cell_line={resolved_cell_line};"
        f"chip_seq_factor={chip_seq_factor};top_n={top_n};check_overlap={str(check_overlap).lower()}"
    )
    return _submit("q1_regulation", {
        "task": "plot_transcription_gradient",
        "gene_name": gene_name,
        "cell_line": resolved_cell_line,
        "chip_seq_factor": chip_seq_factor,
        "check_overlap": check_overlap,
        "top_n": top_n,
        "mode": mode,
        "notes": notes or f"Submitted via MCP: Q1 regulation for {gene_name}",
        "sequence": sequence,
    }, resolution)


# ── Tool: submit_q2_enhancer_importance ───────────────────────────

@server.tool(description="Submit Q2: Mutation importance scan at a genomic coordinate")
def submit_q2_enhancer_importance(
    gene_name: str,
    cell_line: str = "195",
    cell_name: str = "",
    model_id: str = DEFAULT_MODEL_ID,
    assay_type: str = DEFAULT_ASSAY_TYPE,
    coordinate: str = "chr1:207923783-207923857",
    mode: str = "medium",
    notes: str = "",
) -> str:
    """
    Submit a Q2 (enhancer importance) workflow — scans mutation
    importance at a given genomic coordinate for a gene and cell line.

    Args:
        gene_name: Official HGNC gene symbol
        cell_line: Explicit output-channel index (default "195")
        cell_name: Cell-line name to resolve instead of using cell_line
        model_id: Model catalog used for cell-name resolution
        assay_type: Assay used for cell-name resolution (default RNASeq)
        coordinate: Genomic coordinate (e.g. "chr1:207923783-207923857")
        mode: Analysis mode ("fast", "medium", or "high")
        notes: Optional notes or description

    Returns:
        JSON with job ID for tracking.
    """
    resolved_cell_line, resolution = _resolve_workflow_cell(
        cell_line, cell_name, model_id, assay_type
    )
    sequence = f"task=mutation;coordinate={coordinate};mutatedSeq=N;gene={gene_name};cell_line={resolved_cell_line}"
    return _submit("q2_enhancer_importance", {
        "task": "mutation",
        "gene_name": gene_name,
        "cell_line": resolved_cell_line,
        "coordinate": coordinate,
        "mutatedSeq": "N",
        "loci": coordinate,
        "mode": mode,
        "notes": notes or f"Submitted via MCP: Q2 enhancer importance for {gene_name} at {coordinate}",
        "sequence": sequence,
    }, resolution)


# ── Tool: submit_q3_mutation_impact ───────────────────────────────

@server.tool(description="Submit Q3: Test a specific mutated sequence at a coordinate")
def submit_q3_mutation_impact(
    gene_name: str,
    coordinate: str,
    mutated_seq: str,
    cell_line: str = "195",
    cell_name: str = "",
    model_id: str = DEFAULT_MODEL_ID,
    assay_type: str = DEFAULT_ASSAY_TYPE,
    ref: str = "",
    tf: str = "",
    mode: str = "medium",
    notes: str = "",
) -> str:
    """
    Submit a Q3 (mutation impact) workflow — evaluates the effect
    of a specific mutated sequence at a given coordinate.

    Args:
        gene_name: Official HGNC gene symbol
        coordinate: Genomic coordinate (e.g. "chr1:207923783-207923857")
        mutated_seq: The mutated DNA sequence
        cell_line: Explicit output-channel index (default "195")
        cell_name: Cell-line name to resolve instead of using cell_line
        model_id: Model catalog used for cell-name resolution
        assay_type: Assay used for cell-name resolution (default RNASeq)
        ref: Optional reference sequence
        tf: Optional transcription factor to focus on
        mode: Analysis mode ("fast", "medium", or "high")
        notes: Optional notes or description

    Returns:
        JSON with job ID for tracking.
    """
    resolved_cell_line, resolution = _resolve_workflow_cell(
        cell_line, cell_name, model_id, assay_type
    )
    return _submit("q3_mutation_impact", {
        "task": "mutation",
        "gene_name": gene_name,
        "cell_line": resolved_cell_line,
        "coordinate": coordinate,
        "mutatedSeq": mutated_seq,
        "mut": mutated_seq,
        "loci": coordinate,
        "ref": ref,
        "tf": tf,
        "mode": mode,
        "notes": notes or f"Submitted via MCP: Q3 mutation impact for {gene_name} at {coordinate}",
        "sequence": mutated_seq,
    }, resolution)


# ── Tool: submit_q4_enhancer_redesign ─────────────────────────────

@server.tool(description="Submit Q4: Enhancer optimization with AI-driven redesign")
def submit_q4_enhancer_redesign(
    gene_name: str,
    cell_line: str = "195",
    cell_name: str = "",
    model_id: str = DEFAULT_MODEL_ID,
    assay_type: str = DEFAULT_ASSAY_TYPE,
    center: int = 207923820,
    flanking_size: int = 75,
    iterations: int = 250,
    max_runtime_hours: int = 24,
    mode: str = "medium",
    notes: str = "",
) -> str:
    """
    Submit a Q4 (enhancer redesign) workflow — AI-driven enhancer
    sequence optimization for a gene and cell line.

    Args:
        gene_name: Official HGNC gene symbol
        cell_line: Explicit output-channel index (default "195")
        cell_name: Cell-line name to resolve instead of using cell_line
        model_id: Model catalog used for cell-name resolution
        assay_type: Assay used for cell-name resolution (default RNASeq)
        center: Center coordinate for the enhancer region (default 207923820)
        flanking_size: Flanking size in base pairs (default 75)
        iterations: Number of optimization iterations (default 250)
        max_runtime_hours: Maximum runtime in hours (default 24)
        mode: Analysis mode ("fast", "medium", or "high")
        notes: Optional notes or description

    Returns:
        JSON with job ID for tracking.
    """
    resolved_cell_line, resolution = _resolve_workflow_cell(
        cell_line, cell_name, model_id, assay_type
    )
    sequence = (
        f"task=enhancerOpt;center={center};flanking_size={flanking_size};"
        f"iterations={iterations};gene={gene_name};cell_line={resolved_cell_line}"
    )
    return _submit("q4_enhancer_redesign", {
        "task": "enhancerOpt",
        "gene_name": gene_name,
        "cell_line": resolved_cell_line,
        "center": center,
        "flanking_size": flanking_size,
        "iterations": iterations,
        "max_runtime_hours": max_runtime_hours,
        "mode": mode,
        "notes": notes or f"Submitted via MCP: Q4 enhancer redesign for {gene_name}",
        "sequence": sequence,
    }, resolution)


# ── Tool: get_job_status ──────────────────────────────────────────

@server.tool(description="Check the current status of a submitted job")
def get_job_status(job_id: str) -> str:
    """
    Check the current processing status of a job.

    Args:
        job_id: The job ID returned by a submit_* tool

    Returns:
        JSON with current status ("submitted", "processing", "completed",
        "failed", or "cancelled") and timestamps.
    """
    client = _get_client()
    job = client.get_job(job_id)
    return json.dumps({
        "jobId": job.get("jobId"),
        "status": job.get("status"),
        "submissionId": job.get("submissionId"),
        "createdAt": job.get("createdAt"),
        "updatedAt": job.get("updatedAt"),
        "errorMessage": job.get("errorMessage"),
    }, indent=2)


# ── Tool: get_job_result ──────────────────────────────────────────

@server.tool(description="Retrieve the completed result of a job, including data fields, tables, and image URL")
def get_job_result(job_id: str) -> str:
    """
    Retrieve the clean result for a completed job.

    Returns data fields, tables, enhancer table, optimized sequence,
    and image download URL if available.

    Args:
        job_id: The job ID returned by a submit_* tool

    Returns:
        JSON with the full result payload.
    """
    client = _get_client()
    raw = client.get_job_result(job_id)
    clean = client.format_clean_result(raw)
    return json.dumps(clean, indent=2, default=str)


@server.tool(description="Wait for a job and save its JSON result and optional image to local files")
def download_job_result(
    job_id: str,
    output_directory: str = "deepbiology-experiments",
    run_name: Optional[str] = None,
    raw: bool = False,
    download_image: bool = False,
    image_path: Optional[str] = None,
    poll_seconds: int = 5,
    timeout_seconds: int = 1800,
) -> str:
    """Persist completed job artifacts on the machine running this MCP server.

    By default, writes the result to
    ``deepbiology-experiments/run_<jobId>/result_<jobId>.json``.
    The optional image uses ``result_<jobId>.png`` in the same run directory.
    """
    client = _get_client()
    downloaded = client.download_job_result(
        job_id,
        output_directory=output_directory,
        run_name=run_name,
        raw=raw,
        download_image=download_image,
        image_path=image_path,
        poll_seconds=poll_seconds,
        timeout_seconds=timeout_seconds,
    )
    artifact_summary = {
        key: value for key, value in downloaded.items() if key != "result"
    }
    return json.dumps(artifact_summary, indent=2, default=str)


# ── Tool: list_models ─────────────────────────────────────────────

@server.tool(description="List available DeepBiology Lab models and their supported workflows")
def list_models() -> str:
    """
    List the available analysis models and what workflows each supports.

    Returns:
        JSON array of models with id, name, description, and supported workflows.
    """
    return json.dumps(sdk_list_models(), indent=2)


# ── Entry Point ───────────────────────────────────────────────────

def main() -> None:
    """Run the MCP server over stdio transport."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
