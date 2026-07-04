#!/usr/bin/env python3
"""
Submission entrypoint — the single command that produces submission.csv from candidates.jsonl.

    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Runs CPU-only, no network, within the 5-minute budget. Dense candidate embeddings and the JD
embedding are precomputed once (see offline_embedder.py); this ranking step only loads them.
"""

import argparse
import os
import sys

from run_ranking import run_pipeline


def main():
    ap = argparse.ArgumentParser(description="Redrob Senior AI Engineer candidate ranker")
    ap.add_argument("--candidates", default="../candidates.jsonl",
                    help="Path to candidates.jsonl")
    ap.add_argument("--out", default="submission.csv", help="Output CSV path")
    ap.add_argument("--embeddings", default="candidate_embeddings.npy",
                    help="Precomputed candidate embeddings (.npy)")
    ap.add_argument("--ids", default="candidate_ids.npy",
                    help="Candidate ids aligned to embeddings (.npy)")
    ap.add_argument("--jd-embedding", default="jd_embedding.npy",
                    help="Precomputed JD embedding (.npy)")
    ap.add_argument("--top-k", type=int, default=100)
    args = ap.parse_args()

    if not os.path.exists(args.candidates):
        sys.exit(f"Candidates file not found: {args.candidates}")

    run_pipeline(args.candidates, args.out,
                 embeddings_path=args.embeddings, ids_path=args.ids,
                 jd_emb_path=args.jd_embedding, top_k=args.top_k)


if __name__ == "__main__":
    main()
