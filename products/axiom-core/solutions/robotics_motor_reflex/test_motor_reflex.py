"""
Tests for Robotics Motor Reflex Arc
"""

import sys
import os
import unittest
import time

pkg_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from solutions.robotics_motor_reflex.motor_reflex import MotorReflexArc, JointTelemetry

class TestMotorReflexArc(unittest.TestCase):
    def setUp(self):
        self.reflex = MotorReflexArc(
            max_torque_nm=30.0,
            emergency_stop_distance_m=0.20 # 20cm
        )

    def test_nominal_motor_cycle(self):
        telem = JointTelemetry(
            joint_id=1,
            commanded_torque_nm=12.5,
            measured_torque_nm=12.4,
            angular_velocity_rad_s=1.5,
            proximity_distance_m=1.2 # Clean open space
        )
        res = self.reflex.evaluate_cycle(telem)
        self.assertEqual(res["status"], "NORMAL_CONTROL")
        self.assertAlmostEqual(res["commanded_torque"], 12.5)
        self.assertLess(res["latency_us"], 50.0)

    def test_torque_saturation_clipping(self):
        # Commanded torque 50Nm exceeds limit 30Nm, measured torque follows at 30Nm
        telem = JointTelemetry(
            joint_id=2,
            commanded_torque_nm=50.0,
            measured_torque_nm=30.0,
            angular_velocity_rad_s=2.0,
            proximity_distance_m=0.8
        )
        res = self.reflex.evaluate_cycle(telem)
        self.assertEqual(res["status"], "TORQUE_CLIPPED")
        self.assertAlmostEqual(res["commanded_torque"], 30.0)

    def test_mechanical_jam_damping(self):
        # Commanded 30Nm but measured is 5Nm (severe 25Nm delta triggers 50% damping)
        telem = JointTelemetry(
            joint_id=2,
            commanded_torque_nm=30.0,
            measured_torque_nm=5.0,
            angular_velocity_rad_s=0.1,
            proximity_distance_m=0.8
        )
        res = self.reflex.evaluate_cycle(telem)
        self.assertAlmostEqual(res["commanded_torque"], 15.0)

    def test_proximity_estop(self):
        # Obstacle detected at 10cm (trigger distance is 20cm)
        telem = JointTelemetry(
            joint_id=3,
            commanded_torque_nm=15.0,
            measured_torque_nm=15.0,
            angular_velocity_rad_s=1.0,
            proximity_distance_m=0.10
        )
        res = self.reflex.evaluate_cycle(telem)
        self.assertIn("COLLISION_AVOIDANCE_ESTOP", res["status"])
        self.assertEqual(res["commanded_torque"], 0.0)

        # Subsequent cycles must stay latched
        telem2 = JointTelemetry(joint_id=3, commanded_torque_nm=10.0, measured_torque_nm=0.0, angular_velocity_rad_s=0.0, proximity_distance_m=1.0)
        res2 = self.reflex.evaluate_cycle(telem2)
        self.assertEqual(res2["status"], "EMERGENCY_STOP_LATCHED")
        self.assertEqual(res2["commanded_torque"], 0.0)

    def test_1000hz_control_loop_benchmark(self):
        # 1,000 cycles must run well under 1,000ms (budget: < 1ms per cycle)
        t0 = time.perf_counter()
        count = 1000
        for i in range(count):
            telem = JointTelemetry(
                joint_id=i % 6,
                commanded_torque_nm=10.0,
                measured_torque_nm=10.0,
                angular_velocity_rad_s=1.0,
                proximity_distance_m=0.9
            )
            self.reflex.evaluate_cycle(telem)
        elapsed = time.perf_counter() - t0
        rate = count / elapsed
        print(f"\nRobotics Motor Reflex: {count:,} cycles in {elapsed*1000:.2f}ms ({rate:,.0f} Hz / loop)")
        self.assertGreater(rate, 10_000) # Exceeds 10,000 Hz, easily meeting 1,000Hz SLA

if __name__ == "__main__":
    unittest.main()
