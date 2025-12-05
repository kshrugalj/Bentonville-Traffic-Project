import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt


REQUIRED_COLUMNS = {"INTID", "hour", "total_volume"}

# Human-friendly intersection names keyed by INTID
INTID_NAMES = {
    1: "SW Regional Airport Blvd & SW I ST",
    2: "Greenhouse & E Centerton Blvd",
    3: "N Walton & Tiger Blvd",
    4: "SW 14th ST & SW I ST",
    5: "SW Regional Airport Blvd & SE Walton Blvd",
}


def load_hourly_results(csv_path: str) -> pd.DataFrame:
    """Load hourly results (from los_calc) and ensure types are correct."""
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns {missing} in {csv_path}. "
            "Run los_calc.py first to generate los_results.csv."
        )

    df = df[list(REQUIRED_COLUMNS)]
    df["hour"] = pd.to_datetime(df["hour"], errors="coerce")
    df = df.dropna(subset=["hour"])
    df["INTID"] = pd.to_numeric(df["INTID"], errors="coerce").astype(int)
    df["total_volume"] = pd.to_numeric(df["total_volume"], errors="coerce").fillna(0)
    return df.sort_values(["INTID", "hour"])


def plot_all_intersections_one_chart(df: pd.DataFrame, out_dir: str) -> None:
    """Single chart: average total volume by hour-of-day, one line per INTID."""
    os.makedirs(out_dir, exist_ok=True)

    df = df.copy()
    df["hour_of_day"] = df["hour"].dt.hour

    # Average total volume for each INTID at each hour-of-day across all days
    hourly_avg = (
        df.groupby(["INTID", "hour_of_day"], as_index=False)["total_volume"]
        .mean()
        .sort_values(["INTID", "hour_of_day"])
    )

    plt.figure(figsize=(12, 6))
    intids = [1, 2, 3, 4, 5]
    for intid in intids:
        sub = hourly_avg[hourly_avg["INTID"] == intid]
        if sub.empty:
            print(f"No data for INTID {intid}; skipping line plot.")
            continue
        label = INTID_NAMES.get(intid, f"INTID {intid}")
        plt.plot(
            sub["hour_of_day"],
            sub["total_volume"],
            marker="o",
            linewidth=1.8,
            label=label
        )

    plt.title("Average Hourly Volume by Intersection (One Day Profile)")
    plt.xlabel("Hour of Day")
    plt.ylabel("Average Total Volume")
    plt.xticks(range(0, 24))
    plt.grid(True, alpha=0.3)
    plt.legend(title="Intersection")
    plt.tight_layout()

    out_path = os.path.join(out_dir, "intersections_hourly_average.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Saved {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Plot average hourly volumes across days on one chart (INTIDs 1-5)."
    )
    parser.add_argument(
        "--csv",
        default="los_results.csv",
        help="Path to los_results.csv produced by los_calc.py",
    )
    parser.add_argument(
        "--outdir",
        default="plots",
        help="Directory to write the per-intersection plots",
    )
    args = parser.parse_args()

    df = load_hourly_results(args.csv)
    plot_all_intersections_one_chart(df, args.outdir)


if __name__ == "__main__":
    main()
