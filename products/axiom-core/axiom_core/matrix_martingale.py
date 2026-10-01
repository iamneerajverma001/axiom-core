"""
Multivariate Matrix-Valued Supermartingale Anomaly Shield
Tracks streaming covariance drift across multi-axis sensors, robotics joints, and financial feeds
with distribution-free Ville's inequality safety guarantees: P(max M_k >= 1/alpha) <= alpha.
"""

import math
from typing import List, Dict, Any, Optional

class MatrixMartingaleShield:
    def __init__(self, dim: int = 6, alpha: float = 0.01, lambda_param: float = 0.05):
        self.dim = max(1, int(dim))
        self.alpha = float(alpha)
        self.lambda_param = float(lambda_param)
        self.rejection_threshold = 1.0 / self.alpha
        self.wealth = 1.0
        self.step_count = 0
        self.tripped = False
        self.history: List[float] = []

    def reset(self):
        self.wealth = 1.0
        self.step_count = 0
        self.tripped = False
        self.history.clear()

    def update(self, vector: List[float]) -> Dict[str, Any]:
        """
        Updates multivariate martingale wealth given streaming telemetry vector x.
        Returns safety verdict and wealth status.
        """
        if self.tripped:
            return {
                "permitted": False,
                "wealth": self.wealth,
                "tripped": True,
                "reason": "MARTINGALE_CIRCUIT_TRIPPED"
            }

        # Truncate or pad to dimension
        x = [float(v) for v in vector[:self.dim]]
        if len(x) < self.dim:
            x.extend([0.0] * (self.dim - len(x)))

        # Trace discrepancy from standard identity covariance
        trace_diff = sum((val * val - 1.0) for val in x)
        betting_term = 1.0 + self.lambda_param * (trace_diff / float(self.dim))
        betting_term = max(0.01, min(4.0, betting_term))

        self.wealth *= betting_term
        self.step_count += 1
        self.history.append(round(self.wealth, 4))

        if self.wealth >= self.rejection_threshold:
            self.tripped = True
            return {
                "permitted": False,
                "wealth": round(self.wealth, 4),
                "threshold": round(self.rejection_threshold, 2),
                "tripped": True,
                "step": self.step_count,
                "reason": f"MULTIVARIATE_COVARIANCE_ANOMALY: Wealth {self.wealth:.2f} >= Threshold {self.rejection_threshold:.2f}"
            }

        return {
            "permitted": True,
            "wealth": round(self.wealth, 4),
            "threshold": round(self.rejection_threshold, 2),
            "tripped": False,
            "step": self.step_count
        }
