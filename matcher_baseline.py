#!/usr/bin/env python3
"""Matcher baselines for the SCF alignment cases.

This script deliberately ignores SCF dimensions. It scores candidate claim pairs
with label-only and ClimateBERT matchers and then reports how many high-scoring
candidates would still be disallowed by the executable SCF rule.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from scf_review_gate import alpha_for


DEFAULT_BERT_MODEL = "climatebert/distilroberta-base-climate-s"


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


def dense_cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def bert_embeddings(documents: list[str], model_name: str) -> list[list[float]]:
    """Return mean-pooled transformer embeddings when optional deps are present."""
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    try:
        import torch
        from huggingface_hub.utils import logging as hub_logging
        from transformers import logging as transformers_logging
        from transformers import AutoModel, AutoTokenizer
    except ImportError as error:
        raise RuntimeError("install transformers and torch to run the BERT baseline") from error

    hub_logging.set_verbosity_error()
    transformers_logging.set_verbosity_error()
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
    except Exception as error:
        raise RuntimeError(f"could not load BERT model {model_name}: {error}") from error
    model.eval()
    encoded = tokenizer(documents, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        output = model(**encoded)
    token_embeddings = output.last_hidden_state
    attention_mask = encoded["attention_mask"].unsqueeze(-1).expand(token_embeddings.size()).float()
    summed = (token_embeddings * attention_mask).sum(dim=1)
    counts = attention_mask.sum(dim=1).clamp(min=1e-9)
    return (summed / counts).cpu().tolist()


def load_cases(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def run(path: Path, top_k: int, bert_model: str | None, include_tfidf: bool) -> None:
    rows = load_cases(path)
    documents = [value for row in rows for value in (row["left_claim"], row["right_claim"])]
    vectors = tfidf_vectors(documents)
    bert_vectors = None
    bert_error = None
    if bert_model:
        try:
            bert_vectors = bert_embeddings(documents, bert_model)
        except RuntimeError as error:
            bert_error = str(error)
    scored = []
    for row in rows:
        index = len(scored) * 2
        left = row["left_claim"]
        right = row["right_claim"]
        lexical = jaccard(left, right)
        sequence = sequence_ratio(left, right)
        hybrid = (lexical + sequence) / 2
        tfidf = cosine(vectors[index], vectors[index + 1])
        bert = (
            dense_cosine(bert_vectors[index], bert_vectors[index + 1])
            if bert_vectors is not None
            else None
        )
        alpha = alpha_for(row)
        scored.append(
            {
                "row": row,
                "alpha": alpha,
                "hybrid": hybrid,
                "jaccard": lexical,
                "sequence": sequence,
                "tfidf": tfidf,
                "bert": bert,
            }
        )

    print(f"candidate_pairs\t{len(rows)}")
    score_names = ["hybrid"]
    if include_tfidf:
        score_names.append("tfidf")
    if bert_vectors is not None:
        score_names.append("bert")
    for score_name in score_names:
        retrieved = sorted(scored, key=lambda item: item[score_name], reverse=True)[:top_k]
        disallowed = [item for item in retrieved if item["alpha"] != "equiv"]
        merge_safe = [item for item in retrieved if item["alpha"] == "equiv"]
        print(f"retrieval\tlabel_{score_name}_top_{top_k}")
        print(f"retrieved_pairs\t{len(retrieved)}")
        print(f"scf_merge_safe_retrieved\t{len(merge_safe)}")
        print(f"scf_disallowed_retrieved\t{len(disallowed)}")
    if bert_error:
        print(f"bert_baseline_unavailable\t{bert_error}")
    print()
    print("top_label_matches")
    for item in sorted(scored, key=lambda item: item["hybrid"], reverse=True)[:5]:
        row = item["row"]
        bert_value = f"{item['bert']:.3f}" if item["bert"] is not None else "na"
        fields = [
            row["case_id"],
            f"hybrid={item['hybrid']:.3f}",
            f"bert={bert_value}",
            f"alpha={item['alpha']}",
        ]
        if include_tfidf:
            fields.insert(2, f"tfidf={item['tfidf']:.3f}")
        print("\t".join(fields))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the label-only matcher baselines.")
    parser.add_argument("--cases", default="alignment_cases.tsv")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--bert-model",
        default=DEFAULT_BERT_MODEL,
        help="Optional Hugging Face transformer model for mean-pooled BERT embeddings.",
    )
    parser.add_argument(
        "--no-bert",
        action="store_true",
        help="Skip the optional BERT baseline.",
    )
    parser.add_argument(
        "--include-tfidf",
        action="store_true",
        help="Also report the legacy TF-IDF matcher baseline.",
    )
    args = parser.parse_args()
    run(
        Path(args.cases),
        args.top_k,
        None if args.no_bert else args.bert_model,
        args.include_tfidf,
    )


if __name__ == "__main__":
    main()
