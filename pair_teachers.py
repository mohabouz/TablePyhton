import csv
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set, FrozenSet

from timetable_pairing.constants import DAYS
from timetable_pairing.models import Teacher
from timetable_pairing.io_csv import read_timetable, load_pairs_file
from timetable_pairing.scoring import per_day_breakdown
from timetable_pairing.matching import balanced_bottleneck_matching

def write_pairs_csv(out_path: Path, teachers: List[Teacher], pairs: List[Tuple[int, int, Dict[str, int]]], leftover: Optional[int]) -> None:
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "Teacher A",
            "Teacher B",
            "A hours",
            "B hours",
            "Overlap (both work)",
            "Complement slots (XOR)",
            "Both off",
            "Coverage %",
        ])
        total_slots = len(teachers[0].slots) if teachers else 48
        for i, j, s in pairs:
            coverage_pct = round(100 * s["coverage"] / total_slots, 1)
            w.writerow([
                teachers[i].name,
                teachers[j].name,
                teachers[i].hours,
                teachers[j].hours,
                s["overlap"],
                s["xor"],
                s["both_off"],
                coverage_pct,
            ])
        if leftover is not None:
            w.writerow([])
            w.writerow(["Unpaired", teachers[leftover].name, teachers[leftover].hours])

def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: pair_teachers.py <TimeTable.csv> [--out pairs.csv]", file=sys.stderr)
        return 2

    in_csv = Path(argv[1])
    out_csv: Optional[Path] = None
    forbidden: Set[FrozenSet[str]] = set()
    forced: Set[FrozenSet[str]] = set()

    i = 2
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out_csv = Path(argv[i + 1])
            i += 2
        # balanced is default; no objective flag
        elif argv[i] == "--forbid-pair" and i + 2 < len(argv):
            a = argv[i + 1].strip()
            b = argv[i + 2].strip()
            if a and b and a != b:
                forbidden.add(frozenset({a, b}))
            i += 3
        elif argv[i] == "--forbid-file" and i + 1 < len(argv):
            fpath = Path(argv[i + 1])
            if not fpath.exists():
                print(f"Forbidden pairs file not found: {fpath}", file=sys.stderr)
                return 2
            forbidden |= load_pairs_file(fpath)
            i += 2
        elif argv[i] == "--force-pair" and i + 2 < len(argv):
            a = argv[i + 1].strip()
            b = argv[i + 2].strip()
            if a and b and a != b:
                forced.add(frozenset({a, b}))
            i += 3
        elif argv[i] == "--force-file" and i + 1 < len(argv):
            fpath = Path(argv[i + 1])
            if not fpath.exists():
                print(f"Forced pairs file not found: {fpath}", file=sys.stderr)
                return 2
            forced |= load_pairs_file(fpath)
            i += 2
        else:
            i += 1

    if out_csv is None:
        out_csv = in_csv.with_name("teacher_pairs.csv")

    teachers = read_timetable(in_csv)

    if not teachers:
        print("No teachers parsed from CSV.")
        return 1

    # Always run balanced matching, honoring forbidden and forced pairs
    try:
        # If a pair is both forbidden and forced, let forced override forbidden
        if forced:
            forbidden = set(p for p in forbidden if p not in forced)
        pairs = balanced_bottleneck_matching(teachers, forbidden=forbidden, forced_pairs=forced)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2

    used = set()
    for i, j, _ in pairs:
        used.add(i)
        used.add(j)
    leftover = None
    for idx in range(len(teachers)):
        if idx not in used:
            leftover = idx
            break

    write_pairs_csv(out_csv, teachers, pairs, leftover)

    # Console summary
    print(f"Parsed {len(teachers)} teachers from {in_csv.name}")
    print("Objective: balanced")
    if forbidden:
        print(f"Forbidden pairs count: {len(forbidden)}")
    if forced:
        print(f"Forced pairs count: {len(forced)}")
    print(f"Generated {len(pairs)} pairs. Output -> {out_csv}")
    if leftover is not None:
        print(f"Unpaired: {teachers[leftover].name} ({teachers[leftover].hours} h)")

    # Show top 10 with mini breakdown
    print("\nTop pairs (up to 10):")
    total_slots = len(teachers[0].slots) if teachers else 48
    for idx, (i, j, s) in enumerate(pairs[:10], 1):
        coverage_pct = round(100 * s["coverage"] / total_slots)
        print(
            f"{idx:2d}. {teachers[i].name} ({teachers[i].hours}h) ⟷ {teachers[j].name} ({teachers[j].hours}h) | "
            f"XOR={s['xor']}, overlap={s['overlap']}, both-off={s['both_off']}, coverage={coverage_pct}%"
        )

    # Optional: print per-day breakdown for the best pair
    if pairs:
        i0, j0, _ = pairs[0]
        print("\nBest pair per-day breakdown:")
        day_rows = per_day_breakdown(teachers[i0], teachers[j0])
        for d, row in enumerate(day_rows):
            print(f"  {DAYS[d]}: XOR={row['xor']}, overlap={row['overlap']}, both-off={row['both_off']}")


    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
