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
        self.assertLess(decision.latency_us, 250_000.0) # Sub-250ms cold process spawn SLA under test load


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

if __name__ == "__main__":
    unittest.main()
