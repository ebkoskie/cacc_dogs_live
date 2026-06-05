#!/usr/bin/env python3
"""
One-time backfill: recover lost 'Found At', 'is_chipped', and 'Stray Hold Date'
values for outcome dogs (Adopted, RTO, Transferred) by mining git history
of dogs_active.csv.

When a dog leaves the shelter the website clears the "Found At" field.
The scraper then returns an empty value which was overwriting the stored
value during the DuckDB merge (fixed in PR #82). This script recovers
the data from old snapshots of dogs_active.csv preserved in git history.

Usage:
    python scripts/backfill_found_at.py          # dry-run (preview only)
    python scripts/backfill_found_at.py --apply  # write changes to CSV
"""

import argparse
import csv
import io
import subprocess
import sys
from pathlib import Path


HISTORIC_CSV = Path("dogs_historic.csv")
ACTIVE_CSV = "dogs_active.csv"

# Fields to recover from git history
FIELDS_TO_RECOVER = ["Found At", "is_chipped", "Stray Hold Date"]


def get_outcome_ids(historic_path: Path) -> dict[str, dict[str, str]]:
    """Return {dog_id: {field: current_value}} for outcome dogs needing backfill."""
    targets = {}
    with open(historic_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = row.get("Status", "")
            if status in ("Available", "Pending", ""):
                continue
            # Check if any recoverable field is empty
            missing = {
                field: row.get(field, "").strip()
                for field in FIELDS_TO_RECOVER
            }
            if any(not v for v in missing.values()):
                targets[row["id"]] = missing
    return targets


def get_commit_list() -> list[str]:
    """Get all commit hashes that touched dogs_active.csv."""
    result = subprocess.run(
        ["git", "log", "--oneline", "--all", "--", ACTIVE_CSV],
        capture_output=True, text=True, check=True,
    )
    return [line.split()[0] for line in result.stdout.strip().split("\n") if line]


def scan_commit(commit: str, remaining_ids: set[str]) -> dict[str, dict[str, str]]:
    """Parse one commit's dogs_active.csv and extract fields for target IDs."""
    result = subprocess.run(
        ["git", "show", f"{commit}:{ACTIVE_CSV}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return {}

    found = {}
    reader = csv.DictReader(io.StringIO(result.stdout))
    for row in reader:
        dog_id = row.get("id", "")
        if dog_id not in remaining_ids:
            continue
        values = {}
        for field in FIELDS_TO_RECOVER:
            val = row.get(field, "").strip()
            if val:
                values[field] = val
        if values:
            found[dog_id] = values
    return found


def apply_backfill(historic_path: Path, recovered: dict[str, dict[str, str]]) -> int:
    """Update the historic CSV with recovered values. Returns rows updated."""
    rows = []
    updated = 0
    with open(historic_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            dog_id = row.get("id", "")
            if dog_id in recovered:
                changed = False
                for field, value in recovered[dog_id].items():
                    if not row.get(field, "").strip():
                        row[field] = value
                        changed = True
                if changed:
                    updated += 1
            rows.append(row)

    with open(historic_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write changes to CSV (default is dry-run)")
    args = parser.parse_args()

    if not HISTORIC_CSV.exists():
        print(f"Error: {HISTORIC_CSV} not found. Run from project root.", file=sys.stderr)
        sys.exit(1)

    # 1. Find target IDs
    targets = get_outcome_ids(HISTORIC_CSV)
    print(f"Outcome dogs with missing data: {len(targets)}")
    if not targets:
        print("Nothing to backfill.")
        return

    # 2. Get commits
    commits = get_commit_list()
    print(f"Commits to scan: {len(commits)}")

    # 3. Scan commits
    recovered = {}  # dog_id -> {field: value}
    remaining = set(targets.keys())

    for i, commit in enumerate(commits):
        if not remaining:
            break
        batch = scan_commit(commit, remaining)
        for dog_id, values in batch.items():
            if dog_id not in recovered:
                recovered[dog_id] = {}
            for field, val in values.items():
                if field not in recovered[dog_id]:
                    recovered[dog_id][field] = val
            # Check if all fields recovered for this dog
            if all(
                recovered[dog_id].get(f) or targets[dog_id].get(f)
                for f in FIELDS_TO_RECOVER
            ):
                remaining.discard(dog_id)

        if (i + 1) % 200 == 0:
            print(f"  Scanned {i + 1}/{len(commits)} commits, recovered {len(recovered)} dogs so far...")

    # 4. Summary
    found_at_count = sum(1 for v in recovered.values() if v.get("Found At"))
    chipped_count = sum(1 for v in recovered.values() if v.get("is_chipped"))
    hold_count = sum(1 for v in recovered.values() if v.get("Stray Hold Date"))

    print("\n--- Recovery Summary ---")
    print(f"  Found At recovered:       {found_at_count}")
    print(f"  is_chipped recovered:     {chipped_count}")
    print(f"  Stray Hold Date recovered: {hold_count}")
    print(f"  Dogs still missing data:  {len(remaining)}")

    if not recovered:
        print("No data to recover.")
        return

    # 5. Apply or preview
    if args.apply:
        updated = apply_backfill(HISTORIC_CSV, recovered)
        print(f"\n✅ Updated {updated} rows in {HISTORIC_CSV}")
    else:
        print("\nDry-run complete. Use --apply to write changes.")
        # Show a few samples
        samples = list(recovered.items())[:5]
        for dog_id, values in samples:
            print(f"  {dog_id}: {values}")


if __name__ == "__main__":
    main()
