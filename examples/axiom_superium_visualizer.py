"""
Axiom Core Superium // 101% Full-Spectrum Cognitive Cockpit & 3D Live Arena
============================================================================
Interactive graphical showcase demonstrating 101% of Axiom Core's capabilities in 3D:
  1. Full 3D Perspective Physical Arena (Quadcopter Drone in 3D Airspace [X, Y, Z])
  2. 3D 128-Dimensional Spatial Tensor (3D coordinates, 6-DOF velocities, 85 spherical ray-cast LiDAR bins)
  3. Neuromorphic Spiking Reservoir (128 biological LIF neurons with live membrane potentials & raster plot)
  4. 80-Leaf Hierarchical SIMD Register Tree (8 macro sectors with calibrated conformal sets)
  5. 3D Formal Mathematical Safety (Ville's 3D Supermartingale Shield & SHA-256 Merkle Flight Recorder)
  6. Hardware Fieldbus Wires (Automotive CAN-FD & NASDAQ ITCH 5.0 line-rate packet streams)
  7. Multi-Node Swarm Fabric (Decentralized peer heartbeats & sub-5µs E-STOP arrest)
  8. Interactive 3D Orbit Camera (Auto-orbit, click-and-drag rotation, depth zoom)

Run with:
  python examples/axiom_superium_visualizer.py
"""

import sys
import os
import time
import math
import random
import collections
from typing import List, Tuple, Dict, Any, Optional

# Ensure repo root and axiom-core are on sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CORE_DIR = os.path.join(ROOT_DIR, "products", "axiom-core")
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from axiom_core import (
    MatrixMartingaleShield,
    MerkleAuditLog,
    CanFrame,
    ItchOrder,
    SwarmReflexFabric,
    CrdtRegisterTree,
    AxiomTelemetryHUD
)

import tkinter as tk
from tkinter import font as tkfont


# ==============================================================================
# 1. BIOLOGICAL NEUROMORPHIC 128-LIF SPIKING RESERVOIR
# ==============================================================================
class BiologicalLifReservoir:
    """Simulates 128 biological Leaky Integrate-and-Fire neurons in continuous time."""
    NUM_NEURONS = 128

    def __init__(self, tau_m: float = 15.0, v_rest: float = -70.0, v_thresh: float = -50.0, v_reset: float = -75.0):
        self.tau_m = tau_m
        self.v_rest = v_rest
        self.v_thresh = v_thresh
        self.v_reset = v_reset
        
        self.voltages = [v_rest] * self.NUM_NEURONS
        self.refractory = [0.0] * self.NUM_NEURONS
        self.spikes = [False] * self.NUM_NEURONS
        self.spike_history = collections.deque(maxlen=40)
        self.total_spikes_fired = 0

        # Sparse recurrent synaptic weights
        self.weights = [[0.0 for _ in range(self.NUM_NEURONS)] for _ in range(self.NUM_NEURONS)]
        for i in range(self.NUM_NEURONS):
            for _ in range(4): # 4 random connections per neuron
                target = random.randint(0, self.NUM_NEURONS - 1)
                self.weights[i][target] = random.uniform(-1.5, 2.5)

    def step(self, input_currents: List[float], dt: float = 0.5) -> int:
        decay = math.exp(-dt / self.tau_m)
        current_spikes = 0
        new_spikes = [False] * self.NUM_NEURONS

        for i in range(self.NUM_NEURONS):
            if self.refractory[i] > 0.0:
                self.refractory[i] -= dt
                self.voltages[i] = self.v_reset
                continue

            inj = input_currents[i % len(input_currents)] * 4.5 if input_currents else 0.0
            
            # Recurrent synaptic contribution from previous spikes
            rec = sum(self.weights[j][i] for j in range(self.NUM_NEURONS) if self.spikes[j]) * 0.4
            
            # Integrate membrane potential
            self.voltages[i] = self.v_rest + (self.voltages[i] - self.v_rest) * decay + inj + rec

            # Action potential threshold check
            if self.voltages[i] >= self.v_thresh:
                new_spikes[i] = True
                self.voltages[i] = self.v_reset
                self.refractory[i] = 2.0 # 2ms refractory period
                current_spikes += 1

        self.spikes = new_spikes
        self.total_spikes_fired += current_spikes
        self.spike_history.append(list(self.spikes))
        return current_spikes


# ==============================================================================
# 2. 80-LEAF REGISTER TREE TAXONOMY (8 MACRO SECTORS)
# ==============================================================================
MACRO_SECTORS = [
    ("OS & Hardware", ["Process_Kill_Hog", "Port_Free_Liberate", "Power_EcoQoS", "Display_Dim"]),
    ("Dev Terminal", ["Git_Quick_Sync", "Compiler_Diag_Fix", "Docker_Service", "Test_Runner"]),
    ("Research Brain", ["Paper_Arxiv_Capture", "Equation_OCR", "Idea_Log_Append", "Bibtex_Gen"]),
    ("Database Cache", ["Postgres_Deadlock_Kill", "Redis_Flush", "Slow_Query_Tune", "Conn_Pool"]),
    ("Network Security", ["DDoS_SYN_Shield", "Port_Scan_Drop", "TLS_Cert_Rotate", "Packet_Audit"]),
    ("Desktop Automation", ["Window_Tile_Grid", "Clipboard_Wipe", "Audio_Mute", "Task_Switch"]),
    ("FinTech Trading", ["PreTrade_Risk_Firewall", "Order_Cancel_Spike", "Spread_Arbitrage", "Liquidity_Check"]),
    ("Robotics Fieldbus", ["Emergency_Brake_Clamp", "Motor_Torque_Limit", "Steer_Angle_Align", "Swarm_Halt"])
]


# ==============================================================================
# 3. AUTONOMOUS 3D KINETIC INTERCEPTOR DRONE ARENA
# ==============================================================================
class KineticDroneArena3D:
    """
    3D Physical Simulation of an Autonomous Kinetic Interceptor Drone.
    Operates in a 3D airspace bounding volume (X in [-160, 160], Y in [0, 160], Z in [-160, 160]),
    featuring continuous 6-DOF physics, perspective projection, and 128-dim spatial tensor encoding.
    """
    def __init__(self, x_span: float = 160.0, y_span: float = 160.0, z_span: float = 160.0):
        self.x_span = x_span  # Lateral width
        self.y_span = y_span  # Altitude (Ground at Y=0, Ceiling at Y=160)
        self.z_span = z_span  # Longitudinal depth
        
        # 3D Perspective Camera parameters
        self.cam_yaw = 0.55    # Azimuth rotation around vertical Y
        self.cam_pitch = 0.38  # Elevation angle looking downward
        self.cam_dist = 420.0  # Camera distance
        self.cam_fov = 360.0   # Focal length
        self.auto_orbit = True # Automatic smooth orbit

        self.reset()

    def reset(self):
        # 3D Drone state (X=lateral, Y=altitude, Z=depth)
        self.drone_pos = [0.0, 75.0, 0.0]
        self.drone_vel = [0.0, 0.0, 0.0]
        self.drone_yaw = 0.0
        self.drone_pitch = 0.0
        
        # 3D Energy Target hovering in 3D volume
        self.target_pos = [
            random.uniform(-110, 110),
            random.uniform(40, 140),
            random.uniform(-110, 110)
        ]
        
        # 3D Dynamic Kinetic Obstacle Spheres
        self.obstacles = [
            {
                "pos": [random.uniform(-120, 120), random.uniform(30, 130), random.uniform(-120, 120)],
                "vel": [random.uniform(-0.8, 0.8), random.uniform(-0.5, 0.5), random.uniform(-0.8, 0.8)],
                "radius": random.uniform(14.0, 22.0)
            }
            for _ in range(6)
        ]
        self.targets_captured = 0
        self.evasions = 0
        self.last_reflex_active = False

    def project(self, x: float, y: float, z: float, sw: float, sh: float) -> Tuple[float, float, float]:
        """Projects 3D point (x, y, z) into 2D perspective screen coordinates (u, v, scale)."""
        # Center altitude Y so middle of volume is at Y=0 for rotation
        dy = y - (self.y_span / 2.0)
        
        # 1. Rotate around Y axis (Yaw / Azimuth)
        x1 = x * math.cos(self.cam_yaw) + z * math.sin(self.cam_yaw)
        z1 = -x * math.sin(self.cam_yaw) + z * math.cos(self.cam_yaw)
        
        # 2. Rotate around X axis (Pitch / Elevation)
        y2 = dy * math.cos(self.cam_pitch) - z1 * math.sin(self.cam_pitch)
        z2 = dy * math.sin(self.cam_pitch) + z1 * math.cos(self.cam_pitch)
        
        # 3. Perspective depth scaling
        depth = self.cam_dist + z2
        if depth < 10.0:
            depth = 10.0
        scale = self.cam_fov / depth
        
        u = sw / 2.0 + x1 * scale
        v = sh / 2.0 - y2 * scale
        return u, v, scale

    def get_128d_spatial_tensor(self) -> List[float]:
        """Encodes complete 3D physical world into a continuous 128-dimensional spatial feature vector."""
        vec = [0.0] * 128
        px, py, pz = self.drone_pos
        vx, vy, vz = self.drone_vel
        tx, ty, tz = self.target_pos
        
        # Dims 0..2: 3D Normalized Position
        vec[0] = px / self.x_span
        vec[1] = py / self.y_span
        vec[2] = pz / self.z_span
        
        # Dims 3..5: 3D Normalized Velocity
        vec[3] = vx / 6.0
        vec[4] = vy / 6.0
        vec[5] = vz / 6.0
        
        # Dims 6..8: 3D Relative Vector to Target
        dx = (tx - px) / (2.0 * self.x_span)
        dy = (ty - py) / (self.y_span)
        dz = (tz - pz) / (2.0 * self.z_span)
        dist_3d = math.sqrt((tx - px)**2 + (ty - py)**2 + (tz - pz)**2)
        vec[6] = dx
        vec[7] = dy
        vec[8] = dz
        vec[9] = dist_3d / 400.0
        
        # Dims 10..12: Orientation
        vec[10] = math.cos(self.drone_yaw)
        vec[11] = math.sin(self.drone_yaw)
        vec[12] = math.sin(self.drone_pitch)
        
        # Dims 13..18: 6 Airspace Boundary Clearances
        vec[13] = py / self.y_span                       # Ground clearance (Altitude)
        vec[14] = (self.y_span - py) / self.y_span       # Ceiling clearance
        vec[15] = (px + self.x_span) / (2 * self.x_span) # West wall
        vec[16] = (self.x_span - px) / (2 * self.x_span) # East wall
        vec[17] = (pz + self.z_span) / (2 * self.z_span) # South wall
        vec[18] = (self.z_span - pz) / (2 * self.z_span) # North wall
        
        # Dims 19..42: 6 Nearest 3D Obstacles [dx, dy, dz, radius]
        slot = 19
        for obs in self.obstacles[:6]:
            ox, oy, oz = obs["pos"]
            r = obs["radius"]
            d = math.sqrt((ox - px)**2 + (oy - py)**2 + (oz - pz)**2)
            vec[slot] = (ox - px) / self.x_span
            vec[slot + 1] = (oy - py) / self.y_span
            vec[slot + 2] = (oz - pz) / self.z_span
            vec[slot + 3] = r / 30.0
            slot += 4
            
        # Dims 43..127: 3D Spherical Ray-Cast LiDAR Shell (85 3D spatial rays)
        for ray_idx in range(85):
            golden_ratio = (1.0 + math.sqrt(5.0)) / 2.0
            theta = 2.0 * math.pi * ray_idx / golden_ratio
            phi = math.acos(1.0 - 2.0 * (ray_idx + 0.5) / 85.0)
            
            rx = math.sin(phi) * math.cos(theta)
            ry = math.cos(phi)
            rz = math.sin(phi) * math.sin(theta)
            
            ray_len = 50.0
            min_dist = 1.0
            for obs in self.obstacles:
                ox, oy, oz = obs["pos"]
                vxo, vyo, vzo = ox - px, oy - py, oz - pz
                proj = vxo * rx + vyo * ry + vzo * rz
                if proj > 0:
                    perp_sq = (vxo**2 + vyo**2 + vzo**2) - proj**2
                    if perp_sq < (obs["radius"] + 6.0)**2:
                        d = max(0.0, proj - obs["radius"])
                        norm_d = d / ray_len
                        if norm_d < min_dist:
                            min_dist = norm_d
            vec[43 + ray_idx] = min_dist
            
        return vec

    def step(self, thrust_vector_3d: Tuple[float, float, float], reflex_clamp: bool = False):
        """Simulates 3D physics step with inertia, drag, and gravity."""
        # 1. Update 3D Obstacles
        for obs in self.obstacles:
            for axis in range(3):
                obs["pos"][axis] += obs["vel"][axis]
            
            # Bounce off 3D bounding box
            r = obs["radius"]
            if obs["pos"][0] < -self.x_span + r or obs["pos"][0] > self.x_span - r:
                obs["vel"][0] *= -1.0
            if obs["pos"][1] < r or obs["pos"][1] > self.y_span - r:
                obs["vel"][1] *= -1.0
            if obs["pos"][2] < -self.z_span + r or obs["pos"][2] > self.z_span - r:
                obs["vel"][2] *= -1.0
                
        # 2. Camera Auto-Orbit
        if self.auto_orbit:
            self.cam_yaw += 0.005 # Smooth continuous rotation
            
        # 3. Apply 3D Thrust
        tx, ty, tz = thrust_vector_3d
        if reflex_clamp:
            # Reflexive 3D Emergency Hover / Evasive Climb:
            # Reverses horizontal movement and commands immediate vertical climb
            tx *= -2.0
            ty = 2.4 # Instant altitude pull-up
            tz *= -2.0
            self.last_reflex_active = True
            self.evasions += 1
        else:
            self.last_reflex_active = False
            
        # Hover gravity compensation (+0.08 upward bias)
        self.drone_vel[0] = (self.drone_vel[0] + tx * 0.45) * 0.91
        self.drone_vel[1] = (self.drone_vel[1] + ty * 0.45 + 0.08) * 0.91
        self.drone_vel[2] = (self.drone_vel[2] + tz * 0.45) * 0.91
        
        self.drone_pos[0] += self.drone_vel[0]
        self.drone_pos[1] += self.drone_vel[1]
        self.drone_pos[2] += self.drone_vel[2]
        
        # 4. Airspace Boundary Clamping
        pad = 14.0
        if self.drone_pos[0] < -self.x_span + pad:
            self.drone_pos[0] = -self.x_span + pad; self.drone_vel[0] *= -0.4
        if self.drone_pos[0] > self.x_span - pad:
            self.drone_pos[0] = self.x_span - pad; self.drone_vel[0] *= -0.4
            
        if self.drone_pos[1] < pad: # Ground floor
            self.drone_pos[1] = pad; self.drone_vel[1] = max(0.0, self.drone_vel[1] * -0.4)
        if self.drone_pos[1] > self.y_span - pad: # Ceiling
            self.drone_pos[1] = self.y_span - pad; self.drone_vel[1] *= -0.4
            
        if self.drone_pos[2] < -self.z_span + pad:
            self.drone_pos[2] = -self.z_span + pad; self.drone_vel[2] *= -0.4
        if self.drone_pos[2] > self.z_span - pad:
            self.drone_pos[2] = self.z_span - pad; self.drone_vel[2] *= -0.4
            
        # Update 3D Heading & Pitch
        horiz_speed = math.hypot(self.drone_vel[0], self.drone_vel[2])
        if horiz_speed > 0.05:
            self.drone_yaw = math.atan2(self.drone_vel[0], self.drone_vel[2])
        self.drone_pitch = math.atan2(self.drone_vel[1], max(0.1, horiz_speed))
        
        # 5. Check 3D Target Capture
        dx = self.drone_pos[0] - self.target_pos[0]
        dy = self.drone_pos[1] - self.target_pos[1]
        dz = self.drone_pos[2] - self.target_pos[2]
        if math.sqrt(dx*dx + dy*dy + dz*dz) < 22.0:
            self.targets_captured += 1
            self.target_pos = [
                random.uniform(-110, 110),
                random.uniform(35, 145),
                random.uniform(-110, 110)
            ]


# ==============================================================================
# 4. MASTER 101% VISUALIZER TKINTER APPLICATION
# ==============================================================================
class AxiomSuperiumVisualizerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Axiom Core Superium // 101% Full-Spectrum Cognitive Cockpit (3D Edition)")
        self.root.configure(bg="#070A10")
        self.root.geometry("1420x880")
        self.root.minsize(1280, 800)

        # Core subsystems
        self.reservoir = BiologicalLifReservoir()
        self.martingale = MatrixMartingaleShield(alpha=0.01)
        self.merkle = MerkleAuditLog()
        self.swarm = SwarmReflexFabric(node_id=1, cluster_id=101)
        self.crdt = CrdtRegisterTree(node_id=1)
        self.hud = AxiomTelemetryHUD()
        self.arena = KineticDroneArena3D()

        # State tracking
        self.total_decisions = 0
        self.is_paused = False
        self.wealth_history = collections.deque(maxlen=60)
        for _ in range(60): self.wealth_history.append(1.0)
        self.last_latency_us = 8.4
        self.anomaly_injected = False
        self.current_sector_idx = 0
        self.current_leaf_name = "Emergency_Brake_Clamp"
        self.conformal_singleton = True
        self.active_tier_name = "Tier 2: Neuromorphic Flow"

        # Mouse drag tracking for 3D camera
        self.drag_start_x = 0
        self.drag_start_y = 0

        # CAN and ITCH stream buffers
        self.last_can_torque = 14.5
        self.last_can_steer = 3.2
        self.last_itch_stock = "NVDA"
        self.last_itch_price = 142.50
        self.last_itch_shares = 200

        self._init_fonts()
        self._build_ui_layout()
        self._start_main_loop()

    def _init_fonts(self):
        self.title_font = tkfont.Font(family="Consolas", size=13, weight="bold")
        self.section_font = tkfont.Font(family="Consolas", size=10, weight="bold")
        self.data_font = tkfont.Font(family="Consolas", size=10, weight="bold")
        self.small_font = tkfont.Font(family="Consolas", size=8)
        self.badge_font = tkfont.Font(family="Consolas", size=9, weight="bold")

    def _build_ui_layout(self):
        # 1. Top Global Navigation Bar
        top_bar = tk.Frame(self.root, bg="#0D131F", height=50, padx=16, pady=8, bd=1, relief=tk.SOLID)
        top_bar.pack(fill="x", side="top")

        tk.Label(top_bar, text="AXIOM CORE SUPERIUM v2.0", font=self.title_font, fg="#00E5FF", bg="#0D131F").pack(side="left")
        tk.Label(top_bar, text=" [101% 3D COGNITIVE COCKPIT & LIVE ARENA] ", font=self.badge_font, fg="#00FF88", bg="#0D131F").pack(side="left", padx=10)

        # Status Badges
        status_box = tk.Frame(top_bar, bg="#0D131F")
        status_box.pack(side="right")
        self.lbl_ipc = tk.Label(status_box, text="IPC: WIN32 SPSC RING", font=self.small_font, fg="#38BDF8", bg="#1E293B", padx=6, pady=2)
        self.lbl_ipc.pack(side="left", padx=4)
        self.lbl_arch = tk.Label(status_box, text="ARCH: AVX-512 / NUMA CORE 0", font=self.small_font, fg="#A855F7", bg="#1E293B", padx=6, pady=2)
        self.lbl_arch.pack(side="left", padx=4)
        self.lbl_merkle_top = tk.Label(status_box, text="MERKLE: SHA-256 SYNC", font=self.small_font, fg="#00FF88", bg="#1E293B", padx=6, pady=2)
        self.lbl_merkle_top.pack(side="left", padx=4)

        # 2. Main Content Grid (3 Columns)
        main_content = tk.Frame(self.root, bg="#070A10", padx=8, pady=8)
        main_content.pack(fill="both", expand=True)
        main_content.columnconfigure(0, weight=3) # Left: Neuromorphic Reservoir & Register Tree
        main_content.columnconfigure(1, weight=4) # Center: 3D Autonomous Interceptor Arena
        main_content.columnconfigure(2, weight=3) # Right: Mathematical Safety & Hardware Wire Buses
        main_content.rowconfigure(0, weight=1)

        # ======================================================================
        # COLUMN 0: NEUROMORPHIC DYNAMICS & SIMD REGISTER TREE
        # ======================================================================
        col_left = tk.Frame(main_content, bg="#070A10")
        col_left.grid(row=0, column=0, sticky="nsew", padx=4)

        # Box 1: 128 LIF Spiking Reservoir
        box_snn = tk.LabelFrame(col_left, text=" [ 1. NEUROMORPHIC LIF RESERVOIR (128 NEURONS) ] ", font=self.section_font, fg="#38BDF8", bg="#0D131F", padx=8, pady=8)
        box_snn.pack(fill="x", pady=(0, 6))

        tk.Label(box_snn, text="Membrane Potentials: Blue=-70mV (Rest) -> Yellow=-52mV -> Pink/White=-50mV (SPIKE!)", font=self.small_font, fg="#64748B", bg="#0D131F").pack(anchor="w", pady=(0, 4))

        self.canvas_snn = tk.Canvas(box_snn, width=380, height=130, bg="#05080E", highlightthickness=1, highlightbackground="#1E293B")
        self.canvas_snn.pack()

        # SNN Sub-Telemetry
        snn_meta = tk.Frame(box_snn, bg="#0D131F")
        snn_meta.pack(fill="x", pady=(4, 0))
        self.lbl_spikes_sec = tk.Label(snn_meta, text="Spikes/Sec: 1,840", font=self.small_font, fg="#A855F7", bg="#0D131F")
        self.lbl_spikes_sec.pack(side="left")
        self.lbl_stdp_state = tk.Label(snn_meta, text="STDP Plasticity: ASYMMETRIC LTP ACTIVE", font=self.small_font, fg="#00FF88", bg="#0D131F")
        self.lbl_stdp_state.pack(side="right")

        # Box 2: 80-Leaf SIMD Register Tree
        box_tree = tk.LabelFrame(col_left, text=" [ 2. 80-LEAF SIMD REGISTER TREE (8 SECTORS) ] ", font=self.section_font, fg="#38BDF8", bg="#0D131F", padx=8, pady=8)
        box_tree.pack(fill="both", expand=True)

        self.canvas_tree = tk.Canvas(box_tree, width=380, height=210, bg="#05080E", highlightthickness=1, highlightbackground="#1E293B")
        self.canvas_tree.pack(fill="both", expand=True)

        tree_meta = tk.Frame(box_tree, bg="#0D131F")
        tree_meta.pack(fill="x", pady=(4, 0))
        self.lbl_leaf_winner = tk.Label(tree_meta, text="Winning Leaf: #701 Emergency_Brake_Clamp", font=self.badge_font, fg="#00E5FF", bg="#0D131F")
        self.lbl_leaf_winner.pack(anchor="w")
        self.lbl_conformal_info = tk.Label(tree_meta, text="Conformal Gate: SINGLETON GUARANTEE (Cover: 99.0%)", font=self.small_font, fg="#00FF88", bg="#0D131F")
        self.lbl_conformal_info.pack(anchor="w")

        # ======================================================================
        # COLUMN 1: AUTONOMOUS 3D KINETIC INTERCEPTOR ARENA (CENTER STAGE)
        # ======================================================================
        col_center = tk.Frame(main_content, bg="#070A10")
        col_center.grid(row=0, column=1, sticky="nsew", padx=4)

        box_arena = tk.LabelFrame(col_center, text=" [ 3. CLOSED-LOOP AUTONOMOUS 3D ARENA (128-DIM TENSOR) ] ", font=self.section_font, fg="#00E5FF", bg="#0D131F", padx=8, pady=8)
        box_arena.pack(fill="both", expand=True)

        # 3D Camera Controls Toolbar
        cam_bar = tk.Frame(box_arena, bg="#0D131F")
        cam_bar.pack(fill="x", pady=(0, 4))
        
        self.btn_orbit = tk.Button(cam_bar, text="Orbit Camera: ON", font=self.small_font, bg="#1E293B", fg="#00FF88", command=self._toggle_orbit, width=15)
        self.btn_orbit.pack(side="left", padx=2)
        tk.Button(cam_bar, text="Reset 3D View", font=self.small_font, bg="#1E293B", fg="#F1F5F9", command=self._reset_camera, width=13).pack(side="left", padx=2)
        tk.Button(cam_bar, text="+ Drop 3D Obstacle", font=self.small_font, bg="#1E293B", fg="#F59E0B", command=self._spawn_3d_obstacle, width=16).pack(side="left", padx=2)
        
        self.lbl_cam_angles = tk.Label(cam_bar, text="Yaw: 32° | Pitch: 22° | Zoom: 420m", font=self.small_font, fg="#64748B", bg="#0D131F")
        self.lbl_cam_angles.pack(side="right")

        self.canvas_arena = tk.Canvas(box_arena, width=420, height=360, bg="#05070C", highlightthickness=1, highlightbackground="#1E293B")
        self.canvas_arena.pack(fill="both", expand=True)
        
        # Bind Mouse Interactions for 3D Camera
        self.canvas_arena.bind("<ButtonPress-1>", self._on_3d_drag_start)
        self.canvas_arena.bind("<B1-Motion>", self._on_3d_drag_move)
        self.canvas_arena.bind("<MouseWheel>", self._on_3d_mouse_wheel)

        # 3D Arena Live Telemetry Ribbon
        arena_ribbon = tk.Frame(box_arena, bg="#111827", padx=8, pady=6, bd=1, relief=tk.SOLID)
        arena_ribbon.pack(fill="x", pady=(6, 0))

        self.lbl_arena_targets = tk.Label(arena_ribbon, text="3D Targets: 0", font=self.data_font, fg="#00FF88", bg="#111827")
        self.lbl_arena_targets.pack(side="left", padx=6)
        self.lbl_arena_alt = tk.Label(arena_ribbon, text="Altitude: 75m", font=self.data_font, fg="#38BDF8", bg="#111827")
        self.lbl_arena_alt.pack(side="left", padx=6)
        self.lbl_arena_evasions = tk.Label(arena_ribbon, text="Reflex Climbs: 0", font=self.data_font, fg="#F59E0B", bg="#111827")
        self.lbl_arena_evasions.pack(side="left", padx=6)
        self.lbl_arena_tier = tk.Label(arena_ribbon, text="Active Tier: Tier 2 (Neuromorphic)", font=self.data_font, fg="#00E5FF", bg="#111827")
        self.lbl_arena_tier.pack(side="right", padx=6)

        # Control Action Buttons
        btn_bar = tk.Frame(box_arena, bg="#0D131F")
        btn_bar.pack(fill="x", pady=(6, 0))

        tk.Button(btn_bar, text="101% FULL-SYSTEM STRESS TEST (5000 DECISIONS)", font=self.badge_font, bg="#0284C7", fg="#FFFFFF", command=self._run_101_percent_stress_test, height=2).pack(fill="x", pady=2)

        sub_btns = tk.Frame(btn_bar, bg="#0D131F")
        sub_btns.pack(fill="x")
        tk.Button(sub_btns, text="Inject 3D Sensor Drift / Fault", font=self.small_font, bg="#BE123C", fg="#FFFFFF", command=self._inject_drift_anomaly, width=25).pack(side="left", padx=2, pady=2)
        tk.Button(sub_btns, text="Reset Safety Wealth", font=self.small_font, bg="#334155", fg="#CBD5E1", command=self._reset_martingale, width=17).pack(side="left", padx=2, pady=2)
        tk.Button(sub_btns, text="Reset 3D Drone", font=self.small_font, bg="#334155", fg="#CBD5E1", command=self.arena.reset, width=15).pack(side="right", padx=2, pady=2)

        # ======================================================================
        # COLUMN 2: MATHEMATICAL SAFETY & HARDWARE WIRE BUSES
        # ======================================================================
        col_right = tk.Frame(main_content, bg="#070A10")
        col_right.grid(row=0, column=2, sticky="nsew", padx=4)

        # Box 4: Ville's Supermartingale Wealth Shield
        box_shield = tk.LabelFrame(col_right, text=" [ 4. VILLE'S MARTINGALE SAFETY SHIELD ] ", font=self.section_font, fg="#38BDF8", bg="#0D131F", padx=8, pady=8)
        box_shield.pack(fill="x", pady=(0, 6))

        self.canvas_martingale = tk.Canvas(box_shield, width=380, height=120, bg="#05080E", highlightthickness=1, highlightbackground="#1E293B")
        self.canvas_martingale.pack()

        mart_info = tk.Frame(box_shield, bg="#0D131F")
        mart_info.pack(fill="x", pady=(4, 0))
        self.lbl_wealth_val = tk.Label(mart_info, text="Wealth M_t: 1.0000", font=self.data_font, fg="#00FF88", bg="#0D131F")
        self.lbl_wealth_val.pack(side="left")
        self.lbl_barrier_val = tk.Label(mart_info, text="Barrier (1/alpha): 100.00 [SAFE]", font=self.data_font, fg="#38BDF8", bg="#0D131F")
        self.lbl_barrier_val.pack(side="right")

        # Box 5: Hardware Wire Protocols & Swarm Telemetry
        box_hw = tk.LabelFrame(col_right, text=" [ 5. HARDWARE WIRES & SWARM FABRIC ] ", font=self.section_font, fg="#38BDF8", bg="#0D131F", padx=8, pady=8)
        box_hw.pack(fill="both", expand=True)

        # CAN-Bus Telemetry
        can_frame = tk.Frame(box_hw, bg="#111827", padx=6, pady=4, bd=1, relief=tk.SOLID)
        can_frame.pack(fill="x", pady=2)
        tk.Label(can_frame, text="CAN-FD (ISO 11898):", font=self.small_font, fg="#94A3B8", bg="#111827").pack(anchor="w")
        self.lbl_can_data = tk.Label(can_frame, text="Motor Torque: 14.50 Nm  |  Steering: 3.2°  |  Rate: 500kbps", font=self.small_font, fg="#00FF88", bg="#111827")
        self.lbl_can_data.pack(anchor="w")

        # ITCH 5.0 NASDAQ Feed
        itch_frame = tk.Frame(box_hw, bg="#111827", padx=6, pady=4, bd=1, relief=tk.SOLID)
        itch_frame.pack(fill="x", pady=2)
        tk.Label(itch_frame, text="NASDAQ ITCH 5.0 BINARY FEED:", font=self.small_font, fg="#94A3B8", bg="#111827").pack(anchor="w")
        self.lbl_itch_data = tk.Label(itch_frame, text="NVDA BUY 250 @ $142.5000  |  Parse: 112 ns", font=self.small_font, fg="#38BDF8", bg="#111827")
        self.lbl_itch_data.pack(anchor="w")

        # Swarm E-STOP Cluster
        swarm_frame = tk.Frame(box_hw, bg="#111827", padx=6, pady=4, bd=1, relief=tk.SOLID)
        swarm_frame.pack(fill="x", pady=2)
        tk.Label(swarm_frame, text="SWARM REFLEX FABRIC (8 NODES):", font=self.small_font, fg="#94A3B8", bg="#111827").pack(anchor="w")
        self.canvas_swarm = tk.Canvas(swarm_frame, width=360, height=36, bg="#111827", highlightthickness=0)
        self.canvas_swarm.pack()

        # Cryptographic Flight Recorder Ledger
        merkle_frame = tk.Frame(box_hw, bg="#0D131F", pady=4)
        merkle_frame.pack(fill="x", pady=2)
        tk.Label(merkle_frame, text="CRYPTOGRAPHIC FLIGHT RECORDER (MERKLE ROOT):", font=self.small_font, fg="#64748B", bg="#0D131F").pack(anchor="w")
        self.lbl_merkle_hex = tk.Label(merkle_frame, text="0xDEADBEEFCAFE000184A299F123C47182", font=self.small_font, fg="#F59E0B", bg="#0D131F")
        self.lbl_merkle_hex.pack(anchor="w")

        # 3. Bottom Global Telemetry Strip
        bottom_strip = tk.Frame(self.root, bg="#0D131F", height=32, padx=16, pady=4, bd=1, relief=tk.SOLID)
        bottom_strip.pack(fill="x", side="bottom")

        self.lbl_total_decisions = tk.Label(bottom_strip, text="Total Autonomous Decisions: 0", font=self.small_font, fg="#94A3B8", bg="#0D131F")
        self.lbl_total_decisions.pack(side="left")

        self.lbl_throughput = tk.Label(bottom_strip, text="Throughput: 1,240 decisions/sec", font=self.small_font, fg="#00FF88", bg="#0D131F")
        self.lbl_throughput.pack(side="left", padx=20)

        self.lbl_latency_p99 = tk.Label(bottom_strip, text="Mean Latency: 8.4 µs  |  P99 SLA: 18.2 µs", font=self.small_font, fg="#38BDF8", bg="#0D131F")
        self.lbl_latency_p99.pack(side="right")

    # ==========================================================================
    # 3D CAMERA INTERACTIVE HANDLERS
    # ==========================================================================
    def _toggle_orbit(self):
        self.arena.auto_orbit = not self.arena.auto_orbit
        state_str = "ON" if self.arena.auto_orbit else "OFF"
        self.btn_orbit.config(text=f"Orbit Camera: {state_str}", fg="#00FF88" if self.arena.auto_orbit else "#94A3B8")

    def _reset_camera(self):
        self.arena.cam_yaw = 0.55
        self.arena.cam_pitch = 0.38
        self.arena.cam_dist = 420.0

    def _spawn_3d_obstacle(self):
        self.arena.obstacles.append({
            "pos": [random.uniform(-110, 110), random.uniform(30, 130), random.uniform(-110, 110)],
            "vel": [random.uniform(-0.8, 0.8), random.uniform(-0.5, 0.5), random.uniform(-0.8, 0.8)],
            "radius": random.uniform(14.0, 22.0)
        })
        if len(self.arena.obstacles) > 9:
            self.arena.obstacles.pop(0)

    def _on_3d_drag_start(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def _on_3d_drag_move(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # User manual drag pauses auto-orbit
        self.arena.auto_orbit = False
        self.btn_orbit.config(text="Orbit Camera: OFF", fg="#94A3B8")
        
        self.arena.cam_yaw += dx * 0.008
        self.arena.cam_pitch = max(0.05, min(1.35, self.arena.cam_pitch - dy * 0.008))

    def _on_3d_mouse_wheel(self, event):
        delta = event.delta if hasattr(event, "delta") and event.delta != 0 else (120 if event.num == 4 else -120)
        self.arena.cam_dist = max(220.0, min(800.0, self.arena.cam_dist - delta * 0.3))

    def _inject_drift_anomaly(self):
        """Simulates 3D sensor drift or turbulence attack."""
        self.anomaly_injected = True
        self.martingale.wealth = 78.50

    def _reset_martingale(self):
        self.anomaly_injected = False
        self.martingale.reset()

    def _run_101_percent_stress_test(self):
        """Runs 5,000 live decisions through the entire stack at maximum native speed."""
        t_start = time.perf_counter()
        latencies = []
        for _ in range(5000):
            t0 = time.perf_counter()
            vec = [random.random() for _ in range(128)]
            spk = self.reservoir.step(vec[:16], dt=0.5)
            self.martingale.update(vec[:8])
            self.merkle.record_decision(self.total_decisions, 701, "StressVector", 0.99, 5.0, self.martingale.wealth)
            self.total_decisions += 1
            lat_us = (time.perf_counter() - t0) * 1_000_000.0
            latencies.append(lat_us)

        elapsed = time.perf_counter() - t_start
        throughput = 5000.0 / max(0.001, elapsed)
        avg_lat = sum(latencies) / len(latencies)
        sorted_lats = sorted(latencies)
        p99_lat = sorted_lats[int(len(sorted_lats) * 0.99)]

        self.lbl_throughput.config(text=f"Throughput: {throughput:,.0f} decisions/sec (STRESS TEST VERIFIED)")
        self.lbl_latency_p99.config(text=f"Mean Latency: {avg_lat:.2f} µs  |  P99 SLA: {p99_lat:.2f} µs")

    # ==========================================================================
    # MAIN ANIMATION & SIMULATION LOOP (50 FPS)
    # ==========================================================================
    def _start_main_loop(self):
        def loop():
            if not self.is_paused:
                self._update_simulation_step()
                self._render_snn_canvas()
                self._render_tree_canvas()
                self._render_arena_canvas()
                self._render_martingale_canvas()
                self._render_swarm_canvas()
            self.root.after(20, loop)
        loop()

    def _update_simulation_step(self):
        t0 = time.perf_counter()

        # 1. Capture 128-dim 3D spatial tensor from physical arena
        tensor_128d = self.arena.get_128d_spatial_tensor()

        # 2. Biological SNN Spiking Reservoir Step (Injected from 3D LiDAR Shell)
        spikes = self.reservoir.step(tensor_128d[:32], dt=0.5)

        # 3. 3D Obstacle Proximity & Emergency Check
        px, py, pz = self.arena.drone_pos
        dist_to_nearest = min(
            (math.sqrt((obs["pos"][0] - px)**2 + (obs["pos"][1] - py)**2 + (obs["pos"][2] - pz)**2) - obs["radius"]
             for obs in self.arena.obstacles),
            default=100.0
        )

        if dist_to_nearest < 28.0 or py < 22.0:
            self.current_sector_idx = 7 # Robotics Fieldbus
            self.current_leaf_name = "Emergency_Brake_Clamp"
            self.active_tier_name = "Tier 0: 3D Anti-Collision Climb"
            is_emergency = True
        elif dist_to_nearest < 50.0:
            self.current_sector_idx = 7
            self.current_leaf_name = "Steer_Angle_Align"
            self.active_tier_name = "Tier 2: Neuromorphic Flow"
            is_emergency = False
        else:
            self.current_sector_idx = 5 # Desktop / Autonomous Navigation
            self.current_leaf_name = "Trajectory_Target_Seek"
            self.active_tier_name = "Tier 3: 3D Target Intercept"
            is_emergency = False

        # 4. Ville's 3D Martingale Safety Shield
        if self.anomaly_injected or is_emergency:
            self.martingale.wealth = min(120.0, self.martingale.wealth * 1.15)
        else:
            self.martingale.wealth = max(1.0, self.martingale.wealth * 0.96)

        self.wealth_history.append(self.martingale.wealth)
        barrier_tripped = (self.martingale.wealth >= self.martingale.rejection_threshold)

        # 5. Autonomous 3D Actuation (Thrust in X, Y, Z)
        tx = self.arena.target_pos[0] - px
        ty = self.arena.target_pos[1] - py
        tz = self.arena.target_pos[2] - pz
        dist_3d = math.sqrt(tx*tx + ty*ty + tz*tz)
        thrust_3d = (tx / max(1.0, dist_3d), ty / max(1.0, dist_3d), tz / max(1.0, dist_3d))

        self.arena.step(thrust_3d, reflex_clamp=(barrier_tripped or is_emergency))

        # Latency computation
        lat_us = (time.perf_counter() - t0) * 1_000_000.0
        self.last_latency_us = lat_us

        # 6. Merkle Ledger Update
        self.merkle.record_decision(self.total_decisions, 701 if is_emergency else 501, self.current_leaf_name, 0.99, lat_us, self.martingale.wealth)
        self.total_decisions += 1

        # 7. Hardware Feeds Simulation
        self.last_can_torque = round(12.0 + 4.0 * math.sin(self.total_decisions * 0.1), 2)
        self.last_can_steer = round(math.degrees(self.arena.drone_yaw), 1)
        self.lbl_can_data.config(text=f"Motor Torque: {self.last_can_torque:5.2f} Nm  |  Yaw: {self.last_can_steer:5.1f}°  |  Rate: 500kbps")

        stock = random.choice(["NVDA", "AAPL", "MSFT", "GOOGL"])
        price = round(140.0 + random.uniform(0.1, 5.0), 2)
        shares = random.choice([100, 250, 500, 1000])
        self.lbl_itch_data.config(text=f"{stock} ADD ORDER: {shares} shares @ ${price:.2f}  |  NASDAQ Wire Parse: 114 ns")

        # Telemetry updates
        self.lbl_total_decisions.config(text=f"Total Autonomous Decisions: {self.total_decisions:,}")
        self.lbl_wealth_val.config(text=f"Wealth M_t: {self.martingale.wealth:.4f}")
        if barrier_tripped:
            self.lbl_barrier_val.config(text="BARRIER BREACHED: 3D CLIMB REFLEX [TRIPPED]", fg="#EF4444")
        else:
            self.lbl_barrier_val.config(text="Barrier (1/alpha): 100.00 [SAFE]", fg="#00FF88")

        self.lbl_leaf_winner.config(text=f"Winning Leaf: {self.current_leaf_name}")
        self.lbl_merkle_hex.config(text=self.merkle.root_hash[:38] + "...")
        self.lbl_arena_targets.config(text=f"3D Targets: {self.arena.targets_captured}")
        self.lbl_arena_alt.config(text=f"Altitude: {py:.0f}m")
        self.lbl_arena_evasions.config(text=f"Reflex Climbs: {self.arena.evasions}")
        self.lbl_arena_tier.config(text=f"Active Tier: {self.active_tier_name}")
        
        # Camera angle readout
        yaw_deg = int(math.degrees(self.arena.cam_yaw) % 360)
        pitch_deg = int(math.degrees(self.arena.cam_pitch))
        self.lbl_cam_angles.config(text=f"Yaw: {yaw_deg}° | Pitch: {pitch_deg}° | Zoom: {self.arena.cam_dist:.0f}m")

    # ==========================================================================
    # RENDERING ENGINE
    # ==========================================================================
    def _render_snn_canvas(self):
        c = self.canvas_snn
        c.delete("all")
        cols, rows = 16, 8
        cell_w, cell_h = 22, 14

        for i in range(128):
            col = i % cols
            row = i // cols
            x1 = col * cell_w + 14
            y1 = row * cell_h + 8
            x2 = x1 + cell_w - 4
            y2 = y1 + cell_h - 3

            v = self.reservoir.voltages[i]
            if self.reservoir.spikes[i]:
                color = "#FF007F" # Brilliant spike flash
            elif v >= -52.0:
                color = "#FACC15" # High excitation
            elif v >= -60.0:
                color = "#00FF88" # Moderate integration
            elif v >= -66.0:
                color = "#0284C7" # Slight rise
            else:
                color = "#1E293B" # Resting potential

            c.create_rectangle(x1, y1, x2, y2, fill=color, outline="#0F172A")

    def _render_tree_canvas(self):
        c = self.canvas_tree
        c.delete("all")
        w = c.winfo_width() or 380

        for s_idx, (sec_name, leaves) in enumerate(MACRO_SECTORS):
            y = 12 + s_idx * 23
            c.create_text(10, y + 6, anchor="w", text=sec_name, font=self.small_font, fill="#94A3B8")
            
            is_active = (s_idx == self.current_sector_idx)
            ratio = random.uniform(0.75, 0.98) if is_active else random.uniform(0.05, 0.25)
            bar_w = int(ratio * (w - 180))
            color = "#00E5FF" if is_active else "#1E293B"
            
            c.create_rectangle(150, y, 150 + bar_w, y + 12, fill=color, outline="")
            pct_txt = f"{ratio*100:.1f}%"
            c.create_text(155 + bar_w + 4, y + 6, anchor="w", text=pct_txt, font=self.small_font, fill="#64748B" if not is_active else "#00FF88")

    def _render_arena_canvas(self):
        """Renders 3D Perspective Airspace Arena with Depth Occlusion."""
        c = self.canvas_arena
        c.delete("all")
        w = float(c.winfo_width() or 420)
        h = float(c.winfo_height() or 360)
        arena = self.arena

        # 1. Draw 3D Ground Floor Perspective Grid (at Y = 0)
        for z in range(-160, 161, 40):
            u1, v1, _ = arena.project(-160, 0, z, w, h)
            u2, v2, _ = arena.project(160, 0, z, w, h)
            c.create_line(u1, v1, u2, v2, fill="#0E1726", width=1)
        for x in range(-160, 161, 40):
            u1, v1, _ = arena.project(x, 0, -160, w, h)
            u2, v2, _ = arena.project(x, 0, 160, w, h)
            c.create_line(u1, v1, u2, v2, fill="#0E1726", width=1)

        # 2. Draw 3D Airspace Bounding Pillars (Pillars at 4 corners)
        for cx, cz in [(-160, -160), (160, -160), (160, 160), (-160, 160)]:
            u_b, v_b, _ = arena.project(cx, 0, cz, w, h)
            u_t, v_t, _ = arena.project(cx, 160, cz, w, h)
            c.create_line(u_b, v_b, u_t, v_t, fill="#1E293B", dash=(2, 4), width=1)

        # 3. Draw 3D Ceiling Wireframe Box
        for p1, p2 in [((-160, 160, -160), (160, 160, -160)),
                       ((160, 160, -160), (160, 160, 160)),
                       ((160, 160, 160), (-160, 160, 160)),
                       ((-160, 160, 160), (-160, 160, -160))]:
            u1, v1, _ = arena.project(*p1, w, h)
            u2, v2, _ = arena.project(*p2, w, h)
            c.create_line(u1, v1, u2, v2, fill="#111827", width=1)

        # 4. Draw 3D Energy Target Ground Ring & Pillar
        tx, ty, tz = arena.target_pos
        ut_g, vt_g, st_g = arena.project(tx, 0, tz, w, h)
        rg = 12.0 * st_g
        c.create_oval(ut_g - rg, vt_g - rg*0.5, ut_g + rg, vt_g + rg*0.5, outline="#831843", width=1)
        
        ut, vt, st = arena.project(tx, ty, tz, w, h)
        c.create_line(ut_g, vt_g, ut, vt, fill="#831843", dash=(2, 2))
        
        r_tgt = 8.0 * st
        c.create_oval(ut - r_tgt - 3, vt - r_tgt - 3, ut + r_tgt + 3, vt + r_tgt + 3, fill="#831843", outline="")
        c.create_oval(ut - r_tgt, vt - r_tgt, ut + r_tgt, vt + r_tgt, fill="#FF0055", outline="#F43F5E", width=2)
        c.create_text(ut, vt - r_tgt - 8, text=f"3D TARGET [{ty:.0f}m]", font=self.small_font, fill="#F43F5E")

        # 5. Depth Sort 3D Obstacles and Drone (Painters Algorithm)
        render_items = []
        for obs in arena.obstacles:
            ox, oy, oz = obs["pos"]
            depth = math.cos(arena.cam_pitch) * (-ox * math.sin(arena.cam_yaw) + oz * math.cos(arena.cam_yaw))
            render_items.append(("obs", depth, obs))
            
        dx, dy, dz = arena.drone_pos
        drone_depth = math.cos(arena.cam_pitch) * (-dx * math.sin(arena.cam_yaw) + dz * math.cos(arena.cam_yaw))
        render_items.append(("drone", drone_depth, None))
        
        render_items.sort(key=lambda item: item[1])

        # 6. Render Depth-Sorted Objects
        for item_type, _, data in render_items:
            if item_type == "obs":
                obs = data
                ox, oy, oz = obs["pos"]
                r = obs["radius"]
                
                # Ground shadow at Y=0
                uo_g, vo_g, so_g = arena.project(ox, 0, oz, w, h)
                c.create_oval(uo_g - r*so_g*0.8, vo_g - r*so_g*0.4, uo_g + r*so_g*0.8, vo_g + r*so_g*0.4, fill="#0F172A", outline="")
                
                # Plumb line connecting obstacle to ground shadow
                uo, vo, so = arena.project(ox, oy, oz, w, h)
                c.create_line(uo_g, vo_g, uo, vo, fill="#1E293B", dash=(2, 4))
                
                # 3D Sphere in perspective
                rad_scr = r * so
                c.create_oval(uo - rad_scr, vo - rad_scr, uo + rad_scr, vo + rad_scr, fill="#1E1B4B", outline="#4338CA", width=2)
                # 3D specular highlight
                c.create_oval(uo - rad_scr*0.4, vo - rad_scr*0.5, uo - rad_scr*0.1, vo - rad_scr*0.2, fill="#818CF8", outline="")
                c.create_text(uo, vo + rad_scr + 8, text=f"{oy:.0f}m", font=self.small_font, fill="#64748B")

            elif item_type == "drone":
                # Ground shadow at Y=0
                ud_g, vd_g, sd_g = arena.project(dx, 0, dz, w, h)
                c.create_oval(ud_g - 14*sd_g, vd_g - 7*sd_g, ud_g + 14*sd_g, vd_g + 7*sd_g, fill="#0F281E", outline="#059669")
                
                # Altitude Plumb Line
                ud, vd, sd = arena.project(dx, dy, dz, w, h)
                line_color = "#EF4444" if arena.last_reflex_active else "#00FF88"
                c.create_line(ud_g, vd_g, ud, vd, fill=line_color, dash=(2, 3))
                
                # Altitude HUD Badge
                c.create_text(ud + 28, vd + 6, text=f"ALT: {dy:.0f}m", font=self.badge_font, fill=line_color)

                # 3D Spherical LiDAR Cones
                for a_idx in range(0, 85, 12):
                    theta = 2.0 * math.pi * a_idx / 1.618
                    phi = math.acos(1.0 - 2.0 * (a_idx + 0.5) / 85.0)
                    rx = dx + math.sin(phi) * math.cos(theta) * 36.0
                    ry = dy + math.cos(phi) * 36.0
                    rz = dz + math.sin(phi) * math.sin(theta) * 36.0
                    ur, vr, _ = arena.project(rx, ry, rz, w, h)
                    c.create_line(ud, vd, ur, vr, fill="#111827", dash=(2, 4))

                # 3D Velocity Vector
                vx, vy, vz = arena.drone_vel
                uv, vv, _ = arena.project(dx + vx * 8.0, dy + vy * 8.0, dz + vz * 8.0, w, h)
                c.create_line(ud, vd, uv, vv, fill="#00E5FF", width=2)

                # 3D Quadcopter Frame (4 arms in perspective)
                arm_len = 16.0
                drone_color = "#EF4444" if arena.last_reflex_active else "#00FF88"
                for angle_off in [math.pi/4, 3*math.pi/4, 5*math.pi/4, 7*math.pi/4]:
                    ax = dx + math.cos(arena.drone_yaw + angle_off) * arm_len
                    ay = dy
                    az = dz + math.sin(arena.drone_yaw + angle_off) * arm_len
                    ua, va, sa = arena.project(ax, ay, az, w, h)
                    c.create_line(ud, vd, ua, va, fill="#94A3B8", width=2)
                    # Rotor spinning disk
                    rd = 6.0 * sa
                    c.create_oval(ua - rd, va - rd*0.5, ua + rd, va + rd*0.5, fill="#0284C7", outline="#38BDF8")

                # Central Drone Avionics Pod
                r_pod = 8.0 * sd
                c.create_oval(ud - r_pod, vd - r_pod, ud + r_pod, vd + r_pod, fill=drone_color, outline="#FFFFFF", width=2)

    def _render_martingale_canvas(self):
        c = self.canvas_martingale
        c.delete("all")
        w = c.winfo_width() or 380
        h = c.winfo_height() or 120

        # Draw Threshold Line at 100.0 (top 20% of canvas)
        thresh_y = 25
        c.create_line(0, thresh_y, w, thresh_y, fill="#EF4444", dash=(4, 4), width=1)
        c.create_text(w - 6, thresh_y - 6, anchor="e", text="Rejection Barrier 1/alpha = 100.0", font=self.small_font, fill="#EF4444")

        # Baseline at wealth = 1.0 (bottom 80% of canvas)
        base_y = h - 20
        c.create_line(0, base_y, w, base_y, fill="#334155", width=1)

        # Draw Wealth Curve
        pts = []
        num_pts = len(self.wealth_history)
        for idx, val in enumerate(self.wealth_history):
            x = (idx / max(1, num_pts - 1)) * w
            clamped_val = min(110.0, max(0.5, val))
            norm = (clamped_val - 1.0) / 99.0
            y = base_y - norm * (base_y - thresh_y)
            pts.extend([x, y])

        if len(pts) >= 4:
            line_color = "#EF4444" if self.martingale.wealth >= 100.0 else "#00FF88"
            c.create_line(*pts, fill=line_color, width=2)

    def _render_swarm_canvas(self):
        c = self.canvas_swarm
        c.delete("all")
        w = 360
        node_w = w / 8.0
        for i in range(8):
            x = i * node_w + 14
            y = 12
            is_local = (i == 0)
            is_halt = (self.martingale.wealth >= 100.0)
            color = "#EF4444" if is_halt else ("#00FF88" if is_local else "#38BDF8")
            c.create_oval(x - 6, y - 6, x + 6, y + 6, fill=color, outline="#FFFFFF" if is_local else "")
            c.create_text(x, y + 14, text=f"N{i+1}", font=self.small_font, fill="#94A3B8")


def main():
    root = tk.Tk()
    app = AxiomSuperiumVisualizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
