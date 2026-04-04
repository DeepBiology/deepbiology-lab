from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from deepbiology import DeepBiologyClient
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

    workflow = WORKFLOW_MAP[args.workflow]
    client = DeepBiologyClient(api_key=api_key, base_url=base_url)
    inputs = build_inputs(args, workflow)

    job = client.submit_job(workflow=workflow, inputs=inputs)
    print(json.dumps({"submitted": job}, indent=2))

    if args.no_wait:
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deepbiology-lab", description="DeepBiology Lab CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    config_parser = subparsers.add_parser("config", help="Store or show CLI configuration")
    config_parser.add_argument("--api-key", help="DeepBiology API key")
    config_parser.add_argument("--base-url", help="Override API base URL")
    config_parser.add_argument("--show", action="store_true", help="Show current config")
    config_parser.set_defaults(func=cmd_config)

    run_parser = subparsers.add_parser("run", help="Run a DeepBiology Lab workflow")
    run_parser.add_argument("workflow", choices=sorted(WORKFLOW_MAP.keys()))
    run_parser.add_argument("--api-key", help="Override configured API key")
    run_parser.add_argument("--base-url", help="Override configured base URL")
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
    run_parser.add_argument("--no-wait", action="store_true")
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
