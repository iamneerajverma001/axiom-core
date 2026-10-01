"""
Axiom Monorepo Unified Test Runner
Runs the test suites across all 3 products:
1. Axiom Core (High-speed engine, conformal safety gate, typed decisions)
2. Axiom OS (Neuromorphic workstation copilot, brain, actuator, sentinels)
3. Axiom Vision Tensor (Soft-argmax visual click tensor engine)
"""

import sys
import os
import unittest
import time

def run_suite():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    products_dir = os.path.join(root_dir, "products")

    core_dir = os.path.join(products_dir, "axiom-core")
    os_dir = os.path.join(products_dir, "axiom-os")
    vision_dir = os.path.join(products_dir, "axiom-vision-tensor")

    for p in (root_dir, core_dir, os_dir, vision_dir, os.path.join(os_dir, "src")):
        if p not in sys.path:
            sys.path.insert(0, p)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    print("=====================================================================")
    print("           AXIOM MONOREPO UNIFIED TEST RUNNER                        ")
    print("=====================================================================")

    print("[1/3] Loading Axiom Core tests...")
    core_tests = loader.discover(os.path.join(core_dir, "tests"), pattern="test_*.py")
    suite.addTests(core_tests)

    print("[2/3] Loading Axiom OS tests...")
    os_tests = loader.discover(os.path.join(os_dir, "tests"), pattern="test_axiom_os.py")
    suite.addTests(os_tests)

    print("[3/4] Loading Axiom Vision Tensor tests...")
    vision_tests = loader.discover(os.path.join(vision_dir, "tests"), pattern="test_*.py")
    suite.addTests(vision_tests)

    print("[4/4] Loading Autopilot & Showcase tests...")
    top_tests = loader.discover(os.path.join(root_dir, "tests"), pattern="test_snake_*.py")
    suite.addTests(top_tests)

    print(f"Total test cases registered: {suite.countTestCases()}")
    print("---------------------------------------------------------------------")

    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    elapsed = time.time() - start_time

    print("=====================================================================")
    print(f"Unified Test Execution Completed in {elapsed:.2f}s")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)} / {result.testsRun}")
    if result.wasSuccessful():
        print("Status: ALL SUITES PASSED (100% HEALTHY)")
        return 0
    else:
        print(f"Status: FAILED ({len(result.failures)} failures, {len(result.errors)} errors)")
        return 1

if __name__ == "__main__":
    sys.exit(run_suite())
