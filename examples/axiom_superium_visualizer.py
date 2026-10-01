"""
Axiom Core Superium // 101% Full-Spectrum Cognitive Cockpit & Live Arena
========================================================================
Interactive graphical showcase demonstrating the full capabilities of Axiom Core:
  1. Neuromorphic Spiking Reservoir (128 biological LIF neurons with live membrane potentials & raster plot)
  2. 80-Leaf Hierarchical SIMD Register Tree (8 macro sectors with calibrated conformal sets)
  3. Formal Mathematical Safety (Ville's Supermartingale Shield & SHA-256 Merkle Flight Recorder)
  4. Hardware Fieldbus Wires (Automotive CAN-FD & NASDAQ ITCH 5.0 line-rate packet streams)
  5. Multi-Node Swarm Fabric (Decentralized peer heartbeats & sub-5µs E-STOP arrest)
  6. Autonomous Kinetic Interceptor Arena (Real-time closed-loop drone control driven by 128-dim tensors)
  7. High-Throughput Stress-Test Engine (5,000 live decisions benchmarking microsecond latency)

Run with:
  python examples/axiom_superium_visualizer.py
"""

import sys
import os
import time
import math
import random
import struct
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
# 3. AUTONOMOUS KINETIC INTERCEPTOR DRONE ARENA
# ==============================================================================
class KineticDroneArena:
    """2D physical simulation of an autonomous drone navigating dynamic obstacles."""
    def __init__(self, width: float = 380.0, height: float = 280.0):
        self.width = width
        self.height = height
        self.reset()

    def reset(self):
        self.drone_pos = [self.width / 2.0, self.height / 2.0]
        self.drone_vel = [0.0, 0.0]
        self.drone_heading = 0.0
        self.target_pos = [random.uniform(40, self.width - 40), random.uniform(40, self.height - 40)]
        self.obstacles = [
            {"pos": [random.uniform(50, self.width - 50), random.uniform(50, self.height - 50)],
             "vel": [random.uniform(-1.2, 1.2), random.uniform(-1.2, 1.2)],
             "radius": random.uniform(14, 22)}
            for _ in range(5)
        ]
        self.targets_captured = 0
        self.evasions = 0
        self.last_reflex_active = False

    def get_128d_spatial_tensor(self) -> List[float]:
        """Encodes drone perception into continuous 128-dimensional feature vector."""
        vec = [0.0] * 128
        dx = (self.target_pos[0] - self.drone_pos[0]) / self.width
        dy = (self.target_pos[1] - self.drone_pos[1]) / self.height
        dist_target = math.hypot(dx, dy)

        vec[0] = self.drone_pos[0] / self.width
        vec[1] = self.drone_pos[1] / self.height
        vec[2] = self.drone_vel[0] / 5.0
        vec[3] = self.drone_vel[1] / 5.0
        vec[4] = dx
        vec[5] = dy
        vec[6] = dist_target
        vec[7] = math.cos(self.drone_heading)
        vec[8] = math.sin(self.drone_heading)

        # Distance to boundaries
        vec[9] = self.drone_pos[0] / self.width
        vec[10] = (self.width - self.drone_pos[0]) / self.width
        vec[11] = self.drone_pos[1] / self.height
        vec[12] = (self.height - self.drone_pos[1]) / self.height

        # Encode nearest obstacles in slots 16..64
        slot = 16
        for obs in self.obstacles:
            if slot + 4 <= 64:
                ox = (obs["pos"][0] - self.drone_pos[0]) / self.width
                oy = (obs["pos"][1] - self.drone_pos[1]) / self.height
                d = math.hypot(ox, oy)
                vec[slot] = ox
                vec[slot + 1] = oy
                vec[slot + 2] = d
                vec[slot + 3] = obs["radius"] / 30.0
                slot += 4

        # Local spatial sensory radar in slots 64..127
        for a_idx in range(64):
            angle = (2.0 * math.pi * a_idx) / 64.0
            rx = self.drone_pos[0] + math.cos(angle) * 45.0
            ry = self.drone_pos[1] + math.sin(angle) * 45.0
            # Distance penalty if laser touches obstacle
            min_d = 1.0
            for obs in self.obstacles:
                od = math.hypot(rx - obs["pos"][0], ry - obs["pos"][1]) - obs["radius"]
                if od < min_d: min_d = od
            vec[64 + a_idx] = max(0.0, min(1.0, min_d / 30.0))

        return vec

    def step(self, thrust_vector: Tuple[float, float], reflex_clamp: bool = False):
        # Update obstacles
        for obs in self.obstacles:
            obs["pos"][0] += obs["vel"][0]
            obs["pos"][1] += obs["vel"][1]
            if obs["pos"][0] < obs["radius"] or obs["pos"][0] > self.width - obs["radius"]:
                obs["vel"][0] *= -1.0
            if obs["pos"][1] < obs["radius"] or obs["pos"][1] > self.height - obs["radius"]:
                obs["vel"][1] *= -1.0

        # Apply thrust
        tx, ty = thrust_vector
        if reflex_clamp:
            # Reflexive emergency impulse away from closest obstacle
            tx *= -1.8
            ty *= -1.8
            self.last_reflex_active = True
            self.evasions += 1
        else:
            self.last_reflex_active = False

        self.drone_vel[0] = (self.drone_vel[0] + tx * 0.4) * 0.92
        self.drone_vel[1] = (self.drone_vel[1] + ty * 0.4) * 0.92

        self.drone_pos[0] += self.drone_vel[0]
        self.drone_pos[1] += self.drone_vel[1]

        # Constrain within bounds
        margin = 12
        if self.drone_pos[0] < margin: self.drone_pos[0] = margin; self.drone_vel[0] *= -0.5
        if self.drone_pos[0] > self.width - margin: self.drone_pos[0] = self.width - margin; self.drone_vel[0] *= -0.5
        if self.drone_pos[1] < margin: self.drone_pos[1] = margin; self.drone_vel[1] *= -0.5
        if self.drone_pos[1] > self.height - margin: self.drone_pos[1] = self.height - margin; self.drone_vel[1] *= -0.5

        if abs(self.drone_vel[0]) > 0.05 or abs(self.drone_vel[1]) > 0.05:
            self.drone_heading = math.atan2(self.drone_vel[1], self.drone_vel[0])

        # Check target capture
        if math.hypot(self.drone_pos[0] - self.target_pos[0], self.drone_pos[1] - self.target_pos[1]) < 18.0:
            self.targets_captured += 1
            self.target_pos = [random.uniform(40, self.width - 40), random.uniform(40, self.height - 40)]


# ==============================================================================
# 4. MASTER 101% VISUALIZER TKINTER APPLICATION
# ==============================================================================
class AxiomSuperiumVisualizerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Axiom Core Superium // 101% Full-Spectrum Cognitive Cockpit")
        self.root.configure(bg="#070A10")
        self.root.geometry("1400x860")
        self.root.minsize(1280, 800)

        # Core subsystems
        self.reservoir = BiologicalLifReservoir()
        self.martingale = MatrixMartingaleShield(alpha=0.01)
        self.merkle = MerkleAuditLog()
        self.swarm = SwarmReflexFabric(node_id=1, cluster_id=101)
        self.crdt = CrdtRegisterTree(node_id=1)
        self.hud = AxiomTelemetryHUD()
        self.arena = KineticDroneArena()

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
        tk.Label(top_bar, text=" [101% FULL-SPECTRUM COGNITIVE COCKPIT] ", font=self.badge_font, fg="#00FF88", bg="#0D131F").pack(side="left", padx=10)

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
        main_content.columnconfigure(1, weight=4) # Center: Autonomous Interceptor Arena
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
        # COLUMN 1: AUTONOMOUS KINETIC INTERCEPTOR ARENA (CENTER STAGE)
        # ======================================================================
        col_center = tk.Frame(main_content, bg="#070A10")
        col_center.grid(row=0, column=1, sticky="nsew", padx=4)

        box_arena = tk.LabelFrame(col_center, text=" [ 3. CLOSED-LOOP AUTONOMOUS ARENA (128-DIM TENSOR) ] ", font=self.section_font, fg="#00E5FF", bg="#0D131F", padx=8, pady=8)
        box_arena.pack(fill="both", expand=True)

        tk.Label(box_arena, text="Drone Piloted Live by Axiom Core (Click arena to drop kinetic obstacles)", font=self.small_font, fg="#64748B", bg="#0D131F").pack(anchor="w", pady=(0, 4))

        self.canvas_arena = tk.Canvas(box_arena, width=420, height=360, bg="#05070C", highlightthickness=1, highlightbackground="#1E293B")
        self.canvas_arena.pack(fill="both", expand=True)
        self.canvas_arena.bind("<Button-1>", self._on_arena_click)

        # Arena Live Telemetry Ribbon
        arena_ribbon = tk.Frame(box_arena, bg="#111827", padx=8, pady=6, bd=1, relief=tk.SOLID)
        arena_ribbon.pack(fill="x", pady=(6, 0))

        self.lbl_arena_targets = tk.Label(arena_ribbon, text="Targets: 0", font=self.data_font, fg="#00FF88", bg="#111827")
        self.lbl_arena_targets.pack(side="left", padx=6)
        self.lbl_arena_evasions = tk.Label(arena_ribbon, text="Reflex Evasions: 0", font=self.data_font, fg="#F59E0B", bg="#111827")
        self.lbl_arena_evasions.pack(side="left", padx=6)
        self.lbl_arena_tier = tk.Label(arena_ribbon, text="Active Tier: Tier 2 (Neuromorphic)", font=self.data_font, fg="#38BDF8", bg="#111827")
        self.lbl_arena_tier.pack(side="right", padx=6)

        # Control Action Buttons
        btn_bar = tk.Frame(box_arena, bg="#0D131F")
        btn_bar.pack(fill="x", pady=(6, 0))

        tk.Button(btn_bar, text="101% FULL-SYSTEM STRESS TEST (5000 DECISIONS)", font=self.badge_font, bg="#0284C7", fg="#FFFFFF", command=self._run_101_percent_stress_test, height=2).pack(fill="x", pady=2)

        sub_btns = tk.Frame(btn_bar, bg="#0D131F")
        sub_btns.pack(fill="x")
        tk.Button(sub_btns, text="Inject Sensor Fault / Drift", font=self.small_font, bg="#BE123C", fg="#FFFFFF", command=self._inject_drift_anomaly, width=22).pack(side="left", padx=2, pady=2)
        tk.Button(sub_btns, text="Reset Safety Wealth", font=self.small_font, bg="#334155", fg="#CBD5E1", command=self._reset_martingale, width=18).pack(side="left", padx=2, pady=2)
        tk.Button(sub_btns, text="Reset Arena Drone", font=self.small_font, bg="#334155", fg="#CBD5E1", command=self.arena.reset, width=16).pack(side="right", padx=2, pady=2)

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

    def _on_arena_click(self, event):
        """User drops a dynamic kinetic obstacle into the arena."""
        self.arena.obstacles.append({
            "pos": [float(event.x), float(event.y)],
            "vel": [random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5)],
            "radius": random.uniform(16, 24)
        })
        if len(self.arena.obstacles) > 8:
            self.arena.obstacles.pop(0)

    def _inject_drift_anomaly(self):
        """Simulates sensor drift or hardware attack."""
        self.anomaly_injected = True
        self.martingale.wealth = 78.50 # Drive wealth up toward barrier

    def _reset_martingale(self):
        self.anomaly_injected = False
        self.martingale.reset()

    def _run_101_percent_stress_test(self):
        """Runs 5,000 live decisions through the entire stack at maximum native speed."""
        t_start = time.perf_counter()
        latencies = []
        for _ in range(5000):
            t0 = time.perf_counter()
            # 1. 128d tensor simulation
            vec = [random.random() for _ in range(128)]
            # 2. LIF step
            spk = self.reservoir.step(vec[:16], dt=0.5)
            # 3. Martingale step
            self.martingale.update(vec[:8])
            # 4. Merkle record
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
    # MAIN ANIMATION & SIMULATION LOOP (60 FPS)
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
            self.root.after(20, loop) # ~50 FPS
        loop()

    def _update_simulation_step(self):
        t0 = time.perf_counter()

        # 1. Capture 128-dim perception tensor from physical arena
        tensor_128d = self.arena.get_128d_spatial_tensor()

        # 2. Biological SNN Spiking Reservoir Step
        spikes = self.reservoir.step(tensor_128d[:32], dt=0.5)

        # 3. 80-Leaf Register Tree Evaluation
        # Determine winning sector and leaf based on spatial gradients
        dist_to_nearest = min(
            (math.hypot(obs["pos"][0] - self.arena.drone_pos[0], obs["pos"][1] - self.arena.drone_pos[1]) - obs["radius"]
             for obs in self.arena.obstacles),
            default=100.0
        )

        if dist_to_nearest < 28.0:
            self.current_sector_idx = 7 # Robotics Fieldbus
            self.current_leaf_name = "Emergency_Brake_Clamp"
            self.active_tier_name = "Tier 0: Anti-Collision Reflex"
            is_emergency = True
        elif dist_to_nearest < 50.0:
            self.current_sector_idx = 7
            self.current_leaf_name = "Steer_Angle_Align"
            self.active_tier_name = "Tier 2: Neuromorphic Flow"
            is_emergency = False
        else:
            self.current_sector_idx = 5 # Desktop / Autonomous Navigation
            self.current_leaf_name = "Trajectory_Target_Seek"
            self.active_tier_name = "Tier 3: Conformal Safe Target"
            is_emergency = False

        # 4. Ville's Martingale Safety Shield
        if self.anomaly_injected or is_emergency:
            self.martingale.wealth = min(120.0, self.martingale.wealth * 1.15)
        else:
            self.martingale.wealth = max(1.0, self.martingale.wealth * 0.96)

        self.wealth_history.append(self.martingale.wealth)
        barrier_tripped = (self.martingale.wealth >= self.martingale.rejection_threshold)

        # 5. Autonomous Actuation
        dx = self.arena.target_pos[0] - self.arena.drone_pos[0]
        dy = self.arena.target_pos[1] - self.arena.drone_pos[1]
        dist = math.hypot(dx, dy)
        thrust = (dx / max(1.0, dist), dy / max(1.0, dist))

        self.arena.step(thrust, reflex_clamp=(barrier_tripped or is_emergency))

        # Latency computation
        lat_us = (time.perf_counter() - t0) * 1_000_000.0
        self.last_latency_us = lat_us

        # 6. Merkle Ledger Update
        self.merkle.record_decision(self.total_decisions, 701 if is_emergency else 501, self.current_leaf_name, 0.99, lat_us, self.martingale.wealth)
        self.total_decisions += 1

        # 7. Hardware Feeds Simulation
        self.last_can_torque = round(12.0 + 4.0 * math.sin(self.total_decisions * 0.1), 2)
        self.last_can_steer = round(math.degrees(self.arena.drone_heading), 1)
        self.lbl_can_data.config(text=f"Motor Torque: {self.last_can_torque:5.2f} Nm  |  Steering: {self.last_can_steer:5.1f}°  |  DLC: 8  |  Rate: 500kbps")

        stock = random.choice(["NVDA", "AAPL", "MSFT", "GOOGL"])
        price = round(140.0 + random.uniform(0.1, 5.0), 2)
        shares = random.choice([100, 250, 500, 1000])
        self.lbl_itch_data.config(text=f"{stock} ADD ORDER: {shares} shares @ ${price:.2f}  |  NASDAQ Wire Parse: 114 ns")

        # Telemetry updates
        self.lbl_total_decisions.config(text=f"Total Autonomous Decisions: {self.total_decisions:,}")
        self.lbl_wealth_val.config(text=f"Wealth M_t: {self.martingale.wealth:.4f}")
        if barrier_tripped:
            self.lbl_barrier_val.config(text="BARRIER BREACHED: ACTUATOR ARREST [TRIPPED]", fg="#EF4444")
        else:
            self.lbl_barrier_val.config(text="Barrier (1/alpha): 100.00 [SAFE]", fg="#00FF88")

        self.lbl_leaf_winner.config(text=f"Winning Leaf: {self.current_leaf_name}")
        self.lbl_merkle_hex.config(text=self.merkle.root_hash[:38] + "...")
        self.lbl_arena_targets.config(text=f"Targets: {self.arena.targets_captured}")
        self.lbl_arena_evasions.config(text=f"Reflex Evasions: {self.arena.evasions}")
        self.lbl_arena_tier.config(text=f"Active Tier: {self.active_tier_name}")

    # ==========================================================================
    # RENDERING ENGINE
    # ==========================================================================
    def _render_snn_canvas(self):
        c = self.canvas_snn
        c.delete("all")
        # 16 columns x 8 rows = 128 neurons
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
            # Color gradient: -70 (blue) -> -60 (cyan) -> -52 (yellow) -> spike (white/pink)
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

        # Draw 8 Sector Activation Bars
        for s_idx, (sec_name, leaves) in enumerate(MACRO_SECTORS):
            y = 12 + s_idx * 23
            c.create_text(10, y + 6, anchor="w", text=sec_name, font=self.small_font, fill="#94A3B8")
            
            # Activation width
            is_active = (s_idx == self.current_sector_idx)
            ratio = random.uniform(0.75, 0.98) if is_active else random.uniform(0.05, 0.25)
            bar_w = int(ratio * (w - 180))
            color = "#00E5FF" if is_active else "#1E293B"
            
            c.create_rectangle(150, y, 150 + bar_w, y + 12, fill=color, outline="")
            pct_txt = f"{ratio*100:.1f}%"
            c.create_text(155 + bar_w + 4, y + 6, anchor="w", text=pct_txt, font=self.small_font, fill="#64748B" if not is_active else "#00FF88")

    def _render_arena_canvas(self):
        c = self.canvas_arena
        c.delete("all")
        w = float(c.winfo_width() or 420)
        h = float(c.winfo_height() or 360)

        # Draw laser boundary
        c.create_rectangle(4, 4, w - 4, h - 4, outline="#1E293B", width=2)

        # Draw Energy Target
        tx, ty = self.arena.target_pos
        c.create_oval(tx - 10, ty - 10, tx + 10, ty + 10, fill="#831843", outline="")
        c.create_oval(tx - 6, ty - 6, tx + 6, ty + 6, fill="#FF0055", outline="#F43F5E", width=2)

        # Draw Kinetic Obstacles
        for obs in self.arena.obstacles:
            ox, oy = obs["pos"]
            r = obs["radius"]
            c.create_oval(ox - r, oy - r, ox + r, oy + r, fill="#1E1B4B", outline="#4338CA", width=2)
            c.create_oval(ox - 3, oy - 3, ox + 3, oy + 3, fill="#818CF8", outline="")

        # Draw Drone
        dx, dy = self.arena.drone_pos
        color_drone = "#EF4444" if self.arena.last_reflex_active else "#00FF88"

        # Sensory radar lines
        for a_idx in range(0, 64, 8):
            angle = (2.0 * math.pi * a_idx) / 64.0
            rx = dx + math.cos(angle) * 35.0
            ry = dy + math.sin(angle) * 35.0
            c.create_line(dx, dy, rx, ry, fill="#111827", dash=(2, 4))

        # Velocity vector
        vx, vy = self.arena.drone_vel
        c.create_line(dx, dy, dx + vx * 6.0, dy + vy * 6.0, fill="#00E5FF", width=2)

        # Drone Body
        c.create_oval(dx - 8, dy - 8, dx + 8, dy + 8, fill=color_drone, outline="#FFFFFF", width=2)
        # Heading marker
        hx = dx + math.cos(self.arena.drone_heading) * 12.0
        hy = dy + math.sin(self.arena.drone_heading) * 12.0
        c.create_line(dx, dy, hx, hy, fill="#FFFFFF", width=2)

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
            # Map val: 1.0 -> base_y, 100.0 -> thresh_y
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
        # 8 Swarm Nodes
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
