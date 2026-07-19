(base) jinsong@DESKTOP-9BI27J7:~$ bash /home/jinsong/projects/www.deepbiology.ai/python_client/deepbiology_q1_cd34_kasumi1.sh
============================================================
  DeepBiology Lab Q1 - CD34 Regulation in Kasumi-1 Cells
  Alibaba Cloud MCP Server: https://47.89.181.155/mcp
============================================================

[Step 1/5] Initializing MCP session with Alibaba Cloud server...
  Connected to: deepbiology-lab v1.28.1
  Protocol: 2024-11-05
  MCP session initialized successfully.

[Step 2/5] Listing available tools on Alibaba Cloud MCP server...
  Available tools: 15
    - resolve_gene
    - resolve_cell_line
    - find_variants
    - annotate_variant
    - resolve_snps
    - resolve_snp_impact
    - resolve_cancer_mutations
    - submit_q1_regulation
    - submit_q2_enhancer_importance
    - submit_q3_mutation_impact
    - submit_q4_enhancer_redesign
    - get_job_status
    - get_job_result
    - download_job_result
    - list_models

[Step 3/5] Submitting Q1 regulation analysis job...
  Gene: CD34
  Cell Line: Kasumi-1 (index: 195)
  Model: borzoi_finetune_v1
  Assay: RNASeq

  Job ID: ddc08f1d8522235877e4e247c7ea0bea7b8d549878d3c52b333112090f79b826
  Status: IN_QUEUE
  Task: plot_transcription_gradient
  Credit Cost: 0.1

  Cell Line Resolution:
    Input: Kasumi-1 -> Canonical: KASUMI1 (index: 195, match: normalized_exact)

  Job submitted to Alibaba Cloud successfully!

[Step 4/5] Polling job status on Alibaba Cloud (interval: 10s)...

  Poll   1 (  10s): Status = running
  Poll   2 (  20s): Status = running
  Poll   3 (  30s): Status = running
  Poll   4 (  40s): Status = running
  Poll   5 (  50s): Status = running
  Poll   6 (  60s): Status = running
  Poll   7 (  70s): Status = running
  Poll   8 (  80s): Status = completed

  Job completed on Alibaba Cloud after 80 seconds!

[Step 5/5] Retrieving results from Alibaba Cloud...

============================================================
  Q1 RESULTS: CD34 Transcription Regulation in Kasumi-1
  (from Alibaba Cloud MCP Server)
============================================================

{
  "jobId": "ddc08f1d8522235877e4e247c7ea0bea7b8d549878d3c52b333112090f79b826",
  "status": "completed",
  "submissionId": "cd0485ea-9635-4de3-b98c-0df18be52202",
  "question": "q1_regulation",
  "task": "plot_transcription_gradient",
  "creditCost": 0.1,
  "costUsd": 0.1,
  "createdAt": {
    "_seconds": 1784503687,
    "_nanoseconds": 132000000
  },
  "updatedAt": {
    "_seconds": 1784503763,
    "_nanoseconds": 892000000
  },
  "notes": null,
  "image": {
    "url": "https://storage.googleapis.com/deepbiology-471514.firebasestorage.app/job-results/ZWFyqihsxmWjroGFUe7MLKuoBn82/ddc08f1d8522235877e4e247c7ea0bea7b8d549878d3c52b333112090f79b826.png?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=975184631130-compute%40developer.gserviceaccount.com%2F20260719%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260719T232926Z&X-Goog-Expires=3600&X-Goog-SignedHeaders=host&X-Goog-Signature=7232060c4a5fa55d75237185bd24d4492c5a3f69f38d2a13b9d448891d38eb48a733bdecc040abd445dded7191ceac4dae2e5d3b21b43c82353b2c74f9f06eafbf19bf841f52f579656a469cc7455932e94493da4c4aabc18c4acb4f406346eb708fe396f245ade1b9f474e54f98300a8c6d7ae0e6ad7af9f768b7eb24716801b4e3313b0c1b25e68e14a811f272ad00462152f3cedfd68562a54608edb968662fb30a2388833d697f29128b0a3eba327d3b21098ab7e3833c1ca9fa613b1d711ae2df4b0cbde83785f2d86271635a44753336adebd7b7ffc1c95a57371e14cf129c6d68267a0c2a5d0e96b7f93b899e6876c93b3185d28ea7bc8b582588a8f8",
    "path": "job-results/ZWFyqihsxmWjroGFUe7MLKuoBn82/ddc08f1d8522235877e4e247c7ea0bea7b8d549878d3c52b333112090f79b826.png",
    "sizeBytes": 757373
  },
  "fields": {
    "task": "plot_transcription_gradient"
  },
  "tables": [
    {
      "key": "enhancer_table",
      "rows": [
        {
          "chr": "chr1",
          "start": 207923720,
          "end": 207923920,
          "score": 8.069393157958984,
          "type": "intergenic",
          "input_tensor_start": 207636827,
          "input_tensor_end": 208161115,
          "sequence": "GGAGAACCTTTCTCAGGAAGTCCCATTGCTGGGCTGGGCTGGGGGCCGCCTGGGCAGAGAGATAAGCTGCGCCGATGGGTCGGGAGCAGCAGCCTTGGTGGTTTTCTGCCGCCGAAGTCCTGGCCTGCAGGAAACCCCAGGGAGGACCCCTGCATCCTCTTTTACAGCAGAATAATCTTAGCACCCAGTTAACTGCCCAC"
        }
      ]
    }
  ],
  "errorMessage": null,
  "enhancerTable": [
    {
      "chr": "chr1",
      "start": 207923720,
      "end": 207923920,
      "score": 8.069393157958984,
      "type": "intergenic",
      "input_tensor_start": 207636827,
      "input_tensor_end": 208161115,
      "sequence": "GGAGAACCTTTCTCAGGAAGTCCCATTGCTGGGCTGGGCTGGGGGCCGCCTGGGCAGAGAGATAAGCTGCGCCGATGGGTCGGGAGCAGCAGCCTTGGTGGTTTTCTGCCGCCGAAGTCCTGGCCTGCAGGAAACCCCAGGGAGGACCCCTGCATCCTCTTTTACAGCAGAATAATCTTAGCACCCAGTTAACTGCCCAC"
    }
  ]
}

============================================================
  Analysis Complete!
  Alibaba Cloud MCP Server: https://47.89.181.155/mcp
  Server: deepbiology-lab v1.28.1
  Job ID: ddc08f1d8522235877e4e247c7ea0bea7b8d549878d3c52b333112090f79b826
  Gene: CD34 | Cell Line: Kasumi-1
  Task: plot_transcription_gradient
============================================================
(base) jinsong@DESKTOP-9BI27J7:~$