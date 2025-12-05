# Traffic LOS Analysis

This repository computes hourly Level of Service (LOS) per intersection (`INTID`) from 15-minute turning movement data, and provides scripts to summarize worst/best times and average scores. All scripts print clear tables to the terminal and save results to CSV.

## Components
- `los_calc.py`: Ingests the raw CSV, normalizes timestamps, computes hourly LOS per `INTID`, prints all rows, and saves `los_results.csv`.
- `worst_los_summary.py`: Summarizes worst LOS times per `INTID` showing only unique time-of-day (HH:MM) without dates or repetition; saves `worst_los_summary.csv`.
- `best_los_summary.py`: Summarizes best LOS times per `INTID` showing only unique time-of-day (HH:MM) without dates or repetition; saves `best_los_summary.csv`.
- `average_los_by_intersection.py`: Averages hourly LOS scores per `INTID` (no rounding), maps to letters with stricter bands, and saves `average_los_by_intersection.csv`.
- `plot_intersection_volumes.py`: Generates a single chart with average hourly volumes (hour-of-day 0–23) across all days, one line per intersection color-coded by INTID; saves `plots/intersections_hourly_average.png`.

## Input CSV Requirements
- Header row: `DATE,TIME,INTID,NBL,NBT,NBR,SBL,SBT,SBR,EBL,EBT,EBR,WBL,WBT,WBR` (two note lines above are allowed).
- Trailing commas: Allowed; unnamed extra columns are dropped.
- `TIME` normalization: Excel-style values (e.g., `="0000"`) are converted to `HH:MM`.
- Robust header detection ensures only pre-header lines are skipped; `index_col=False` preserves all columns.

## LOS Computation
- Movements aggregated: `NBL,NBT,NBR,SBL,SBT,SBR,EBL,EBT,EBR,WBL,WBT,WBR`.
- Per 15-minute interval:
  - `total_volume` = sum of movement columns
  - Strict thresholds (15-min totals) to increase grade variety: A ≤ 100, B ≤ 200, C ≤ 350, D ≤ 500, E ≤ 700, F > 700
  - Score mapping: A=1, B=2, C=3, D=4, E=5, F=6
- Hourly per `INTID`:
  - Average the four 15-min scores for that hour and round to nearest integer, then map to LOS
  - Output rows are ordered by `INTID` then `hour`
- Intersection averages (across hours):
  - Average hourly scores per `INTID` with no rounding; letter mapping uses harsher bands: A < 1.2, B < 2.0, C < 2.8, D < 3.6, E < 4.4, else F

## Setup
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
- Worst summary (unique times + table):
```zsh
python worst_los_summary.py --source los_results.csv --out worst_los_summary.csv --top 10
```
- Best summary (unique times + table):
```zsh
python best_los_summary.py --source los_results.csv --out best_los_summary.csv --top 10
```
- Average hourly score per intersection:
```zsh
python average_los_by_intersection.py --source los_results.csv --out average_los_by_intersection.csv
```
- Plot average hourly volumes:
```zsh
python plot_intersection_volumes.py --csv los_results.csv --outdir plots
```

## Outputs
- Terminal (hourly LOS): `INTID <id> | <hour> | volume=<sum> | LOS=<letter> | score=<1-6>`
- Terminal (worst/best): `INTID <id> | Worst/Best LOS <letter> (score <1-6>) | Times: HH:MM, HH:MM, ...`
- Terminal (average): `INTID <id> | AvgHourlyScore <float> | LOS <letter>`
- Files:
  - `los_results.csv`: `INTID,hour,total_volume,LOS,los_score`
  - `worst_los_summary.csv`: worst LOS per `INTID` with unique time-of-day list
  - `best_los_summary.csv`: best LOS per `INTID` with unique time-of-day list
  - `average_los_by_intersection.csv`: average hourly score and letter per `INTID`
  - `plots/intersections_hourly_average.png`: single chart with average hourly volumes by hour-of-day (0–23) for INTIDs 1–5 (SW Regional Airport Blvd & SW I ST, Greenhouse & E Centerton Blvd, N Walton & Tiger Blvd, SW 14th ST & SW I ST, SW Regional Airport Blvd & SE Walton Blvd)

## Notes & Practices
- Parsing resilience: Explicit format parsing with safe fallbacks; fallback warnings suppressed only when necessary.
- Data hygiene: Unnamed columns from trailing commas are dropped; movement columns coerced to numeric.
- Extensibility: Thresholds and average-to-letter bands can be parameterized via CLI; hourly aggregation can switch from mean to max if emphasizing peak conditions is desired.
