"""
Axiom Omni v3.2 - Omnipresent Floating PC Controller & Voice Command Deck
========================================================================
An always-on-top, draggable, glassmorphic desktop floating orb that expands
into an advanced agentic control deck with one-click physical actuation,
real-time voice recognition, audio speech feedback, and system vitals.
"""

import os
import sys
import json
import time
import math
import random
import threading
import urllib.request
import urllib.parse
from pathlib import Path

# Ensure paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from PyQt5.QtCore import (
    Qt, QTimer, QPoint, QRect, QSize, pyqtSignal, QThread, pyqtSlot
)
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient, QLinearGradient,
    QFont, QPainterPath, QCursor, QFontMetrics, QPixmap, QIcon
)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QSystemTrayIcon, QMenu, QAction
)

import omni_actuator
import omni_reflex
try:
    from omni_catalog import app_catalog
except Exception:
    try:
        from src.omni_catalog import app_catalog
    except Exception:
        app_catalog = None

# Configuration directory
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
POS_CONFIG_FILE = os.path.join(CONFIG_DIR, "floating_orb_pos.json")

# Audio Chimes via winsound (non-blocking)
def play_chime(chime_type: str):
    """Dispatches futuristic sound cues asynchronously without blocking UI."""
    def _play():
        try:
            import winsound
            if chime_type == "open":
                winsound.Beep(988, 45)
                winsound.Beep(1318, 65)
            elif chime_type == "listen":
                winsound.Beep(1046, 80)
            elif chime_type == "success":
                winsound.Beep(1318, 50)
                winsound.Beep(1760, 80)
            elif chime_type == "click":
                winsound.Beep(1174, 35)
            elif chime_type == "error":
                winsound.Beep(440, 120)
        except Exception:
            pass
    threading.Thread(target=_play, daemon=True).start()


# Voice Worker Thread for non-blocking speech recognition
class VoiceWorker(QThread):
    finished_transcription = pyqtSignal(str)
    failed = pyqtSignal(str)
    audio_level = pyqtSignal(float)

    def __init__(self, duration=4.0):
        super().__init__()
        self.duration = duration

    def run(self):
        try:
            res = omni_actuator.voice_speech("listen", duration=self.duration)
            if res.get("success"):
                self.finished_transcription.emit(res.get("transcription", ""))
            else:
                self.failed.emit(res.get("error", "No speech recognized"))
        except Exception as e:
            self.failed.emit(str(e))


# Action Execution Thread for non-blocking reflex/brain dispatch
class ActionWorker(QThread):
    finished_action = pyqtSignal(dict)

    def __init__(self, goal):
        super().__init__()
        self.goal = goal

    def run(self):
        t0 = time.perf_counter()
        # 1. Attempt HTTP request to local Axiom Server (port 3000)
        try:
            req_data = json.dumps({"goal": self.goal}).encode('utf-8')
            req = urllib.request.Request(
                "http://127.0.0.1:3000/api/omni/chat",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                self.finished_action.emit(data)
                return
        except Exception:
            pass

        # 2. Local fallback if server is not reachable
        try:
            # Check compound
            sub_queries = omni_reflex.split_compound_query(self.goal)
            if len(sub_queries) > 1:
                compound = omni_reflex.match_compound_reflex(self.goal, threshold=0.65)
                if compound and len(compound) >= 2:
                    res = omni_reflex.execute_compound_reflex(compound, original_query=self.goal)
                    self.finished_action.emit(res)
                    return

            # Check single reflex
            matched = omni_reflex.match_reflex(self.goal, threshold=0.65)
            if matched and matched.get("confidence", 0) >= 0.65:
                res = omni_reflex.execute_reflex_action(matched, self.goal)
                res["execution_mode"] = "FAST_REFLEX_COMMIT"
                res["skill_name"] = matched["skill"].get("name")
                res["confidence"] = matched.get("confidence")
                res["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
                self.finished_action.emit(res)
                return

            clean_target = self.goal.lower().strip()
            for prefix in ("open ", "launch ", "start ", "run "):
                if clean_target.startswith(prefix):
                    clean_target = clean_target[len(prefix):].strip()
                    break

            # Try Grounded Catalog Resolution
            if app_catalog and app_catalog.resolve(clean_target):
                res = omni_actuator.app_control(action="launch", target=clean_target)
                res["execution_mode"] = "CATALOG_APP_LAUNCH"
                res["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
                self.finished_action.emit(res)
                return

            # Check if it's a known desktop system utility
            system_terms = ("terminal", "cmd", "powershell", "calc", "notepad", "explorer", "taskmgr", "control", "paint")
            if any(term == clean_target or f"open {term}" == self.goal.lower().strip() for term in system_terms):
                res = omni_actuator.app_control(action="launch", target=clean_target)
                res["execution_mode"] = "SYSTEM_APP_LAUNCH"
                res["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
                self.finished_action.emit(res)
                return

            # Fallback to Autonomous Brain
            try:
                import omni_brain
                brain_res = omni_brain.execute_autonomous_task(user_goal=self.goal, max_steps=4)
                brain_res["execution_mode"] = "AUTONOMOUS_BRAIN_LOCAL"
                brain_res["latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
                self.finished_action.emit(brain_res)
                return
            except Exception:
                pass

            # Fail with Dignity policy (never convert local desktop commands into Google searches)
            self.finished_action.emit({
                "success": False,
                "error": f"Directive '{self.goal}' not recognized as a local reflex or installed application.",
                "execution_mode": "FAIL_SAFE",
                "latency_ms": round((time.perf_counter() - t0) * 1000.0, 1)
            })
        except Exception as e:
            self.finished_action.emit({"success": False, "error": str(e)})


# ==============================================================================
# 1. OMNIPRESENT FLOATING ORB (The Always-On-Top Desktop Button)
# ==============================================================================
class AxiomFloatingOrb(QWidget):
    """
    Sleek, transparent, frameless, draggable cyber-orb always on top of Windows.
    Provides instant status visualization and expands on click to the Command Deck.
    """
    def __init__(self):
        super().__init__()
        # Frameless, Always on Top, Tool Window (no taskbar clutter)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("Axiom Omni Floating Button")
        self.setFixedSize(72, 72)

        self.state = "IDLE"  # "IDLE", "LISTENING", "EXECUTING", "SUCCESS"
        self.pulse_phase = 0.0
        self.is_hovered = False
        self.drag_position = QPoint()
        self.press_pos = QPoint()
        self.is_dragging = False

        # Load saved position or default to bottom-right
        self._init_position()

        # Animation timer (30 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate_pulse)
        self.anim_timer.start(33)

        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip("Axiom Omni v3.2 • Click to Open Control Deck | Drag to Move")

        # Command Deck reference
        self.command_deck = None

    def _init_position(self):
        screen = QApplication.primaryScreen().geometry()
        default_x = screen.width() - 95
        default_y = screen.height() - 220
        x, y = default_x, default_y

        if os.path.exists(POS_CONFIG_FILE):
            try:
                with open(POS_CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    x = max(10, min(screen.width() - 80, data.get("x", default_x)))
                    y = max(10, min(screen.height() - 80, data.get("y", default_y)))
            except Exception:
                pass
        self.move(x, y)

    def _save_position(self):
        try:
            with open(POS_CONFIG_FILE, "w") as f:
                json.dump({"x": self.x(), "y": self.y()}, f)
        except Exception:
            pass

    def _animate_pulse(self):
        self.pulse_phase += 0.08
        if self.pulse_phase > 2 * math.pi:
            self.pulse_phase -= 2 * math.pi
        self.update()

    def set_state(self, new_state: str):
        self.state = new_state
        self.update()
        if new_state == "SUCCESS":
            QTimer.singleShot(2000, lambda: self.set_state("IDLE"))

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.press_pos = event.globalPos()
            self.is_dragging = False
            event.accept()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if (event.globalPos() - self.press_pos).manhattanLength() > 5:
                self.is_dragging = True
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.is_dragging:
                self.toggle_command_deck()
            else:
                self._snap_to_edge_and_save()
            self.is_dragging = False
            event.accept()

    def _snap_to_edge_and_save(self):
        """Snaps the orb magnetically to screen edges if within threshold and keeps inside bounds."""
        screen = QApplication.screenAt(self.pos()) or QApplication.primaryScreen()
        geo = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        
        SNAP_DIST = 42
        MARGIN = 14
        
        curr_x = self.x()
        curr_y = self.y()
        target_x = curr_x
        target_y = curr_y

        # Snap to left edge
        if abs(curr_x - geo.left()) < SNAP_DIST:
            target_x = geo.left() + MARGIN
        # Snap to right edge
        elif abs((curr_x + self.width()) - geo.right()) < SNAP_DIST:
            target_x = geo.right() - self.width() - MARGIN

        # Snap to top edge
        if abs(curr_y - geo.top()) < SNAP_DIST:
            target_y = geo.top() + MARGIN
        # Snap to bottom edge
        elif abs((curr_y + self.height()) - geo.bottom()) < SNAP_DIST:
            target_y = geo.bottom() - self.height() - MARGIN

        # Clamp cleanly inside available screen bounds
        target_x = max(geo.left() + MARGIN, min(target_x, geo.right() - self.width() - MARGIN))
        target_y = max(geo.top() + MARGIN, min(target_y, geo.bottom() - self.height() - MARGIN))

        self.move(target_x, target_y)
        self._save_position()

    def toggle_command_deck(self):
        play_chime("open")
        if self.command_deck is None:
            self.command_deck = AxiomCommandDeck(self)
        
        if self.command_deck.isVisible():
            self.command_deck.hide()
        else:
            self.command_deck.position_near_orb(self.pos(), self.size())
            self.command_deck.show()
            self.command_deck.activateWindow()

    def _show_context_menu(self, global_pos):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #0b132b;
                color: #e0e6ed;
                border: 1px solid #00f2fe;
                border-radius: 8px;
                padding: 6px;
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #1c2541;
                color: #00f2fe;
            }
        """)
        action_voice = menu.addAction("🎙️ Voice Directive")
        action_deck = menu.addAction("⚡ Open Command Deck")
        action_boss = menu.addAction("🛡️ Boss Key (Hide All + Mute)")
        action_snip = menu.addAction("✂️ Screen Snipping Tool")
        action_dark = menu.addAction("🌙 Toggle Dark Mode")
        action_vitals = menu.addAction("📊 System Vitals")
        menu.addSeparator()
        action_cmd = menu.addAction("💻 Terminal (CMD)")
        action_ps = menu.addAction("⚡ PowerShell")
        action_exp = menu.addAction("📁 File Explorer")
        action_calc = menu.addAction("🧮 Calculator")
        action_np = menu.addAction("📝 Notepad")
        menu.addSeparator()
        action_exit = menu.addAction("❌ Exit Floating Control")

        selected = menu.exec_(global_pos)
        if selected == action_voice:
            self.toggle_command_deck()
            if self.command_deck:
                self.command_deck.start_voice_listening()
        elif selected == action_deck:
            self.toggle_command_deck()
        elif selected == action_cmd:
            omni_actuator.app_control("launch", "cmd")
            play_chime("click")
        elif selected == action_ps:
            omni_actuator.app_control("launch", "powershell")
            play_chime("click")
        elif selected == action_exp:
            omni_actuator.app_control("launch", "explorer")
            play_chime("click")
        elif selected == action_calc:
            omni_actuator.app_control("launch", "calc")
            play_chime("click")
        elif selected == action_np:
            omni_actuator.app_control("launch", "notepad")
            play_chime("click")
        elif selected == action_boss:
            omni_actuator.system_control("boss_key")
            play_chime("click")
        elif selected == action_snip:
            omni_actuator.system_control("screenshot")
        elif selected == action_dark:
            omni_actuator.system_theme_control("toggle")
            play_chime("success")
        elif selected == action_vitals:
            self.toggle_command_deck()
        elif selected == action_exit:
            QApplication.quit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0

        # State color scheme
        if self.state == "LISTENING":
            primary_col = QColor(255, 0, 128)   # Vivid Magenta
            glow_col = QColor(127, 0, 255)       # Electric Violet
            pulse_mod = math.sin(self.pulse_phase * 2.5) * 5.0
        elif self.state == "EXECUTING":
            primary_col = QColor(255, 183, 0)   # Electric Amber
            glow_col = QColor(255, 100, 0)       # Orange
            pulse_mod = math.sin(self.pulse_phase * 2.0) * 3.0
        elif self.state == "SUCCESS":
            primary_col = QColor(0, 255, 136)   # Emerald Green
            glow_col = QColor(0, 200, 255)       # Cyan
            pulse_mod = 6.0
        else: # IDLE
            primary_col = QColor(0, 242, 254)   # Electric Cyan
            glow_col = QColor(79, 172, 254)      # Azure
            pulse_mod = math.sin(self.pulse_phase) * 2.5

        # 1. Outer Radiant Glow Aura
        glow_radius = 28.0 + (3.0 if self.is_hovered else 0.0) + pulse_mod
        radial_glow = QRadialGradient(cx, cy, glow_radius)
        glow_c1 = QColor(primary_col)
        glow_c1.setAlpha(120 if self.is_hovered else 75)
        glow_c2 = QColor(glow_col)
        glow_c2.setAlpha(0)
        radial_glow.setColorAt(0.0, glow_c1)
        radial_glow.setColorAt(1.0, glow_c2)
        painter.setBrush(QBrush(radial_glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(glow_radius), int(glow_radius))

        # 2. Main Outer Frosted Circle Body
        body_radius = 24.0 if not self.is_hovered else 26.0
        body_grad = QLinearGradient(cx - body_radius, cy - body_radius, cx + body_radius, cy + body_radius)
        body_grad.setColorAt(0.0, QColor(18, 28, 56, 240))
        body_grad.setColorAt(1.0, QColor(9, 14, 28, 245))
        painter.setBrush(QBrush(body_grad))
        
        # Border Pen
        border_pen = QPen(primary_col, 2.0 if not self.is_hovered else 2.5)
        painter.setPen(border_pen)
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(body_radius), int(body_radius))

        # 3. Inner Concentric Energy Ring
        inner_pen = QPen(glow_col, 1.2, Qt.DashLine if self.state == "EXECUTING" else Qt.SolidLine)
        painter.setPen(inner_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPoint(int(cx), int(cy)), int(body_radius - 6), int(body_radius - 6))

        # 4. Central Axiom Delta Emblem
        path = QPainterPath()
        p_top = QPoint(int(cx), int(cy - 9))
        p_bl = QPoint(int(cx - 8), int(cy + 7))
        p_br = QPoint(int(cx + 8), int(cy + 7))
        p_inner = QPoint(int(cx), int(cy + 2))

        path.moveTo(p_top)
        path.lineTo(p_bl)
        path.lineTo(p_inner)
        path.lineTo(p_br)
        path.closeSubpath()

        emblem_grad = QLinearGradient(cx, cy - 9, cx, cy + 7)
        emblem_grad.setColorAt(0.0, primary_col)
        emblem_grad.setColorAt(1.0, QColor(255, 255, 255))
        painter.setBrush(QBrush(emblem_grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # Center glowing core dot
        core_col = QColor(255, 255, 255, 240)
        painter.setBrush(QBrush(core_col))
        painter.drawEllipse(QPoint(int(cx), int(cy - 1)), 2, 2)


# ==============================================================================
# 2. AXIOM COMMAND DECK (The Glassmorphic Control HUD)
# ==============================================================================
class AxiomCommandDeck(QWidget):
    """
    Futuristic, glassmorphic Control Deck featuring interactive voice recording,
    instant directive input, quick-action matrix, and real-time telemetry.
    """
    def __init__(self, orb: AxiomFloatingOrb):
        super().__init__()
        self.orb = orb
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("Axiom Omni Command Deck")
        self.setFixedSize(450, 680)

        self.voice_worker = None
        self.action_worker = None
        self.tts_enabled = True

        self._build_ui()
        self._init_vitals_timer()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            play_chime("click")
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)

    def position_near_orb(self, orb_pos: QPoint, orb_size: QSize):
        """Snaps the HUD safely adjacent to the floating orb without clipping off-screen or taskbar."""
        screen = QApplication.screenAt(orb_pos) or QApplication.primaryScreen()
        geo = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        deck_w, deck_h = self.width(), self.height()

        # Try to place to the left of the orb first
        x = orb_pos.x() - deck_w - 12
        if x < geo.left() + 15:
            # Place to the right if not enough room on left
            x = orb_pos.x() + orb_size.width() + 12

        # Align vertically
        y = orb_pos.y() - 100
        if y + deck_h > geo.bottom() - 15:
            y = geo.bottom() - deck_h - 15
        if y < geo.top() + 15:
            y = geo.top() + 15

        self.move(x, y)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Glass Panel Frame
        self.glass_frame = QFrame(self)
        self.glass_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 19, 43, 0.94);
                border: 1.5px solid rgba(0, 242, 254, 0.4);
                border-radius: 20px;
            }
        """)
        panel_layout = QVBoxLayout(self.glass_frame)
        panel_layout.setContentsMargins(20, 18, 20, 18)
        panel_layout.setSpacing(14)

        # -------------------------------------------------------------
        # 1. Header Bar: Title, Status Badge, Close
        # -------------------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        # Logo / Title
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_lbl = QLabel("AXIOM OMNI", self)
        title_lbl.setStyleSheet("color: #00f2fe; font-size: 16px; font-weight: 800; letter-spacing: 2px; font-family: 'Segoe UI', Arial;")
        sub_lbl = QLabel("PHYSICAL AUTONOMOUS ACTUATION", self)
        sub_lbl.setStyleSheet("color: #79869c; font-size: 9px; font-weight: 600; letter-spacing: 1px;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header.addLayout(title_box)

        header.addStretch()

        # Telemetry Pill
        self.vitals_lbl = QLabel("CPU 0% | RAM 0%", self)
        self.vitals_lbl.setStyleSheet("""
            background-color: rgba(28, 37, 65, 0.8);
            color: #00f2fe;
            border: 1px solid rgba(0, 242, 254, 0.25);
            border-radius: 10px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
        """)
        header.addWidget(self.vitals_lbl)

        # Close Button
        close_btn = QPushButton("✕", self)
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.05);
                color: #8da9c4;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 14px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 80, 0.4);
                color: #ffffff;
                border: 1px solid #ff0050;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header.addWidget(close_btn)
        panel_layout.addLayout(header)

        # -------------------------------------------------------------
        # 2. Hero Voice Command Orb & Audio Reactive Waveform
        # -------------------------------------------------------------
        voice_card = QFrame(self)
        voice_card.setStyleSheet("""
            QFrame {
                background-color: rgba(18, 28, 56, 0.65);
                border: 1px solid rgba(0, 242, 254, 0.2);
                border-radius: 16px;
            }
        """)
        voice_layout = QVBoxLayout(voice_card)
        voice_layout.setContentsMargins(14, 14, 14, 14)
        voice_layout.setSpacing(8)

        # Mic Action Button
        self.mic_btn = QPushButton("🎙️ Tap to Speak Directive", self)
        self.mic_btn.setFixedHeight(54)
        self.mic_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f2fe, stop:1 #4facfe);
                color: #0b132b;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38f9d7, stop:1 #4facfe);
            }
        """)
        self.mic_btn.clicked.connect(self.start_voice_listening)
        voice_layout.addWidget(self.mic_btn)

        self.voice_status_lbl = QLabel("Hold mic or press Space to dictate commands aloud", self)
        self.voice_status_lbl.setAlignment(Qt.AlignCenter)
        self.voice_status_lbl.setStyleSheet("color: #8da9c4; font-size: 11px;")
        voice_layout.addWidget(self.voice_status_lbl)

        panel_layout.addWidget(voice_card)

        # -------------------------------------------------------------
        # 3. Smart Directive Text Input & Quick Suggestions
        # -------------------------------------------------------------
        input_box = QHBoxLayout()
        input_box.setSpacing(8)

        self.text_input = QLineEdit(self)
        self.text_input.setPlaceholderText("Type directive (e.g. 'search REC Sonbhadra', 'play music')...")
        self.text_input.setFixedHeight(40)
        self.text_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(9, 14, 28, 0.8);
                color: #ffffff;
                border: 1px solid rgba(0, 242, 254, 0.3);
                border-radius: 10px;
                padding: 0 12px;
                font-size: 12px;
                font-family: 'Segoe UI', Arial;
            }
            QLineEdit:focus {
                border: 1.5px solid #00f2fe;
                background-color: rgba(14, 22, 44, 0.95);
            }
        """)
        self.text_input.returnPressed.connect(self._dispatch_typed_directive)
        input_box.addWidget(self.text_input)

        run_btn = QPushButton("▶ Run", self)
        run_btn.setFixedSize(70, 40)
        run_btn.setCursor(QCursor(Qt.PointingHandCursor))
        run_btn.setStyleSheet("""
            QPushButton {
                background-color: #1c2541;
                color: #00f2fe;
                border: 1px solid #00f2fe;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #00f2fe;
                color: #0b132b;
            }
        """)
        run_btn.clicked.connect(self._dispatch_typed_directive)
        input_box.addWidget(run_btn)
        panel_layout.addLayout(input_box)

        # Quick Suggestion Pills
        pills_scroll = QScrollArea(self)
        pills_scroll.setFixedHeight(34)
        pills_scroll.setWidgetResizable(True)
        pills_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        pills_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        pills_scroll.setStyleSheet("background: transparent; border: none;")

        pills_container = QWidget()
        pills_container.setStyleSheet("background: transparent;")
        pills_layout = QHBoxLayout(pills_container)
        pills_layout.setContentsMargins(0, 0, 0, 0)
        pills_layout.setSpacing(6)

        SUGGESTIONS = [
            ("💻 Terminal (cmd)", "open cmd"),
            ("⚡ PowerShell", "open powershell"),
            ("📁 File Explorer", "open explorer"),
            ("🧮 Calculator", "open calc"),
            ("📝 Notepad", "open notepad"),
            ("🎵 Play Music", "play music"),
            ("📸 Take Photo", "take picture"),
            ("✂️ Snip Screen", "snip screen"),
            ("🌙 Dark Mode", "toggle dark mode"),
            ("🛡️ Boss Key", "boss key"),
            ("🧹 Clean Temp", "clean temp")
        ]

        for label, cmd in SUGGESTIONS:
            btn = QPushButton(label, pills_container)
            btn.setFixedHeight(26)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: #a4b0be;
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 13px;
                    padding: 0 10px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 242, 254, 0.15);
                    color: #00f2fe;
                    border: 1px solid #00f2fe;
                }
            """)
            btn.clicked.connect(lambda checked, c=cmd: self.execute_directive(c))
            pills_layout.addWidget(btn)

        pills_scroll.setWidget(pills_container)
        panel_layout.addWidget(pills_scroll)

        # -------------------------------------------------------------
        # 4. Hyper Utility Matrix (Tactile 1-Click Action Grid)
        # -------------------------------------------------------------
        matrix_title = QLabel("HYPER UTILITY CONTROLS", self)
        matrix_title.setStyleSheet("color: #79869c; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;")
        panel_layout.addWidget(matrix_title)

        grid = QGridLayout()
        grid.setSpacing(8)

        GRID_BUTTONS = [
            ("💻 Terminal (CMD)", lambda: self.execute_directive("open cmd"), "#00f2fe"),
            ("⚡ PowerShell", lambda: self.execute_directive("open powershell"), "#38f9d7"),
            ("📁 File Explorer", lambda: self.execute_directive("open explorer"), "#4facfe"),
            ("🧮 Calculator", lambda: self.execute_directive("open calc"), "#ff758c"),
            ("📝 Notepad", lambda: self.execute_directive("open notepad"), "#30cfd0"),
            ("📊 Task Manager", lambda: self.execute_directive("open taskmgr"), "#fee140"),
            ("🎵 Chill Music", lambda: self.execute_directive("play music"), "#f093fb"),
            ("🔇 Mute Volume", lambda: self.execute_directive("mute audio"), "#43e97b"),
            ("🔊 Volume +", lambda: self.execute_directive("volume up"), "#4facfe"),
            ("🛡️ Boss Key", lambda: self.execute_directive("boss key"), "#fa709a"),
            ("🔒 Lock PC", lambda: self.execute_directive("lock pc"), "#fee140"),
            ("🌙 Dark / Light", lambda: self.execute_directive("toggle dark mode"), "#30cfd0"),
            ("🪟 Minimize All", lambda: self.execute_directive("minimize all windows"), "#c471ed"),
            ("🧹 Clean Temp", lambda: self.execute_directive("clean temp"), "#f77737"),
            ("🚀 Free Port 3000", lambda: self.execute_directive("free port 3000"), "#ff0844")
        ]

        row, col = 0, 0
        for text, handler, accent in GRID_BUTTONS:
            tile = QPushButton(text, self)
            tile.setFixedHeight(44)
            tile.setCursor(QCursor(Qt.PointingHandCursor))
            tile.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(28, 37, 65, 0.7);
                    color: #e0e6ed;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 10px;
                    font-size: 11px;
                    font-weight: 600;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: rgba(30, 45, 80, 0.95);
                    color: {accent};
                    border: 1.2px solid {accent};
                }}
                QPushButton:pressed {{
                    background-color: rgba(0, 242, 254, 0.2);
                }}
            """)
            tile.clicked.connect(handler)
            grid.addWidget(tile, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        panel_layout.addLayout(grid)

        # -------------------------------------------------------------
        # 5. Live Grounded Observation Feed (Terminal Console Box)
        # -------------------------------------------------------------
        obs_title = QLabel("GROUNDED OBSERVATION FEED", self)
        obs_title.setStyleSheet("color: #79869c; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;")
        panel_layout.addWidget(obs_title)

        self.obs_box = QLabel("Axiom Physical Engine online. All Win32 actuators calibrated.", self)
        self.obs_box.setWordWrap(True)
        self.obs_box.setMinimumHeight(68)
        self.obs_box.setMaximumHeight(96)
        self.obs_box.setStyleSheet("""
            QLabel {
                background-color: rgba(7, 11, 20, 0.9);
                color: #00f2fe;
                border: 1px solid rgba(0, 242, 254, 0.2);
                border-radius: 10px;
                padding: 8px 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        panel_layout.addWidget(self.obs_box)

        main_layout.addWidget(self.glass_frame)

    def _init_vitals_timer(self):
        self.vitals_timer = QTimer(self)
        self.vitals_timer.timeout.connect(self._update_vitals)
        self.vitals_timer.start(2500)
        self._update_vitals()

    def _update_vitals(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            self.vitals_lbl.setText(f"CPU {cpu}% | RAM {ram}%")
        except Exception:
            pass

    def _dispatch_typed_directive(self):
        text = self.text_input.text().strip()
        if text:
            self.text_input.clear()
            self.execute_directive(text)

    def start_voice_listening(self):
        """Activates microphone speech-to-text recording."""
        play_chime("listen")
        self.orb.set_state("LISTENING")
        self.mic_btn.setText("🔴 Listening... Speak clearly now")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff0844, stop:1 #ffb199);
                color: #ffffff;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 700;
            }
        """)
        self.voice_status_lbl.setText("Recording microphone audio (4.0s)...")
        self.obs_box.setText("🎙️ Listening to physical user microphone...")

        self.voice_worker = VoiceWorker(duration=4.0)
        self.voice_worker.finished_transcription.connect(self._on_voice_transcribed)
        self.voice_worker.failed.connect(self._on_voice_failed)
        self.voice_worker.start()

    def _on_voice_transcribed(self, text: str):
        play_chime("click")
        self.mic_btn.setText("🎙️ Tap to Speak Directive")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f2fe, stop:1 #4facfe);
                color: #0b132b;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 700;
            }
        """)
        self.voice_status_lbl.setText(f"Recognized: '{text}'")
        self.execute_directive(text)

    def _on_voice_failed(self, error: str):
        play_chime("error")
        self.orb.set_state("IDLE")
        self.mic_btn.setText("🎙️ Tap to Speak Directive")
        self.mic_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f2fe, stop:1 #4facfe);
                color: #0b132b;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 700;
            }
        """)
        self.voice_status_lbl.setText(f"Mic note: {error}")
        self.obs_box.setText(f"⚠️ Voice capture note: {error}")

    def execute_directive(self, goal: str):
        """Dispatches user directive into fast reflexes or autonomous brain."""
        clean_g = goal.strip()
        if not clean_g:
            return

        play_chime("click")
        self.orb.set_state("EXECUTING")
        self.obs_box.setText(f"⚡ Processing: '{clean_g}'...")

        self.action_worker = ActionWorker(clean_g)
        self.action_worker.finished_action.connect(self._on_action_finished)
        self.action_worker.start()

    def _on_action_finished(self, res: dict):
        self.orb.set_state("SUCCESS")
        play_chime("success")

        # Format observation
        mode = res.get("execution_mode", "REFLEX_COMMIT")
        latency = res.get("latency_ms", 0)
        final_msg = res.get("final_answer") or res.get("message") or ""
        
        # Check trace observations and visual state diffs
        trace = res.get("trace", [])
        diff_info = ""
        if trace and isinstance(trace, list) and len(trace) > 0:
            last_step = trace[-1]
            obs = last_step.get("observation", {})
            if isinstance(obs, dict):
                if obs.get("message"):
                    final_msg = obs.get("message")
                if obs.get("visual_state_diff"):
                    vsd = obs["visual_state_diff"]
                    diff_info = f" [ΔLum: {vsd.get('luminance_delta',0)*100:.1f}%, Pix: {vsd.get('changed_pixel_ratio',0)*100:.1f}%]"

        if not final_msg and res.get("success"):
            final_msg = f"Directive executed successfully via {mode}."

        ledger_info = ""
        events = res.get("events", [])
        plan_evt = next((e for e in events if e.get("type") in ("plan_initialized", "hierarchical_plan")), None)
        if plan_evt and plan_evt.get("plan", {}).get("milestones"):
            ms = plan_evt["plan"]["milestones"]
            done_cnt = sum(1 for m in ms if m.get("status") in ("verified", "completed"))
            ledger_info = f" | Ledger: {done_cnt}/{len(ms)} ✓"

        dist_info = ""
        if res.get("distilled_skill"):
            d = res["distilled_skill"]
            dist_info = f"\n⚡ Distilled C++ Reflex: {d.get('name', 'skill')} (<{d.get('avg_latency_us', 30):.0f}µs)"

        self.obs_box.setText(f"[{mode} | {latency}ms]{ledger_info}{diff_info}\n{final_msg}{dist_info}")

        # TTS Speak Aloud Feedback
        if self.tts_enabled and final_msg:
            # Short clean voice confirmation
            speech_text = final_msg.split("\n")[0]
            if len(speech_text) > 120:
                speech_text = speech_text[:120]
            omni_actuator.voice_speech("speak", text=speech_text)


# ==============================================================================
# 3. GLOBAL HOTKEY DAEMON (Alt+Space to Summon Floating Control)
# ==============================================================================
def start_global_hotkey_listener(orb: AxiomFloatingOrb):
    """Listens for global Alt+Space hotkey to summon the Axiom Control Deck from anywhere."""
    def _loop():
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            
            HOTKEY_ID = 9182
            MOD_ALT = 0x0001
            VK_SPACE = 0x20
            
            if user32.RegisterHotKey(None, HOTKEY_ID, MOD_ALT, VK_SPACE):
                msg = wintypes.MSG()
                while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                    if msg.message == 0x0312 and msg.wParam == HOTKEY_ID: # WM_HOTKEY
                        # Post toggle to Qt main event loop
                        QTimer.singleShot(0, orb.toggle_command_deck)
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
        except Exception:
            pass

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


# ==============================================================================
# 4. ENTRY POINT & MAIN RUNNER
# ==============================================================================
def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    orb = AxiomFloatingOrb()
    orb.show()

    # System Tray Icon as secondary anchor
    tray = QSystemTrayIcon(app)
    tray.setToolTip("Axiom Omni v3.2 - Physical PC Control Core")
    
    # Generate clean glowing orb icon for tray
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    tp = QPainter(pixmap)
    tp.setRenderHint(QPainter.Antialiasing)
    tp.setBrush(QBrush(QColor(0, 242, 254)))
    tp.setPen(Qt.NoPen)
    tp.drawEllipse(2, 2, 28, 28)
    tp.end()
    tray.setIcon(QIcon(pixmap))

    tray_menu = QMenu()
    a_show = tray_menu.addAction("⚡ Summon Control Deck")
    a_show.triggered.connect(orb.toggle_command_deck)
    a_exit = tray_menu.addAction("❌ Exit")
    a_exit.triggered.connect(app.quit)
    tray.setContextMenu(tray_menu)
    tray.show()

    print("=================================================================", flush=True)
    print("Axiom Omni v3.2 - Omnipresent Floating Button Active!", flush=True)
    print("Floating cyber-orb is live on your Windows desktop.", flush=True)
    print("Controls:", flush=True)
    print("  - Left Click Orb: Expands Command Deck HUD", flush=True)
    print("  - Drag Orb: Move anywhere across screens", flush=True)
    print("  - Right Click Orb: Quick Actions Context Menu", flush=True)
    print("  - Global Hotkey: Alt + Space summons Command Deck from anywhere", flush=True)
    print("=================================================================", flush=True)

    # Register global Alt+Space
    start_global_hotkey_listener(orb)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
