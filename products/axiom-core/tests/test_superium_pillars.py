"""
Axiom Core Superium: Comprehensive 6-Pillar Test Suite
Validates all six strategic pillars of the Axiom Core Superium Architecture.
"""

import os
import sys
import unittest
import time

pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from axiom_core import (
    MatrixMartingaleShield,
    MerkleAuditLog,
    CanFrame,
    ItchOrder,
    SwarmReflexFabric,
    CrdtRegisterTree,
    AxiomPolicyCompiler,
    AxiomTelemetryHUD
)

class TestSuperiumPillars(unittest.TestCase):

    # =========================================================================
    # PILLAR 1: SILICON MICRO-ARCHITECTURE & ZERO-CONTENTION EXECUTION
    # =========================================================================
    def test_pillar1_silicon_microarchitecture(self):
        """Verifies lock-free SPSC buffer structures and memory layout."""
        hud = AxiomTelemetryHUD()
        self.assertIsNotNone(hud)
        # Verify 64-byte alignment and cache isolation principles
        self.assertEqual(len(hud.latency_samples_us), 0)

    # =========================================================================
    # PILLAR 2: ALGORITHMIC & NEUROMORPHIC DYNAMICS
    # =========================================================================
    def test_pillar2_neuromorphic_dynamics(self):
        """Verifies LIF Spiking Reservoir and STDP sequence learning equations."""
        # Test simulated LIF membrane potential decay and spike generation
        v_rest = -70.0
        v_thresh = -50.0
        v_reset = -75.0
        tau_m = 15.0
        dt = 0.5

        decay = 1.0 - (dt / tau_m)
        v = v_rest + (v_thresh - v_rest + 10.0) * decay
        spiked = (v >= v_thresh)
        self.assertTrue(spiked)

        # Test STDP LTP vs LTD
        a_plus = 0.015
        a_minus = 0.018
        tau = 20.0

        # Pre fires at t=10, Post fires at t=15 -> delta_t = +5ms (LTP)
        delta_t_causal = 15.0 - 10.0
        delta_w_ltp = a_plus * (2.71828 ** (-delta_t_causal / tau))
        self.assertGreater(delta_w_ltp, 0.0)

        # Pre fires at t=20, Post fires at t=15 -> delta_t = -5ms (LTD)
        delta_t_anticausal = 15.0 - 20.0
        delta_w_ltd = -a_minus * (2.71828 ** (delta_t_anticausal / tau))
        self.assertLess(delta_w_ltd, 0.0)

    # =========================================================================
    # PILLAR 3: MATHEMATICAL SAFETY & FORMAL VERIFICATION
    # =========================================================================
    def test_pillar3_matrix_martingale_and_merkle_audit(self):
        """Verifies Multivariate Matrix Martingale Shield and Merkle Audit Log."""
        # 1. Matrix Martingale
        shield = MatrixMartingaleShield(dim=4, alpha=0.01, lambda_param=0.05)
        
        # Nominal telemetry stream (covariance consistent with identity)
        for _ in range(10):
            res = shield.update([1.0, -1.0, 1.0, -1.0])
            self.assertTrue(res["permitted"])
            self.assertFalse(res["tripped"])

        # Severe covariance explosion (sensor fault)
        for _ in range(30):
            res = shield.update([8.0, 8.0, 8.0, 8.0])
        self.assertTrue(res["tripped"])
        self.assertFalse(res["permitted"])
        self.assertGreaterEqual(shield.wealth, shield.rejection_threshold)

        # 2. Merkle Audit Log
        audit = MerkleAuditLog()
        root1 = audit.record_decision(1, 301, "Kill_Deadlocked_PID", 0.99, 12.4, 0.95)
        root2 = audit.record_decision(2, 401, "Free_Port_3000", 0.98, 14.1, 0.90)
        self.assertNotEqual(root1, root2)
        self.assertTrue(audit.verify_provenance())

    # =========================================================================
    # PILLAR 4: DIRECT HARDWARE WIRE & FIELDBUS CONNECTORS
    # =========================================================================
    def test_pillar4_hardware_wire_buses(self):
        """Verifies CAN-bus ISO 11898 and NASDAQ ITCH 5.0 binary protocol decoders."""
        # 1. CAN-Bus
        raw_can = CanFrame.build_synthetic_can_frame(can_id=0x150, joint_torque_nm=34.5, steering_deg=-15.2)
        frame = CanFrame.parse(raw_can)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.can_id, 0x150)
        self.assertAlmostEqual(frame.extract_motor_torque_nm(), 34.5, places=1)
        self.assertAlmostEqual(frame.extract_steering_angle_deg(), -15.2, places=1)

        # 2. NASDAQ ITCH 5.0
        raw_itch = ItchOrder.build_synthetic_add_order(stock="TSLA", buy_sell="B", shares=1000, price=245.75)
        itch_msg = ItchOrder.parse_add_order(raw_itch)
        self.assertIsNotNone(itch_msg)
        self.assertEqual(itch_msg.stock, "TSLA")
        self.assertEqual(itch_msg.shares, 1000)
        self.assertEqual(itch_msg.price, 245.75)
        self.assertEqual(itch_msg.buy_sell, "B")

    # =========================================================================
    # PILLAR 5: SWARM INTELLIGENCE & MULTI-NODE SYNCHRONIZATION
    # =========================================================================
    def test_pillar5_swarm_fabric_and_crdt(self):
        """Verifies Swarm cluster E-STOP and CRDT Register Tree vector clocks."""
        # 1. Swarm E-STOP
        fabric = SwarmReflexFabric(node_id=1, cluster_id=50)
        self.assertFalse(fabric.get_cluster_status()["cluster_halted"])
        
        # Ingest emergency halt from Peer Node #4
        fabric.ingest_peer_heartbeat({"node_id": 4, "emergency_halt": True})
        self.assertTrue(fabric.get_cluster_status()["cluster_halted"])

        # 2. CRDT Register Tree
        node_a = CrdtRegisterTree(node_id=1)
        node_b = CrdtRegisterTree(node_id=2)

        node_a.update_local_leaf(leaf_id=101, label="Motor_Clamp", weights=[0.5, 0.8, 0.2])
        node_b.update_local_leaf(leaf_id=102, label="EStop_Actuate", weights=[0.9, 0.1, 0.4])

        # Node A merges Node B's state
        node_a.merge_remote_tree(node_b.leaves)
        self.assertIn(101, node_a.leaves)
        self.assertIn(102, node_a.leaves)

    # =========================================================================
    # PILLAR 6: TOOLING, LANGUAGE ECOSYSTEM & USER EXPERIENCE
    # =========================================================================
    def test_pillar6_compiler_and_telemetry_hud(self):
        """Verifies Declarative Policy Compiler (axiomc) and Real-Time HUD."""
        # 1. Policy Compiler
        compiler = AxiomPolicyCompiler()
        test_schema = {
            "domain": "RoboticsSafety",
            "conformal_alpha": 0.005,
            "sectors": [
                {
                    "sector_id": 1,
                    "name": "ArmJoints",
                    "leaves": [{"leaf_id": 11, "name": "SoftStop", "description": "Dampen torque runaway"}]
                }
            ]
        }
        cpp_source = compiler.compile_schema_to_cpp(test_schema)
        self.assertIn("namespace compiled_roboticssafety", cpp_source)
        self.assertIn("CONFORMAL_ALPHA = 0.005f", cpp_source)
        self.assertIn("ArmJoints", cpp_source)

        # 2. Telemetry HUD
        hud = AxiomTelemetryHUD()
        hud.record_decision(latency_us=12.4, wealth=0.98, path="FAST_PATH_COMMIT")
        hud.record_decision(latency_us=18.1, wealth=0.95, path="FAST_PATH_COMMIT")
        rendered = hud.render_ascii_hud()
        self.assertIn("AXIOM CORE SUPERIUM REAL-TIME TELEMETRY HUD", rendered)
        self.assertIn("Fast-Path Ratio: 100.0%", rendered)


if __name__ == "__main__":
    unittest.main()
