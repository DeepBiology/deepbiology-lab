import unittest

from deepbiology import ResolutionError, resolve_cell_line


CATALOG = [
    {"index": "0", "Cell Line": "KASUMI1", "Assay Type": "GroSeq", "Factor": "Nascent_RNA_Plus"},
    {"index": "1", "Cell Line": "KASUMI1", "Assay Type": "GroSeq", "Factor": "Nascent_RNA_Minus"},
    {"index": "195", "Cell Line": "KASUMI1", "Assay Type": "RNASeq", "Factor": "RNA"},
    {"index": "196", "Cell Line": "K562", "Assay Type": "RNASeq", "Factor": "RNA"},
]


class CellLineResolutionTests(unittest.TestCase):
    def test_resolves_normalized_name_for_assay(self):
        result = resolve_cell_line("kasumi-1", assay_type="RNA-seq", catalog_rows=CATALOG)

        self.assertEqual(result["canonicalName"], "KASUMI1")
        self.assertEqual(result["cellLineIndex"], 195)
        self.assertEqual(result["assayType"], "RNASeq")
        self.assertEqual(result["matchType"], "normalized_exact")

    def test_rejects_ambiguous_assay_matches(self):
        with self.assertRaisesRegex(ResolutionError, "Ambiguous cell line"):
            resolve_cell_line("KASUMI1", assay_type="GroSeq", catalog_rows=CATALOG)

    def test_rejects_missing_assay_column(self):
        rows = [{"index": "195", "Cell Line": "KASUMI1"}]
        with self.assertRaisesRegex(ResolutionError, "no assay-type column"):
            resolve_cell_line("KASUMI1", assay_type="RNASeq", catalog_rows=rows)

    def test_partial_match_must_resolve_to_one_index(self):
        rows = [
            {"index": "1", "Cell Line": "SKMEL28", "Assay Type": "RNASeq"},
            {"index": "2", "Cell Line": "SKMEL2", "Assay Type": "RNASeq"},
        ]
        with self.assertRaisesRegex(ResolutionError, "Ambiguous cell line"):
            resolve_cell_line("SKMEL", catalog_rows=rows)


if __name__ == "__main__":
    unittest.main()
