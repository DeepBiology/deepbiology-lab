from __future__ import annotations

import csv
import io
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

import requests

from .exceptions import ExternalServiceError, ResolutionError


DEFAULT_MODEL_ID = "borzoi_finetune_v1"
DEFAULT_ASSAY_TYPE = "RNASeq"

MODEL_CATALOGS: Dict[str, Dict[str, str]] = {
    "borzoi_finetune_v1": {
        "label": "Borzoi fine-tuned (current production)",
        "metadata_url": "https://www.deepbiology.ai/samplefile_w_anno_for_chipseq_with6cols.csv",
        "modelConfigPath": "/projects/data_all/i_196608_w_32_c_0_x_163840_s_1.000000_time_20241112-185938/torch_finetune_20250613_224239/files/config.yaml",
        "runpodEndpointKey": "default",
    },
    "borzoi_finetune_ccle_v1": {
        "label": "Borzoi fine-tuned (CCLE 1019 cancer cell lines)",
        "metadata_url": "https://www.deepbiology.ai/samplefile_annotated_ccle_new.csv",
        "modelConfigPath": "/projects/rnaseq_aws/i_196608_w_32_c_0_x_163840_s_1.000000_time_20251027-125614/torch_finetune_20251028_114355/files/config.yaml",
        "runpodEndpointKey": "ccle",
    },
}

_CELL_COLUMNS = ("cell line", "cell_line", "cell")
_INDEX_COLUMNS = ("index", "idx", "channel")
_ASSAY_COLUMNS = ("assay type", "assay_type", "assay")


def _normalize(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value).upper().strip())


def _normalized_row(row: Mapping[str, Any]) -> Dict[str, str]:
    return {str(key).strip().lower(): "" if value is None else str(value) for key, value in row.items()}


def _find_column(row: Mapping[str, str], candidates: Sequence[str]) -> Optional[str]:
    return next((candidate for candidate in candidates if candidate in row), None)


def list_models() -> List[Dict[str, str]]:
    """Return the SDK's configured model catalogs."""
    return [
        {
            "id": model_id,
            "label": metadata["label"],
            "metadataUrl": metadata["metadata_url"],
            "runpodEndpointKey": metadata["runpodEndpointKey"],
        }
        for model_id, metadata in MODEL_CATALOGS.items()
    ]


def fetch_model_catalog(
    model_id: str = DEFAULT_MODEL_ID,
    *,
    timeout: int = 30,
    session: Any = None,
) -> List[Dict[str, str]]:
    """Download and parse the metadata catalog for a model."""
    if model_id not in MODEL_CATALOGS:
        raise ResolutionError(
            "Unknown model '{}'. Available: {}".format(model_id, ", ".join(MODEL_CATALOGS))
        )

    http = session or requests
    url = MODEL_CATALOGS[model_id]["metadata_url"]
    try:
        response = http.get(url, timeout=timeout)
        response.raise_for_status()
    except Exception as exc:
        raise ExternalServiceError("Failed to download model catalog from {}: {}".format(url, exc)) from exc

    rows = []
    for row in csv.DictReader(io.StringIO(response.text)):
        if row and any(str(value or "").strip() for value in row.values()):
            rows.append({str(key): "" if value is None else str(value) for key, value in row.items()})
    if not rows:
        raise ResolutionError("Model catalog '{}' is empty.".format(model_id))
    return rows


def resolve_cell_line(
    cell_name: str,
    model_id: str = DEFAULT_MODEL_ID,
    assay_type: Optional[str] = DEFAULT_ASSAY_TYPE,
    *,
    catalog_rows: Optional[Sequence[Mapping[str, Any]]] = None,
    timeout: int = 30,
    session: Any = None,
) -> Dict[str, Any]:
    """Resolve a cell name to one model output channel for a specific assay.

    Exact normalized cell-name matches are preferred. A partial normalized match
    is accepted only when it identifies one output-channel index.
    """
    if model_id not in MODEL_CATALOGS:
        raise ResolutionError(
            "Unknown model '{}'. Available: {}".format(model_id, ", ".join(MODEL_CATALOGS))
        )
    query = _normalize(cell_name)
    if not query:
        raise ResolutionError("Cell-line name cannot be empty.")

    source_rows = list(catalog_rows) if catalog_rows is not None else fetch_model_catalog(
        model_id, timeout=timeout, session=session
    )
    if not source_rows:
        raise ResolutionError("Model catalog '{}' is empty.".format(model_id))
    rows = [_normalized_row(row) for row in source_rows]

    cell_col = _find_column(rows[0], _CELL_COLUMNS)
    index_col = _find_column(rows[0], _INDEX_COLUMNS)
    assay_col = _find_column(rows[0], _ASSAY_COLUMNS)
    if not cell_col or not index_col:
        raise ResolutionError(
            "Catalog '{}' must contain cell-line and index columns; found: {}".format(
                model_id, ", ".join(rows[0].keys())
            )
        )
    if assay_type and not assay_col:
        raise ResolutionError(
            "Catalog '{}' has no assay-type column, so assay '{}' cannot be applied.".format(
                model_id, assay_type
            )
        )

    assay_query = _normalize(assay_type or "")
    assay_rows = [
        row for row in rows
        if not assay_query or _normalize(row.get(assay_col or "", "")) == assay_query
    ]
    exact = [row for row in assay_rows if _normalize(row.get(cell_col, "")) == query]
    matches = exact or [row for row in assay_rows if query in _normalize(row.get(cell_col, ""))]
    match_type = "normalized_exact" if exact else "normalized_partial"

    if not matches:
        assay_message = " with assay type '{}'".format(assay_type) if assay_type else ""
        raise ResolutionError(
            "No match for cell line '{}'{} in model '{}'.".format(cell_name, assay_message, model_id)
        )

    indices: Dict[int, List[Dict[str, str]]] = {}
    for row in matches:
        try:
            index = int(row[index_col])
        except (TypeError, ValueError) as exc:
            raise ResolutionError(
                "Catalog '{}' contains a non-integer index '{}' for '{}'.".format(
                    model_id, row.get(index_col), row.get(cell_col)
                )
            ) from exc
        indices.setdefault(index, []).append(row)

    if len(indices) != 1:
        candidates = [
            {
                "cellLineIndex": index,
                "cellName": grouped[0].get(cell_col, ""),
                "assayType": grouped[0].get(assay_col or "", ""),
                "factor": grouped[0].get("factor", ""),
                "accession": grouped[0].get("accession", ""),
            }
            for index, grouped in sorted(indices.items())
        ]
        raise ResolutionError(
            "Ambiguous cell line '{}' for assay '{}' in model '{}': {}".format(
                cell_name, assay_type or "any", model_id, candidates
            )
        )

    index, grouped = next(iter(indices.items()))
    matched = grouped[0]
    return {
        "inputCellName": cell_name,
        "canonicalName": _normalize(matched.get(cell_col, "")),
        "matchedCellName": matched.get(cell_col, ""),
        "cellLineIndex": index,
        "modelId": model_id,
        "assayType": matched.get(assay_col or "", assay_type or ""),
        "matchType": match_type,
        "matchingRows": len(grouped),
        "catalogUrl": MODEL_CATALOGS[model_id]["metadata_url"],
    }
