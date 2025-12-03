# Traffic LOS (Hourly by Intersection)

This project computes hourly Level of Service (LOS) per intersection (`INTID`) from 15-minute turning movement counts, and provides plots. Terminal output prints all hourly rows, grouped by `INTID` then `hour`.

## Scripts
- `los_calc.py`: Loads the CSV, computes hourly LOS per `INTID`, prints all rows, and saves results to CSV.
- `los_plots.py`: Generates plots from the same CSV (hourly total volume, daily average volume, and a heatmap).

## Input CSV format
- File includes two header note lines, then the header row: `DATE,TIME,INTID,NBL,NBT,NBR,SBL,SBT,SBR,EBL,EBT,EBR,WBL,WBT,WBR`.
- Data rows may have a trailing comma; the code drops any unnamed extra column.
- `TIME` values can be Excel-style (e.g., `="0000"`, `="0015"`); the code normalizes to `HH:MM`.
- The loader finds the header line, skips only lines before it, and reads with `index_col=False` to ensure `DATE` isn’t used as an index.

## LOS logic
- Movement columns: `NBL,NBT,NBR,SBL,SBT,SBR,EBL,EBT,EBR,WBL,WBT,WBR`.
- Per 15-minute interval:
  - `total_volume = sum(movement columns)`
  - LOS by volume threshold:
    - A ≤ 600, B ≤ 900, C ≤ 1200, D ≤ 1500, E ≤ 1800, F > 1800
  - Map LOS to score: A=1, B=2, C=3, D=4, E=5, F=6
- Per hour per `INTID`:
  - Average the four 15-minute `los_score` values in that hour
  - Round to nearest integer; map back to LOS letter
- Output is sorted by `INTID`, then `hour`.

## Setup (macOS, zsh)

```zsh
cd /Users/kshrugal/Desktop/Traffic_Los
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Usage

Compute hourly LOS and print all rows:
```zsh
python los_calc.py --csv "VehicleVolume_1Wal_2Hwy_4Hwy_11162025_11222025.csv" --out los_results.csv
```

Generate plots:
```zsh
python los_plots.py --csv "VehicleVolume_1Wal_2Hwy_4Hwy_11162025_11222025.csv" --plot-prefix "los"
```

## Outputs
- Terminal: All hourly rows printed as `INTID <id> | <hour> | volume=<sum> | LOS=<letter> | score=<1-6>`.
- File: `los_results.csv` with columns `INTID,hour,total_volume,LOS,los_score`.
- Plots:
  - `los_hourly_volume.png` — Hourly total volume per `INTID`
  - `los_daily_avg_volume.png` — Average daily total volume per `INTID`
  - `los_volume_heatmap.png` — Heatmap of total volume (INTID × hour)

## Notes
- If parsing fails, verify the CSV has the described header and that the first two lines are notes.
- `TIME` normalization converts Excel formulas to `HH:MM` before datetime parsing.
- We use explicit datetime formats (`%m/%d/%Y %H:%M`) and only fall back to generic parsing if needed.
