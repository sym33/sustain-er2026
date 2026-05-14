# LLM-Assisted Recoding Protocol

This protocol uses a large language model (LLM) as a recoding assistant, not as ground truth. The main goal is to stress-test whether the coding protocol is clear enough for another reasoner to reconstruct SCF dimensions from source-based claim descriptions. Relation labels are exploratory unless the recoder is also given the full candidate-pair context.

## Inputs

Use `llm_recoding_input.tsv`, not `case_coding.tsv`, for recoding. Use `value_domains.tsv` as the controlled vocabulary and `SCF_REFERENCE_SCHEMA.md` for the interpretation of value domains and preorders. The input file contains only:

```text
id	source	claim_family	claim_form
```

The LLM must not see `primary_relation`, `secondary_relations`, `modeling_consequence`, or `coding_rationale` during recoding.

## Prompt

```text
You are an independent recoder for a conceptual-modeling validation study.

Use the supplied coding protocol, SCF_REFERENCE_SCHEMA.md, value_domains.tsv,
and the rows in llm_recoding_input.tsv.
Do not infer unsupported detail. Use "Unspecified" when a relevant dimension
is missing or too vague. Select dimension values from value_domains.tsv where
possible. First code the ten SCF dimensions. Assign a primary relation only
where the row itself gives enough pairwise context; otherwise mark it as
"Unspecified".

Return TSV only with these columns:
id	actor	object	boundary	metric_basis	temporal_structure	intervention_logic	normative_threshold	evidence_basis	accountability_relation	sustainability_purpose	primary_relation	secondary_relations	modeling_consequence	recoding_note
```

## Interpretation

LLM disagreement is not an error by itself and is not evidence of correctness. It is an ambiguity audit. Disagreements should be localized to source ambiguity, dimension coding, relevance judgment, relation precedence, or operation mapping.
