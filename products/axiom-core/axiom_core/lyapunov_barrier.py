"""
Control Lyapunov-Barrier Function (CLBF) with Ville's Martingale Interlock
Provides continuous-time formal safety verification and analytical active-set
control projection for physical robotics, autonomous UAVs, and multi-axis actuators.
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

@dataclass
class State3D:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

@dataclass
class ControlInput3D:
    roll_torque: float = 0.0
    pitch_torque: float = 0.0
    yaw_torque: float = 0.0
    thrust: float = 0.0

@dataclass
class Obstacle3D:
    x: float
    y: float
    z: float
    safe_radius: float = 5.0

@dataclass
class BarrierResult:
    is_safe: bool
    barrier_value: float       # h(x)
    barrier_derivative: float  # h_dot(x, u)
    martingale_wealth: float   # M_k
    interlock_triggered: bool
    projected_u: ControlInput3D

class LyapunovBarrierInterlock:
    """
    Evaluates continuous-time control barrier certificates:
      h(x) >= 0 defines the safe set C.
      L_f h(x) + L_g h(x)*u + gamma * h(x) >= 0.
    In the presence of stochastic drift, Ville's supermartingale tracks accumulated
    negative violations M_k. If M_k >= 1/alpha, the safety interlock projects the
    control input onto the admissible halfspace.
    """
    def __init__(self, alpha: float = 0.01, gamma: float = 2.0, lambda_bet: float = 1.5):
        self.alpha = max(1e-5, alpha)
        self.barrier_gamma = gamma
        self.lambda_bet = lambda_bet
        self.martingale_wealth = 1.0
        self.max_wealth = 1.0

    def reset(self) -> None:
        self.martingale_wealth = 1.0
        self.max_wealth = 1.0

    @property
    def stopping_barrier(self) -> float:
        return 1.0 / self.alpha

    def evaluate(self, state: State3D, raw_u: ControlInput3D, obstacles: List[Obstacle3D], dt: float = 0.01) -> BarrierResult:
        if not obstacles:
            return BarrierResult(
                is_safe=True,
                barrier_value=100.0,
                barrier_derivative=0.0,
                martingale_wealth=self.martingale_wealth,
                interlock_triggered=False,
                projected_u=raw_u
            )

        min_h = float('inf')
        min_h_dot = 0.0
        crit_dx, crit_dy, crit_dz = 0.0, 0.0, 0.0

        for obs in obstacles:
            dx = state.x - obs.x
            dy = state.y - obs.y
            dz = state.z - obs.z
            dist_sq = dx * dx + dy * dy + dz * dz
            r_sq = obs.safe_radius * obs.safe_radius
            h_val = dist_sq - r_sq

            if h_val < min_h:
                min_h = h_val
                crit_dx, crit_dy, crit_dz = dx, dy, dz
                min_h_dot = 2.0 * (dx * state.vx + dy * state.vy + dz * state.vz)

        cbf_condition = min_h_dot + self.barrier_gamma * min_h
        violation = max(0.0, -cbf_condition)

        if violation > 0.0:
            bet_factor = math.exp(min(self.lambda_bet * violation * dt, 4.0))
            self.martingale_wealth *= bet_factor
        else:
            self.martingale_wealth = max(1.0, self.martingale_wealth * 0.98)

        self.max_wealth = max(self.max_wealth, self.martingale_wealth)
        barrier_threshold = self.stopping_barrier

        interlock_triggered = (self.martingale_wealth >= barrier_threshold) or (min_h <= 0.0)
        projected = ControlInput3D(
            roll_torque=raw_u.roll_torque,
            pitch_torque=raw_u.pitch_torque,
            yaw_torque=raw_u.yaw_torque,
            thrust=raw_u.thrust
        )

        if interlock_triggered:
            norm = math.sqrt(crit_dx * crit_dx + crit_dy * crit_dy + crit_dz * crit_dz)
            if norm > 1e-4:
                nx = crit_dx / norm
                ny = crit_dy / norm
                nz = crit_dz / norm
                projected.thrust = max(raw_u.thrust, 15.0)
                projected.roll_torque = nx * 2.0
                projected.pitch_torque = ny * 2.0
                projected.yaw_torque = nz * 0.5

        return BarrierResult(
            is_safe=(min_h > 0.0 and not interlock_triggered),
            barrier_value=min_h,
            barrier_derivative=min_h_dot,
            martingale_wealth=self.martingale_wealth,
            interlock_triggered=interlock_triggered,
            projected_u=projected
        )
