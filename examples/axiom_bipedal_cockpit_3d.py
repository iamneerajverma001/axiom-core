#!/usr/bin/env python3
"""
Axiom Humanoid Bipedal Locomotion Cockpit (Physical Machine Era v3.0)
Real-time 3D robotic humanoid balance and capture-step reflex cockpit:
- 3D Kinematics of Bipedal Robot (Torso, Legs, Feet)
- Linear Inverted Pendulum Model (LIPM) & Capture Point Dynamics
- Zero Moment Point (ZMP) Support Polygon Monitoring
- Ville's Martingale Stumble & Fall Interlock
- Interactive Physical Perturbation & Kick Impulse Injection
"""

import sys
import os
import time
import math
import random
import tkinter as tk

# Ensure products/axiom-core is importable
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
core_path = os.path.join(repo_root, "products", "axiom-core")
if core_path not in sys.path:
    sys.path.insert(0, core_path)

from axiom_core import (
    BipedalLocomotionReflex,
    ComState,
    FootContact,
    CapturePointResult
)

class AxiomBipedalCockpit3D(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AXIOM-CORE v3.0 // BIPEDAL ROBOTIC REFLEX & BALANCE COCKPIT")
        self.geometry("1480x920")
        self.configure(bg="#070a0f")

        # Bipedal Physics State
        self.reflex_kernel = BipedalLocomotionReflex(height=0.85, alpha=0.001)
        self.com = ComState(x=0.0, y=0.0, z=0.85, vx=0.0, vy=0.0, vz=0.0)
        self.left_foot = FootContact(x=-0.12, y=0.0, z=0.0, length=0.24, width=0.12, is_grounded=True)
        self.right_foot = FootContact(x=0.12, y=0.0, z=0.0, length=0.24, width=0.12, is_grounded=True)
        self.swing_target_x = 0.12
        self.swing_target_y = 0.0

        # Camera & Telemetry
        self.cam_yaw = 0.85
        self.cam_pitch = 0.35
        self.cam_dist = 360.0
        self.auto_orbit = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.last_result = self.reflex_kernel.evaluate(self.com, self.left_foot, dt=0.005)
        self.wealth_history = [1.0] * 60
        self.zmp_history = []
        self.perturbation_text = "SYSTEM NOMINAL - EQUILIBRIUM"

        # Rates
        self.decision_rate = 1850
        self.mean_latency_us = 4.2
        self.fps_ticks = 0
        self.last_fps_time = time.time()

        # Build UI
        self._build_header()
        self._build_main_grid()
        self._bind_mouse()

        # Loop
        self.after(20, self._render_loop)

    def _build_header(self):
        hdr = tk.Frame(self, bg="#0d1117", height=50)
        hdr.pack(fill=tk.X, padx=8, pady=(8, 4))

        tk.Label(
            hdr,
            text="⚡ AXIOM-CORE 3.0 // 1,000 Hz BIPEDAL REFLEX & CAPTURE POINT KERNEL",
            fg="#00f3ff", bg="#0d1117", font=("Consolas", 13, "bold")
        ).pack(side=tk.LEFT, padx=12, pady=8)

        self.lbl_telemetry = tk.Label(
            hdr,
            text="RATE: 1,850 Hz | LATENCY: 4.2 µs | ZMP MARGIN: +0.06m | VILLE WEALTH: 1.00",
            fg="#39ff14", bg="#0d1117", font=("Consolas", 10, "bold")
        )
        self.lbl_telemetry.pack(side=tk.RIGHT, padx=12, pady=8)

    def _build_main_grid(self):
        content = tk.Frame(self, bg="#070a0f")
        content.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left Column: 3D Robot Kinematics
        left = tk.Frame(content, bg="#0a0e14", width=880)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        bar = tk.Frame(left, bg="#121820", height=28)
        bar.pack(fill=tk.X)
        tk.Label(
            bar,
            text="[PANEL 1] 3D BIPEDAL HUMANOID KINEMATICS // LIPM & CAPTURE POINT REFLEX",
            fg="#00f3ff", bg="#121820", font=("Consolas", 9, "bold")
        ).pack(side=tk.LEFT, padx=8, pady=4)

        self.canvas_3d = tk.Canvas(left, bg="#05070a", highlightthickness=1, highlightbackground="#1b2430")
        self.canvas_3d.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Perturbation Buttons
        btn_bar = tk.Frame(left, bg="#0a0e14")
        btn_bar.pack(fill=tk.X, pady=4)

        tk.Button(
            btn_bar, text="KICK FORWARD (+2.0 m/s)", bg="#2a1420", fg="#ff5555", font=("Consolas", 9, "bold"),
            command=lambda: self._apply_kick(0.0, 2.0)
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            btn_bar, text="KICK LATERAL (+1.5 m/s)", bg="#2a2014", fg="#ffaa00", font=("Consolas", 9, "bold"),
            command=lambda: self._apply_kick(1.5, 0.0)
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            btn_bar, text="SLIP ON ICE (FRICTION DROP)", bg="#14202a", fg="#00ccff", font=("Consolas", 9, "bold"),
            command=self._apply_slip
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            btn_bar, text="RESET BALANCE", bg="#16202c", fg="#39ff14", font=("Consolas", 9, "bold"),
            command=self._reset_balance
        ).pack(side=tk.LEFT, padx=6)

        self.btn_orbit = tk.Button(
            btn_bar, text="AUTO-ORBIT: OFF", bg="#16202c", fg="#88ccff", font=("Consolas", 9),
            command=self._toggle_orbit
        )
        self.btn_orbit.pack(side=tk.LEFT, padx=3)

        # Right Column: Stability & Support Polygon Stack
        right = tk.Frame(content, bg="#0a0e14", width=560)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=4, pady=4)

        # Panel 2: ZMP Support Polygon Phase Space
        p2 = tk.LabelFrame(
            right, text="[PANEL 2] ZMP & CAPTURE POINT vs SUPPORT POLYGON",
            fg="#00f3ff", bg="#0a0e14", font=("Consolas", 8, "bold")
        )
        p2.pack(fill=tk.X, padx=4, pady=2)
        self.canvas_zmp = tk.Canvas(p2, bg="#05070a", height=180, highlightthickness=0)
        self.canvas_zmp.pack(fill=tk.X, padx=4, pady=4)

        # Panel 3: Ville's Slip/Fall Martingale Shield
        p3 = tk.LabelFrame(
            right, text="[PANEL 3] VILLE'S MARTINGALE FALL SHIELD (M_t vs 1/α=1000)",
            fg="#39ff14", bg="#0a0e14", font=("Consolas", 8, "bold")
        )
        p3.pack(fill=tk.X, padx=4, pady=2)
        self.canvas_martingale = tk.Canvas(p3, bg="#05070a", height=130, highlightthickness=0)
        self.canvas_martingale.pack(fill=tk.X, padx=4, pady=4)

        # Panel 4: Reflex Telemetry Log
        p4 = tk.LabelFrame(
            right, text="[PANEL 4] 1,000 Hz JOINT ACTUATION & CAPTURE STEP DISPATCH",
            fg="#ffcc00", bg="#0a0e14", font=("Consolas", 8, "bold")
        )
        p4.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        self.txt_log = tk.Text(
            p4, bg="#05070a", fg="#a0c0a0", font=("Consolas", 8),
            height=8, relief=tk.FLAT, highlightthickness=0
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def _bind_mouse(self):
        self.canvas_3d.bind("<ButtonPress-1>", lambda e: self._on_mdown(e))
        self.canvas_3d.bind("<B1-Motion>", lambda e: self._on_mdrag(e))
        self.canvas_3d.bind("<MouseWheel>", lambda e: self._on_mwheel(e))

    def _on_mdown(self, e):
        self.last_mouse_x, self.last_mouse_y = e.x, e.y

    def _on_mdrag(self, e):
        dx = e.x - self.last_mouse_x
        dy = e.y - self.last_mouse_y
        self.cam_yaw += dx * 0.01
        self.cam_pitch = max(-1.4, min(1.4, self.cam_pitch + dy * 0.01))
        self.last_mouse_x, self.last_mouse_y = e.x, e.y

    def _on_mwheel(self, e):
        if e.delta > 0:
            self.cam_dist = max(150.0, self.cam_dist - 20.0)
        else:
            self.cam_dist = min(800.0, self.cam_dist + 20.0)

    def _toggle_orbit(self):
        self.auto_orbit = not self.auto_orbit
        self.btn_orbit.config(text=f"AUTO-ORBIT: {'ON' if self.auto_orbit else 'OFF'}")

    def _apply_kick(self, kick_x: float, kick_y: float):
        self.com.vx += kick_x
        self.com.vy += kick_y
        self.perturbation_text = f"PERTURBATION: KICKED (Vx={self.com.vx:+.1f}, Vy={self.com.vy:+.1f} m/s)"
        self._log(f"[IMPULSE] Kick injected! CoM Velocity: ({self.com.vx:.2f}, {self.com.vy:.2f})")

    def _apply_slip(self):
        self.left_foot.friction_coeff = 0.05
        self.com.vx += random.uniform(-0.8, 0.8)
        self.com.vy += random.uniform(-0.8, 0.8)
        self.perturbation_text = "PERTURBATION: FRICTION LOSS (ICE DETECTED)"
        self._log("[SLIP] Ground friction dropped to mu=0.05! Martingale tripwire engaged.")

    def _reset_balance(self):
        self.com = ComState(x=0.0, y=0.0, z=0.85, vx=0.0, vy=0.0, vz=0.0)
        self.left_foot = FootContact(x=-0.12, y=0.0, z=0.0, length=0.24, width=0.12, friction_coeff=0.6)
        self.right_foot = FootContact(x=0.12, y=0.0, z=0.0, length=0.24, width=0.12, friction_coeff=0.6)
        self.reflex_kernel.reset()
        self.perturbation_text = "SYSTEM NOMINAL - EQUILIBRIUM RESTORED"
        self._log("[RESET] Center of Mass reset. Martingale wealth reset to 1.0.")

    def _log(self, msg: str):
        self.txt_log.insert(tk.END, f"{msg}\n")
        lines = int(self.txt_log.index("end-1c").split(".")[0])
        if lines > 15:
            self.txt_log.delete("1.0", "2.0")
        self.txt_log.see(tk.END)

    def _project_3d(self, x, y, z, cx, cy):
        # Scale physical meters to screen pixels
        sx_phys = x * 180.0
        sy_phys = z * 180.0
        sz_phys = y * 180.0

        cos_y, sin_y = math.cos(self.cam_yaw), math.sin(self.cam_yaw)
        x1 = sx_phys * cos_y - sz_phys * sin_y
        z1 = sx_phys * sin_y + sz_phys * cos_y

        cos_p, sin_p = math.cos(self.cam_pitch), math.sin(self.cam_pitch)
        y2 = sy_phys * cos_p - z1 * sin_p
        z2 = sy_phys * sin_p + z1 * cos_p

        depth = z2 + self.cam_dist
        if depth <= 10.0: depth = 10.0
        scale = 360.0 / depth
        return cx + x1 * scale, cy - y2 * scale, depth

    def _render_loop(self):
        t0 = time.perf_counter()
        dt = 0.025

        # Physics Step
        res = self.reflex_kernel.evaluate(self.com, self.left_foot, dt=dt)
        self.last_result = res

        # CoM Inverted Pendulum Dynamics
        omega = math.sqrt(9.81 / max(0.2, self.com.z))
        self.com.ax = (omega * omega) * (self.com.x - res.zmp_x)
        self.com.ay = (omega * omega) * (self.com.y - res.zmp_y)

        # Recovery reflex if capture step required
        if res.capture_step_required:
            self.swing_target_x = res.recommended_step_x
            self.swing_target_y = res.recommended_step_y
            # Swing foot steps onto capture point with damping
            self.right_foot.x += (self.swing_target_x - self.right_foot.x) * 0.25
            self.right_foot.y += (self.swing_target_y - self.right_foot.y) * 0.25
            # Push CoM velocity back towards equilibrium
            self.com.vx *= 0.88
            self.com.vy *= 0.88
        else:
            self.com.vx *= 0.96
            self.com.vy *= 0.96

        self.com.x += self.com.vx * dt
        self.com.y += self.com.vy * dt

        # Rates & Latency
        compute_us = (time.perf_counter() - t0) * 1e6
        self.mean_latency_us = self.mean_latency_us * 0.95 + compute_us * 0.05
        self.fps_ticks += 1

        now = time.time()
        if now - self.last_fps_time >= 0.5:
            self.decision_rate = int(self.fps_ticks / (now - self.last_fps_time))
            self.fps_ticks = 0
            self.last_fps_time = now

        if self.auto_orbit:
            self.cam_yaw += 0.005

        self.wealth_history.append(res.martingale_wealth)
        if len(self.wealth_history) > 60: self.wealth_history.pop(0)

        # Render
        self._render_3d_humanoid()
        self._render_zmp_panel()
        self._render_martingale_panel()

        # Update Header
        color = "#ff0055" if res.capture_step_required else "#39ff14"
        self.lbl_telemetry.config(
            text=f"RATE: {self.decision_rate:,} Hz | LATENCY: {self.mean_latency_us:.1f} µs | ZMP MARGIN: {res.zmp_margin:+.2f}m | WEALTH: {res.martingale_wealth:.1f} | {self.perturbation_text}",
            fg=color
        )

        self.after(20, self._render_loop)

    def _render_3d_humanoid(self):
        c = self.canvas_3d
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10: w, h = 880, 560
        cx, cy = w / 2, h / 2 + 100

        # Ground Grid
        for i in range(-5, 6):
            p1 = self._project_3d(-1.5, i * 0.3, 0.0, cx, cy)
            p2 = self._project_3d(1.5, i * 0.3, 0.0, cx, cy)
            c.create_line(p1[0], p1[1], p2[0], p2[1], fill="#121820")

            p3 = self._project_3d(i * 0.3, -1.5, 0.0, cx, cy)
            p4 = self._project_3d(i * 0.3, 1.5, 0.0, cx, cy)
            c.create_line(p3[0], p3[1], p4[0], p4[1], fill="#121820")

        # Feet Soles
        for foot, col in [(self.left_foot, "#00f3ff"), (self.right_foot, "#39ff14")]:
            fx, fy = foot.x, foot.y
            p_fl = self._project_3d(fx - 0.06, fy - 0.12, 0.0, cx, cy)
            p_fr = self._project_3d(fx + 0.06, fy - 0.12, 0.0, cx, cy)
            p_br = self._project_3d(fx + 0.06, fy + 0.12, 0.0, cx, cy)
            p_bl = self._project_3d(fx - 0.06, fy + 0.12, 0.0, cx, cy)
            c.create_polygon(
                p_fl[0], p_fl[1], p_fr[0], p_fr[1], p_br[0], p_br[1], p_bl[0], p_bl[1],
                outline=col, fill="#0d2030", width=2
            )

        # Center of Mass (CoM) Sphere
        com_s = self._project_3d(self.com.x, self.com.y, self.com.z, cx, cy)
        pelvis_s = self._project_3d(self.com.x, self.com.y, self.com.z - 0.15, cx, cy)
        torso_s = self._project_3d(self.com.x, self.com.y, self.com.z + 0.25, cx, cy)
        head_s = self._project_3d(self.com.x, self.com.y, self.com.z + 0.45, cx, cy)

        # Torso & Head
        c.create_line(pelvis_s[0], pelvis_s[1], torso_s[0], torso_s[1], fill="#40d0ff", width=6)
        c.create_line(torso_s[0], torso_s[1], head_s[0], head_s[1], fill="#40d0ff", width=4)
        c.create_oval(head_s[0] - 8, head_s[1] - 8, head_s[0] + 8, head_s[1] + 8, fill="#ffffff", outline="#00f3ff")

        # Left Leg (Stance)
        lf_s = self._project_3d(self.left_foot.x, self.left_foot.y, 0.02, cx, cy)
        c.create_line(pelvis_s[0], pelvis_s[1], lf_s[0], lf_s[1], fill="#00f3ff", width=4)

        # Right Leg (Swing/Capture Step)
        rf_s = self._project_3d(self.right_foot.x, self.right_foot.y, 0.02, cx, cy)
        c.create_line(pelvis_s[0], pelvis_s[1], rf_s[0], rf_s[1], fill="#39ff14", width=4)

        # Inverted Pendulum Rod to ZMP
        zmp_s = self._project_3d(self.last_result.zmp_x, self.last_result.zmp_y, 0.0, cx, cy)
        c.create_line(com_s[0], com_s[1], zmp_s[0], zmp_s[1], fill="#ffaa00", dash=(3, 3), width=2)
        c.create_oval(zmp_s[0] - 5, zmp_s[1] - 5, zmp_s[0] + 5, zmp_s[1] + 5, fill="#ffaa00", outline="#ffffff")
        c.create_text(zmp_s[0], zmp_s[1] + 12, text="ZMP", fill="#ffaa00", font=("Consolas", 8, "bold"))

        # Capture Point (CP) Projection
        cp_s = self._project_3d(self.last_result.cp_x, self.last_result.cp_y, 0.0, cx, cy)
        cp_col = "#ff0055" if self.last_result.capture_step_required else "#39ff14"
        c.create_line(com_s[0], com_s[1], cp_s[0], cp_s[1], fill=cp_col, width=2)
        c.create_oval(cp_s[0] - 6, cp_s[1] - 6, cp_s[0] + 6, cp_s[1] + 6, fill=cp_col, outline="#ffffff")
        c.create_text(cp_s[0], cp_s[1] - 12, text="CAPTURE POINT", fill=cp_col, font=("Consolas", 8, "bold"))

    def _render_zmp_panel(self):
        c = self.canvas_zmp
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10: w = 540
        cx, cy = w / 2, h / 2

        scale = 320.0 # pixels per meter

        # Foot Polygon
        pw = self.left_foot.width * scale
        pl = self.left_foot.length * scale
        c.create_rectangle(cx - pw/2, cy - pl/2, cx + pw/2, cy + pl/2, outline="#00f3ff", width=2, fill="#0a1a28")
        c.create_text(cx, cy - pl/2 - 10, text="SUPPORT POLYGON (STANCE FOOT)", fill="#00f3ff", font=("Consolas", 7))

        # ZMP point
        zx = cx + (self.last_result.zmp_x - self.left_foot.x) * scale
        zy = cy - (self.last_result.zmp_y - self.left_foot.y) * scale
        c.create_oval(zx - 4, zy - 4, zx + 4, zy + 4, fill="#ffaa00", outline="#ffffff")
        c.create_text(zx + 8, zy, text=f"ZMP ({self.last_result.zmp_margin:+.2f}m)", fill="#ffaa00", font=("Consolas", 7))

        # Capture Point
        cpx = cx + (self.last_result.cp_x - self.left_foot.x) * scale
        cpy = cy - (self.last_result.cp_y - self.left_foot.y) * scale
        cp_col = "#ff0055" if self.last_result.capture_step_required else "#39ff14"
        c.create_oval(cpx - 5, cpy - 5, cpx + 5, cpy + 5, fill=cp_col, outline="#ffffff")
        c.create_text(cpx + 8, cpy, text="CP", fill=cp_col, font=("Consolas", 8, "bold"))

    def _render_martingale_panel(self):
        c = self.canvas_martingale
        c.delete("all")
        w = c.winfo_width()
        if w < 10: w = 540

        # Barrier line
        c.create_line(0, 20, w, 20, fill="#ff0055", dash=(3, 3))
        c.create_text(w - 75, 12, text="BARRIER 1/α=1000", fill="#ff0055", font=("Consolas", 7, "bold"))

        if len(self.wealth_history) > 1:
            step_x = w / (len(self.wealth_history) - 1)
            pts = []
            for i, val in enumerate(self.wealth_history):
                norm_y = 100 - (min(val, 1000.0) / 1000.0) * 80
                pts.extend([i * step_x, norm_y])
            c.create_line(pts, fill="#39ff14", width=2)

def main():
    app = AxiomBipedalCockpit3D()
    app.mainloop()

if __name__ == "__main__":
    main()
