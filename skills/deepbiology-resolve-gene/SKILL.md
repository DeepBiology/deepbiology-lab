---
name: deepbiology-resolve-gene
description: Resolve a gene name, alias, or description to its official HGNC symbol. Use for natural-language or historical names such as cyclin D1, p53, HER2, or AML1 before running gene-based DeepBiology workflows.
---

# Resolve a gene

Call `resolve_gene` with the user's gene reference. Report the canonical HGNC symbol and resolution method. Preserve the original input in the explanation. If no confident match is returned, ask for a symbol or additional context rather than guessing.
