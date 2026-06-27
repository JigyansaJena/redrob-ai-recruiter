#!/usr/bin/env python3
"""
rank.py — Redrob Hackathon Submission Script
---------------------------------------------
Usage:
    python rank.py --candidates ./data/sample_candidates.json --out ./submission.csv
    python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
    python rank.py --candidates ./data/candidates.jsonl.gz --out ./submission.csv

Produces a valid submission CSV with top 100 ranked candidates.
Runs fully offline — no API calls, no GPU needed.
Must complete in under 5 minutes for 100K candidates.
"""

import argparse
import csv
import gzip
import json
import os
import sys
import time

# Add backend folder to path so we can import scorer
sys.path.insert(0, os.path.dirname(__file__))
from scorer import rank_candidates, score_candidate


# ════════════════════════════════════════════════════════════════════════════
# FILE LOADERS — supports .json, .jsonl, .jsonl.gz
# ════════════════════════════════════════════════════════════════════════════

def load_candidates(filepath: str) -> list[dict]:
    """
    Loads candidates from:
    - .json  → a JSON array (like sample_candidates.json)
    - .jsonl → one JSON object per line
    - .jsonl.gz → gzipped JSONL (the real 100K dataset)
    """
    print(f"Loading candidates from: {filepath}")

    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    candidates = []

    # ── Gzipped JSONL (the real dataset) ────────────────────────────────────
    if filepath.endswith(".jsonl.gz"):
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    candidates.append(json.loads(line))

    # ── Plain JSONL ──────────────────────────────────────────────────────────
    elif filepath.endswith(".jsonl"):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    candidates.append(json.loads(line))

    # ── JSON array (sample file) ─────────────────────────────────────────────
    elif filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                candidates = data
            else:
                candidates = [data]

    else:
        print(f"ERROR: Unknown file format: {filepath}")
        print("Supported: .json, .jsonl, .jsonl.gz")
        sys.exit(1)

    print(f"Loaded {len(candidates):,} candidates")
    return candidates


# ════════════════════════════════════════════════════════════════════════════
# CSV WRITER — produces valid submission file
# ════════════════════════════════════════════════════════════════════════════

def write_submission_csv(ranked: list[dict], output_path: str, team_id: str = "team_001"):
    """
    Writes the ranked candidates to a CSV file.
    Follows exact spec from submission_spec.md:
    - Exactly 100 rows
    - Columns: candidate_id, rank, score, reasoning
    - Scores non-increasing
    - UTF-8 encoding
    """
    # Make sure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header row
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        # Data rows — exactly 100
        for result in ranked[:100]:
            writer.writerow([
                result["candidate_id"],
                result["rank"],
                f"{result['final_score']:.4f}",
                result["reasoning"]
            ])

    print(f"\nSubmission CSV written to: {output_path}")
    print(f"Total rows: {min(len(ranked), 100)}")


# ════════════════════════════════════════════════════════════════════════════
# VALIDATION — check our own output before submitting
# ════════════════════════════════════════════════════════════════════════════

def validate_output(output_path: str) -> bool:
    """
    Quick self-check on the CSV we just wrote.
    Catches common mistakes before submission.
    """
    print("\nValidating output...")
    errors = []

    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Check header
    if rows[0] != ["candidate_id", "rank", "score", "reasoning"]:
        errors.append(f"Wrong header: {rows[0]}")

    data_rows = rows[1:]

    # Check row count
    if len(data_rows) != 100:
        errors.append(f"Expected 100 data rows, got {len(data_rows)}")

    ranks_seen = set()
    ids_seen = set()
    prev_score = float("inf")

    for i, row in enumerate(data_rows):
        if len(row) != 4:
            errors.append(f"Row {i+2}: expected 4 columns, got {len(row)}")
            continue

        cid, rank_s, score_s, reasoning = row

        # Check candidate ID format
        if not cid.startswith("CAND_") or len(cid) != 12:
            errors.append(f"Row {i+2}: invalid candidate_id: {cid}")

        # Check rank
        try:
            rank = int(rank_s)
            if rank in ranks_seen:
                errors.append(f"Row {i+2}: duplicate rank {rank}")
            ranks_seen.add(rank)
        except ValueError:
            errors.append(f"Row {i+2}: invalid rank: {rank_s}")

        # Check score
        try:
            score = float(score_s)
            if score > prev_score + 0.0001:
                errors.append(f"Row {i+2}: score not non-increasing ({score} > {prev_score})")
            prev_score = score
        except ValueError:
            errors.append(f"Row {i+2}: invalid score: {score_s}")

        # Check duplicate IDs
        if cid in ids_seen:
            errors.append(f"Row {i+2}: duplicate candidate_id: {cid}")
        ids_seen.add(cid)

    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("Validation PASSED! Submission is ready.")
        return True


# ════════════════════════════════════════════════════════════════════════════
# PRETTY PRINT — show top results in terminal
# ════════════════════════════════════════════════════════════════════════════

def print_results(ranked: list[dict], show_n: int = 15):
    """Print a nice summary of top ranked candidates."""

    print("\n" + "=" * 70)
    print(f"{'RANK':<6} {'NAME':<22} {'TITLE':<28} {'SCORE':<8} {'LOC'}")
    print("=" * 70)

    for r in ranked[:show_n]:
        name = r.get("name", "")[:20]
        title = r.get("title", "")[:26]
        score = r["final_score"]
        loc = r.get("location", "")[:15]
        rank = r["rank"]

        # Score bar
        bar_len = int(score * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)

        print(f"#{rank:<5} {name:<22} {title:<28} {score:.3f}  {loc}")

    print("=" * 70)
    print(f"\nBottom 5 (lowest scores):")
    for r in ranked[-5:]:
        print(f"  #{r['rank']} {r.get('name', '')} | {r.get('title', '')} | {r['final_score']:.3f}")


# ════════════════════════════════════════════════════════════════════════════
# SCORE BREAKDOWN — useful for debugging
# ════════════════════════════════════════════════════════════════════════════

def print_score_breakdown(ranked: list[dict], show_n: int = 10):
    """Print detailed score breakdown for top N candidates."""
    print(f"\n{'DETAILED SCORE BREAKDOWN — TOP ' + str(show_n)}")
    print("-" * 80)

    headers = f"{'#':<4} {'Name':<20} {'Car':>5} {'Sem':>5} {'Beh':>5} {'Ski':>5} {'Log':>5} {'TOTAL':>7}"
    print(headers)
    print("-" * 80)

    for r in ranked[:show_n]:
        name = r.get("name", "")[:18]
        print(
            f"#{r['rank']:<3} {name:<20} "
            f"{r.get('career_score', 0):>5.2f} "
            f"{r.get('semantic_score', 0):>5.2f} "
            f"{r.get('behavioral_score', 0):>5.2f} "
            f"{r.get('skills_score', 0):>5.2f} "
            f"{r.get('logistics_score', 0):>5.2f} "
            f"{r['final_score']:>7.4f}"
        )


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Redrob Hackathon — Candidate Ranker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run on sample data (50 candidates):
  python backend/rank.py --candidates data/sample_candidates.json --out submission.csv

  # Run on full dataset (100K candidates):
  python backend/rank.py --candidates data/candidates.jsonl.gz --out submission.csv

  # Run with custom team ID in filename:
  python backend/rank.py --candidates data/sample_candidates.json --out submission.csv --team team_redrob
        """
    )

    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to candidates file (.json, .jsonl, or .jsonl.gz)"
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output CSV path (e.g. ./submission.csv)"
    )
    parser.add_argument(
        "--team",
        default="team_001",
        help="Your team ID (used in output filename if needed)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=100,
        help="Number of candidates to include in output (default: 100)"
    )
    parser.add_argument(
        "--show",
        type=int,
        default=15,
        help="Number of results to display in terminal (default: 15)"
    )

    args = parser.parse_args()

    # ── Start timing ─────────────────────────────────────────────────────────
    start_time = time.time()

    print("=" * 60)
    print("  REDROB AI HACKATHON — Candidate Ranker")
    print("=" * 60)

    # ── Load candidates ───────────────────────────────────────────────────────
    candidates = load_candidates(args.candidates)

    # ── Rank them ─────────────────────────────────────────────────────────────
    ranked = rank_candidates(candidates, top_n=args.top)

    # ── Print results ─────────────────────────────────────────────────────────
    print_results(ranked, show_n=args.show)
    print_score_breakdown(ranked, show_n=10)

    # ── Write CSV ─────────────────────────────────────────────────────────────
    write_submission_csv(ranked, args.out, team_id=args.team)

    # ── Validate output ───────────────────────────────────────────────────────
    validate_output(args.out)

    # ── Time report ───────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.1f} seconds")

    if elapsed > 300:
        print("WARNING: Took over 5 minutes! Optimize before submitting.")
    else:
        print(f"Within 5-minute limit ({300 - elapsed:.0f}s to spare)")

    print("\nDone! Submit your CSV file to the hackathon portal.")


if __name__ == "__main__":
    main()