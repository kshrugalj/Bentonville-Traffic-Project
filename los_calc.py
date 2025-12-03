import argparse
import os
import pandas as pd

MOVEMENT_COLUMNS = [
    "NBL", "NBT", "NBR",
    "SBL", "SBT", "SBR",
    "EBL", "EBT", "EBR",
    "WBL", "WBT", "WBR",
]

LOS_THRESHOLDS = [
    (600, "A"),
    (900, "B"),
    (1200, "C"),
    (1500, "D"),
    (1800, "E"),
]

LOS_TO_SCORE = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}


def compute_los_from_volume(total_vol: float) -> str:
    for threshold, los in LOS_THRESHOLDS:
        if total_vol <= threshold:
            return los
    return "F"


def load_and_prepare(csv_path: str) -> pd.DataFrame:
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    # Detect header row
    header_line_idx = None
    total_lines = 0
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            total_lines = i + 1
            if "DATE" in line and "TIME" in line and "INTID" in line:
                header_line_idx = i
                break
    
    if header_line_idx is None:
        raise ValueError(
            f"Could not find header row with DATE,TIME,INTID columns in {csv_path}.\n"
            f"File has {total_lines} lines. Please check the CSV format."
        )

    # Read with the detected header row
    # skiprows expects lines to skip BEFORE reading header
    skip_lines = list(range(header_line_idx))
    df = pd.read_csv(
        csv_path,
        sep=",",
        engine="python",
        skiprows=skip_lines,
        header=0,
        index_col=False,
        on_bad_lines="skip",
        skipinitialspace=True,
    )
    
    # Drop any unnamed columns (from trailing commas)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed', na=False)]
    
    if df.empty:
        raise ValueError(f"No data rows found in {csv_path} after parsing.")

    # Ensure required columns
    expected_cols = ["DATE", "TIME", "INTID"] + MOVEMENT_COLUMNS
    df = df[[c for c in df.columns if c in expected_cols]]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = 0
    df = df[expected_cols]

    # Normalize TIME like ="0000" -> 00:00
    t = df["TIME"].astype(str).str.strip()
    t = t.str.replace('="', '', regex=False).str.replace('"', '', regex=False).str.replace('=', '', regex=False)
    t = t.str.replace(r"[^0-9]", "", regex=True).str.zfill(4)
    t = t.str.replace(r"^(\d{2})(\d{2})$", r"\1:\2", regex=True)
    t = t.where(t.str.match(r"^\d{2}:\d{2}$"), "00:00")
    df["TIME"] = t

    # Build datetime
    combo = (df["DATE"].astype(str).str.strip() + " " + df["TIME"].astype(str).str.strip()).str.strip()
    dt = pd.to_datetime(combo, format="%m/%d/%Y %H:%M", errors="coerce")
    if dt.isna().all():
        dt = pd.to_datetime(combo, format="%m/%d/%Y %H:%M:%S", errors="coerce")
    if dt.isna().all():
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dt = pd.to_datetime(combo, errors="coerce")
    if dt.isna().all():
        dt = pd.to_datetime(df["DATE"].astype(str).str.strip(), format="%m/%d/%Y", errors="coerce").dt.floor("D")
    df["datetime"] = dt

    # Coerce movements numeric
    for col in MOVEMENT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def compute_hourly_los(df: pd.DataFrame) -> pd.DataFrame:
    df["hour"] = df["datetime"].dt.floor("h")
    df["total_volume"] = df[MOVEMENT_COLUMNS].sum(axis=1)
    
    # Compute LOS for each 15-min interval
    df["LOS"] = df["total_volume"].apply(compute_los_from_volume)
    df["los_score"] = df["LOS"].map(LOS_TO_SCORE)
    
    # Group by INTID and hour, take average of 15-min scores
    grouped = df.groupby(["INTID", "hour"], as_index=False).agg({
        "total_volume": "sum",
        "los_score": "mean"
    })
    
    # Round average score and map back to LOS letter
    grouped["los_score"] = grouped["los_score"].round().astype(int)
    score_to_los = {v: k for k, v in LOS_TO_SCORE.items()}
    grouped["LOS"] = grouped["los_score"].map(score_to_los)
    
    return grouped


def main():
    parser = argparse.ArgumentParser(description="Compute hourly LOS by intersection and print to terminal")
    default_candidates = [
        os.path.join(os.getcwd(), "VehicleVolume_1Wal_2Hwy_4Hwy_11162025_11222025.csv"),
        "/Users/kshrugal/Desktop/Traffic_Los/VehicleVolume_1Wal_2Hwy_4Hwy_11162025_11222025.csv",
    ]
    default_csv = next((p for p in default_candidates if os.path.isfile(p)), default_candidates[0])
    parser.add_argument("--csv", default=default_csv, help="Path to input CSV")
    parser.add_argument("--out", default="los_results.csv", help="Optional output CSV")

    args = parser.parse_args()

    df = load_and_prepare(args.csv)
    grouped = compute_hourly_los(df)

    rows = grouped.sort_values(["INTID", "hour"])
    print("Hourly LOS by intersection:")
    for _, row in rows.iterrows():
        print(f"INTID {row['INTID']} | {row['hour']} | volume={int(row['total_volume'])} | LOS={row['LOS']} | score={int(row['los_score'])}")

    if args.out:
        rows.to_csv(args.out, index=False)
        print(f"Saved results to {args.out}")


if __name__ == "__main__":
    main()
