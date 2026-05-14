# Sustainability Commitment Alignment Artifact

This repository contains supplementary material for the double-blind ER 2026 submission `Modeling Sustainability Commitments for Governed Transformations`. It provides the coded validation corpus, the review gate used to reproduce the reported validation summary, and an auxiliary recoding audit.

## Contents

- `case_coding.tsv` contains the structured validation coding: 29 claim formulations across six claim families, 18 candidate alignments, ten SCF dimensions, primary and secondary commitment-alignment relations, modeling consequences, and a short coding rationale for each row.
- `CODING_PROTOCOL.md` describes the recoding steps and relation guidelines used to produce the table.
- `SCF_REFERENCE_SCHEMA.md` and `value_domains.tsv` document the controlled value domains used for recoding.
- `scf_review_gate.py` is a small command-line review gate that reads the coding table and summarizes the governance operation implied by each primary relation.
- `LLM_RECODING_PROTOCOL.md`, `llm_recoding_input.tsv`, `codex_recoding_schema.tsv`, `llm_recoding_compare.py`, and `llm_recoding_results.txt` document one label-hidden LLM recoding audit using the controlled value domains.

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

## Reproduce the LLM Recoding Audit

Run:

```sh
python3 llm_recoding_compare.py codex_recoding_schema.tsv
```

The supplied audit compares the table against an LLM recoding that saw the source labels, claim families, claim forms, controlled value domains, and schema guidance, but not the original SCF dimension labels or rationales. It is an ambiguity check, not a substitute for human inter-coder reliability.

Expected headline output:

```text
gold_rows	29
recoded_rows	29
dimension_matches	237
dimension_mismatches	53
exploratory_primary_relation_matches	12
exploratory_primary_relation_mismatches	17
```

Dimension recoding is the relevant stability check. Primary-relation comparison is reported only as diagnostic, because the recoding input does not include full candidate-pair context, \(S(C_1,C_2)\), or purpose-specific relevance decisions.

## Anonymity

The artifact is prepared for double-blind review. It contains no author names, affiliations, emails, local paths, or project identifiers.
