import argparse
import sys
from typing import List

import pandas as pd


SCORE_TO_LOS = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F"}


def format_hour(value) -> str:
    """
    Format the 'hour' field for display.
    Accepts pandas Timestamp, datetime, or string.
    Returns a string in 'YYYY-MM-DD HH:MM' format when possible.
    """
    try:
        ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return str(value)
        return ts.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)


def build_per_intersection_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each INTID, find the maximum los_score and list all hours with that worst score.
    Returns a DataFrame with: INTID, worst_score, worst_LOS, worst_hours (comma-separated).
    """
    # Ensure expected columns exist
    required = {"INTID", "hour", "los_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in source CSV: {sorted(missing)}")

    # Coerce types
    df = df.copy()
    df["los_score"] = pd.to_numeric(df["los_score"], errors="coerce")
    df = df.dropna(subset=["INTID", "hour", "los_score"])  # drop rows without essentials

    # Compute worst score per intersection
    worst_scores = df.groupby("INTID", as_index=False)["los_score"].max().rename(columns={"los_score": "worst_score"})

    # Join back to get all rows where intersection hits its worst score
    merged = df.merge(worst_scores, on="INTID")
    worst_rows = merged[merged["los_score"] == merged["worst_score"]]

    # Aggregate hours per intersection
    # Build both a list (for compact display) and a flat string (for CSV)
    summary = (
        worst_rows
        .groupby(["INTID", "worst_score"], as_index=False)
        .agg({
            "hour": list,
        })
        .rename(columns={"hour": "worst_hours_list"})
    )

    # Add prettified string for CSV
    summary["worst_hours"] = summary["worst_hours_list"].apply(
        lambda lst: ", ".join(sorted({format_hour(x) for x in lst}))
    )

    # Add worst LOS letter (prefer from SCORE_TO_LOS mapping)
    summary["worst_LOS"] = summary["worst_score"].map(SCORE_TO_LOS).fillna("")

    # Order by INTID
    summary = summary.sort_values(["INTID"]).reset_index(drop=True)
    return summary[["INTID", "worst_score", "worst_LOS", "worst_hours", "worst_hours_list"]]


def build_overall_worst(df: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """
    Return top-N worst hours across all intersections, sorted by los_score desc then total_volume desc.
    Includes columns: INTID, hour, los_score, LOS, total_volume.
    """
    cols_needed = ["INTID", "hour", "los_score"]
    for c in cols_needed:
        if c not in df.columns:
            raise ValueError(f"Missing required column '{c}' in source CSV")

    out = df.copy()
    out["los_score"] = pd.to_numeric(out["los_score"], errors="coerce")
    if "total_volume" in out.columns:
        out["total_volume"] = pd.to_numeric(out["total_volume"], errors="coerce")
    else:
        out["total_volume"] = pd.NA

    if "LOS" not in out.columns:
        out["LOS"] = out["los_score"].map(SCORE_TO_LOS)

    out = out.dropna(subset=["INTID", "hour", "los_score"])  # essential rows only

    # Sort by score desc then volume desc, pick top N
    out_sorted = out.sort_values(["los_score", "total_volume"], ascending=[False, False])
    result = out_sorted.head(top).copy()
    result["hour"] = result["hour"].map(format_hour)
    return result[["INTID", "hour", "los_score", "LOS", "total_volume"]]


def _compress_times(times: List[pd.Timestamp]) -> List[str]:
    """Compress a list of times (same date) into ranges like '07:00–08:00; 15:00–17:00'."""
    # Normalize to Timestamp and sort
    ts_list = [pd.to_datetime(t, errors="coerce") for t in times]
    ts_list = [t for t in ts_list if pd.notna(t)]
    ts_list.sort()
    # Extract just time components in minutes from midnight
    minutes = [t.hour * 60 + t.minute for t in ts_list]
    if not minutes:
        return []
    # Detect consecutive hours (60 min steps)
    ranges = []
    start = minutes[0]
    prev = minutes[0]
    for m in minutes[1:]:
        if m == prev + 60:
            prev = m
            continue
        else:
            # close previous range
            start_str = f"{start//60:02d}:{start%60:02d}"
            end_str = f"{prev//60:02d}:{prev%60:02d}"
            ranges.append(start_str if start == prev else f"{start_str}–{end_str}")
            start = prev = m
    # close final range
    start_str = f"{start//60:02d}:{start%60:02d}"
    end_str = f"{prev//60:02d}:{prev%60:02d}"
    ranges.append(start_str if start == prev else f"{start_str}–{end_str}")
    return ranges


def _format_worst_hours_compact(hour_list: List) -> List[str]:
    """Group by date and compress consecutive hours; return lines like '- 2025-11-17: 07:00–08:00; 15:00–16:00' or 'All hours'."""
    ts_list = [pd.to_datetime(h, errors="coerce") for h in hour_list]
    ts_list = [t for t in ts_list if pd.notna(t)]
    if not ts_list:
        return []
    # Group by date
    df = pd.DataFrame({"ts": ts_list})
    df["date"] = df["ts"].dt.date
    grouped = df.groupby("date")
    lines = []
    all_hours_set = {f"{h:02d}:00" for h in range(24)}
    for date, g in grouped:
        # Build set of hour strings
        time_strs = sorted({f"{t.hour:02d}:{t.minute:02d}" for t in g["ts"]})
        if set(time_strs) == all_hours_set:
            lines.append(f"- {date}: All hours")
            continue
        # Compress consecutive hours
        ranges = _compress_times(list(g["ts"]))
        lines.append(f"- {date}: {'; '.join(ranges)}")
    return sorted(lines)


def print_summary(per_int: pd.DataFrame, overall: pd.DataFrame) -> None:
    print("Worst LOS per intersection:")
    for _, row in per_int.iterrows():
        print(f"INTID {row['INTID']} | Worst LOS {row['worst_LOS']} (score {int(row['worst_score'])})")
        lines = _format_worst_hours_compact(row.get("worst_hours_list", []))
        for line in lines:
            print(line)

    print("\nOverall worst hours across intersections:")
    # Aligned table header
    header = f"{'INTID':<6} {'Date':<10} {'Time':<5} {'LOS':<3} {'Score':<5} {'Volume':<7}"
    print(header)
    print("-" * len(header))
    for _, row in overall.iterrows():
        ts = pd.to_datetime(row["hour"], errors="coerce")
        date_str = ts.strftime("%Y-%m-%d") if pd.notna(ts) else str(row["hour"])[:10]
        time_str = ts.strftime("%H:%M") if pd.notna(ts) else str(row["hour"])[-5:]
        vol = row.get("total_volume")
        vol_str = f"{int(vol):<7}" if pd.notna(vol) else f"{'-':<7}"
        print(f"{str(row['INTID']):<6} {date_str:<10} {time_str:<5} {row['LOS']:<3} {int(row['los_score']):<5} {vol_str}")


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize worst LOS times per intersection and overall.")
    parser.add_argument("--source", default="los_results.csv", help="Path to hourly LOS results CSV (default: los_results.csv)")
    parser.add_argument("--out", default="worst_los_summary.csv", help="Path to save per-intersection worst summary CSV")
    parser.add_argument("--top", type=int, default=10, help="Top-N overall worst entries to display (default: 10)")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.source)
    except FileNotFoundError:
        print(f"Source file not found: {args.source}. Run 'python los_calc.py' first to generate hourly LOS.")
        return 1

    # Build summaries
    per_int = build_per_intersection_summary(df)
    overall = build_overall_worst(df, top=args.top)

    # Save per-intersection summary (drop the list column for CSV)
    save_df = per_int.drop(columns=["worst_hours_list"], errors="ignore")
    save_df.to_csv(args.out, index=False)

    # Print to terminal
    print_summary(per_int, overall)
    print(f"\nSaved per-intersection worst summary to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
