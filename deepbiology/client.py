from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, Optional, List

import requests
import base64

from .exceptions import AuthenticationError, DeepBiologyError, InsufficientCreditsError, NotFoundError


class DeepBiologyClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})

    @staticmethod
    def normalize_result_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        result = payload.get("result") or {}
        image = result.get("image") or {}
        return {
            "ok": payload.get("ok"),
            "jobId": payload.get("jobId"),
            "status": payload.get("status"),
            "submissionId": payload.get("submissionId"),
            "question": payload.get("question"),
            "task": payload.get("task"),
            "creditCost": payload.get("creditCost"),
            "costUsd": payload.get("costUsd"),
            "createdAt": payload.get("createdAt"),
            "updatedAt": payload.get("updatedAt"),
            "result": {
                "fields": result.get("fields") if payload.get("result") else payload.get("resultFields"),
                "tables": result.get("tables") if payload.get("result") else payload.get("resultTables"),
                "enhancerTable": result.get("enhancerTable") if payload.get("result") else payload.get("enhancerTable"),
                "image": {
                    "base64": image.get("base64") if payload.get("result") else payload.get("resultImageBase64"),
                    "charLength": image.get("charLength") if payload.get("result") else payload.get("resultImageCharLength"),
                    "inlineTruncated": image.get("inlineTruncated") if payload.get("result") else payload.get("resultImageInlineTruncated"),
                    "resultPath": image.get("resultPath") if payload.get("result") else payload.get("resultPath"),
                    "storagePath": image.get("storagePath") if payload.get("result") else payload.get("resultStoragePath"),
                    "storageSignedUrl": image.get("storageSignedUrl") if payload.get("result") else payload.get("resultStorageSignedUrl"),
                    "sizeBytes": image.get("sizeBytes") if payload.get("result") else payload.get("resultSizeBytes"),
                },
                "providerParsedOutput": result.get("providerParsedOutput") if payload.get("result") else payload.get("providerParsedOutput"),
            },
            "errorMessage": payload.get("errorMessage"),
        }

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            data = response.json()
        except Exception as exc:
            raise DeepBiologyError(f"Invalid response: {response.text}") from exc

        if response.status_code == 401:
            raise AuthenticationError(data.get("error", "Authentication failed"))
        if response.status_code == 402:
            raise InsufficientCreditsError(data.get("error", "Insufficient credits"))
        if response.status_code == 404:
            raise NotFoundError(data.get("error", "Not found"))
        if response.status_code >= 400:
            raise DeepBiologyError(data.get("error", f"Request failed: {response.status_code}"))
        return data

    def submit_job(self, workflow: str, inputs: Dict[str, Any], submission_id: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "submissionId": submission_id or str(uuid.uuid4()),
            "jobType": "deepbinder",
            "payload": {
                "targetName": inputs.get("gene_name") or inputs.get("target_name") or workflow,
                "sequence": inputs.get("sequence") or inputs.get("mutatedSeq") or f"workflow={workflow}",
                "mode": inputs.get("mode", "medium"),
                "notes": inputs.get("notes", ""),
                "question": workflow,
                **inputs,
            },
        }
        response = self.session.post(f"{self.base_url}/submitDeepbiologyJobApi", json=payload, timeout=120)
        return self._handle_response(response)

    def get_job(self, job_id: str) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}/getDeepbiologyJobApi", params={"jobId": job_id}, timeout=60)
        return self._handle_response(response)

    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}/getDeepbiologyJobResultApi", params={"jobId": job_id}, timeout=60)
        return self.normalize_result_payload(self._handle_response(response))

    @staticmethod
    def _find_table_rows(result: Dict[str, Any], key: str) -> Optional[List[Dict[str, Any]]]:
        for table in result.get("tables") or []:
            if table.get("key") == key:
                return table.get("rows")
        return None

    @staticmethod
    def format_clean_result(payload: Dict[str, Any]) -> Dict[str, Any]:
        result = payload.get("result") or {}
        fields = result.get("fields") or {}
        image = result.get("image") or {}
        task = payload.get("task") or fields.get("task")

        clean = {
            "jobId": payload.get("jobId"),
            "status": payload.get("status"),
            "submissionId": payload.get("submissionId"),
            "question": payload.get("question"),
            "task": task,
            "creditCost": payload.get("creditCost"),
            "costUsd": payload.get("costUsd"),
            "createdAt": payload.get("createdAt"),
            "updatedAt": payload.get("updatedAt"),
            "notes": fields.get("notes") or fields.get("summary") or None,
            "image": {
                "url": image.get("storageSignedUrl"),
                "path": image.get("storagePath") or image.get("resultPath"),
                "sizeBytes": image.get("sizeBytes"),
            },
            "fields": fields,
            "tables": result.get("tables") or [],
            "errorMessage": payload.get("errorMessage"),
        }

        enhancer_rows = result.get("enhancerTable") or DeepBiologyClient._find_table_rows(result, "enhancer_table")
        if enhancer_rows:
            clean["enhancerTable"] = enhancer_rows

        provider = result.get("providerParsedOutput") or {}
        if provider.get("optimized_sequence"):
            clean["optimizedSequence"] = provider.get("optimized_sequence")
        if provider.get("means"):
            clean["means"] = provider.get("means")

        return clean

    def get_clean_result(self, job_id: str) -> Dict[str, Any]:
        return self.format_clean_result(self.get_job_result(job_id))

    def wait_for_job(self, job_id: str, poll_seconds: int = 5, timeout_seconds: int = 1800) -> Dict[str, Any]:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            job = self.get_job(job_id)
            status = job.get("status")
            if status in {"completed", "failed", "cancelled"}:
                return job
            time.sleep(poll_seconds)
        raise DeepBiologyError(f"Timed out waiting for job {job_id}")

    def download_result_image(self, job_id: str, output_path: str) -> str:
        result = self.get_job_result(job_id)
        image = (result.get("result") or {}).get("image") or {}
        if image.get("base64"):
            with open(output_path, "wb") as fh:
                fh.write(base64.b64decode(image["base64"]))
            return output_path
        if image.get("storageSignedUrl"):
            response = requests.get(image["storageSignedUrl"], timeout=120)
            if response.status_code >= 400:
                raise DeepBiologyError(f"Failed to download image: {response.status_code}")
            with open(output_path, "wb") as fh:
                fh.write(response.content)
            return output_path
        raise NotFoundError("No result image available for this job")

    def download_job_result(
        self,
        job_id: str,
        output_directory: str = "deepbiology-experiments",
        run_name: Optional[str] = None,
        raw: bool = False,
        download_image: bool = False,
        image_path: Optional[str] = None,
        poll_seconds: int = 5,
        timeout_seconds: int = 1800,
    ) -> Dict[str, Any]:
        """Wait for a job and persist its result artifacts using the CLI layout."""
        self.wait_for_job(
            job_id,
            poll_seconds=poll_seconds,
            timeout_seconds=timeout_seconds,
        )
        normalized = self.get_job_result(job_id)
        payload = normalized if raw else self.format_clean_result(normalized)

        resolved_run_name = run_name or "run_{}".format(job_id)
        run_directory = os.path.join(output_directory, resolved_run_name)
        os.makedirs(run_directory, exist_ok=True)

        result_file = os.path.join(run_directory, "result_{}.json".format(job_id))
        with open(result_file, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

        downloaded_image = None
        if download_image:
            resolved_image_path = image_path or os.path.join(
                run_directory, "result_{}.png".format(job_id)
            )
            downloaded_image = self.download_result_image(job_id, resolved_image_path)

        return {
            "jobId": job_id,
            "runDirectory": run_directory,
            "resultFile": result_file,
            "imageFile": downloaded_image,
            "raw": raw,
            "result": payload,
        }
