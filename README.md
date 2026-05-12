# Sustainability Commitment Alignment Artifact

This repository contains supplementary material for a double-blind ER 2026 submission on modeling sustainability commitments for governed transformations.

## Contents

- `case_coding.tsv` contains the structured validation coding: 29 claim formulations across six claim families, 18 candidate alignments, primary and secondary commitment-alignment relations, and modeling consequences.
- `scf_review_gate.py` is a small command-line review gate that reads the coding table and summarizes the governance operation implied by each primary relation.

## Reproduce the Validation Summary

Run:

```sh
python3 scf_review_gate.py
```

Expected output:

```text
claim_formulations	29
claim_families	6
candidate_alignment_labels	18
merge_safe_rows	1
```

The script then reports counts for primary relations, secondary relations, and governance operations.

To inspect one candidate alignment:

```sh
python3 scf_review_gate.py --alignment C1=C2
```

## Anonymity

The artifact is prepared for double-blind review. It contains no author names, affiliations, emails, local paths, or project identifiers.
