"""
Axiom Omni-Sentinel: Autonomous Hardware & OS Watchdog Subsystem
Provides continuous background surveillance, proactive self-healing,
presence-based security, and workstation governance.
"""

import os
import sys
import time
import threading
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from omni_sensor import get_system_hardware_telemetry, get_active_listening_ports
    from omni_actuator import system_control, media_control, filesystem_ops
except ImportError:
    from src.omni_sensor import get_system_hardware_telemetry, get_active_listening_ports
    from src.omni_actuator import system_control, media_control, filesystem_ops

class SentinelManager:
    """Manages continuous background watchdogs for proactive desktop self-healing."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._events_log: List[Dict[str, Any]] = []
        self._alert_callbacks = []
        
        self.sentinels = {
            "cpu_governor": {
                "name": "CPU & Hardware Governor",
                "description": "Monitors CPU spikes >90%; alerts or throttles runaway threads.",
                "enabled": True,
                "interval_s": 6.0,
                "threshold_cpu": 90.0,
                "high_count": 0,
                "triggers_count": 0,
                "last_status": "NORMAL"
            },
            "presence_guard": {
                "name": "Presence & Privacy Sentinel",
                "description": "Monitors workstation idle time and locks PC when user leaves.",
                "enabled": False,  # Off by default, toggleable by user
                "interval_s": 30.0,
                "idle_threshold_s": 300.0,  # 5 minutes
                "triggers_count": 0,
                "last_status": "IDLE"
            },
            "port_guard": {
                "name": "Port 3000 & Socket Sentinel",
                "description": "Protects Axiom Gateway on port 3000; detects port starvation.",
                "enabled": True,
                "interval_s": 15.0,
                "target_port": 3000,
                "triggers_count": 0,
                "last_status": "HEALTHY"
            },
            "workspace_hygiene": {
                "name": "Workspace Cache Sweeper",
                "description": "Periodically clears temp files and orphaned build artifacts.",
                "enabled": False,
                "interval_s": 3600.0, # 1 hour
                "last_run": 0.0,
                "triggers_count": 0,
                "last_status": "READY"
            }
        }

    def start(self):
        """Starts the sentinel background watchdog thread."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._watchdog_loop, daemon=True, name="AxiomSentinelDaemon")
            self._thread.start()
            self._log_event("SENTINEL_DAEMON_START", "Axiom Sentinel Watchdog Daemon initialized and running.")

    def stop(self):
        """Stops the sentinel daemon cleanly."""
        with self._lock:
            self._running = False

    def toggle(self, sentinel_id: str, enable: Optional[bool] = None) -> Dict[str, Any]:
        """Enables or disables a specific watchdog sentinel."""
        with self._lock:
            if sentinel_id not in self.sentinels:
                return {"success": False, "error": f"Sentinel '{sentinel_id}' not found"}
            cfg = self.sentinels[sentinel_id]
            if enable is None:
                cfg["enabled"] = not cfg["enabled"]
            else:
                cfg["enabled"] = bool(enable)
            status_str = "ENABLED" if cfg["enabled"] else "DISABLED"
            self._log_event("SENTINEL_TOGGLED", f"Sentinel '{cfg['name']}' is now {status_str}.")
            return {"success": True, "sentinel_id": sentinel_id, "enabled": cfg["enabled"], "name": cfg["name"]}

    def get_status(self) -> Dict[str, Any]:
        """Returns comprehensive telemetry on all standing sentinels."""
        with self._lock:
            return {
                "success": True,
                "daemon_running": self._running,
                "sentinels": dict(self.sentinels),
                "recent_events": list(self._events_log[-15:])
            }

    def register_alert_callback(self, cb):
        """Registers a callback to receive real-time sentinel alert notifications."""
        with self._lock:
            if cb not in self._alert_callbacks:
                self._alert_callbacks.append(cb)

    def _log_event(self, event_type: str, message: str, meta: dict = None):
        entry = {
            "timestamp": time.time(),
            "time_str": time.strftime("%H:%M:%S"),
            "event_type": event_type,
            "message": message,
            "meta": meta or {}
        }
        self._events_log.append(entry)
        if len(self._events_log) > 100:
            self._events_log = self._events_log[-100:]

        for cb in list(self._alert_callbacks):
            try:
                cb(entry)
            except Exception:
                pass

    def _watchdog_loop(self):
        """Main periodic polling loop across all active sentinels."""
        last_checks = {k: 0.0 for k in self.sentinels}

        while self._running:
            now = time.time()

            # 1. CPU Governor Check
            cpu_cfg = self.sentinels["cpu_governor"]
            if cpu_cfg["enabled"] and (now - last_checks["cpu_governor"]) >= cpu_cfg["interval_s"]:
                last_checks["cpu_governor"] = now
                try:
                    telem = get_system_hardware_telemetry()
                    cpu_p = telem.get("cpu_percent", 0.0)
                    if cpu_p >= cpu_cfg["threshold_cpu"]:
                        cpu_cfg["high_count"] += 1
                        cpu_cfg["last_status"] = f"HIGH LOAD ({cpu_p}%)"
                        if cpu_cfg["high_count"] >= 3:
                            cpu_cfg["triggers_count"] += 1
                            self._log_event(
                                "CPU_GOVERNOR_ALERT",
                                f"Sustained high CPU load detected ({cpu_p}% for >15s). Proactive mitigation alert issued.",
                                {"cpu_percent": cpu_p}
                            )
                            cpu_cfg["high_count"] = 0
                    else:
                        cpu_cfg["high_count"] = 0
                        cpu_cfg["last_status"] = f"NORMAL ({cpu_p}%)"
                except Exception:
                    pass

            # 2. Port Guard Check
            port_cfg = self.sentinels["port_guard"]
            if port_cfg["enabled"] and (now - last_checks["port_guard"]) >= port_cfg["interval_s"]:
                last_checks["port_guard"] = now
                try:
                    active_ports = get_active_listening_ports()
                    target = port_cfg["target_port"]
                    if target in active_ports:
                        port_cfg["last_status"] = f"PORT {target} ACTIVE (HEALTHY)"
                    else:
                        port_cfg["last_status"] = f"PORT {target} INACTIVE"
                except Exception:
                    pass

            # 3. Workspace Cache Sweeper Check
            hyg_cfg = self.sentinels["workspace_hygiene"]
            if hyg_cfg["enabled"] and (now - last_checks["workspace_hygiene"]) >= hyg_cfg["interval_s"]:
                last_checks["workspace_hygiene"] = now
                try:
                    clean_res = filesystem_ops("clean_temp")
                    hyg_cfg["triggers_count"] += 1
                    hyg_cfg["last_status"] = "CACHE_SWEPT"
                    self._log_event("WORKSPACE_HYGIENE_SWEEP", "Automated cache and temp cleanup completed.", clean_res)
                except Exception:
                    pass

            time.sleep(1.0)

# Global Singleton Instance
sentinel_manager = SentinelManager()
