from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from deepbiology import (
    DEFAULT_ASSAY_TYPE,
    DEFAULT_MODEL_ID,
    MODEL_CATALOGS,
    DeepBiologyClient,
    DeepBiologyError,
    annotate_variant,
    fetch_model_catalog,
    find_variants,
    list_models,
    resolve_cell_line,
)
from .config import DEFAULT_BASE_URL, CONFIG_PATH, load_config, save_config

WORKFLOW_MAP = {
    "q1": "q1_regulation",
    "q2": "q2_enhancer_importance",
    "q3": "q3_mutation_impact",
    "q4": "q4_enhancer_redesign",
}


def build_inputs(args: argparse.Namespace, workflow: str) -> Dict[str, Any]:
    gene_name = args.gene_name
    cell_line = args.cell_line
    mode = args.mode
    notes = args.notes

    if workflow == "q1_regulation":
        sequence = args.sequence or f"task=plot_transcription_gradient;gene={gene_name};cell_line={cell_line}"
        return {
            "task": "plot_transcription_gradient",
            "gene_name": gene_name,
            "cell_line": cell_line,
            "mode": mode,
            "notes": notes or "Submitted from deepbiology-lab CLI: Q1",
            "sequence": sequence,
        }

    if workflow == "q2_enhancer_importance":
        coordinate = args.coordinate
        sequence = args.sequence or f"task=mutation;coordinate={coordinate};mutatedSeq=N;gene={gene_name};cell_line={cell_line}"
        return {
            "task": "mutation",
            "gene_name": gene_name,
            "cell_line": cell_line,
            "coordinate": coordinate,
            "mutatedSeq": "N",
            "loci": coordinate,
            "mode": mode,
            "notes": notes or "Submitted from deepbiology-lab CLI: Q2",
            "sequence": sequence,
        }

    if workflow == "q3_mutation_impact":
        coordinate = args.coordinate
        mutated_seq = args.mutated_seq
        sequence = args.sequence or mutated_seq
        return {
            "task": "mutation",
            "gene_name": gene_name,
            "cell_line": cell_line,
            "coordinate": coordinate,
            "mutatedSeq": mutated_seq,
            "mut": mutated_seq,
            "loci": coordinate,
            "ref": args.ref,
            "tf": args.tf,
            "cellline": cell_line,
            "mode": mode,
            "notes": notes or "Submitted from deepbiology-lab CLI: Q3",
            "sequence": sequence,
        }

    center = args.center
    flanking_size = args.flanking_size
    iterations = args.iterations
    sequence = args.sequence or (
        f"task=enhancerOpt;center={center};flanking_size={flanking_size};iterations={iterations};gene={gene_name};cell_line={cell_line}"
    )
    return {
        "task": "enhancerOpt",
        "gene_name": gene_name,
        "cell_line": cell_line,
        "center": center,
        "flanking_size": flanking_size,
        "iterations": iterations,
        "mode": mode,
        "notes": notes or "Submitted from deepbiology-lab CLI: Q4",
        "sequence": sequence,
    }


def cmd_config(args: argparse.Namespace) -> int:
    if args.show:
        print(json.dumps(load_config(), indent=2))
        return 0

    if not args.api_key and not args.base_url:
        print(f"Config file: {CONFIG_PATH}")
        print(json.dumps(load_config(), indent=2))
        return 0

    config = save_config(api_key=args.api_key, base_url=args.base_url)
    print(f"Saved config to {CONFIG_PATH}")
    print(json.dumps({"api_key": "***configured***" if config.get("api_key") else None, "base_url": config.get("base_url")}, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config()
    api_key = args.api_key or config.get("api_key")
    base_url = args.base_url or config.get("base_url") or DEFAULT_BASE_URL

    if not api_key:
        raise SystemExit("Missing API key. Run 'deepbiology-lab config --api-key ...' or pass --api-key.")

    # Resolve --cell-name to an index if provided
    if args.cell_name:
        try:
            resolution = resolve_cell_line(args.cell_name, args.model, args.assay_type)
        except DeepBiologyError as exc:
            raise SystemExit(str(exc)) from exc
        print(
            "Resolved '{}' → cell-line {} (assay: {}, model: {})".format(
                args.cell_name,
                resolution["cellLineIndex"],
                resolution["assayType"],
                resolution["modelId"],
            ),
            file=sys.stderr,
        )
        args.cell_line = str(resolution["cellLineIndex"])

    workflow = WORKFLOW_MAP[args.workflow]
    client = DeepBiologyClient(api_key=api_key, base_url=base_url)
    inputs = build_inputs(args, workflow)

    job = client.submit_job(workflow=workflow, inputs=inputs)
    print(json.dumps({"submitted": job}, indent=2))

    if not args.wait:
        return 0

    client.wait_for_job(job["jobId"], poll_seconds=args.poll_seconds, timeout_seconds=args.timeout_seconds)
    normalized = client.get_job_result(job["jobId"])
    clean = client.format_clean_result(normalized)

    if args.download_image:
        saved = client.download_result_image(job["jobId"], args.image_path)
        clean["downloadedImage"] = saved

    if args.raw:
        print(json.dumps(normalized, indent=2))
    else:
        print(json.dumps(clean, indent=2))
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    """Download result for a previously submitted job (e.g. submitted with --no-wait)."""
    config = load_config()
    api_key = args.api_key or config.get("api_key")
    base_url = args.base_url or config.get("base_url") or DEFAULT_BASE_URL

    if not api_key:
        raise SystemExit("Missing API key. Run 'deepbiology-lab config --api-key ...' or pass --api-key.")

    client = DeepBiologyClient(api_key=api_key, base_url=base_url)
    job_id = args.job_id

    print(f"Waiting for job {job_id}...", file=sys.stderr)
    downloaded = client.download_job_result(
        job_id,
        output_directory=args.output or "deepbiology-experiments",
        run_name=args.run_name,
        raw=args.raw,
        download_image=args.download_image,
        image_path=args.image_path,
        poll_seconds=args.poll_seconds,
        timeout_seconds=args.timeout_seconds,
    )
    print(f"Job {job_id} completed.", file=sys.stderr)
    print(f"Result saved to {downloaded['resultFile']}", file=sys.stderr)
    if downloaded["imageFile"]:
        print(f"Image saved to {downloaded['imageFile']}", file=sys.stderr)

    # Also print the result to stdout for piping
    print(json.dumps(downloaded["result"], indent=2))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List available models and optionally show metadata catalog."""
    print(f"{'Model ID':<30} {'Label':<50} {'Endpoint':<15}")
    print("-" * 95)
    for model in list_models():
        print(f"{model['id']:<30} {model['label']:<50} {model['runpodEndpointKey']:<15}")

    if args.model:
        print(f"\nMetadata catalog for {args.model}:")
        try:
            rows = fetch_model_catalog(args.model)
        except DeepBiologyError as exc:
            raise SystemExit(str(exc)) from exc
        print(f"  URL: {MODEL_CATALOGS[args.model]['metadata_url']}")
        if not rows:
            print("  (empty catalog)")
            return 0
        headers = list(rows[0].keys())
        print("  Columns:", ", ".join(headers))
        print(f"  Rows: {len(rows)}")
        # Print first 20 rows as compact table
        print()
        col_widths = {h: max(len(h), 10) for h in headers}
        for row in rows[:20]:
            for h in headers:
                col_widths[h] = max(col_widths[h], len(str(row.get(h, ""))) + 1)
        header_line = "  " + " | ".join(h.ljust(col_widths[h]) for h in headers)
        print(header_line)
        print("  " + "-" * (len(header_line) - 2))
        for row in rows[:20]:
            print("  " + " | ".join(str(row.get(h, "")).ljust(col_widths[h]) for h in headers))
        if len(rows) > 20:
            print(f"  ... and {len(rows) - 20} more rows")
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    """Resolve a cell line name to its output channel index for a given model."""
    try:
        resolution = resolve_cell_line(args.cell_line_name, args.model, args.assay_type)
    except DeepBiologyError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(resolution, indent=2))
    return 0


def cmd_snps(args: argparse.Namespace) -> int:
    """Find regional variants or annotate one rsID through the shared SDK."""
    try:
        if args.snp_command == "region":
            result = find_variants(
                args.region,
                assembly=args.assembly,
                limit=args.max_results,
            )
        else:
            result = annotate_variant(args.rsid, assembly=args.assembly)
    except DeepBiologyError as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(result, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deepbiology-lab", description="DeepBiology Lab CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    config_parser = subparsers.add_parser("config", help="Store or show CLI configuration")
    config_parser.add_argument("--api-key", help="DeepBiology API key")
    config_parser.add_argument("--base-url", help="Override API base URL")
    config_parser.add_argument("--show", action="store_true", help="Show current config")
    config_parser.set_defaults(func=cmd_config)

    list_parser = subparsers.add_parser("list", help="List available models and optionally show metadata catalog")
    list_parser.add_argument("--model", help="Model ID to show metadata catalog for")
    list_parser.set_defaults(func=cmd_list)

    download_parser = subparsers.add_parser("download", help="Download result for a previously submitted job by ID")
    download_parser.add_argument("job_id", help="Job ID (e.g. dbio_abc123)")
    download_parser.add_argument("--api-key", help="Override configured API key")
    download_parser.add_argument("--base-url", help="Override configured base URL")
    download_parser.add_argument("--output", help="Parent output directory (default: deepbiology-experiments)")
    download_parser.add_argument("--run-name", help="Subfolder name for this run (default: run_<jobId>)")
    download_parser.add_argument("--raw", action="store_true", help="Save raw normalized API result instead of clean result")
    download_parser.add_argument("--download-image", action="store_true", help="Also download the result image")
    download_parser.add_argument("--image-path", help="Image output path (overrides default: <run_dir>/result_<jobId>.png)")
    download_parser.add_argument("--poll-seconds", type=int, default=5, help="Polling interval when waiting (default: 5)")
    download_parser.add_argument("--timeout-seconds", type=int, default=1800, help="Max wait time in seconds (default: 1800)")
    download_parser.set_defaults(func=cmd_download)

    resolve_parser = subparsers.add_parser("resolve", help="Resolve a cell line name to its output channel index")
    resolve_parser.add_argument("cell_line_name", help="Cell line name to search (e.g. MCF7, KASUMI1)")
    resolve_parser.add_argument("--model", default=DEFAULT_MODEL_ID, help=f"Model ID to resolve against (default: {DEFAULT_MODEL_ID})")
    resolve_parser.add_argument("--assay-type", default=DEFAULT_ASSAY_TYPE, help=f"Assay type to resolve (default: {DEFAULT_ASSAY_TYPE})")
    resolve_parser.set_defaults(func=cmd_resolve)

    snps_parser = subparsers.add_parser("snps", help="Find regional variants or annotate a dbSNP rsID")
    snps_subparsers = snps_parser.add_subparsers(dest="snp_command", required=True)
    snps_region = snps_subparsers.add_parser("region", help="Find known variants in a genomic region")
    snps_region.add_argument("region", help="Region such as chr1:207923720-207923920")
    snps_region.add_argument("--assembly", default="GRCh38", help="Genome assembly (default: GRCh38)")
    snps_region.add_argument("--max-results", type=int, default=50, help="Maximum records to return (1-200)")
    snps_region.set_defaults(func=cmd_snps)
    snps_impact = snps_subparsers.add_parser("impact", help="Annotate a dbSNP rsID with Ensembl VEP")
    snps_impact.add_argument("rsid", help="dbSNP rsID such as rs1053802528")
    snps_impact.add_argument("--assembly", default="GRCh38", help="Genome assembly (default: GRCh38)")
    snps_impact.set_defaults(func=cmd_snps)

    run_parser = subparsers.add_parser("run", help="Run a DeepBiology Lab workflow")
    run_parser.add_argument("workflow", choices=sorted(WORKFLOW_MAP.keys()))
    run_parser.add_argument("--api-key", help="Override configured API key")
    run_parser.add_argument("--base-url", help="Override configured base URL")
    run_parser.add_argument("--model", default=DEFAULT_MODEL_ID, help=f"Model ID for cell-line resolution (default: {DEFAULT_MODEL_ID})")
    run_parser.add_argument("--assay-type", default=DEFAULT_ASSAY_TYPE, help=f"Assay type to filter cell-line resolution (default: {DEFAULT_ASSAY_TYPE})")
    run_parser.add_argument("--cell-name", help="Cell line name to resolve (e.g. KASUMI1, MCF7) — overrides --cell-line")
    run_parser.add_argument("--gene-name", default="CD34")
    run_parser.add_argument("--cell-line", default="195")
    run_parser.add_argument("--mode", default="medium")
    run_parser.add_argument("--notes", default="")
    run_parser.add_argument("--sequence", default="")
    run_parser.add_argument("--coordinate", default="chr1:207923783-207923857")
    run_parser.add_argument("--mutated-seq", default="ATGGCCATGGCCATGGCCATGGCCATGGCC")
    run_parser.add_argument("--ref", default="")
    run_parser.add_argument("--tf", default="")
    run_parser.add_argument("--center", type=int, default=207923820)
    run_parser.add_argument("--flanking-size", type=int, default=75)
    run_parser.add_argument("--iterations", type=int, default=250)
    run_parser.add_argument("--poll-seconds", type=int, default=5)
    run_parser.add_argument("--timeout-seconds", type=int, default=1800)
    run_parser.add_argument("--wait", action="store_true", help="Wait for job completion before returning (default: submit and return immediately)")
    run_parser.add_argument("--download-image", action="store_true")
    run_parser.add_argument("--image-path", default="result.png")
    run_parser.add_argument("--json", action="store_true", help="Print clean result as JSON (default behavior)")
    run_parser.add_argument("--raw", action="store_true", help="Print normalized raw API result instead of clean result")
    run_parser.set_defaults(func=cmd_run)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
