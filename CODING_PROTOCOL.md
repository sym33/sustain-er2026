# Coding Protocol

This protocol supports independent inspection or recoding of the validation table.

## Unit of Coding

Each row represents one claim formulation used in a candidate alignment test. A claim formulation is coded as a Sustainability Commitment Frame profile with the following dimensions:

- actor
- object
- boundary
- metric basis
- temporal structure
- intervention logic
- accountability relation

The remaining alignment columns record the tested comparison, primary relation, secondary relations, and modeling consequence.
The `coding_rationale` column gives a short source-based explanation for the assigned relation and consequence.

## Reference Schema

Coding uses a documented reference schema rather than free label interpretation. The schema is induced from the source frameworks used in the validation:

- GHG Protocol terms for organizational boundary, operational boundary, scopes 1--3, and value-chain coverage.
- ISO 14068-1 terms for carbon neutrality, compensation, transition, and claim evidence.
- SBTi terms for net-zero targets, pathway validation, scope coverage, and residual-emissions treatment.
- EU taxonomy terms for activity-level alignment, environmental objective, substantial contribution, do-no-significant-harm criteria, and safeguards.
- Circular-economy terms for product design, reuse, repair, recycling, remanufacturing, and product-service models.
- Sustainability-reporting terms for indicator mapping, disclosure item, reporting entity, and framework provenance.

For each SCF dimension, equality means that two values refer to the same reference-schema value. Refinement means that one value is a documented specialization of another, such as operations being narrower than value-chain coverage when the source semantics support that relation. If the source does not support a value or refinement relation, the dimension is marked `Unspecified` or the relation is recorded as trace-only rather than inferred.

## Coding Steps

1. **Source paraphrase**: restate the claim using only the source-framework semantics listed in the `source` and `claim_form` fields.
2. **Dimension coding**: fill each SCF dimension with the most specific reference-schema value supported by the source formulation.
3. **Underspecification marking**: use `Unspecified` when a relevant dimension is missing or too vague to support alignment.
4. **Comparison construction**: compare the two claim profiles in the `alignment_test` using the SCF dimensions.
5. **Primary relation assignment**: apply the decision rule from the paper to assign one primary relation.
6. **Secondary relation recording**: record additional mismatches that are diagnostically relevant but do not change the primary relation.
7. **Modeling consequence**: record the operation implied by the primary relation, such as split, qualify, translate, trace, complete, block, revise, or merge with provenance.
8. **Rationale note**: summarize the source-framework reason for the primary relation so that disagreements can be traced to source semantics, dimension coding, or relation precedence.

## Relation Guidelines

- Use `Equivalence with provenance` only when relevant commitment dimensions are preserved and evidence provenance is retained.
- Use `Refinement` when one profile adds detail while preserving the parent commitment.
- Use `Boundary shift` when actor, object, scope, territory, lifecycle phase, or value-chain coverage changes.
- Use `Metric translation` only when an explicit mapping or conversion is available.
- Use `Intervention substitution` when a different action logic is substituted, such as offsetting, disclosure, classification, or removals.
- Use `Accountability qualification` when target content is preserved but validation, assurance, evidence, or responsibility changes.
- Use `Underspecification` when a relevant missing or vague dimension prevents preservation judgment.
- Use `Conflict` when relevant requirements, safeguards, thresholds, responsibilities, or evidence expectations are incompatible.
- Use `Replacement` when one claim supersedes another.
- Use `Trace-only relation` when claims share context or purpose but do not preserve enough commitment structure for merge, refinement, or translation.

## Recoding Check

Independent recoding should first reproduce the SCF dimension profile before inspecting the primary relation. Disagreement can then be localized to either dimension coding, relevance judgment, relation precedence, or operation mapping.
