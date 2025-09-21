import csv
from pathlib import Path
from typing import List, Optional, Set, FrozenSet

from .constants import DAYS
from .models import Teacher


def read_timetable(csv_path: Path) -> List[Teacher]:
    rows: List[List[str]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if row is not None:
                rows.append(row)

    header: Optional[List[str]] = None
    data_rows: List[List[str]] = []
    for row in rows:
        if not row:
            continue
        first = (row[0] or "").strip()
        if first == "الاسم" or first.lower() == "name":
            header = row
            continue
        data_rows.append(row)

    def infer_slots_from_header(hdr: List[str]) -> Optional[int]:
        cells = hdr[1:] if len(hdr) > 1 else []
        if cells:
            last = (cells[-1] or "").strip().lower()
            if "h" in last or "hour" in last or "ساعات" in last or "ساعة" in last:
                cells = cells[:-1]
        count = len(cells)
        return count if count % len(DAYS) == 0 else None

    def infer_slots_from_row(r: List[str]) -> Optional[int]:
        cells = r[1:] if len(r) > 1 else []
        last_non_empty_idx: Optional[int] = None
        for idx in range(len(cells) - 1, -1, -1):
            val = (cells[idx] or "").strip()
            if val:
                last_non_empty_idx = idx
                low = val.lower()
                if "h" in low:
                    cells = cells[:idx]
                break
        count = len(cells)
        return count if count % len(DAYS) == 0 else None

    inferred: Optional[int] = None
    if header:
        inferred = infer_slots_from_header(header)
    if inferred is None and data_rows:
        inferred = infer_slots_from_row(data_rows[0])
    if inferred in (48, 60):
        total_slots = inferred
    else:
        total_slots = 48

    teachers: List[Teacher] = []
    for row in data_rows:
        if not row:
            continue
        name = (row[0] or "").strip()
        cells = row[1:]

        hours: Optional[int] = None
        last_non_empty_idx: Optional[int] = None
        for idx in range(len(cells) - 1, -1, -1):
            val = (cells[idx] or "").strip()
            if val:
                last_non_empty_idx = idx
                low = val.lower()
                if "h" in low:
                    num_part = low.replace("h", "").strip()
                    try:
                        hours = int(num_part)
                    except Exception:
                        hours = None
                break

        slot_cells = cells
        if last_non_empty_idx is not None and "h" in (cells[last_non_empty_idx] or "").lower():
            slot_cells = cells[: last_non_empty_idx]

        slot_cells = slot_cells[:total_slots]
        if len(slot_cells) < total_slots:
            slot_cells = slot_cells + [""] * (total_slots - len(slot_cells))

        slots = [1 if (c or "").strip().lower() == "x" else 0 for c in slot_cells]
        if hours is None:
            hours = sum(slots)

        teachers.append(Teacher(name=name, slots=slots, hours=hours))

    return teachers


def load_pairs_file(path: Path) -> Set[FrozenSet[str]]:
    pairs: Set[FrozenSet[str]] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        # Skip header if present
        for row in reader:
            if not row:
                continue
            a = (row[0] or "").strip()
            b = (row[1] or "").strip() if len(row) > 1 else ""
            if a and b and a != b and a.lower() != "teacher a":
                pairs.add(frozenset({a, b}))
    return pairs
