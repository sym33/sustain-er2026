#!/usr/bin/env python3
"""Minimal SCF model-review gate for the ER 2026 supplementary material.

The script reads the anonymized case coding table and reports whether candidate
alignments are merge-safe or require governance actions such as qualifying,
splitting, tracing, translating, completing, or blocking.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


MERGE_SAFE = {"Equivalence with provenance"}


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
    args = parser.parse_args()

    rows = load_rows(Path(args.coding))
    if args.alignment:
        query(rows, args.alignment)
    else:
        summarize(rows)


if __name__ == "__main__":
    main()
