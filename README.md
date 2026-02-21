# 🚀 Real-Time IoT Sensor Anomaly Detection

A real-time anomaly detection pipeline for streaming multi-sensor IoT data using **MQTT**, **rolling-window feature engineering**, and an **Isolation Forest** (unsupervised ML). Built to detect abnormal behavior reliably while minimizing noisy false alerts via **adaptive thresholding** and **alert smoothing**.

---

## Why this project?

IoT sensor streams are noisy and rarely labeled. Simple rule-based thresholds often lead to:
- frequent false positives
- unstable alerting (alert “flapping”)
- poor adaptability to changing baselines

This project focuses on **production-style stability**:
- real-time stream processing
- unsupervised anomaly scoring
- percentile-based thresholds
- smoothing + root-cause heuristics for interpretable alerts

---

## Key Results

- **>95% anomaly detection correctness** under injected fault conditions  
- **~80% reduction in false alerts** after stabilizing thresholds + smoothing  
- More stable, interpretable alerting in steady-state operation

---

## Architecture
