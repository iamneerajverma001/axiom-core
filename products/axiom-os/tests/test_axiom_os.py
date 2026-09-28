"""
Axiom-OS Standalone Integration Test Suite
Validates dual-speed System 1 / System 2 dispatch, autonomous sentinels, and Win32 hardware control.
"""

import sys
import os
import unittest
import time
import json

pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from src import (
    omni_sensor,
    omni_actuator,
    omni_reflex,
    omni_sentinel,
    omni_ldu,
    omni_mesh_swarm,
    omni_brain,
    omni_vision_tensor
)

class TestAxiomOSArchitecture(unittest.TestCase):
    def test_sensor_telemetry(self):
        telem = omni_sensor.get_system_hardware_telemetry()
        self.assertIn("cpu_percent", telem)
        self.assertIn("ram_percent", telem)
        self.assertIn("screen_resolution", telem)
        self.assertGreater(telem["ram_percent"], 0)

    def test_actuator_powershell_execution(self):
        res = omni_actuator.powershell_exec("Get-Date")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("exit_code"), 0)

    def test_martingale_conformal_actuator_blocking(self):
        # Destructive command must be immediately quarantined by conformal barrier
        res = omni_actuator.execute_tool("powershell_exec", script="rmdir /s /q C:\\TestQuarantine")
        self.assertFalse(res.get("success"))
        self.assertIn("MARTINGALE", res.get("error", ""))

    def test_latent_deliberation_lif_spikes(self):
        ldu = omni_ldu.LatentDeliberationUnit(recurrence_steps=3)
        res = ldu.deliberate("cleanup temporary files and disk space")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("latent_vector_dim"), 256)
        self.assertIn("shannon_entropy", res)
        self.assertIn("latency_ms", res)
        self.assertLess(res.get("latency_ms", 10.0), 5.0) # Sub-5ms SLA

    def test_sentinel_alert_dispatch(self):
        mgr = omni_sentinel.SentinelManager()
        alerts_received = []
        mgr.register_alert_callback(lambda a: alerts_received.append(a))
        # Trigger synthetic alert via _log_event
        mgr._log_event("HIGH_RAM_PRESSURE", "RAM usage exceeded threshold", meta={"ram_pct": 94.2})
        self.assertEqual(len(alerts_received), 1)
        self.assertEqual(alerts_received[0]["event_type"], "HIGH_RAM_PRESSURE")

    def test_mesh_swarm_crdt_sync(self):
        node = omni_mesh_swarm.AxiomMeshNode()
        status = node.get_swarm_status()
        self.assertIn("node_id", status)
        self.assertIn("peers_count", status)
        self.assertIn("hostname", status)

    def test_visual_spatial_soft_argmax_click(self):
        res = omni_actuator.execute_tool("visual_spatial_click", target="close button", click=False)
        self.assertTrue(res.get("success"))
        self.assertIn("phys_x", res)
        self.assertIn("phys_y", res)
        self.assertIn("confidence", res)

    def test_visual_click_sequence_dispatch(self):
        orig = omni_vision_tensor.vision_tensor_engine.execute_direct_click
        try:
            omni_vision_tensor.vision_tensor_engine.execute_direct_click = lambda t, click=True, verify=False: {
                "phys_x": 400, "phys_y": 600, "confidence": 0.95, "total_elapsed_ms": 3.0
            }
            res = omni_actuator.execute_tool("visual_click_sequence", targets=["button 7", "button 8"], delay_between_s=0.01)
            self.assertTrue(res.get("success"))
            self.assertEqual(res.get("total_clicks"), 2)
        finally:
            omni_vision_tensor.vision_tensor_engine.execute_direct_click = orig

    def test_hierarchical_planner_dag_and_ledger(self):
        plan = omni_brain.decompose_hierarchical_plan("open calc and compute 7 * 8", {})
        self.assertIsNotNone(plan)
        self.assertGreater(len(plan.milestones), 2)
        active = plan.get_active_milestone()
        self.assertIsNotNone(active)
        ledger = plan.render_ledger()
        self.assertIn("[HIERARCHICAL MULTI-STEP EXECUTION GRAPH & PROGRESS LEDGER]", ledger)

if __name__ == "__main__":
    unittest.main()

