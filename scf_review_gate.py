#!/usr/bin/env python3
"""SCF model-review gate for the ER 2026 supplementary material.

The script reads the anonymized case coding table and reports whether candidate
alignments are merge-safe or require governance actions such as qualifying,
splitting, tracing, translating, completing, or blocking.

It can also execute the paper's precedence rule on comparison vectors in
alignment_cases.tsv. Those vectors are the compact, auditable form of
S(C1, C2): one symbol per relevant SCF dimension.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


MERGE_SAFE = {"Equivalence with provenance"}
BOUNDARY_DIMS = {"actor", "object", "boundary"}
EVIDENCE_DIMS = {"evidence_basis", "accountability_relation"}
NON_BOUNDARY_DIMS = {
    "metric_basis",
    "temporal_structure",
    "intervention_logic",
    "normative_threshold",
    "evidence_basis",
    "accountability_relation",
    "sustainability_purpose",
}
DIMENSIONS = (
    "actor",
    "object",
    "boundary",
    "metric_basis",
    "temporal_structure",
    "intervention_logic",
    "normative_threshold",
    "evidence_basis",
    "accountability_relation",
    "sustainability_purpose",
)
ALPHA_TO_OPERATION = {
    "equiv": "merge-with-provenance",
    "Ref": "qualify",
    "B": "split",
    "M": "translate",
    "T": "qualify",
    "I": "qualify",
    "A": "qualify",
    "U": "complete",
    "#": "block",
    "Repl": "revise",
    "Trace": "trace",
}
BASELINE_MASKS = {
    "generic_candidate_link": (),
    "purpose_only": ("sustainability_purpose",),
    "metric_time_purpose": ("metric_basis", "temporal_structure", "sustainability_purpose"),
    "evidence_accountability_purpose": (
        "evidence_basis",
        "accountability_relation",
        "sustainability_purpose",
    ),
}
MATCHLIKE = {"=", "approx", "subset", "supset"}


def operation_for(relation: str, consequence: str) -> str:
    text = f"{relation} {consequence}".lower()
    if relation in MERGE_SAFE:
        return "merge-with-provenance"
    if "block" in text or "do not" in text:
        return "block"
    if "split" in text or "separate" in text:
        return "split"
    if "translate" in text or "translation" in text:
        return "translate"
    if "trace" in text or "link" in text:
        return "trace"
    if "underspecification" in text or "underspecified" in text or "complete" in text:
        return "complete"
    if "replacement" in text or "supersede" in text or "revise" in text:
        return "revise"
    if "qualif" in text or "refinement" in text or "record" in text or "component" in text or "interim" in text:
        return "qualify"
    return "review"


def alpha_for(vector: dict[str, str]) -> str:
    """Apply the manuscript's precedence rule to an SCF comparison vector."""
    deltas = {dim: vector[dim] for dim in DIMENSIONS}
    if vector.get("supersedes", "").lower() in {"yes", "true", "1"}:
        return "Repl"
    if "bot" in deltas.values():
        return "#"
    if "?" in deltas.values():
        return "U"
    if any(deltas[dim] != "=" for dim in BOUNDARY_DIMS):
        return "B"
    if deltas["metric_basis"] == "approx":
        return "M"
    if deltas["temporal_structure"] not in {"=", "subset", "supset"}:
        return "T"
    if deltas["intervention_logic"] not in {"=", "subset", "supset"}:
        return "I"
    if any(deltas[dim] != "=" for dim in EVIDENCE_DIMS):
        return "A"
    refinement_symbols = {deltas[dim] for dim in NON_BOUNDARY_DIMS}
    if refinement_symbols <= {"=", "subset"} and "subset" in refinement_symbols:
        return "Ref"
    if refinement_symbols <= {"=", "supset"} and "supset" in refinement_symbols:
        return "Ref"
    if all(value == "=" for value in deltas.values()):
        return "equiv"
    return "Trace"


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    required = {
        "id",
        "source",
        "claim_family",
        "claim_form",
        "actor",
        "object",
        "boundary",
        "metric_basis",
        "temporal_structure",
        "intervention_logic",
        "normative_threshold",
        "evidence_basis",
        "accountability_relation",
        "sustainability_purpose",
        "alignment_test",
        "primary_relation",
        "secondary_relations",
        "modeling_consequence",
        "coding_rationale",
    }
    missing = required.difference(reader.fieldnames or [])
    if missing:
        raise SystemExit(f"Missing columns: {', '.join(sorted(missing))}")
    return rows


def summarize(rows: list[dict[str, str]]) -> None:
    families = Counter(row["id"][:2] for row in rows)
    alignments = Counter(row["alignment_test"] for row in rows)
    relations = Counter(row["primary_relation"] for row in rows)
    secondary = Counter(
        rel.strip()
        for row in rows
        for rel in row["secondary_relations"].split(";")
        if rel.strip()
    )
    operations = Counter(
        operation_for(row["primary_relation"], row["modeling_consequence"]) for row in rows
    )
    merge_safe = [
        row for row in rows if operation_for(row["primary_relation"], row["modeling_consequence"]).startswith("merge")
    ]

    print(f"claim_formulations\t{len(rows)}")
    print(f"claim_families\t{len(families)}")
    print(f"candidate_alignment_labels\t{len(alignments)}")
    print(f"merge_safe_rows\t{len(merge_safe)}")
    print()
    print("primary_relations")
    for relation, count in relations.most_common():
        print(f"{count}\t{relation}")
    print()
    print("secondary_relations")
    for relation, count in secondary.most_common():
        print(f"{count}\t{relation}")
    print()
    print("governance_operations")
    for operation, count in operations.most_common():
        print(f"{count}\t{operation}")


def load_alignment_cases(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    required = {
        "case_id",
        "left_claim",
        "right_claim",
        "supersedes",
        *DIMENSIONS,
        "expected_alpha",
        "operation",
    }
    missing = required.difference(reader.fieldnames or [])
    if missing:
        raise SystemExit(f"Missing columns: {', '.join(sorted(missing))}")
    return rows


def check_alignment_cases(path: Path) -> None:
    rows = load_alignment_cases(path)
    mismatches = []
    operation_mismatches = []
    baseline_merge_candidates = 0
    merge_safe = 0
    for row in rows:
        baseline_merge_candidates += 1
        actual = alpha_for(row)
        actual_operation = ALPHA_TO_OPERATION[actual]
        if actual == "equiv":
            merge_safe += 1
        if actual != row["expected_alpha"]:
            mismatches.append((row["case_id"], row["expected_alpha"], actual))
        if actual_operation != row["operation"]:
            operation_mismatches.append((row["case_id"], row["operation"], actual_operation))

    print(f"alignment_cases\t{len(rows)}")
    print(f"generic_match_baseline_merge_candidates\t{baseline_merge_candidates}")
    print(f"scf_merge_safe_cases\t{merge_safe}")
    print(f"alpha_mismatches\t{len(mismatches)}")
    print(f"operation_mismatches\t{len(operation_mismatches)}")
    if mismatches:
        print()
        print("alpha_mismatch_details")
        for case_id, expected, actual in mismatches:
            print(f"{case_id}\texpected={expected}\tactual={actual}")
    if operation_mismatches:
        print()
        print("operation_mismatch_details")
        for case_id, expected, actual in operation_mismatches:
            print(f"{case_id}\texpected={expected}\tactual={actual}")


def compare_baselines(path: Path) -> None:
    rows = load_alignment_cases(path)
    for name, dimensions in BASELINE_MASKS.items():
        merge_candidates = 0
        scf_disallowed = 0
        for row in rows:
            if all(row[dim] in MATCHLIKE for dim in dimensions):
                merge_candidates += 1
                if alpha_for(row) != "equiv":
                    scf_disallowed += 1
        print(
            f"{name}\tmerge_candidates={merge_candidates}\t"
            f"scf_disallowed_merges={scf_disallowed}"
        )


def load_ablation_cases(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    required = {
        "case_id",
        "masked_dimension",
        "supersedes",
        *DIMENSIONS,
        "expected_full_alpha",
        "expected_masked_alpha",
    }
    missing = required.difference(reader.fieldnames or [])
    if missing:
        raise SystemExit(f"Missing columns: {', '.join(sorted(missing))}")
    return rows


def check_ablation_cases(path: Path) -> None:
    rows = load_ablation_cases(path)
    full_mismatches = []
    masked_mismatches = []
    unsafe_merges_without_dimension = 0
    for row in rows:
        full_alpha = alpha_for(row)
        masked = dict(row)
        masked[masked["masked_dimension"]] = "="
        masked_alpha = alpha_for(masked)
        if full_alpha != row["expected_full_alpha"]:
            full_mismatches.append((row["case_id"], row["expected_full_alpha"], full_alpha))
        if masked_alpha != row["expected_masked_alpha"]:
            masked_mismatches.append((row["case_id"], row["expected_masked_alpha"], masked_alpha))
        if full_alpha != "equiv" and masked_alpha == "equiv":
            unsafe_merges_without_dimension += 1

    print(f"dimension_ablation_cases\t{len(rows)}")
    print(f"unsafe_merges_when_masked\t{unsafe_merges_without_dimension}")
    print(f"full_alpha_mismatches\t{len(full_mismatches)}")
    print(f"masked_alpha_mismatches\t{len(masked_mismatches)}")
    if full_mismatches:
        print()
        print("full_alpha_mismatch_details")
        for case_id, expected, actual in full_mismatches:
            print(f"{case_id}\texpected={expected}\tactual={actual}")
    if masked_mismatches:
        print()
        print("masked_alpha_mismatch_details")
        for case_id, expected, actual in masked_mismatches:
            print(f"{case_id}\texpected={expected}\tactual={actual}")


def query(rows: list[dict[str, str]], alignment: str) -> None:
    matches = [
        row for row in rows if row["alignment_test"].lower() == alignment.lower()
    ]
    if not matches:
        raise SystemExit(f"No rows found for alignment: {alignment}")
    for row in matches:
        operation = operation_for(row["primary_relation"], row["modeling_consequence"])
        print(f"{row['id']}\t{row['claim_form']}")
        print(f"primary_relation\t{row['primary_relation']}")
        if row["secondary_relations"]:
            print(f"secondary_relations\t{row['secondary_relations']}")
        print(f"operation\t{operation}")
        print(f"consequence\t{row['modeling_consequence']}")
        if row.get("coding_rationale"):
            print(f"rationale\t{row['coding_rationale']}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SCF review gate.")
    parser.add_argument(
        "--coding",
        default="case_coding.tsv",
        help="Path to the anonymized SCF coding table.",
    )
    parser.add_argument(
        "--alignment",
        help="Optional alignment label to inspect, for example C1=C2.",
    )
    parser.add_argument(
        "--cases",
        default="alignment_cases.tsv",
        help="Path to SCF comparison vectors for rule execution.",
    )
    parser.add_argument(
        "--check-cases",
        action="store_true",
        help="Execute the alpha decision rule on the alignment case vectors.",
    )
    parser.add_argument(
        "--compare-baselines",
        action="store_true",
        help="Compare simple merge-licensing baselines against the SCF rule.",
    )
    parser.add_argument(
        "--ablation-cases",
        default="dimension_ablation_cases.tsv",
        help="Path to one-dimension ablation witness vectors.",
    )
    parser.add_argument(
        "--check-ablation",
        action="store_true",
        help="Check that each SCF dimension prevents at least one unsafe merge.",
    )
    args = parser.parse_args()

    if args.check_cases:
        check_alignment_cases(Path(args.cases))
        return
    if args.compare_baselines:
        compare_baselines(Path(args.cases))
        return
    if args.check_ablation:
        check_ablation_cases(Path(args.ablation_cases))
        return

    rows = load_rows(Path(args.coding))
    if args.alignment:
        query(rows, args.alignment)
    else:
        summarize(rows)


if __name__ == "__main__":
    main()
