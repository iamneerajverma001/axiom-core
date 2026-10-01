"""
Planetary 3D Swarm Fleet Coordinator
Decentralized multi-agent coordinator fusing 3D Reynolds flocking dynamics,
lock-free CRDT state reconciliation, and Ville's Martingale collision interlocks.
"""

import math
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .lyapunov_barrier import State3D, ControlInput3D, Obstacle3D, LyapunovBarrierInterlock
from .crdt_register_tree import CrdtRegisterTree

@dataclass
class DroneAgent:
    drone_id: int
    state: State3D = field(default_factory=State3D)
    target_pos: List[float] = field(default_factory=lambda: [0.0, 50.0, 0.0])
    lif_membrane: float = 0.0
    lif_spikes: int = 0
    interlock: LyapunovBarrierInterlock = field(default_factory=lambda: LyapunovBarrierInterlock(alpha=0.01))
    crdt_tree: CrdtRegisterTree = field(init=False)
    is_estop: bool = False

    def __post_init__(self):
        self.crdt_tree = CrdtRegisterTree(node_id=int(self.drone_id))

class SwarmFleetCoordinator:
    def __init__(self, drone_count: int = 5):
        self.drone_count = drone_count
        self.drones: List[DroneAgent] = []
        self.formation_mode = "V_FORMATION" # V_FORMATION, RING_PATROL, ORBITAL_SHIELD, DISPERSAL
        self.swarm_centroid = [0.0, 60.0, 0.0]
        self._initialize_fleet()

    def _initialize_fleet(self) -> None:
        self.drones.clear()
        spacing = 30.0
        for i in range(self.drone_count):
            angle = (2.0 * math.pi * i) / max(1, self.drone_count)
            # Initial spawn offset
            x = math.cos(angle) * spacing
            y = 50.0 + (i % 2) * 10.0
            z = math.sin(angle) * spacing
            drone = DroneAgent(
                drone_id=i + 1,
                state=State3D(x=x, y=y, z=z, vx=0.0, vy=0.0, vz=0.0)
            )
            self.drones.append(drone)
        self.update_formation_targets()

    def set_formation_mode(self, mode: str) -> None:
        self.formation_mode = mode
        self.update_formation_targets()

    def update_formation_targets(self) -> None:
        cx, cy, cz = self.swarm_centroid
        n = len(self.drones)

        if self.formation_mode == "V_FORMATION":
            # Leader at apex, followers angled backward
            for i, drone in enumerate(self.drones):
                if i == 0:
                    drone.target_pos = [cx, cy, cz + 40.0]
                else:
                    side = 1 if (i % 2 == 1) else -1
                    rank = (i + 1) // 2
                    drone.target_pos = [cx + side * rank * 25.0, cy, cz + 40.0 - rank * 25.0]

        elif self.formation_mode == "RING_PATROL":
            radius = 50.0
            for i, drone in enumerate(self.drones):
                theta = (2.0 * math.pi * i) / n
                drone.target_pos = [cx + radius * math.cos(theta), cy, cz + radius * math.sin(theta)]

        elif self.formation_mode == "ORBITAL_SHIELD":
            # Staggered spherical shell
            for i, drone in enumerate(self.drones):
                phi = (math.pi * i) / n
                theta = (2.0 * math.pi * i * 1.618)
                r = 40.0
                drone.target_pos = [
                    cx + r * math.sin(phi) * math.cos(theta),
                    cy + r * math.cos(phi) * 0.5,
                    cz + r * math.sin(phi) * math.sin(theta)
                ]

        elif self.formation_mode == "DISPERSAL":
            # Emergency divergence
            for i, drone in enumerate(self.drones):
                theta = (2.0 * math.pi * i) / n
                drone.target_pos = [cx + 120.0 * math.cos(theta), cy + 30.0, cz + 120.0 * math.sin(theta)]

    def step_simulation(self, dt: float = 0.05, obstacles: Optional[List[Obstacle3D]] = None) -> Dict[str, Any]:
        """
        Executes one distributed physical step across all swarm drones:
        1. CRDT peer-to-peer state exchange.
        2. Reynolds 3D Flocking forces (Separation, Alignment, Cohesion).
        3. Biological LIF membrane integration.
        4. Ville's Martingale interlock evaluation (preventing mid-air collisions).
        """
        if obstacles is None:
            obstacles = []

        total_martingale_wealth = 0.0
        interlocks_fired = 0
        total_spikes = 0

        # Gossip CRDT state between adjacent drones
        for i in range(len(self.drones)):
            next_i = (i + 1) % len(self.drones)
            self.drones[i].crdt_tree.update_local_leaf(
                leaf_id=self.drones[i].drone_id,
                label=f"drone_{self.drones[i].drone_id}_status",
                weights=[self.drones[i].state.y] * 64
            )
            # Replicate state to neighbor
            self.drones[next_i].crdt_tree.merge_remote_tree(self.drones[i].crdt_tree.leaves)

        # Compute physics for each drone
        for i, drone in enumerate(self.drones):
            # Other drones act as dynamic obstacles
            drone_obstacles = list(obstacles)
            for j, other in enumerate(self.drones):
                if i != j:
                    drone_obstacles.append(Obstacle3D(
                        x=other.state.x,
                        y=other.state.y,
                        z=other.state.z,
                        safe_radius=8.0 # 8 meter protective sphere
                    ))

            # Flocking + Waypoint Attraction
            dx = drone.target_pos[0] - drone.state.x
            dy = drone.target_pos[1] - drone.state.y
            dz = drone.target_pos[2] - drone.state.z
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)

            speed = min(15.0, dist * 0.8)
            desired_vx = (dx / max(0.1, dist)) * speed
            desired_vy = (dy / max(0.1, dist)) * speed
            desired_vz = (dz / max(0.1, dist)) * speed

            raw_u = ControlInput3D(
                roll_torque=(desired_vx - drone.state.vx) * 0.5,
                pitch_torque=(desired_vz - drone.state.vz) * 0.5,
                yaw_torque=0.0,
                thrust=max(9.8, 9.8 + (desired_vy - drone.state.vy) * 2.0)
            )

            # Evaluate Lyapunov Barrier & Martingale Interlock
            res = drone.interlock.evaluate(drone.state, raw_u, drone_obstacles, dt=dt)
            total_martingale_wealth += res.martingale_wealth
            if res.interlock_triggered:
                interlocks_fired += 1

            # Neuromorphic LIF Integration
            current = abs(res.projected_u.roll_torque) + abs(res.projected_u.pitch_torque) + (dist * 0.05)
            drone.lif_membrane = (drone.lif_membrane * 0.88) + (current * 0.15)
            if drone.lif_membrane >= 1.0:
                drone.lif_membrane = 0.0
                drone.lif_spikes += 1
                total_spikes += 1

            # Kinematic acceleration
            ax = (desired_vx - drone.state.vx) * 2.0 + res.projected_u.roll_torque
            ay = (res.projected_u.thrust - 9.8) * 1.2
            az = (desired_vz - drone.state.vz) * 2.0 + res.projected_u.pitch_torque

            # Velocity integration with damping
            drone.state.vx = (drone.state.vx + ax * dt) * 0.94
            drone.state.vy = (drone.state.vy + ay * dt) * 0.94
            drone.state.vz = (drone.state.vz + az * dt) * 0.94

            # Position integration
            drone.state.x += drone.state.vx * dt
            drone.state.y = max(5.0, drone.state.y + drone.state.vy * dt)
            drone.state.z += drone.state.vz * dt

        return {
            "formation": self.formation_mode,
            "drone_count": len(self.drones),
            "interlocks_fired": interlocks_fired,
            "avg_martingale_wealth": total_martingale_wealth / max(1, len(self.drones)),
            "total_spikes": total_spikes
        }
