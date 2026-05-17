#!/usr/bin/env python3
"""Label-only matcher baseline for the SCF alignment cases.

This script deliberately ignores SCF dimensions. It scores candidate claim pairs
with simple label matchers and then reports how many high-scoring candidates
would still be disallowed by the executable SCF rule.
"""

from __future__ import annotations

import argparse
import csv
import re
from difflib import SequenceMatcher
from pathlib import Path

from scf_review_gate import alpha_for


STOPWORDS = {
    "a",
    "an",
    "and",
    "by",
    "claim",
    "corporate",
    "earlier",
    "externally",
    "later",
    "same",
    "target",
    "the",
    "to",
    "updated",
    "with",
}


def tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def jaccard(left: str, right: str) -> float:
    left_tokens = tokens(left)
    right_tokens = tokens(right)
    if not left_tokens and not right_tokens:
        return 1.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def sequence_ratio(left: str, right: str) -> float:
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()


def load_cases(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def run(path: Path, top_k: int) -> None:
    rows = load_cases(path)
    scored = []
    for row in rows:
        left = row["left_claim"]
        right = row["right_claim"]
        lexical = jaccard(left, right)
        sequence = sequence_ratio(left, right)
        hybrid = (lexical + sequence) / 2
        alpha = alpha_for(row)
        scored.append((hybrid, lexical, sequence, row, alpha))

    retrieved = sorted(scored, reverse=True)[:top_k]
    disallowed = [item for item in retrieved if item[4] != "equiv"]
    merge_safe = [item for item in retrieved if item[4] == "equiv"]

    print(f"candidate_pairs\t{len(rows)}")
    print(f"retrieval\tlabel_hybrid_top_{top_k}")
    print(f"retrieved_pairs\t{len(retrieved)}")
    print(f"scf_merge_safe_retrieved\t{len(merge_safe)}")
    print(f"scf_disallowed_retrieved\t{len(disallowed)}")
    print()
    print("top_label_matches")
    for hybrid, lexical, sequence, row, alpha in sorted(scored, reverse=True)[:5]:
        print(
            f"{row['case_id']}\thybrid={hybrid:.3f}\t"
            f"jaccard={lexical:.3f}\tsequence={sequence:.3f}\talpha={alpha}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the label-only matcher baseline.")
    parser.add_argument("--cases", default="alignment_cases.tsv")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    run(Path(args.cases), args.top_k)


if __name__ == "__main__":
    main()
