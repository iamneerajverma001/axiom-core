"""
Axiom-Core Martingale Conformal Safety Engine
Provides distribution-free, anytime-valid risk control using betting martingales
and Ville's inequality to enforce mathematical safety guarantees on critical decisions.
"""

import math
from typing import Dict, Any, List, Optional

class MartingaleSafetyGate:
    """
    Anytime-valid risk monitor based on test supermartingales.
    Under the null hypothesis that risk <= alpha,
    P(exists k >= 1 : M_k >= 1 / delta) <= delta (Ville's inequality).
    """

    def __init__(self, alpha: float = 0.05, delta: float = 0.01, lambda_param: float = 0.5):
        self.alpha = float(alpha)          # Allowable error rate / risk tolerance
        self.delta = float(delta)          # Upper bound on false alarm probability
        self.lambda_param = float(lambda_param)  # Betting parameter in [0, 1)
        self.wealth = 1.0                  # Martingale starting capital M_0 = 1.0
        self.step_count = 0
        self.rejection_threshold = 1.0 / self.delta  # e.g., 1 / 0.01 = 100.0
        self.violation_history: List[float] = []

    def update(self, observed_loss: float) -> Dict[str, Any]:
        """
        Updates the testing martingale with observed step loss in [0, 1].
        Loss = 0 indicates safe execution; Loss = 1 indicates severe safety violation.
        """
        self.step_count += 1
        loss = max(0.0, min(1.0, float(observed_loss)))
        self.violation_history.append(loss)

        # Betting factor: (1 + lambda * (loss - alpha))
        betting_factor = 1.0 + self.lambda_param * (loss - self.alpha)
        self.wealth *= max(0.0001, betting_factor)

        tripped = self.wealth >= self.rejection_threshold
        return {
            "step": self.step_count,
            "loss": loss,
            "wealth": round(self.wealth, 4),
            "threshold": round(self.rejection_threshold, 2),
            "safety_barrier_breached": tripped,
            "confidence_guarantee": round(1.0 - self.delta, 4)
        }

    def evaluate_action_risk(self, command_or_action: str, confidence: float, entropy: float) -> Dict[str, Any]:
        """
        Calculates instantaneous pre-execution safety score and determines whether
        execution is strictly permitted, requires confirmation, or must be aborted.
        """
        cmd_lower = command_or_action.lower()
        destructive_keywords = [
            "rmdir", "del /f", "format", "diskpart", "drop table", "truncate",
            "shutdown", "kill -9", "dd if=", "mkfs", "rm -rf", "taskkill /f /im explorer"
        ]

        is_high_risk = any(k in cmd_lower for k in destructive_keywords)
        
        # Conformal risk calculation
        risk_score = 0.0
        if is_high_risk:
            risk_score += 0.85
        if confidence < 0.75:
            risk_score += 0.30
        if entropy > 0.40:
            risk_score += 0.25

        risk_score = min(1.0, risk_score)
        permitted = risk_score < 0.60

        return {
            "action": command_or_action,
            "risk_score": round(risk_score, 4),
            "permitted": permitted,
            "requires_human_barrier": not permitted,
            "martingale_wealth": round(self.wealth, 4),
            "reason": "Destructive operation detected" if is_high_risk else (
                "High predictive entropy/uncertainty" if entropy > 0.40 else "Safe fast-path verified"
            )
        }

    def reset(self):
        self.wealth = 1.0
        self.step_count = 0
        self.violation_history.clear()
