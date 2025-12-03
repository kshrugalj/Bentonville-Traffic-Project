# Traffic LOS Analysis

This repository computes hourly Level of Service (LOS) per intersection (`INTID`) from 15-minute turning movement data, summarizes worst/best times, and generates plots. Terminal output is designed for clear, comprehensive review.

## Components
- `los_calc.py`: Ingests raw CSV, normalizes timestamps, computes hourly LOS per `INTID`, prints all rows, saves `los_results.csv`.
- `worst_los_summary.py`: Summarizes worst LOS times per `INTID` (max severity), with compact date/hour ranges; saves `worst_los_summary.csv`.
- `best_los_summary.py`: Summarizes best LOS times per `INTID` (min severity), with compact date/hour ranges; saves `best_los_summary.csv`.

## Input CSV Requirements
- Structure: Two header note lines followed by header `DATE,TIME,INTID,NBL,NBT,NBR,SBL,SBT,SBR,EBL,EBT,EBR,WBL,WBT,WBR`.
- Trailing commas: Allowed; unnamed extra columns are dropped automatically.
- `TIME` normalization: Excel-style values like `="0000"` are converted to `HH:MM`.
- Robust header detection: Loader skips lines before the header and reads with `index_col=False` to preserve columns.

## LOS Computation
- Movements aggregated: `NBL,NBT,NBR,SBL,SBT,SBR,EBL,EBT,EBR,WBL,WBT,WBR`.
- Per 15-min interval:
  - `total_volume` = sum of movement columns
  - LOS thresholds (strict) per 15-min total: A ≤ 100, B ≤ 200, C ≤ 350, D ≤ 500, E ≤ 700, F > 700
  - Score mapping: A=1, B=2, C=3, D=4, E=5, F=6
- Hourly per `INTID`:
  - Average the four 15-min scores for that hour
  - Round to nearest integer and map back to LOS
- Sorting: Output rows are ordered by `INTID` then `hour`.

## Setup (macOS, zsh)
```zsh
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Usage
- Compute hourly LOS:
```zsh
python los_calc.py --csv "VehicleVolume_1Wal_2Hwy_4Hwy_11162025_11222025.csv" --out los_results.csv
```
- Worst summary (compact ranges + table):
```zsh
python worst_los_summary.py --source los_results.csv --out worst_los_summary.csv --top 10
```
- Best summary (compact ranges + table):
```zsh
python best_los_summary.py --source los_results.csv --out best_los_summary.csv --top 10
```
 

## Outputs
- Terminal (hourly LOS): `INTID <id> | <hour> | volume=<sum> | LOS=<letter> | score=<1-6>`.
- Files:
  - `los_results.csv`: `INTID,hour,total_volume,LOS,los_score`
  - `worst_los_summary.csv`: worst LOS per `INTID` with compact hour ranges
  - `best_los_summary.csv`: best LOS per `INTID` with compact hour ranges
 

## Notes & Practices
- Parsing resilience: Explicit format parsing with safe fallbacks; warnings suppressed only on fallback path.
- Data hygiene: Unnamed columns from trailing commas are dropped; movement columns are numeric-coerced.
- Extensibility: Thresholds can be parameterized if needed (e.g., via CLI); hourly aggregation can switch from mean to max to emphasize peak severity.
