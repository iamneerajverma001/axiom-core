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
root_dir = os.path.dirname(os.path.dirname(pkg_dir))
core_dir = os.path.join(root_dir, "products", "axiom-core")

for d in (pkg_dir, root_dir, core_dir):
    if d not in sys.path:
        sys.path.insert(0, d)

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
        self.assertLess(res.get("latency_ms", 10.0), 25.0) # Sub-25ms SLA under full test runner load

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

    def test_axiom_os_binary_feature_tensor_ipc(self):
        """Validates that Axiom-OS IPC buffer structure matches C++ engine 128-dim binary float tensor layout."""
        from src.axiom_ipc_bridge import AxiomIpcBufferStruct
        buf = AxiomIpcBufferStruct()
        self.assertTrue(hasattr(buf, "feature_dim"))
        self.assertTrue(hasattr(buf, "feature_vector"))
        self.assertEqual(len(buf.feature_vector), 128)

    def test_vision_tensor_128d_feature_vector_extraction(self):
        """Validates that VisualSpatialTensorEngine transforms 2D activation maps into 128-dim float tensors."""
        import numpy as np
        engine = omni_vision_tensor.vision_tensor_engine
        mock_map = np.ones((128, 128), dtype=np.float32)
        vec = engine.extract_128d_feature_vector(mock_map)
        self.assertEqual(len(vec), 128)
        self.assertTrue(all(isinstance(x, float) for x in vec))
        # Horizontal and vertical projections must both sum to ~1.0
        self.assertAlmostEqual(sum(vec[:64]), 1.0, places=3)
        self.assertAlmostEqual(sum(vec[64:]), 1.0, places=3)

    def test_visual_tensor_click_tool_dispatch(self):
        """Validates visual_tensor_click tool dispatch and presence of 128-dim feature vector."""
        res = omni_actuator.execute_tool("visual_tensor_click", target="calculator button 7", click=False)
        self.assertTrue(res.get("success"))
        self.assertIn("feature_vector_128d", res)
        self.assertEqual(len(res["feature_vector_128d"]), 128)
        self.assertIn("phys_x", res)
        self.assertIn("phys_y", res)

    def test_gui_workflow_hierarchical_planning(self):
        """Validates multi-window GUI workflow DAG decomposition for typing and visual clicking."""
        plan = omni_brain.decompose_hierarchical_plan("open notepad and write 'hello world'", {})
        self.assertIsNotNone(plan)
        self.assertGreaterEqual(len(plan.milestones), 4)
        tools = [m.designated_tool for m in plan.milestones if m.designated_tool]
        self.assertIn("app_control", tools)
        self.assertIn("visual_tensor_click", tools)
        self.assertIn("keyboard_type", tools)

    def test_keyboard_type_tool_dispatch(self):
        """Validates keyboard_type tool execution dispatch."""
        res = omni_actuator.execute_tool("keyboard_type", text="test_token")
        self.assertTrue(res.get("success"))
        self.assertIn("method", res)

    def test_hotkey_reflex_daemon(self):
        """Validates HotkeyReflexDaemon status lifecycle."""
        from src.axiom_os_bridge import HotkeyReflexDaemon
        daemon = HotkeyReflexDaemon(hotkey_id=9999, modifiers=0x0001, vk=0x56)
        status = daemon.get_status()
        self.assertFalse(status["active"])
        self.assertEqual(status["id"], 9999)
        self.assertEqual(status["vk"], "0x56")

    def test_enterprise_benchmark_solutions(self):
        """Validates that FinTech, Cybersecurity, and Robotics reference solutions run and report telemetry."""
        from solutions.fintech_pretrade_firewall.firewall import PreTradeRiskFirewall, TradeOrder
        from solutions.cybersecurity_packet_guard.packet_guard import PacketGuard, PacketHeader
        from solutions.robotics_motor_reflex.motor_reflex import MotorReflexArc, JointTelemetry

        # FinTech
        fw = PreTradeRiskFirewall(max_order_notional=50_000.0)
        order = TradeOrder(order_id="TEST-1", symbol="NVDA", side="BUY", price=120.0, quantity=10, account_id="ACC-1")
        res_fw = fw.evaluate_order(order, mid_market_price=120.0)
        self.assertTrue(res_fw.get("approved"))

        # Cyber
        pg = PacketGuard()
        pkt = PacketHeader(
            packet_id=1,
            src_ip="10.0.0.1",
            dst_ip="192.168.1.1",
            src_port=1234,
            dst_port=443,
            protocol=6,
            tcp_flags=0x10,
            payload_len=128,
            window_size=65535
        )
        res_pg = pg.inspect_packet(pkt)
        self.assertEqual(res_pg.get("action"), "PASS")

        # Robotics
        ctrl = MotorReflexArc()
        telem = JointTelemetry(
            joint_id=1,
            commanded_torque_nm=12.0,
            measured_torque_nm=11.9,
            angular_velocity_rad_s=3.14,
            proximity_distance_m=0.8
        )
        res_rob = ctrl.evaluate_cycle(telem)
        self.assertIn("NORMAL", res_rob.get("status", ""))

if __name__ == "__main__":
    unittest.main()



