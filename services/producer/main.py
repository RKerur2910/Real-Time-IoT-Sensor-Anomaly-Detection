import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "sensors/building1"

# --- Simulation config ---
LOCATION = "lab_A"

# Normal ranges (roughly realistic)
BASE_TEMP = 22.0          # °C
BASE_HUMIDITY = 0.45      # 0-1
BASE_GAS = 12.0           # ppm
BASE_SMOKE = 0.02         # arbitrary units
BASE_BATTERY = 3.75       # V

PUBLISH_EVERY_SEC = 1.0

# Anomaly modes: "none", "spike_gas", "drift_temp", "stuck_gas", "noisy_smoke"
ANOMALY_MODE = "stuck_gas"
ANOMALY_START_AFTER_SEC = 90   # start anomaly after N seconds
ANOMALY_DURATION_SEC = 40      # how long anomaly lasts


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def make_event(t: float, anomaly_active: bool) -> dict:
    """Generate one sensor event. t is seconds since start."""
    temp = BASE_TEMP + random.gauss(0, 0.2)
    humidity = min(max(BASE_HUMIDITY + random.gauss(0, 0.02), 0.0), 1.0)
    gas = max(BASE_GAS + random.gauss(0, 0.8), 0.0)
    smoke = max(BASE_SMOKE + random.gauss(0, 0.01), 0.0)
    battery = max(BASE_BATTERY - 0.00002 * t + random.gauss(0, 0.005), 3.2)

    if anomaly_active:
        if ANOMALY_MODE == "spike_gas":
            gas = gas * random.uniform(8, 15)  # big spike
        elif ANOMALY_MODE == "drift_temp":
            temp = temp + (0.03 * (t)) / 60.0   # slow drift up over time
        elif ANOMALY_MODE == "stuck_gas":
            gas = BASE_GAS                      # flatline
        elif ANOMALY_MODE == "noisy_smoke":
            smoke = max(BASE_SMOKE + random.gauss(0, 0.12), 0.0)  # high variance

    return {
        "ts": now_iso(),
        "sensor_id": "sensor_01",
        "location": LOCATION,
        "temp_c": round(temp, 3),
        "humidity": round(humidity, 3),
        "gas_ppm": round(gas, 3),
        "smoke": round(smoke, 3),
        "battery_v": round(battery, 3),
    }


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    start = time.time()
    print(f"Publishing to mqtt://{BROKER_HOST}:{BROKER_PORT} topic='{TOPIC}'")
    print("Tip: change ANOMALY_MODE in the file (none/spike_gas/drift_temp/stuck_gas/noisy_smoke)\n")

    while True:
        t = time.time() - start
        anomaly_active = (t >= ANOMALY_START_AFTER_SEC) and (t <= ANOMALY_START_AFTER_SEC + ANOMALY_DURATION_SEC)

        payload = make_event(t=t, anomaly_active=anomaly_active)
        client.publish(TOPIC, json.dumps(payload), qos=0)

        if int(t) % 5 == 0:
            mode = ANOMALY_MODE if anomaly_active else "none"
            print(f"[t={int(t)}s] published (anomaly={mode}): gas_ppm={payload['gas_ppm']} temp_c={payload['temp_c']}")

        time.sleep(PUBLISH_EVERY_SEC)


if __name__ == "__main__":
    main()
