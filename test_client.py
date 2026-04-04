import argparse
import os
from deepbiology import DeepBiologyClient

DEFAULT_BASE_URL = "https://us-central1-deepbiology-471514.cloudfunctions.net"
WORKFLOW_MAP = {
    "q1": "q1_regulation",
    "q2": "q2_enhancer_importance",
    "q3": "q3_mutation_impact",
    "q4": "q4_enhancer_redesign",
    "q1_regulation": "q1_regulation",
    "q2_enhancer_importance": "q2_enhancer_importance",
    "q3_mutation_impact": "q3_mutation_impact",
    "q4_enhancer_redesign": "q4_enhancer_redesign",
}


def build_inputs(args, workflow):
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
            "notes": notes or "Python client test: Q1",
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
            "notes": notes or "Python client test: Q2",
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
            "notes": notes or "Python client test: Q3",
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
        "notes": notes or "Python client test: Q4",
        "sequence": sequence,
    }


def main():
    parser = argparse.ArgumentParser(description="DeepBiology Python client test script")
    parser.add_argument("workflow", choices=sorted(WORKFLOW_MAP.keys()), help="Workflow to run: q1, q2, q3, q4")
    parser.add_argument("--api-key", default=os.environ.get("DEEPBIOLOGY_API_KEY"), help="DeepBiology API key")
    parser.add_argument("--base-url", default=os.environ.get("DEEPBIOLOGY_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--gene-name", default="CD34")
    parser.add_argument("--cell-line", default="195")
    parser.add_argument("--mode", default="medium")
    parser.add_argument("--notes", default="")
    parser.add_argument("--sequence", default="")
    parser.add_argument("--coordinate", default="chr1:207923783-207923857")
    parser.add_argument("--mutated-seq", default="ATGGCCATGGCCATGGCCATGGCCATGGCC")
    parser.add_argument("--ref", default="")
    parser.add_argument("--tf", default="")
    parser.add_argument("--center", type=int, default=207923820)
    parser.add_argument("--flanking-size", type=int, default=75)
    parser.add_argument("--iterations", type=int, default=250)
    parser.add_argument("--poll-seconds", type=int, default=5)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--download-image", action="store_true")
    parser.add_argument("--image-path", default="result.png")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Missing API key. Pass --api-key or set DEEPBIOLOGY_API_KEY.")

    workflow = WORKFLOW_MAP[args.workflow]
    client = DeepBiologyClient(api_key=args.api_key, base_url=args.base_url)
    inputs = build_inputs(args, workflow)

    job = client.submit_job(workflow=workflow, inputs=inputs)
    print("Submitted:", job)

    job_id = job["jobId"]
    status = client.wait_for_job(job_id, poll_seconds=args.poll_seconds, timeout_seconds=args.timeout_seconds)
    print("Final status:", status)

    result = client.get_job_result(job_id)
    clean_result = client.get_clean_result(job_id)
    print("Normalized result:", result)
    print("Normalized result keys:", result.keys())
    print("Canonical result keys:", (result.get("result") or {}).keys())
    print("Clean result:", clean_result)

    if args.download_image:
        saved = client.download_result_image(job_id, args.image_path)
        print("Saved image:", saved)


if __name__ == "__main__":
    main()