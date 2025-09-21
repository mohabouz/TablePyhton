# Teacher Pairing (Balanced Matching)

A small tool to pair teachers with complementary schedules from a timetable CSV using a balanced (minimax) matching objective. Supports forbidding specific pairs and forcing pairs, and adapts automatically to timetables with 4 or 5 slots per period (8 or 10 slots/day).

## Features

- Balanced pairing using graph matching (NetworkX)
- Forbid pairs (hard exclude)
- Force pairs (lock specific pairs, others match around them)
- Auto-detect 4 vs 5 slots per period from CSV header/data
- CSV outputs with XOR/overlap/both-off/coverage

## Project Layout

- `pair_teachers.py`: CLI entry that orchestrates I/O and matching
- `timetable_pairing/`
  - `constants.py`: common constants (`DAYS`)
  - `models.py`: `Teacher` dataclass
  - `io_csv.py`: CSV parsing for timetable and pairs
  - `scoring.py`: pair scoring + per-day breakdown
  - `matching.py`: balanced matching with forbidden/forced pairs
- CSV files:
  - `TimeTable.csv` / `timeTable5H.csv`: input timetable
  - `forbid.csv`: forbidden pairs (two columns)
  - `force.csv`: forced pairs (two columns)
  - `teacher_pairs*.csv`: generated outputs

## Input CSV Formats

### Timetable CSV
- First row header must include the first column as `الاسم` or `Name`.
- Subsequent columns are per-slot cells with `X` for working.
- The last non-empty cell per row may be the total hours (e.g., `17 h`), optional.
- The tool auto-detects whether there are 8 (4 per period) or 10 (5 per period) slots per day across 6 days.

Example (partial):
```
الاسم,Mon-1,Mon-2,...,Fri-10,Sat-10,17 h
Teacher 1,x,,x,...
```

### Forbidden / Forced Pairs CSV
- Two columns: `Teacher A,Teacher B`
- Header is optional; if present, it will be skipped.

Example:
```
Teacher A,Teacher B
Teacher X,Teacher Y
```


## Running

You can use a Python virtual environment (recommended for isolation), or install dependencies globally/system-wide.

### Option 1: With venv (recommended)
Create and activate a venv (Git Bash):
```bash
python -m venv .venv
source .venv/Scripts/activate
```
Install dependencies:
```bash
pip install networkx
```

### Option 2: System Python (no venv)
Just install dependencies globally (may require admin):
```bash
pip install networkx
```

---

Run with a standard 4-slot-per-period timetable:
```bash
python pair_teachers.py TimeTable.csv --out teacher_pairs_balanced.csv \
  --forbid-file forbid.csv --force-file force.csv
```

Run with a 5-slot-per-period timetable:
```bash
python pair_teachers.py timeTable5H.csv --out teacher_pairs_balanced.csv \
  --forbid-file forbid.csv --force-file force.csv
```

### CLI Options
- `--out <file>`: output CSV path
- `--forbid-pair "A" "B"`: forbid a single pair inline (repeatable)
- `--forbid-file <file>`: forbid pairs via CSV file
- `--force-pair "A" "B"`: force a single pair inline (repeatable)
- `--force-file <file>`: force pairs via CSV file

Notes:
- If the same pair is both forced and forbidden, the force wins.
- One teacher cannot be in more than one forced pair.

## Output CSV (`teacher_pairs_balanced.csv`)
Columns:
- `Teacher A, Teacher B, A hours, B hours, Overlap (both work), Complement slots (XOR), Both off, Coverage %`


## Troubleshooting
- `networkx` missing: `pip install networkx`
- Wrong slot count: ensure the header includes all slot columns; the tool expects total slots divisible by 6 (days). It supports 48 or 60 total slots.
- Non-UTF-8 CSV: files are read with `utf-8-sig` to handle BOM.

## License
Internal use. No explicit license.
