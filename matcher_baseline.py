#!/usr/bin/env python3
"""Matcher baselines for the SCF alignment cases.

This script deliberately ignores SCF dimensions. It scores candidate claim pairs
with label-only matchers and then reports how many high-scoring candidates would
still be disallowed by the executable SCF rule.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from collections import Counter
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


def tfidf_vectors(documents: list[str]) -> list[dict[str, float]]:
    tokenized = [tokens(document) for document in documents]
    doc_count = len(documents)
    document_frequencies = Counter(
        token for document_tokens in tokenized for token in document_tokens
    )
    vectors = []
    for document, document_tokens in zip(documents, tokenized):
        term_counts = Counter(
            token
            for token in re.findall(r"[a-z0-9]+", document.lower())
            if token in document_tokens
        )
        vector = {}
        for token, count in term_counts.items():
            idf = math.log((1 + doc_count) / (1 + document_frequencies[token])) + 1
            vector[token] = count * idf
        vectors.append(vector)
    return vectors


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    shared = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def load_cases(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def run(path: Path, top_k: int) -> None:
    rows = load_cases(path)
    documents = [value for row in rows for value in (row["left_claim"], row["right_claim"])]
    vectors = tfidf_vectors(documents)
    scored = []
    for row in rows:
        index = len(scored) * 2
        left = row["left_claim"]
        right = row["right_claim"]
        lexical = jaccard(left, right)
        sequence = sequence_ratio(left, right)
        hybrid = (lexical + sequence) / 2
        tfidf = cosine(vectors[index], vectors[index + 1])
        alpha = alpha_for(row)
        scored.append(
            {
                "row": row,
                "alpha": alpha,
                "hybrid": hybrid,
                "jaccard": lexical,
                "sequence": sequence,
                "tfidf": tfidf,
            }
        )

    print(f"candidate_pairs\t{len(rows)}")
    for score_name in ("hybrid", "tfidf"):
        retrieved = sorted(scored, key=lambda item: item[score_name], reverse=True)[:top_k]
        disallowed = [item for item in retrieved if item["alpha"] != "equiv"]
        merge_safe = [item for item in retrieved if item["alpha"] == "equiv"]
        print(f"retrieval\tlabel_{score_name}_top_{top_k}")
        print(f"retrieved_pairs\t{len(retrieved)}")
        print(f"scf_merge_safe_retrieved\t{len(merge_safe)}")
        print(f"scf_disallowed_retrieved\t{len(disallowed)}")
    print()
    print("top_label_matches")
    for item in sorted(scored, key=lambda item: item["hybrid"], reverse=True)[:5]:
        row = item["row"]
        print(
            f"{row['case_id']}\thybrid={item['hybrid']:.3f}\t"
            f"tfidf={item['tfidf']:.3f}\talpha={item['alpha']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the label-only matcher baselines.")
    parser.add_argument("--cases", default="alignment_cases.tsv")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    run(Path(args.cases), args.top_k)


if __name__ == "__main__":
    main()
