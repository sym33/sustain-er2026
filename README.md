# Sustainability Commitment Alignment Artifact

This repository contains supplementary material for the double-blind ER 2026 submission `Modeling Sustainability Commitments for Governed Transformations`. It provides the coded validation corpus, the review gate used to reproduce the reported validation summary, and an auxiliary recoding audit.

## Contents

- `case_coding.tsv` contains the structured validation coding: 29 claim formulations across six claim families, 18 candidate alignments, ten SCF dimensions, primary and secondary commitment-alignment relations, modeling consequences, and a short coding rationale for each row.
- `alignment_cases.tsv` contains comparison vectors for the core alignments. The review gate executes the paper's precedence rule over these vectors and checks the resulting alpha relation and governance operation.
- `dimension_justification.tsv` records the dimension-selection audit: source distinction, preservation question, ablation failure, and witness case for each SCF dimension.
- `matcher_baseline.py` runs a label-only matcher over the executable alignment cases and reports how many retrieved candidates are merge-safe under SCF.
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

To execute the SCF decision rule on comparison vectors:

```sh
python3 scf_review_gate.py --check-cases
```

Expected headline output:

```text
alignment_cases	9
generic_match_baseline_merge_candidates	9
scf_merge_safe_cases	1
alpha_mismatches	0
operation_mismatches	0
```

To compare simple merge-licensing baselines:

```sh
python3 scf_review_gate.py --compare-baselines
```

The baselines are not competing matchers; they show what remains indistinguishable if a transformation uses only generic candidate links, purpose, metric/time/purpose, or evidence/accountability/purpose before deciding to merge.

To run the label-only matcher baseline:

```sh
python3 matcher_baseline.py
```

Expected headline output:

```text
candidate_pairs	9
retrieved_pairs	5
scf_merge_safe_retrieved	1
scf_disallowed_retrieved	4
```

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
