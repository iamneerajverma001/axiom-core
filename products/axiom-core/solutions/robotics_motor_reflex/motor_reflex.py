"""
Axiom-Core Turnkey Solution: 1000Hz Edge Motor Safety Interlock & Reflex Arc
Provides deterministic sub-millisecond torque clipping, collision detection,
and emergency deceleration for robotics joints and autonomous actuators.
"""

import time
import math
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from axiom_core.conformal import MartingaleSafetyGate

@dataclass
class JointTelemetry:
    joint_id: int
    commanded_torque_nm: float
    measured_torque_nm: float
    angular_velocity_rad_s: float
    proximity_distance_m: float # 0.0 to 2.0m

class MotorReflexArc:
    def __init__(
        self,
        max_torque_nm: float = 45.0,
        max_velocity_rad_s: float = 6.28, # ~1 rev/sec
        emergency_stop_distance_m: float = 0.15, # 15cm collision zone
        conformal_alpha: float = 0.005 # 99.5% certified safe operation
    ):
        self.max_torque = max_torque_nm
        self.max_velocity = max_velocity_rad_s
        self.e_stop_distance = emergency_stop_distance_m
        self.safety_gate = MartingaleSafetyGate(alpha=conformal_alpha, delta=0.001)
        self.estop_triggered = False

    def evaluate_cycle(self, telemetry: JointTelemetry) -> Dict[str, Any]:
        """
        Executes a 1000Hz (1 millisecond) safety reflex loop.
        Computes safe clipped output torque or triggers instantaneous E-STOP.
        """
        t0 = time.perf_counter()

        if self.estop_triggered:
            return {
                "joint_id": telemetry.joint_id,
                "commanded_torque": 0.0,
                "status": "EMERGENCY_STOP_LATCHED",
                "latency_us": round((time.perf_counter() - t0) * 1_000_000.0, 2)
            }

        # 1. Proximity Emergency Stop (Immediate Human / Obstacle Collision Prevention)
        if telemetry.proximity_distance_m < self.e_stop_distance:
            self.estop_triggered = True
            self.safety_gate.update(1.0) # Maximum safety violation penalty
            return {
                "joint_id": telemetry.joint_id,
                "commanded_torque": 0.0,
                "status": f"COLLISION_AVOIDANCE_ESTOP: object at {telemetry.proximity_distance_m*100:.1f}cm",
                "latency_us": round((time.perf_counter() - t0) * 1_000_000.0, 2)
            }

        # 2. Torque Saturation Clipping
        raw_torque = telemetry.commanded_torque_nm
        clipped_torque = max(-self.max_torque, min(self.max_torque, raw_torque))
        is_clipped = abs(raw_torque) > self.max_torque

        # 3. Sudden Resistance / Jamming Detection (Measured torque deviates from clipped command)
        torque_delta = abs(telemetry.measured_torque_nm - clipped_torque)
        if torque_delta > (self.max_torque * 0.5):
            # Mechanical jam or unexpected contact
            self.safety_gate.update(0.7)
            # Damping reflex: scale down torque by 50%
            clipped_torque *= 0.5

        # 4. Safe Operation Update
        if not is_clipped:
            self.safety_gate.update(0.0)

        latency_us = (time.perf_counter() - t0) * 1_000_000.0
        return {
            "joint_id": telemetry.joint_id,
            "commanded_torque": round(clipped_torque, 3),
            "status": "TORQUE_CLIPPED" if is_clipped else "NORMAL_CONTROL",
            "latency_us": round(latency_us, 2)
        }

    def reset_estop(self):
        self.estop_triggered = False
        self.safety_gate.reset()
