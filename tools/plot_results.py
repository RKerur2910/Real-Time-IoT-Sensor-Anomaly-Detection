# tools/plot_results.py
import sys
import glob
import os
import pandas as pd
import matplotlib.pyplot as plt

DEFAULT_GLOB = "data/feature_windows_scored_*.csv"

def pick_latest_csv(pattern: str = DEFAULT_GLOB) -> str:
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(
            f"No files match '{pattern}'. Run the consumer first to generate a scored CSV."
        )
    files.sort(key=os.path.getmtime)
    return files[-1]

def main():
    # Usage:
    #   python tools/plot_results.py
    #   python tools/plot_results.py data/feature_windows_scored_20260131_105244.csv
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = pick_latest_csv()

    print(f"Reading: {path}")
    df = pd.read_csv(path)

    # Parse timestamps
    if "ts" in df.columns:
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
        df = df.dropna(subset=["ts"]).sort_values("ts")
    else:
        raise KeyError("CSV missing 'ts' column.")

    # Safety: some older files might miss these columns
    for col in ["anomaly_score", "is_anomaly", "alert_active", "gas_ppm_mean", "root_cause"]:
        if col not in df.columns:
            df[col] = 0 if col != "root_cause" else ""

    # ---- Plot 1: Anomaly score over time ----
    plt.figure()
    plt.plot(df["ts"], df["anomaly_score"])
    plt.title("Anomaly Score vs Time")
    plt.xlabel("Time")
    plt.ylabel("anomaly_score (higher = more normal)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.show()

    # ---- Plot 2: Alert active (0/1) over time ----
    plt.figure()
    plt.plot(df["ts"], df["alert_active"])
    plt.title("Alert Active vs Time")
    plt.xlabel("Time")
    plt.ylabel("alert_active (0/1)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.show()

    # ---- Plot 3: Gas mean over time (to visually confirm spike/stuck) ----
    plt.figure()
    plt.plot(df["ts"], df["gas_ppm_mean"])
    plt.title("Gas Mean (gas_ppm_mean) vs Time")
    plt.xlabel("Time")
    plt.ylabel("gas_ppm_mean")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.show()

    # ---- Quick summary ----
    alerts = int(df["alert_active"].sum())
    anomalies = int(df["is_anomaly"].sum())
    print(f"Rows: {len(df)} | anomalies: {anomalies} | alert_active sum: {alerts}")

    # Root cause counts (only meaningful when alert_active=1)
    rc = df.loc[df["alert_active"] == 1, "root_cause"].value_counts()
    if len(rc) > 0:
        print("\nRoot cause counts (during alerts):")
        print(rc.to_string())
    else:
        print("\nNo alerts in this file (root_cause summary empty).")

if __name__ == "__main__":
    main()
