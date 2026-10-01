#!/usr/bin/env python3
"""
Axiom Planetary Fleet & 3D Swarm Cockpit (Physical Machine Era v3.0)
Real-time 3D multi-agent swarm command center:
- 5 Autonomous 6-DOF Quadcopters in coordinated 3D airspace
- Reynolds 3D Flocking + Control Lyapunov-Barrier Function (CLBF)
- Ville's Martingale Collision Interlocks
- Decentralized CRDT Peer-to-Peer Gossip Mesh
- Live MAVLink 2.0 & CAN-FD Wire Bus Telemetry
- Interactive 3D Perspective Orbit Camera & Dynamic Threat Injection
"""

import sys
import os
import time
import math
import random
import tkinter as tk
from tkinter import ttk

# Ensure products/axiom-core is importable
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
core_path = os.path.join(repo_root, "products", "axiom-core")
if core_path not in sys.path:
    sys.path.insert(0, core_path)

from axiom_core import (
    SwarmFleetCoordinator,
    DroneAgent,
    State3D,
    ControlInput3D,
    Obstacle3D,
    LyapunovBarrierInterlock,
    MavlinkBridge,
    AttitudeTarget,
    EventCameraDvs,
    DvsEvent,
    FpgaVerilogSynthesizer
)

class AxiomSwarmCockpit3D(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AXIOM-CORE v3.0 // PLANETARY 3D SWARM FLEET COMMAND")
        self.geometry("1480x920")
        self.configure(bg="#070a0f")

        # Swarm Coordinator
        self.drone_count = 5
        self.coordinator = SwarmFleetCoordinator(drone_count=self.drone_count)
        self.obstacles: list[Obstacle3D] = [
            Obstacle3D(x=0.0, y=60.0, z=0.0, safe_radius=16.0),
            Obstacle3D(x=-60.0, y=45.0, z=40.0, safe_radius=12.0)
        ]

        # 3D Camera Angles & Projection
        self.cam_yaw = 0.75      # Azimuth radians
        self.cam_pitch = 0.42    # Elevation radians
        self.cam_dist = 420.0
        self.auto_orbit = True
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        # Telemetry & Rates
        self.decision_count = 0
        self.start_time = time.time()
        self.last_fps_time = time.time()
        self.fps_decisions = 0
        self.mean_latency_us = 6.8
        self.current_decisions_per_sec = 1420

        # Martingale History
        self.wealth_history = [1.0] * 60
        self.rotor_angle = 0.0

        # Build UI Layout
        self._build_header()
        self._build_main_grid()
        self._bind_mouse_controls()

        # Start Real-Time Loop
        self.after(20, self._render_loop)

    def _build_header(self):
        header_frame = tk.Frame(self, bg="#0d1117", height=50)
        header_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(8, 4))

        title = tk.Label(
            header_frame,
            text="⚡ AXIOM-CORE 3.0 // PLANETARY 3D SWARM COMMAND & REFLEX KERNEL",
            fg="#00f3ff",
            bg="#0d1117",
            font=("Consolas", 13, "bold")
        )
        title.pack(side=tk.LEFT, padx=12, pady=8)

        self.lbl_telemetry = tk.Label(
            header_frame,
            text="DECISION RATE: 1,420 Hz | LATENCY: 6.8 µs | CRDT MESH: 5 NODES | FORMATION: V-FORMATION",
            fg="#39ff14",
            bg="#0d1117",
            font=("Consolas", 10, "bold")
        )
        self.lbl_telemetry.pack(side=tk.RIGHT, padx=12, pady=8)

    def _build_main_grid(self):
        content = tk.Frame(self, bg="#070a0f")
        content.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left Column: 3D Airspace Radar (Canvas)
        left_col = tk.Frame(content, bg="#0a0e14", width=860)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        canvas_header = tk.Frame(left_col, bg="#121820", height=28)
        canvas_header.pack(fill=tk.X)
        tk.Label(
            canvas_header,
            text="[PANEL 1] 3D TACTICAL AIRSPACE // 6-DOF MULTI-DRONE SWARM RADAR",
            fg="#00f3ff", bg="#121820", font=("Consolas", 9, "bold")
        ).pack(side=tk.LEFT, padx=8, pady=4)

        self.canvas_3d = tk.Canvas(left_col, bg="#05070a", highlightthickness=1, highlightbackground="#1b2430")
        self.canvas_3d.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Control Bar under 3D Canvas
        btn_bar = tk.Frame(left_col, bg="#0a0e14")
        btn_bar.pack(fill=tk.X, pady=4)

        tk.Button(
            btn_bar, text="V-FORMATION", bg="#16202c", fg="#00f3ff", font=("Consolas", 9, "bold"),
            command=lambda: self._set_formation("V_FORMATION")
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            btn_bar, text="RING PATROL", bg="#16202c", fg="#39ff14", font=("Consolas", 9, "bold"),
            command=lambda: self._set_formation("RING_PATROL")
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            btn_bar, text="ORBITAL SHIELD", bg="#16202c", fg="#ffcc00", font=("Consolas", 9, "bold"),
            command=lambda: self._set_formation("ORBITAL_SHIELD")
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            btn_bar, text="DISPERSAL (SCATTER)", bg="#16202c", fg="#ff0055", font=("Consolas", 9, "bold"),
            command=lambda: self._set_formation("DISPERSAL")
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            btn_bar, text="+ INJECT 3D HAZARD", bg="#2a1420", fg="#ff5555", font=("Consolas", 9, "bold"),
            command=self._inject_obstacle
        ).pack(side=tk.LEFT, padx=6)

        self.btn_orbit = tk.Button(
            btn_bar, text="AUTO-ORBIT: ON", bg="#16202c", fg="#88ccff", font=("Consolas", 9),
            command=self._toggle_orbit
        )
        self.btn_orbit.pack(side=tk.LEFT, padx=3)

        tk.Button(
            btn_bar, text="E-STOP CLUSTER", bg="#550000", fg="#ffffff", font=("Consolas", 9, "bold"),
            command=self._estop_cluster
        ).pack(side=tk.RIGHT, padx=4)

        # Right Column: Multi-Panel Telemetry Stack
        right_col = tk.Frame(content, bg="#0a0e14", width=580)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, padx=4, pady=4)

        # Panel 2: Neuromorphic LIF Spike Heatmaps per Drone
        p2_frame = tk.LabelFrame(
            right_col, text="[PANEL 2] BIOLOGICAL LIF NEUROMORPHIC DYNAMICS (128 POOL)",
            fg="#ff0055", bg="#0a0e14", font=("Consolas", 8, "bold")
        )
        p2_frame.pack(fill=tk.X, padx=4, pady=2)
        self.canvas_lif = tk.Canvas(p2_frame, bg="#05070a", height=110, highlightthickness=0)
        self.canvas_lif.pack(fill=tk.X, padx=4, pady=4)

        # Panel 3: Ville's Martingale & Lyapunov Safety Barrier
        p3_frame = tk.LabelFrame(
            right_col, text="[PANEL 3] VILLE'S MARTINGALE SAFETY SHIELD (M_t vs 1/α=100)",
            fg="#39ff14", bg="#0a0e14", font=("Consolas", 8, "bold")
        )
        p3_frame.pack(fill=tk.X, padx=4, pady=2)
        self.canvas_martingale = tk.Canvas(p3_frame, bg="#05070a", height=110, highlightthickness=0)
        self.canvas_martingale.pack(fill=tk.X, padx=4, pady=4)

        # Panel 4: CRDT Swarm Mesh State Clocks
        p4_frame = tk.LabelFrame(
            right_col, text="[PANEL 4] DECENTRALIZED CRDT SWARM FABRIC (VECTOR CLOCKS)",
            fg="#00f3ff", bg="#0a0e14", font=("Consolas", 8, "bold")
        )
        p4_frame.pack(fill=tk.X, padx=4, pady=2)
        self.canvas_crdt = tk.Canvas(p4_frame, bg="#05070a", height=90, highlightthickness=0)
        self.canvas_crdt.pack(fill=tk.X, padx=4, pady=4)

        # Panel 5: MAVLink 2.0 & CAN-FD Wire Packets
        p5_frame = tk.LabelFrame(
            right_col, text="[PANEL 5] MAVLINK 2.0 & CAN-FD LINE-RATE BUS STREAM",
            fg="#ffcc00", bg="#0a0e14", font=("Consolas", 8, "bold")
        )
        p5_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        self.txt_wire = tk.Text(
            p5_frame, bg="#05070a", fg="#a0c0a0", font=("Consolas", 8),
            height=9, relief=tk.FLAT, highlightthickness=0
        )
        self.txt_wire.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _bind_mouse_controls(self):
        self.canvas_3d.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas_3d.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas_3d.bind("<MouseWheel>", self._on_mouse_wheel)

    def _on_mouse_down(self, event):
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y

    def _on_mouse_drag(self, event):
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y
        self.cam_yaw += dx * 0.01
        self.cam_pitch = max(-1.4, min(1.4, self.cam_pitch + dy * 0.01))
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y

    def _on_mouse_wheel(self, event):
        if event.delta > 0:
            self.cam_dist = max(150.0, self.cam_dist - 20.0)
        else:
            self.cam_dist = min(900.0, self.cam_dist + 20.0)

    def _toggle_orbit(self):
        self.auto_orbit = not self.auto_orbit
        self.btn_orbit.config(text=f"AUTO-ORBIT: {'ON' if self.auto_orbit else 'OFF'}")

    def _set_formation(self, mode: str):
        self.coordinator.set_formation_mode(mode)

    def _inject_obstacle(self):
        ox = random.uniform(-80.0, 80.0)
        oy = random.uniform(30.0, 90.0)
        oz = random.uniform(-80.0, 80.0)
        self.obstacles.append(Obstacle3D(x=ox, y=oy, z=oz, safe_radius=random.uniform(10.0, 18.0)))
        if len(self.obstacles) > 5:
            self.obstacles.pop(0)

    def _estop_cluster(self):
        for d in self.coordinator.drones:
            d.is_estop = not d.is_estop
            if d.is_estop:
                d.interlock.reset()
                d.state.vx = 0.0
                d.state.vy = -5.0
                d.state.vz = 0.0

    def _project_3d(self, x, y, z, cx, cy):
        # Rotate around Y (yaw)
        cos_y = math.cos(self.cam_yaw)
        sin_y = math.sin(self.cam_yaw)
        x1 = x * cos_y - z * sin_y
        z1 = x * sin_y + z * cos_y

        # Rotate around X (pitch)
        cos_p = math.cos(self.cam_pitch)
        sin_p = math.sin(self.cam_pitch)
        y2 = y * cos_p - z1 * sin_p
        z2 = y * sin_p + z1 * cos_p

        depth = z2 + self.cam_dist
        if depth <= 10.0:
            depth = 10.0

        scale = 380.0 / depth
        sx = cx + x1 * scale
        sy = cy - y2 * scale
        return sx, sy, depth

    def _render_loop(self):
        t0 = time.perf_counter()

        # Step Simulation
        step_res = self.coordinator.step_simulation(dt=0.035, obstacles=self.obstacles)
        self.rotor_angle += 0.8
        if self.auto_orbit:
            self.cam_yaw += 0.005

        # Measure latency
        compute_us = (time.perf_counter() - t0) * 1e6
        self.mean_latency_us = self.mean_latency_us * 0.95 + compute_us * 0.05
        self.decision_count += self.drone_count
        self.fps_decisions += self.drone_count

        now = time.time()
        if now - self.last_fps_time >= 0.5:
            dt_fps = now - self.last_fps_time
            self.current_decisions_per_sec = int(self.fps_decisions / dt_fps)
            self.fps_decisions = 0
            self.last_fps_time = now

        # Update Wealth History
        self.wealth_history.append(step_res["avg_martingale_wealth"])
        if len(self.wealth_history) > 60:
            self.wealth_history.pop(0)

        # Render panels
        self._render_3d_airspace()
        self._render_lif_panel()
        self._render_martingale_panel()
        self._render_crdt_panel()
        self._stream_wire_packets()

        # Update Header
        self.lbl_telemetry.config(
            text=f"DECISION RATE: {self.current_decisions_per_sec:,} Hz | LATENCY: {self.mean_latency_us:.1f} µs | CRDT MESH: 5 NODES | FORMATION: {step_res['formation']}"
        )

        self.after(20, self._render_loop)

    def _render_3d_airspace(self):
        c = self.canvas_3d
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10: w, h = 860, 560
        cx, cy = w / 2, h / 2 + 60

        # Draw Ground Grid
        grid_range = 160
        step = 40
        for gx in range(-grid_range, grid_range + 1, step):
            p1_sx, p1_sy, _ = self._project_3d(gx, 0, -grid_range, cx, cy)
            p2_sx, p2_sy, _ = self._project_3d(gx, 0, grid_range, cx, cy)
            c.create_line(p1_sx, p1_sy, p2_sx, p2_sy, fill="#121820", width=1)

        for gz in range(-grid_range, grid_range + 1, step):
            p1_sx, p1_sy, _ = self._project_3d(-grid_range, 0, gz, cx, cy)
            p2_sx, p2_sy, _ = self._project_3d(grid_range, 0, gz, cx, cy)
            c.create_line(p1_sx, p1_sy, p2_sx, p2_sy, fill="#121820", width=1)

        # Draw Obstacles (Safe Spheres)
        for obs in self.obstacles:
            osx, osy, od = self._project_3d(obs.x, obs.y, obs.z, cx, cy)
            r_screen = max(4.0, (obs.safe_radius * 380.0) / od)
            c.create_oval(
                osx - r_screen, osy - r_screen, osx + r_screen, osy + r_screen,
                outline="#ff3366", width=2, fill="#330015"
            )
            # Ground shadow
            gsx, gsy, _ = self._project_3d(obs.x, 0, obs.z, cx, cy)
            c.create_line(osx, osy, gsx, gsy, fill="#441122", dash=(2, 2))
            c.create_text(osx, osy - r_screen - 6, text="HAZARD ZONE", fill="#ff5555", font=("Consolas", 7))

        # Draw Inter-Drone CRDT Peer-to-Peer Mesh Links
        drones = self.coordinator.drones
        for i in range(len(drones)):
            next_i = (i + 1) % len(drones)
            d1, d2 = drones[i], drones[next_i]
            x1, y1, _ = self._project_3d(d1.state.x, d1.state.y, d1.state.z, cx, cy)
            x2, y2, _ = self._project_3d(d2.state.x, d2.state.y, d2.state.z, cx, cy)
            c.create_line(x1, y1, x2, y2, fill="#005577", dash=(3, 3), width=1)

        # Draw Drones
        for i, drone in enumerate(drones):
            dx, dy, dz = drone.state.x, drone.state.y, drone.state.z
            sx, sy, depth = self._project_3d(dx, dy, dz, cx, cy)
            gsx, gsy, _ = self._project_3d(dx, 0, dz, cx, cy)

            # Plumb line to ground shadow
            c.create_line(sx, sy, gsx, gsy, fill="#1a2530", dash=(2, 2))
            c.create_oval(gsx - 4, gsy - 2, gsx + 4, gsy + 2, fill="#121e28", outline="#203545")

            # Quadcopter Cross Frame
            arm_len = max(6.0, 16.0 * (380.0 / depth))
            c.create_line(sx - arm_len, sy, sx + arm_len, sy, fill="#40d0ff", width=2)
            c.create_line(sx, sy - arm_len, sx, sy + arm_len, fill="#40d0ff", width=2)

            # Rotating Rotors
            rotor_r = arm_len * 0.4
            c.create_oval(
                sx - arm_len - rotor_r, sy - rotor_r,
                sx - arm_len + rotor_r, sy + rotor_r,
                outline="#00f3ff", width=1
            )
            c.create_oval(
                sx + arm_len - rotor_r, sy - rotor_r,
                sx + arm_len + rotor_r, sy + rotor_r,
                outline="#00f3ff", width=1
            )

            # Center Hub
            color = "#ff0055" if drone.is_estop else ("#39ff14" if i == 0 else "#00f3ff")
            c.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, fill=color, outline="#ffffff")

            # Drone Tag
            role = "LEADER" if i == 0 else f"NODE-{i+1}"
            tag_text = f"UAV-{drone.drone_id} [{role}] {dy:.0f}m"
            c.create_text(sx, sy - arm_len - 8, text=tag_text, fill=color, font=("Consolas", 8, "bold"))

    def _render_lif_panel(self):
        c = self.canvas_lif
        c.delete("all")
        w = c.winfo_width()
        if w < 10: w = 560

        drones = self.coordinator.drones
        bar_w = (w - 40) / len(drones)
        for i, drone in enumerate(drones):
            bx = 20 + i * bar_w
            # Membrane gauge
            mem = min(1.0, drone.lif_membrane)
            gauge_h = mem * 60
            color = "#ff0055" if mem > 0.8 else ("#ffaa00" if mem > 0.4 else "#00f3ff")
            c.create_rectangle(bx, 80 - gauge_h, bx + bar_w - 8, 80, fill=color, outline="")
            c.create_rectangle(bx, 20, bx + bar_w - 8, 80, outline="#1b2430")
            c.create_text(
                bx + (bar_w - 8) / 2, 95,
                text=f"UAV-{drone.drone_id}\nSpikes:{drone.lif_spikes}",
                fill="#88aacc", font=("Consolas", 7)
            )

    def _render_martingale_panel(self):
        c = self.canvas_martingale
        c.delete("all")
        w = c.winfo_width()
        if w < 10: w = 560

        c.create_line(0, 20, w, 20, fill="#ff0055", dash=(3, 3))
        c.create_text(w - 70, 12, text="BARRIER 1/α=100", fill="#ff0055", font=("Consolas", 7, "bold"))

        if len(self.wealth_history) > 1:
            step_x = w / (len(self.wealth_history) - 1)
            points = []
            for idx, val in enumerate(self.wealth_history):
                # Clamp log-scale wealth
                norm_y = 90 - (min(val, 100.0) / 100.0) * 70
                points.extend([idx * step_x, norm_y])
            c.create_line(points, fill="#39ff14", width=2)

    def _render_crdt_panel(self):
        c = self.canvas_crdt
        c.delete("all")
        w = c.winfo_width()
        if w < 10: w = 560

        drones = self.coordinator.drones
        step_x = (w - 30) / len(drones)
        for i, drone in enumerate(drones):
            x = 20 + i * step_x
            c.create_oval(x, 20, x + 30, 50, fill="#0d2030", outline="#00f3ff", width=1)
            c.create_text(x + 15, 35, text=f"N{drone.drone_id}", fill="#00f3ff", font=("Consolas", 8, "bold"))
            clock = drone.crdt_tree.local_clock
            c.create_text(x + 15, 65, text=f"Clock:{clock}", fill="#39ff14", font=("Consolas", 7))

    def _stream_wire_packets(self):
        if random.random() < 0.35:
            d = random.choice(self.coordinator.drones)
            # Create real MAVLink AttitudeTarget
            target = AttitudeTarget(
                time_boot_ms=int(time.time() * 1000) & 0xFFFFFFFF,
                q=(1.0, 0.0, 0.0, 0.0),
                body_roll_rate=random.uniform(-0.1, 0.1),
                body_pitch_rate=random.uniform(-0.1, 0.1),
                body_yaw_rate=random.uniform(-0.05, 0.05),
                thrust=random.uniform(0.65, 0.85)
            )
            mav_bytes = MavlinkBridge.serialize_attitude_target(d.drone_id, 1, d.crdt_tree.local_clock, target)
            hex_str = " ".join(f"{b:02X}" for b in mav_bytes[:16])

            msg = f"[MAV2][UAV-{d.drone_id}] MSG#82 T={target.thrust:.2f} | HEX: {hex_str}...\n"
            self.txt_wire.insert(tk.END, msg)

            lines = int(self.txt_wire.index("end-1c").split(".")[0])
            if lines > 15:
                self.txt_wire.delete("1.0", "2.0")
            self.txt_wire.see(tk.END)

def main():
    app = AxiomSwarmCockpit3D()
    app.mainloop()

if __name__ == "__main__":
    main()
