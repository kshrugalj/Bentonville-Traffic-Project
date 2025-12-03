import argparse
import sys
from typing import List

import pandas as pd


SCORE_TO_LOS = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F"}


def compute_intersection_averages(df: pd.DataFrame) -> pd.DataFrame:
    required = {"INTID", "hour", "los_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in source CSV: {sorted(missing)}")

    out = df.copy()
    out["los_score"] = pd.to_numeric(out["los_score"], errors="coerce")
    out = out.dropna(subset=["INTID", "hour", "los_score"])  

    # Average hourly scores per intersection across the dataset (no rounding)
    avg = (
        out.groupby("INTID", as_index=False)["los_score"].mean()
        .rename(columns={"los_score": "avg_hourly_score"})
    )
    # Derive LOS letter from average without rounding using mid-point bands
    def score_to_letter(x: float) -> str:
        if pd.isna(x):
            return ""
        # Harsher bands to produce lower letters for the same average
        if x < 1.2:
            return "A"
        elif x < 2.0:
            return "B"
        elif x < 2.8:
            return "C"
        elif x < 3.6:
            return "D"
        elif x < 4.4:
            return "E"
        else:
            return "F"

    avg["avg_LOS"] = avg["avg_hourly_score"].apply(score_to_letter)

    # Order by INTID ascending (lowest to highest)
    avg = avg.sort_values(["INTID"], ascending=[True]).reset_index(drop=True)
    return avg[["INTID", "avg_hourly_score", "avg_LOS"]]


def print_terminal(avg_df: pd.DataFrame) -> None:
    print("Average of hourly LOS scores per intersection (no rounding):")
    header = f"{'INTID':<6} {'AvgHourlyScore':<15} {'LOS':<3}"
    print(header)
    print("-" * len(header))
    for _, row in avg_df.iterrows():
        print(f"{str(row['INTID']):<6} {row['avg_hourly_score']:<15.2f} {row['avg_LOS']:<3}")


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Average hourly LOS scores per intersection from los_results.csv (no rounding)")
    parser.add_argument("--source", default="los_results.csv", help="Path to hourly LOS results CSV (default: los_results.csv)")
    parser.add_argument("--out", default="average_los_by_intersection.csv", help="Path to save intersection averages CSV")
    args = parser.parse_args(argv)

    try:
        df = pd.read_csv(args.source)
    except FileNotFoundError:
        print(f"Source file not found: {args.source}. Run 'python los_calc.py' first to generate hourly LOS.")
        return 1

    avg_df = compute_intersection_averages(df)
    avg_df.to_csv(args.out, index=False)
    print_terminal(avg_df)
    print(f"\nSaved intersection averages to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
