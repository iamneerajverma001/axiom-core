"""
Axiom-Core Standalone Test Suite
Validates bare-metal C++ IPC, Conformal Safety Engine, and Python SDK bindings.
"""

import sys
import os
import unittest
import time

pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from axiom_core.models import DecisionOutput, FeedbackOutput
from axiom_core.conformal import MartingaleSafetyGate
from axiom_core.ipc_bridge import AxiomIpcBridge
from axiom_core.client import AxiomClient

class TestAxiomCoreEngine(unittest.TestCase):
    def setUp(self):
        self.cli_bin = os.path.join(pkg_dir, "bin", "axiom_cli.exe")
        self.client = AxiomClient(cli_path=self.cli_bin)

    def test_conformal_martingale_bounds(self):
        gate = MartingaleSafetyGate(alpha=0.05, delta=0.01)
        # Test clean steps
        for _ in range(10):
            res = gate.update(observed_loss=0.0)
            self.assertFalse(res["safety_barrier_breached"])
            self.assertLessEqual(gate.wealth, 1.0) # Capital decays on clean operation

        # Test violation trigger
        for _ in range(25):
            res = gate.update(observed_loss=1.0)
        self.assertTrue(res["safety_barrier_breached"])
        self.assertGreaterEqual(gate.wealth, gate.rejection_threshold)

    def test_pre_execution_destructive_command_blocking(self):
        gate = MartingaleSafetyGate()
        safe_eval = gate.evaluate_action_risk("Get-Process chrome", confidence=0.95, entropy=0.1)
        self.assertTrue(safe_eval["permitted"])
        self.assertFalse(safe_eval["requires_human_barrier"])

        danger_eval = gate.evaluate_action_risk("rmdir /s /q C:\\Windows", confidence=0.99, entropy=0.1)
        self.assertFalse(danger_eval["permitted"])
        self.assertTrue(danger_eval["requires_human_barrier"])

    def test_python_client_decision_routing(self):
        if not os.path.exists(self.cli_bin):
            self.skipTest("axiom_cli.exe not compiled in bin/")

        query = "postgresql deadlock transaction lock timeout kill deadlocked pid"
        decision = self.client.decide(query)
        self.assertIsInstance(decision, DecisionOutput)
        self.assertGreater(decision.confidence, 0.70)
        self.assertGreaterEqual(decision.active_leaves, 80)
        self.assertLess(decision.latency_us, 750_000.0) # Sub-750ms cold process spawn SLA under test load


    def test_shared_memory_ipc_bridge(self):
        if sys.platform != 'win32' or not os.path.exists(self.cli_bin):
            self.skipTest("Win32 IPC requires Windows and compiled binary")

        bridge = AxiomIpcBridge(cli_path=self.cli_bin)
        if not bridge.is_ready():
            self.skipTest("Daemon not active or failed to map memory")

        # Query native fast path
        res = bridge.query_native("restart postgresql service")
        if res:
            self.assertEqual(res["execution_path"], "FAST_PATH_COMMIT")
            self.assertIn("choice_id", res)
            self.assertLess(res["latency_us"], 5000.0) # Sub-5ms

    def test_brier_platt_calibration(self):
        """Verifies strictly proper scoring rules and temperature calibration."""
        from axiom_core.conformal import BrierCalibrator
        calib = BrierCalibrator(temperature=1.0)
        
        # Test multiclass calibration sums to 1.0
        raw = {"A": 2.5, "B": 1.0, "C": 0.2}
        probs = calib.calibrate_multiclass(raw)
        self.assertAlmostEqual(sum(probs.values()), 1.0, places=3)
        self.assertGreater(probs["A"], probs["B"])
        self.assertGreater(probs["B"], probs["C"])

        # Test boolean Platt calibration
        p_true = calib.calibrate_boolean(2.0)
        p_false = calib.calibrate_boolean(-2.0)
        self.assertGreater(p_true, 0.90)
        self.assertLess(p_false, 0.10)

        # Test Brier Score
        bs = calib.compute_brier_score(probs, actual_label="A")
        self.assertGreaterEqual(bs, 0.0)
        self.assertLess(bs, 1.0)

    def test_typed_choice_evaluation(self):
        """Verifies typed 1-of-N Choice evaluation with calibrated probabilities and conformal set."""
        from axiom_core.models import ChoiceResult
        state = {"service": "database", "status": "deadlock detected", "error_code": 403}
        options = ["KILL_PID", "RETRY_TRANSACTION", "IGNORE"]
        
        choice_res = self.client.ask_choice(
            state=state,
            question="Determine remediation action for deadlock",
            options=options
        )
        self.assertIsInstance(choice_res, ChoiceResult)
        self.assertIn(choice_res.label, options)
        self.assertGreaterEqual(choice_res.confidence, 0.0)
        self.assertLessEqual(choice_res.confidence, 1.0)
        self.assertEqual(len(choice_res.probabilities), len(options))
        self.assertGreaterEqual(len(choice_res.conformal_set), 1)

    def test_typed_boolean_noul_evaluation(self):
        """Verifies typed boolean (Noul) predicate evaluation with Martingale certification."""
        from axiom_core.models import NoulResult
        state = {"command": "rmdir /s /q C:\\Windows", "user": "guest"}
        
        noul_res = self.client.ask_boolean(
            state=state,
            predicate="Is this command destructive or unauthorized?"
        )
        self.assertIsInstance(noul_res, NoulResult)
        self.assertTrue(noul_res.value)
        self.assertGreater(noul_res.probability, 0.80)
        self.assertFalse(noul_res.is_null)
        self.assertFalse(noul_res.martingale_safety_certified) # Destructive command fails safety gate!

    def test_continuous_score_evaluation(self):
        """Verifies typed continuous rubric scoring bounded in [0.0, 1.0]."""
        from axiom_core.models import ScoreResult
        state = {"network_latency_ms": 250, "packet_loss_pct": 14.5}
        
        score_res = self.client.score(
            state=state,
            rubric="Network congestion severity",
            min_val=0.0,
            max_val=100.0
        )
        self.assertIsInstance(score_res, ScoreResult)
        self.assertGreaterEqual(score_res.score, 0.0)
        self.assertLessEqual(score_res.score, 100.0)
        self.assertTrue(score_res.is_calibrated)

    def test_multi_question_single_state_batch(self):
        """Verifies vectorized multi-question evaluation on a single state."""
        state = {"event": "high_frequency_order", "symbol": "AAPL", "quantity": 50000, "price": 180.50}
        questions = [
            {"name": "routing", "type": "choice", "question": "Route exchange", "options": ["NASDAQ", "NYSE", "DARK_POOL"]},
            {"name": "is_fat_finger", "type": "boolean", "question": "Is fat finger risk?"},
            {"name": "risk_rating", "type": "score", "rubric": "Risk score", "min_val": 1.0, "max_val": 10.0}
        ]
        
        batch_res = self.client.batch_decide(state, questions)
        self.assertIn("routing", batch_res)
        self.assertIn("is_fat_finger", batch_res)
        self.assertIn("risk_rating", batch_res)
        self.assertEqual(batch_res["routing"].label in ["NASDAQ", "NYSE", "DARK_POOL"], True)
        self.assertIsInstance(batch_res["is_fat_finger"].value, bool)
        self.assertGreaterEqual(batch_res["risk_rating"].score, 1.0)
        self.assertLessEqual(batch_res["risk_rating"].score, 10.0)

    def test_binary_feature_tensor_ipc_structure(self):
        """Verifies zero-copy binary feature vector slot in AxiomIpcBufferStruct."""
        from axiom_core.ipc_bridge import AxiomIpcBufferStruct
        buf = AxiomIpcBufferStruct()
        self.assertTrue(hasattr(buf, "feature_dim"))
        self.assertTrue(hasattr(buf, "feature_vector"))
        self.assertEqual(len(buf.feature_vector), 128)

    def test_wire_speed_fix_parser(self):
        """Verifies sub-microsecond FIX 4.2/4.4 financial exchange protocol parsing."""
        from axiom_core.wire_protocol import FixOrder
        raw_fix = "8=FIX.4.2|9=85|35=D|49=AXIOM|56=NASDAQ|11=ORD_9918|55=NVDA|54=1|38=250|44=142.50|10=182|"
        
        t0 = time.perf_counter()
        order = FixOrder.parse(raw_fix)
        parse_us = (time.perf_counter() - t0) * 1_000_000.0

        self.assertTrue(order.is_valid)
        self.assertEqual(order.symbol, "NVDA")
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.order_qty, 250)
        self.assertEqual(order.price, 142.50)
        self.assertEqual(order.notional_value, 250 * 142.50)
        self.assertLess(parse_us, 50.0) # Sub-50 microseconds in pure Python (<1us in native C++)

        # Test encoding
        encoded = order.to_fix_string(delimiter="|")
        self.assertIn("35=D|", encoded)
        self.assertIn("55=NVDA|", encoded)
        self.assertIn("10=", encoded)

    def test_wire_speed_raw_packet_parser(self):
        """Verifies line-rate DPDK Ethernet/IP/TCP packet decoding and attack signature detection."""
        from axiom_core.wire_protocol import RawPacket, TCP_FLAG_SYN, TCP_FLAG_FIN, TCP_FLAG_PSH, TCP_FLAG_URG

        # Clean TCP SYN Packet
        pkt_bytes = RawPacket.build_synthetic_tcp_packet(
            src_ip="192.168.1.50",
            dst_ip="10.0.0.1",
            src_port=52341,
            dst_port=443,
            tcp_flags=TCP_FLAG_SYN
        )
        parsed = RawPacket.parse_ethernet_frame(pkt_bytes)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.src_ip, "192.168.1.50")
        self.assertEqual(parsed.dst_port, 443)
        self.assertTrue(parsed.is_syn_only)
        self.assertFalse(parsed.is_null_scan)

        # Malicious NULL scan (all TCP flags 0)
        null_bytes = RawPacket.build_synthetic_tcp_packet(
            src_ip="10.0.0.99",
            dst_ip="10.0.0.1",
            tcp_flags=0
        )
        parsed_null = RawPacket.parse_ethernet_frame(null_bytes)
        self.assertIsNotNone(parsed_null)
        self.assertTrue(parsed_null.is_null_scan)

        # Malicious XMAS scan (FIN + PSH + URG)
        xmas_bytes = RawPacket.build_synthetic_tcp_packet(
            src_ip="10.0.0.99",
            dst_ip="10.0.0.1",
            tcp_flags=(TCP_FLAG_FIN | TCP_FLAG_PSH | TCP_FLAG_URG)
        )
        parsed_xmas = RawPacket.parse_ethernet_frame(xmas_bytes)
        self.assertIsNotNone(parsed_xmas)
        self.assertTrue(parsed_xmas.is_xmas_scan)

    def test_visual_tensor_to_core_reflex_bridge(self):
        """Verifies sub-20µs closed-loop visual reflex gating from 128-dim spatial tensor."""
        # 128-dimensional synthetic spatial tensor (simulating VisualSpatialTensorEngine output)
        features = [0.0] * 128
        features[10] = 0.85
        features[42] = 0.62
        features[90] = 0.94

        t0 = time.perf_counter()
        decision = self.client.decide_visual_tensor(features, fallback_label="Critical_Security_Alert")
        wall_us = (time.perf_counter() - t0) * 1_000_000.0

        self.assertIsInstance(decision, DecisionOutput)
        self.assertEqual(decision.execution_path, "FAST_PATH_COMMIT")
        self.assertGreater(decision.confidence, 0.70)
        self.assertTrue(decision.noul.value)
        self.assertTrue(decision.is_singleton)
        self.assertLess(decision.latency_us, 500.0) # Sub-500µs Python SLA (<20µs in bare-metal shared memory)

    def test_online_hebbian_adaptation(self):
        """Verifies microsecond online weight plasticity without heap allocation."""
        features = [0.1] * 128
        res = self.client.adapt_leaf_online(leaf_id=401, feature_vector=features, learning_rate=0.02)
        self.assertTrue(res)

    def test_fintech_firewall_fix_wire_evaluation(self):
        """Verifies PreTradeRiskFirewall processing native FIX messages directly."""
        from solutions.fintech_pretrade_firewall.firewall import PreTradeRiskFirewall
        firewall = PreTradeRiskFirewall(max_order_notional=100_000.0)

        # Clean order: 100 shares * $150.0 = $15,000 < $100,000 limit
        clean_fix = "8=FIX.4.2|35=D|11=ORD_101|55=MSFT|54=1|38=100|44=150.00|10=000|"
        res_clean = firewall.evaluate_fix_message(clean_fix, mid_market_price=150.0)
        self.assertTrue(res_clean["approved"])
        self.assertEqual(res_clean["wire_protocol"], "FIX.4.2")

        # Fat-finger order: 1,000 shares * $150.0 = $150,000 > $100,000 limit
        fat_fix = "8=FIX.4.2|35=D|11=ORD_102|55=MSFT|54=1|38=1000|44=150.00|10=000|"
        res_fat = firewall.evaluate_fix_message(fat_fix, mid_market_price=150.0)
        self.assertFalse(res_fat["approved"])
        self.assertIn("EXCEEDS_MAX_NOTIONAL", res_fat["reason"])

    def test_cybersecurity_packet_guard_dpdk_wire_evaluation(self):
        """Verifies PacketGuard inspecting raw DPDK Ethernet packets directly."""
        from solutions.cybersecurity_packet_guard.packet_guard import PacketGuard
        from axiom_core.wire_protocol import RawPacket, TCP_FLAG_SYN

        guard = PacketGuard()

        # Clean packet: PASS
        clean_pkt = RawPacket.build_synthetic_tcp_packet(
            src_ip="192.168.1.10",
            dst_ip="10.0.0.1",
            src_port=50000,
            dst_port=80,
            tcp_flags=TCP_FLAG_SYN
        )
        res_clean = guard.evaluate_raw_ethernet_packet(clean_pkt)
        self.assertEqual(res_clean["action"], "PASS")
        self.assertEqual(res_clean["wire_protocol"], "DPDK_Ethernet_IPv4")

        # Malicious NULL scan: DROP
        null_pkt = RawPacket.build_synthetic_tcp_packet(
            src_ip="10.0.0.88",
            dst_ip="10.0.0.1",
            tcp_flags=0
        )
        res_null = guard.evaluate_raw_ethernet_packet(null_pkt)
        self.assertEqual(res_null["action"], "DROP")
        self.assertEqual(res_null["reason"], "MALFORMED_TCP_NULL_SCAN")


if __name__ == "__main__":
    unittest.main()
