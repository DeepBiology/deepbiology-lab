from __future__ import annotations

import json
import re
import urllib.request
from typing import Any, Dict, List, Mapping

from .exceptions import ExternalServiceError, ResolutionError


_ENSEMBL_BASES = {
    "GRCH38": "https://rest.ensembl.org",
    "HG38": "https://rest.ensembl.org",
    "GRCH37": "https://grch37.rest.ensembl.org",
    "HG19": "https://grch37.rest.ensembl.org",
}


def _ensembl_base(assembly: str) -> str:
    key = str(assembly).upper()
    if key not in _ENSEMBL_BASES:
        raise ResolutionError("Unsupported assembly '{}'. Use GRCh38/hg38 or GRCh37/hg19.".format(assembly))
    return _ENSEMBL_BASES[key]


def _get_json(url: str, timeout: int, session: Any) -> Any:
    try:
        if session is not None:
            response = session.get(url, headers={"Content-Type": "application/json"}, timeout=timeout)
            response.raise_for_status()
            return response.json()
        request = urllib.request.Request(
            url,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except Exception as exc:
        raise ExternalServiceError("Failed to query Ensembl at {}: {}".format(url, exc)) from exc


def _variant_class(alleles: List[str]) -> str:
    cleaned = [allele for allele in alleles if allele not in {"", "-"}]
    if cleaned and all(len(allele) == 1 for allele in cleaned):
        return "SNV"
    lengths = {len(allele) for allele in cleaned}
    if len(lengths) > 1 or "-" in alleles:
        return "indel"
    if cleaned and all(len(allele) > 1 for allele in cleaned):
        return "MNV"
    return "variation"


def find_variants(
    region: str,
    assembly: str = "GRCh38",
    limit: int = 50,
    *,
    timeout: int = 15,
    session: Any = None,
) -> Dict[str, Any]:
    """Find known Ensembl variation records overlapping a genomic region."""
    match = re.fullmatch(r"(?:chr)?([0-9]+|X|Y|MT):([0-9]+)-([0-9]+)", region.strip(), re.IGNORECASE)
    if not match:
        raise ResolutionError("Region must use the form chr1:100-200.")
    chromosome, start_text, end_text = match.groups()
    start, end = int(start_text), int(end_text)
    if start < 1 or end < start:
        raise ResolutionError("Region coordinates must be positive and end must be >= start.")
    if limit < 1 or limit > 200:
        raise ResolutionError("Variant result limit must be between 1 and 200.")

    normalized_region = "{}:{}-{}".format(chromosome.upper(), start, end)
    url = "{}/overlap/region/human/{}?feature=variation".format(
        _ensembl_base(assembly), normalized_region
    )
    data = _get_json(url, timeout, session)
    if not isinstance(data, list):
        raise ExternalServiceError("Ensembl returned an unexpected regional-variation payload.")

    variants = []
    for record in data[:limit]:
        alleles = [str(allele) for allele in (record.get("alleles") or [])]
        variants.append({
            "rsid": record.get("id"),
            "chromosome": record.get("seq_region_name"),
            "start": record.get("start"),
            "end": record.get("end"),
            "alleles": alleles,
            "alleleString": "/".join(alleles),
            "variantClass": _variant_class(alleles),
            "consequenceType": record.get("consequence_type"),
            "clinicalSignificance": record.get("clinical_significance") or [],
            "source": record.get("source"),
        })

    return {
        "region": "chr{}:{}-{}".format(chromosome.upper(), start, end),
        "assembly": "GRCh37" if str(assembly).upper() in {"GRCH37", "HG19"} else "GRCh38",
        "totalMatches": len(data),
        "returned": len(variants),
        "limit": limit,
        "truncated": len(data) > limit,
        "variants": variants,
        "source": "Ensembl REST overlap/region",
    }


def _copy_consequence(record: Mapping[str, Any], consequence_type: str) -> Dict[str, Any]:
    result = {
        "type": consequence_type,
        "consequenceTerms": record.get("consequence_terms") or [],
        "impact": record.get("impact"),
        "variantAllele": record.get("variant_allele"),
    }
    field_map = {
        "gene_symbol": "geneSymbol",
        "gene_id": "geneId",
        "transcript_id": "transcriptId",
        "biotype": "biotype",
        "hgnc_id": "hgncId",
        "regulatory_feature_id": "regulatoryFeatureId",
        "distance": "distance",
    }
    for source, target in field_map.items():
        if record.get(source) is not None:
            result[target] = record.get(source)
    return result


def annotate_variant(
    variant_id: str,
    assembly: str = "GRCh38",
    *,
    timeout: int = 30,
    session: Any = None,
) -> Dict[str, Any]:
    """Annotate an rsID with Ensembl VEP without flattening mappings or transcripts."""
    rsid = str(variant_id).strip()
    if not rsid:
        raise ResolutionError("Variant identifier cannot be empty.")
    if rsid.isdigit():
        rsid = "rs{}".format(rsid)
    if not re.fullmatch(r"rs[0-9]+", rsid, re.IGNORECASE):
        raise ResolutionError("Variant identifier must be a dbSNP rsID, such as rs1053802528.")
    rsid = rsid.lower()

    url = "{}/vep/human/id/{}".format(_ensembl_base(assembly), rsid)
    data = _get_json(url, timeout, session)
    if not isinstance(data, list):
        raise ExternalServiceError("Ensembl returned an unexpected VEP payload.")

    mappings = []
    for item in data:
        colocated = []
        for variant in item.get("colocated_variants") or []:
            colocated.append({
                "id": variant.get("id"),
                "location": "{}:{}".format(variant.get("seq_region_name"), variant.get("start")),
                "alleleString": variant.get("allele_string"),
                "frequencies": variant.get("frequencies") or {},
            })
        mappings.append({
            "location": "{}:{}".format(item.get("seq_region_name"), item.get("start")),
            "start": item.get("start"),
            "end": item.get("end"),
            "strand": item.get("strand"),
            "alleleString": item.get("allele_string"),
            "mostSevereConsequence": item.get("most_severe_consequence"),
            "transcriptConsequences": [
                _copy_consequence(record, "transcript")
                for record in item.get("transcript_consequences") or []
            ],
            "regulatoryFeatureConsequences": [
                _copy_consequence(record, "regulatory_feature")
                for record in item.get("regulatory_feature_consequences") or []
            ],
            "intergenicConsequences": [
                _copy_consequence(record, "intergenic")
                for record in item.get("intergenic_consequences") or []
            ],
            "colocatedVariants": colocated,
        })

    return {
        "variantId": rsid,
        "assembly": "GRCh37" if str(assembly).upper() in {"GRCH37", "HG19"} else "GRCh38",
        "mappingCount": len(mappings),
        "mappings": mappings,
        "source": "Ensembl VEP",
    }
