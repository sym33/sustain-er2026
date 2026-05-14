#!/usr/bin/env python3
"""Compare an LLM-assisted SCF recoding against the validation table."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


DIMENSIONS = [
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
]


def normalize(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare LLM recoding with SCF validation coding.")
    parser.add_argument("recoding", type=Path, help="TSV file produced by an LLM recoder")
    parser.add_argument("--gold", type=Path, default=Path("case_coding.tsv"), help="Gold coding TSV")
    args = parser.parse_args()

    gold_rows = {row["id"]: row for row in read_tsv(args.gold)}
    recoded_rows = read_tsv(args.recoding)
    dimension_matches = Counter()
    relation_matches = Counter()
    disagreements: list[tuple[str, str, str, str]] = []
    unknown_ids: list[str] = []

    for row in recoded_rows:
        row_id = row.get("id", "")
        gold = gold_rows.get(row_id)
        if gold is None:
            unknown_ids.append(row_id)
            continue
        for dim in DIMENSIONS:
            if normalize(row.get(dim, "")) == normalize(gold.get(dim, "")):
                dimension_matches["match"] += 1
            else:
                dimension_matches["mismatch"] += 1
                disagreements.append((row_id, dim, gold.get(dim, ""), row.get(dim, "")))
        if normalize(row.get("primary_relation", "")) == normalize(gold.get("primary_relation", "")):
            relation_matches["match"] += 1
        else:
            relation_matches["mismatch"] += 1
            disagreements.append((row_id, "primary_relation", gold.get("primary_relation", ""), row.get("primary_relation", "")))

    print(f"gold_rows\t{len(gold_rows)}")
    print(f"recoded_rows\t{len(recoded_rows)}")
    print(f"unknown_ids\t{len(unknown_ids)}")
    print(f"dimension_matches\t{dimension_matches['match']}")
    print(f"dimension_mismatches\t{dimension_matches['mismatch']}")
    print(f"exploratory_primary_relation_matches\t{relation_matches['match']}")
    print(f"exploratory_primary_relation_mismatches\t{relation_matches['mismatch']}")
    print("note\tprimary_relation comparison is diagnostic only unless the recoder received full candidate-pair context")

    if disagreements:
        print("\nfirst disagreements")
        for row_id, field, gold_value, recoded_value in disagreements[:30]:
            print(f"{row_id}\t{field}\tgold={gold_value}\trecoded={recoded_value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
