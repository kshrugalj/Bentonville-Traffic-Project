# Traffic LOS Analysis

This program analyzes a CSV of traffic counts and computes per-hour Level of Service (LOS) tiers for each lane using a simple v/c (volume-to-capacity) formula.

## Assumptions
- CSV contains a timestamp column (e.g., `datetime`, `timestamp`, `time`, or `date`). The script attempts to auto-detect and parse it.
- Lane volumes are either:
  - Long format: columns like `lane` (identifier) and `volume`/`count` for measured vehicles, or
  - Wide format: multiple numeric columns representing lane counts (e.g., `Lane1`, `Lane2`, `Hwy4`, etc.).
- Counts can be summed per hour (`--aggregation sum`, default) or averaged (`--aggregation mean`).

## LOS Formula
We compute $v/c$ per lane per hour using an assumed per-lane capacity. Default capacity is `1900 veh/hr/lane`.

LOS tiers by $v/c$:
- A: $\le 0.35$
- B: $\le 0.54$
- C: $\le 0.77$
- D: $\le 0.93$
- E: $\le 1.00$
- F: $> 1.00$

These thresholds are heuristic and intended for quick screening. Adjust capacity using `--capacity` to reflect local conditions.

## Quick Start (macOS, zsh)

```zsh
# From the workspace folder
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# Option 1: Original lane-based analyzer
python analyze_traffic_los.py "VehicleVolume_1Wal_2Hwy_4Hwy_11162025_11222025.csv" \
  --capacity 1900 \
  --aggregation sum \
  --out los_results.csv

# Option 2: Hourly LOS by intersection with plots
python los_by_intersection.py \
  --csv "VehicleVolume_1Wal_2Hwy_4Hwy_11162025_11222025.csv" \
  --out "los_by_intersection.csv" \
  --plot-prefix "los"
```

- Results preview prints to console; full output saved to `los_results.csv`.
- Adjust `--capacity` if you have better local capacity estimates.

## Notes
- If the script cannot infer the datetime or lane columns, open the CSV to verify column names and consider renaming them to include `datetime`/`timestamp` and `lane`/`volume`.
- For custom logic (e.g., speed-based LOS), we can extend the script to incorporate speed and density if present.
