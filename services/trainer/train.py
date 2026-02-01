import os
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

DATA_PATH = "data/feature_windows.csv"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "model_v1.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler_v1.joblib")

def main():
    df = pd.read_csv(DATA_PATH)

    # Remove timestamp
    X = df.drop(columns=["ts"], errors="ignore")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_scaled)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    print("✅ Model trained and saved")
    print("Model:", MODEL_PATH)
    print("Scaler:", SCALER_PATH)
    print(f"Rows: {len(df)}, Features: {X.shape[1]}")

if __name__ == "__main__":
    main()