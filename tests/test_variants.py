import unittest

from deepbiology import annotate_variant, find_variants


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append(url)
        return FakeResponse(self.payload)


class VariantResolutionTests(unittest.TestCase):
    def test_region_parser_maps_alleles_and_enforces_limit(self):
        session = FakeSession([
            {
                "id": "rs1",
                "seq_region_name": "1",
                "start": 100,
                "end": 100,
                "alleles": ["A", "G"],
                "consequence_type": "intron_variant",
                "clinical_significance": [],
                "source": "dbSNP",
            },
            {
                "id": "rs2",
                "seq_region_name": "1",
                "start": 101,
                "end": 102,
                "alleles": ["AC", "A"],
                "source": "dbSNP",
            },
        ])

        result = find_variants("chr1:100-102", limit=1, session=session)

        self.assertEqual(result["totalMatches"], 2)
        self.assertEqual(result["returned"], 1)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["variants"][0]["alleleString"], "A/G")
        self.assertEqual(result["variants"][0]["variantClass"], "SNV")

    def test_vep_preserves_transcript_and_regulatory_consequences(self):
        session = FakeSession([{
            "seq_region_name": "1",
            "start": 207923720,
            "end": 207923720,
            "strand": 1,
            "allele_string": "A/G",
            "most_severe_consequence": "intron_variant",
            "transcript_consequences": [{
                "transcript_id": "ENST00000742948",
                "gene_symbol": "LINC02767",
                "gene_id": "ENSG00000284237",
                "consequence_terms": ["intron_variant"],
                "impact": "MODIFIER",
                "biotype": "lncRNA",
                "variant_allele": "G",
            }],
            "regulatory_feature_consequences": [{
                "regulatory_feature_id": "ENSR1_B3J95J",
                "consequence_terms": ["regulatory_region_variant"],
                "impact": "MODIFIER",
                "variant_allele": "G",
            }],
        }])

        result = annotate_variant("1053802528", session=session)
        mapping = result["mappings"][0]

        self.assertEqual(result["variantId"], "rs1053802528")
        self.assertEqual(mapping["transcriptConsequences"][0]["transcriptId"], "ENST00000742948")
        self.assertEqual(
            mapping["regulatoryFeatureConsequences"][0]["regulatoryFeatureId"],
            "ENSR1_B3J95J",
        )


if __name__ == "__main__":
    unittest.main()
