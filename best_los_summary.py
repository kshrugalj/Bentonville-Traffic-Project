import argparse
import sys
from typing import List

import pandas as pd


SCORE_TO_LOS = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F"}


def format_hour(value) -> str:
    try:
        ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return str(value)
        return ts.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)


def _compress_times(times: List[pd.Timestamp]) -> List[str]:
    ts_list = [pd.to_datetime(t, errors="coerce") for t in times]
    ts_list = [t for t in ts_list if pd.notna(t)]
    ts_list.sort()
    minutes = [t.hour * 60 + t.minute for t in ts_list]
    if not minutes:
        return []
    ranges = []
    start = minutes[0]
    prev = minutes[0]
    for m in minutes[1:]:
        if m == prev + 60:
            prev = m
            continue
        else:
            start_str = f"{start//60:02d}:{start%60:02d}"
            end_str = f"{prev//60:02d}:{prev%60:02d}"
            ranges.append(start_str if start == prev else f"{start_str}–{end_str}")
            start = prev = m
    start_str = f"{start//60:02d}:{start%60:02d}"
    end_str = f"{prev//60:02d}:{prev%60:02d}"
    ranges.append(start_str if start == prev else f"{start_str}–{end_str}")
    return ranges


def _format_hours_compact(hour_list: List) -> List[str]:
    """Extract unique times (HH:MM) without dates, sorted and deduplicated."""
    ts_list = [pd.to_datetime(h, errors="coerce") for h in hour_list]
    ts_list = [t for t in ts_list if pd.notna(t)]
    if not ts_list:
        return []
    # Extract unique time-of-day strings
    time_strs = sorted({f"{t.hour:02d}:{t.minute:02d}" for t in ts_list})
    # Return as comma-separated string wrapped in a list
    return [', '.join(time_strs)]


def build_per_intersection_best(df: pd.DataFrame) -> pd.DataFrame:
    required = {"INTID", "hour", "los_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in source CSV: {sorted(missing)}")

    df = df.copy()
    df["los_score"] = pd.to_numeric(df["los_score"], errors="coerce")
    df = df.dropna(subset=["INTID", "hour", "los_score"]) 

    # Minimum score per intersection (best)
    best_scores = df.groupby("INTID", as_index=False)["los_score"].min().rename(columns={"los_score": "best_score"})
    merged = df.merge(best_scores, on="INTID")
    best_rows = merged[merged["los_score"] == merged["best_score"]]

    summary = (
        best_rows
        .groupby(["INTID", "best_score"], as_index=False)
        .agg({"hour": list})
        .rename(columns={"hour": "best_hours_list"})
    )
    summary["best_hours"] = summary["best_hours_list"].apply(
        lambda lst: ", ".join(sorted({format_hour(x) for x in lst}))
    )
    summary["best_LOS"] = summary["best_score"].map(SCORE_TO_LOS).fillna("")
    summary = summary.sort_values(["INTID"]).reset_index(drop=True)
    return summary[["INTID", "best_score", "best_LOS", "best_hours", "best_hours_list"]]


def build_overall_best(df: pd.DataFrame, top: int = 10) -> pd.DataFrame:
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

    out = out.dropna(subset=["INTID", "hour", "los_score"]) 

    # Sort by score asc (best first), then volume asc (lower volume typical for best)
    out_sorted = out.sort_values(["los_score", "total_volume"], ascending=[True, True])
    result = out_sorted.head(top).copy()
    result["hour"] = result["hour"].map(format_hour)
    return result[["INTID", "hour", "los_score", "LOS", "total_volume"]]


def print_summary(per_int: pd.DataFrame, overall: pd.DataFrame) -> None:
    print("Best LOS per intersection:")
    for _, row in per_int.iterrows():
        lines = _format_hours_compact(row.get("best_hours_list", []))
        times_str = lines[0] if lines else "No data"
        print(f"INTID {row['INTID']} | Best LOS {row['best_LOS']} (score {int(row['best_score'])}) | Times: {times_str}")

    print("\nOverall best hours across intersections:")
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
    parser = argparse.ArgumentParser(description="Summarize best LOS times per intersection and overall.")
    parser.add_argument("--source", default="los_results.csv", help="Path to hourly LOS results CSV (default: los_results.csv)")
    parser.add_argument("--out", default="best_los_summary.csv", help="Path to save per-intersection best summary CSV")
    parser.add_argument("--top", type=int, default=10, help="Top-N overall best entries to display (default: 10)")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.source)
    except FileNotFoundError:
        print(f"Source file not found: {args.source}. Run 'python los_calc.py' first to generate hourly LOS.")
        return 1

    per_int = build_per_intersection_best(df)
    overall = build_overall_best(df, top=args.top)

    save_df = per_int.drop(columns=["best_hours_list"], errors="ignore")
    save_df.to_csv(args.out, index=False)

    print_summary(per_int, overall)
    print(f"\nSaved per-intersection best summary to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
