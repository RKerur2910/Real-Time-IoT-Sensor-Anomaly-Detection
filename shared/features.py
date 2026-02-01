from collections import deque
from typing import Deque, Dict, List
import numpy as np

FIELDS = ["temp_c", "humidity", "gas_ppm", "smoke", "battery_v"]

def _slope(y: np.ndarray) -> float:
    n = y.size
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    denom = np.var(x)
    if denom == 0:
        return 0.0
    return float(np.cov(x, y, bias=True)[0, 1] / denom)

def window_features(window: List[Dict]) -> Dict[str, float]:
    feats: Dict[str, float] = {}
    for f in FIELDS:
        vals = np.array([float(e[f]) for e in window], dtype=float)
        feats[f"{f}_mean"] = float(np.mean(vals))
        feats[f"{f}_std"] = float(np.std(vals))
        feats[f"{f}_min"] = float(np.min(vals))
        feats[f"{f}_max"] = float(np.max(vals))
        feats[f"{f}_slope"] = _slope(vals)
        feats[f"{f}_delta"] = float(vals[-1] - vals[-2]) if vals.size >= 2 else 0.0
    return feats

class RollingWindow:
    def __init__(self, size: int = 60):
        self.size = size
        self.buf: Deque[Dict] = deque(maxlen=size)

    def add(self, event: Dict) -> None:
        self.buf.append(event)

    def ready(self) -> bool:
        return len(self.buf) == self.size

    def features(self) -> Dict[str, float]:
        return window_features(list(self.buf))