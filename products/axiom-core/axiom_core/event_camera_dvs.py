"""
Dynamic Vision Sensor (DVS) / Event-Based Camera Neuromorphic Ingestor
Ingests asynchronous microsecond pixel events (x, y, timestamp, polarity)
and computes an Exponential Decaying Time Surface (EDTS) mapped directly
into Axiom Core's 128-dimensional spatial input tensor.
"""

import math
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class DvsEvent:
    x: int
    y: int
    timestamp_us: int
    polarity: int # +1 or -1

class EventCameraDvs:
    GRID_WIDTH = 32
    GRID_HEIGHT = 32
    TENSOR_DIMS = 128

    def __init__(self, tau_us: float = 10000.0):
        self.decay_tau_us = max(100.0, tau_us)
        self.surface = [0.0] * (self.GRID_WIDTH * self.GRID_HEIGHT)
        self.last_pixel_ts = [0] * (self.GRID_WIDTH * self.GRID_HEIGHT)
        self.last_timestamp_us = 0

    def reset(self) -> None:
        self.surface = [0.0] * (self.GRID_WIDTH * self.GRID_HEIGHT)
        self.last_pixel_ts = [0] * (self.GRID_WIDTH * self.GRID_HEIGHT)
        self.last_timestamp_us = 0

    def ingest_event(self, ev: DvsEvent, sensor_w: int = 640, sensor_h: int = 480) -> None:
        if ev.timestamp_us > self.last_timestamp_us:
            self.last_timestamp_us = ev.timestamp_us

        gx = min(self.GRID_WIDTH - 1, int((ev.x * self.GRID_WIDTH) / sensor_w))
        gy = min(self.GRID_HEIGHT - 1, int((ev.y * self.GRID_HEIGHT) / sensor_h))
        idx = gy * self.GRID_WIDTH + gx

        prev_ts = self.last_pixel_ts[idx]
        if prev_ts > 0 and ev.timestamp_us >= prev_ts:
            dt = float(ev.timestamp_us - prev_ts)
            self.surface[idx] *= math.exp(-dt / self.decay_tau_us)
        else:
            self.surface[idx] = 0.0

        self.surface[idx] += 1.0 if ev.polarity > 0 else -0.5
        self.surface[idx] = max(-2.0, min(10.0, self.surface[idx]))
        self.last_pixel_ts[idx] = ev.timestamp_us

    def ingest_batch(self, events: List[DvsEvent], sensor_w: int = 640, sensor_h: int = 480) -> None:
        for ev in events:
            self.ingest_event(ev, sensor_w, sensor_h)

    def extract_128d_tensor(self, current_time_us: int) -> List[float]:
        pixels_per_bin = (self.GRID_WIDTH * self.GRID_HEIGHT) // self.TENSOR_DIMS
        tensor = [0.0] * self.TENSOR_DIMS

        for b in range(self.TENSOR_DIMS):
            bin_energy = 0.0
            start_idx = b * pixels_per_bin
            for p in range(pixels_per_bin):
                idx = start_idx + p
                val = self.surface[idx]
                pts = self.last_pixel_ts[idx]
                if pts > 0 and current_time_us >= pts:
                    dt = float(current_time_us - pts)
                    val *= math.exp(-dt / self.decay_tau_us)
                bin_energy += abs(val)
            tensor[b] = math.tanh(bin_energy / float(pixels_per_bin))

        return tensor
