import unittest
import math
from axiom_core.seven_axis_arm import SevenAxisArm


class TestSevenAxisArm(unittest.TestCase):
    def setUp(self):
        self.arm = SevenAxisArm(alpha=0.001, tau_shock_thresh=15.0)

    def test_forward_kinematics(self):
        fk = self.arm.forward_kinematics()
        self.assertIn("base", fk)
        self.assertIn("shoulder", fk)
        self.assertIn("elbow", fk)
        self.assertIn("wrist", fk)
        self.assertIn("tcp", fk)

        # Base is at origin
        self.assertEqual(fk["base"], (0.0, 0.0, 0.0))
        # Shoulder has z = d1
        self.assertAlmostEqual(fk["shoulder"][2], 0.333, places=3)
        # TCP distance from base must not exceed max reach
        tcp_dist = math.sqrt(sum(x**2 for x in fk["tcp"]))
        self.assertLessEqual(tcp_dist, self.arm.max_reach + 0.05)

    def test_jacobian_and_manipulability(self):
        J = self.arm.compute_jacobian()
        self.assertEqual(len(J), 3)
        self.assertEqual(len(J[0]), 7)

        # In standard ready configuration, arm should not be in singularity
        step_res = self.arm.step(target_pos=(0.0, 0.2, 0.8))
        self.assertGreater(step_res["manipulability"], 0.001)
        self.assertLess(step_res["latency_us"], 5000.0) # < 5.0 ms in pure Python interpreter

    def test_submillimeter_trajectory_tracking(self):
        p0 = self.arm.forward_kinematics()["tcp"]
        # Sub-millimeter task target near current position
        target = (p0[0] + 0.015, p0[1] + 0.010, p0[2] - 0.015)
        # Run closed-loop tracking for 150 steps
        for _ in range(150):
            res = self.arm.step(target_pos=target, dt=0.005)

        # Verifies precision convergence (< 1.0 mm)
        self.assertLess(res["tracking_error_mm"], 1.0)

    def test_nullspace_elbow_obstacle_evasion(self):
        fk0 = self.arm.forward_kinematics()
        p_elbow0 = fk0["elbow"]

        # Place dynamic obstacle directly near elbow
        obs_pos = (p_elbow0[0], p_elbow0[1] + 0.05, p_elbow0[2])
        target_tcp = fk0["tcp"]

        # Step with obstacle
        res = self.arm.step(target_pos=target_tcp, obstacle_pos=obs_pos, dt=0.005)

        # Nullspace must compute elbow distance
        self.assertIsNotNone(res["elbow_obs_dist"])
        self.assertFalse(res["collision_e_stop"])

    def test_ville_shock_martingale_and_compliant_backdrive(self):
        p0 = self.arm.forward_kinematics()["tcp"]
        # Nominal motion: wealth remains low
        res_nominal = self.arm.step(target_pos=p0, external_shock=0.5)
        self.assertFalse(res_nominal["collision_e_stop"])
        self.assertLess(res_nominal["martingale_wealth"], self.arm.get_stopping_barrier())

        # Inject violent 30 Nm kinetic strike
        res_shock = self.arm.step(target_pos=p0, external_shock=30.0)
        self.assertTrue(res_shock["collision_e_stop"])
        # Commanded velocities must be zeroed for safety
        for qd in res_shock["cmd_qd"]:
            self.assertEqual(qd, 0.0)

    def test_128d_tensor_encoding(self):
        tensor = self.arm.encode_128d_tensor()
        self.assertEqual(len(tensor), 128)
        # Joint 1 angle must be encoded
        self.assertAlmostEqual(tensor[0], self.arm.q[0] / 3.14159, places=4)


if __name__ == "__main__":
    unittest.main()
