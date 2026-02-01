# services/trainer/calibrate_threshold.py

import sys
import pandas as pd

def main():
    if len(sys.argv) != 2:
        print("Usage: python calibrate_threshold.py <scored_csv_path>")
        sys.exit(1)

    path = sys.argv[1]
    df = pd.read_csv(path)

    if "anomaly_score" not in df.columns:
        raise ValueError("CSV must contain anomaly_score column")

    scores = df["anomaly_score"]

    print("Score percentiles (lower = more anomalous):")
    for p in [1, 5, 10]:
        print(f" {p}% : {scores.quantile(p/100):.6f}")

    print("\nSuggested thresholds:")
    print(f"  Conservative (1%) : {scores.quantile(0.01):.6f}")
    print(f"  Balanced (5%)     : {scores.quantile(0.05):.6f}")
    print(f"  Sensitive (10%)   : {scores.quantile(0.10):.6f}")

if __name__ == "__main__":
    main()
