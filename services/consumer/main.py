# services/consumer/main.py

import csv
import json
import os
import time
from collections import deque
from typing import Any, Dict

import joblib
import pandas as pd
import paho.mqtt.client as mqtt

from shared.features import RollingWindow

BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "sensors/building1"

# Window + logging
WINDOW_SIZE = 60          # you changed this; keep it consistent across runs
PRINT_EVERY_SEC = 10

# Output: new file per run (no more deleting the same file)
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
RUN_ID = time.strftime("%Y%m%d_%H%M%S")
CSV_PATH = os.path.join(DATA_DIR, f"feature_windows_scored_{RUN_ID}.csv")

# --- Load model once ---
MODEL_PATH = "models/model_v1.joblib"
SCALER_PATH = "models/scaler_v1.joblib"
model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

# Threshold (OPTION A = Conservative 1% from your calibration on the scored file)
# If you calibrated and chose Option A: set it to the “1%” value you got.
# Example you showed: 1% : -0.649129
ANOMALY_THRESHOLD = -0.649129

FEATURE_NAMES = [
    "temp_c_mean","temp_c_std","temp_c_min","temp_c_max","temp_c_slope","temp_c_delta",
    "humidity_mean","humidity_std","humidity_min","humidity_max","humidity_slope","humidity_delta",
    "gas_ppm_mean","gas_ppm_std","gas_ppm_min","gas_ppm_max","gas_ppm_slope","gas_ppm_delta",
    "smoke_mean","smoke_std","smoke_min","smoke_max","smoke_slope","smoke_delta",
    "battery_v_mean","battery_v_std","battery_v_min","battery_v_max","battery_v_slope","battery_v_delta"
]

# --- Root-cause rules (simple, explainable heuristics) ---
ROOT_CAUSE_RULES = [
    ("gas_spike",   "gas_ppm_mean", 30),
    ("gas_stuck",   "gas_ppm_std",  0.05),
    ("temp_drift",  "temp_c_slope", 0.01),
    ("smoke_noise", "smoke_std",    0.05),
]

def root_cause(feats: Dict[str, float]) -> str:
    # Explicit and readable (and robust to missing keys)
    if feats.get("gas_ppm_mean", 0.0) > 30:
        return "gas_spike"
    if feats.get("gas_ppm_std", 999.0) < 0.05:
        return "gas_stuck"
    if abs(feats.get("temp_c_slope", 0.0)) > 0.01:
        return "temp_drift"
    if feats.get("smoke_std", 0.0) > 0.05:
        return "smoke_noise"
    return "unknown"

# --- Alert smoothing (reduces noisy one-off alerts) ---
ANOMALY_HISTORY = deque(maxlen=5)   # last 5 window decisions
ALERT_ON_COUNT = 3                 # ON if >=3 anomalies in last 5
ALERT_OFF_COUNT = 0                # OFF if 0 anomalies in last 5 (when full)
alert_state = 0

rw = RollingWindow(size=WINDOW_SIZE)
last_print = 0.0

# CSV writer (overwrite per run, no header fights)
csv_file = open(CSV_PATH, "w", newline="")
csv_writer = None

def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
    global last_print, csv_writer, alert_state

    # Parse JSON safely
    try:
        event: Dict[str, Any] = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        print("Bad JSON:", e)
        return

    # Minimal validation
    for k in ["ts", "temp_c", "humidity", "gas_ppm", "smoke", "battery_v"]:
        if k not in event:
            print("Missing key:", k)
            return

    rw.add(event)

    if not rw.ready():
        return

    feats = rw.features()

    # Model input with feature names (prevents sklearn warning)
    try:
        X_df = pd.DataFrame([[feats[f] for f in FEATURE_NAMES]], columns=FEATURE_NAMES)
    except KeyError as e:
        print("Feature missing from feats:", e)
        return

    X_scaled = scaler.transform(X_df)
    score = float(model.score_samples(X_scaled)[0])

    is_anomaly = int(score < ANOMALY_THRESHOLD)

    # Update alert smoothing history
    ANOMALY_HISTORY.append(is_anomaly)

    # Turn alert ON
    if sum(ANOMALY_HISTORY) >= ALERT_ON_COUNT:
        alert_state = 1

    # Turn alert OFF (only after we have a full buffer)
    if len(ANOMALY_HISTORY) == ANOMALY_HISTORY.maxlen and sum(ANOMALY_HISTORY) <= ALERT_OFF_COUNT:
        alert_state = 0

    alert_active = int(alert_state)

    # Root cause only when alert is active
    cause = root_cause(feats) if alert_active else ""

    row = {
        "ts": event["ts"],
        **feats,
        "anomaly_score": score,
        "is_anomaly": is_anomaly,
        "alert_active": alert_active,
        "root_cause": cause,
    }

    if csv_writer is None:
        csv_writer = csv.DictWriter(csv_file, fieldnames=row.keys())
        csv_writer.writeheader()

    csv_writer.writerow(row)
    csv_file.flush()

    # Print periodically
    now = time.time()
    if now - last_print >= PRINT_EVERY_SEC:
        gas_mean = feats.get("gas_ppm_mean", float("nan"))

        if alert_active:
            print(f"[ALERT] score={score:.3f} cause={cause} gas_mean={gas_mean:.2f}")
        else:
            if is_anomaly:
                print(f"[anomaly] score={score:.3f} (not alerted yet) gas_mean={gas_mean:.2f}")
            else:
                print(f"[ok] score={score:.3f} gas_mean={gas_mean:.2f}")

        last_print = now

def main():
    print(">>> USING SCORED CONSUMER <<<")
    print(">>> Writing to:", CSV_PATH)
    print(f">>> threshold={ANOMALY_THRESHOLD}")
    print(f">>> model={MODEL_PATH} scaler={SCALER_PATH}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.subscribe(TOPIC, qos=0)
    client.loop_forever()

if __name__ == "__main__":
    main()
