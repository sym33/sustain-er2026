# SCF Reference Schema

The validation uses controlled value domains rather than free-text interpretation. The file `value_domains.tsv` lists the canonical values observed in the validation corpus for each SCF dimension.

## Value Domains

For a dimension \(d\), the value domain \(V_d\) is a controlled set of source-supported values. A value may be a standard term, a documented modeling category, or the explicit marker `Unspecified`. A recoder should choose the most specific value supported by the source claim and should not invent a more precise value when the claim does not support it.

In an implementation, each value-domain row should contain at least:

- `dimension`: the SCF dimension to which the value belongs;
- `value_id`: a stable identifier used by scripts and mappings;
- `label`: the human-readable value;
- `source`: the framework, standard, model, or source document supporting the value;
- `parent_value_id`: optional parent value for preorder reasoning;
- `translations`: optional admissible conversions or framework mappings;
- `conflicts`: optional values or predicates that make co-satisfaction impossible.

## Preorders

Each dimension may define a refinement preorder. The validation uses three practical cases:

- **Entity or boundary refinement**: a site, product, activity, portfolio, scope, or value-chain segment specializes a broader object or boundary. These refinements are not automatically merge-safe, because they change who or what the commitment binds.
- **Metric or framework refinement**: a metric, pathway, disclosure item, or indicator mapping specializes a broader measurement basis when the framework documents the relation.
- **Evidence or accountability refinement**: validation, assurance, provenance, or reporting governance adds detail to a claim without changing the target content.

## Translation and Conflict

Metric translation requires an explicit mapping, conversion, or framework correspondence. Conflict requires a documented incompatibility, such as failed safeguards, incompatible thresholds, or mutually inconsistent evidence requirements. Missing information remains `Unspecified`; it is not treated as a wildcard.

The comparison function uses these fields directly. Equal value identifiers return `=`. A value whose `parent_value_id` chain reaches the other value returns subset or superset, depending on direction. A declared translation returns `approx`. A declared conflict predicate returns conflict. If one relevant value is `Unspecified`, comparison returns `?`. If none of these tests applies, the values remain non-equivalent and are handled by the ordered relation rule in the manuscript.
