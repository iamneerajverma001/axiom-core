import unittest
import math
import sys
import os

core_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if core_path not in sys.path:
    sys.path.insert(0, core_path)

from axiom_core.full_humanoid import (
    FullHumanoidReflex,
    HumanoidState,
    KeypointFrames,
    WholeBodyCommand,
    HEAD_YAW, HEAD_PITCH,
    TORSO_YAW, TORSO_PITCH, TORSO_ROLL,
    L_SHOULDER_PITCH, L_ELBOW_PITCH,
    R_SHOULDER_PITCH, R_ELBOW_PITCH,
    L_KNEE_PITCH, R_KNEE_PITCH,
    L_ANKLE_PITCH, R_ANKLE_PITCH,
    DOF
)


class TestFullHumanoid(unittest.TestCase):
    def setUp(self):
        self.humanoid = FullHumanoidReflex(height=0.88, alpha=0.001, tau_shock_thresh=45.0)

    def test_whole_body_forward_kinematics(self):
        state = HumanoidState()
        kf = self.humanoid.forward_kinematics(state)

        # Check keypoint existence and upright structure
        self.assertAlmostEqual(kf.pelvis[2], 0.88, places=2)
        self.assertGreater(kf.chest[2], kf.pelvis[2])
        self.assertGreater(kf.head[2], 1.50)

        # Check dual arm symmetry
        self.assertGreater(kf.left_hand[1], 0.15)
        self.assertLess(kf.right_hand[1], -0.15)

        # Check feet placement
        self.assertAlmostEqual(kf.left_ankle[2], 0.03, places=2)
        self.assertAlmostEqual(kf.right_ankle[2], 0.03, places=2)

        # Whole body CoM must be between pelvis and chest
        self.assertGreater(kf.whole_body_com[2], 0.70)
        self.assertLess(kf.whole_body_com[2], 1.10)

    def test_whole_body_com_and_zmp_equilibrium(self):
        state = HumanoidState()
        cmd = self.humanoid.evaluate(state, dt=0.005)

        # In nominal quiet standing, robot is stable and inside support polygon
        self.assertGreater(cmd.zmp_margin, 0.02)
        self.assertFalse(cmd.capture_step_required)
        self.assertFalse(cmd.ice_slip_detected)
        self.assertFalse(cmd.fall_e_stop_active)

    def test_violent_push_disturbance_and_capture_step(self):
        state = HumanoidState()
        # High forward velocity kick
        state.pelvis_vel = (1.2, 0.0, 0.0)
        state.pelvis_acc = (3.5, 0.0, 0.0)

        cmd = self.humanoid.evaluate(state, dt=0.005)

        # Capture Point escapes support polygon -> emergency capture step recommended
        self.assertTrue(cmd.capture_step_required)
        self.assertGreater(cmd.recommended_step[0], 0.20)

    def test_low_friction_ice_slip_recovery(self):
        state = HumanoidState()
        # On ice: friction = 0.08
        state.ground_friction = 0.08
        state.pelvis_acc = (1.5, 0.8, 0.0) # Lateral shear acceleration

        cmd = self.humanoid.evaluate(state, dt=0.005)

        # Coulomb friction cone violation detected
        self.assertTrue(cmd.ice_slip_detected)
        self.assertTrue(cmd.capture_step_required)

    def test_heavy_payload_dual_arm_box_lift(self):
        state = HumanoidState()
        state.is_payload_grasped = True
        state.payload_mass = 20.0 # 20 kg heavy box

        kf_loaded = self.humanoid.forward_kinematics(state)
        # Whole body CoM should be shifted forward
        self.assertGreater(kf_loaded.whole_body_com[0], -0.01)

        cmd = self.humanoid.evaluate(state, dt=0.005)
        # Spine pitch torque should be commanded to counteract load
        self.assertNotEqual(cmd.cmd_tau[TORSO_PITCH], 0.0)

    def test_ville_shock_martingale_and_compliant_damping(self):
        state = HumanoidState()
        # Nominal step has low wealth
        cmd_nominal = self.humanoid.evaluate(state, dt=0.005)
        self.assertFalse(cmd_nominal.fall_e_stop_active)
        self.assertLess(cmd_nominal.martingale_wealth, 1000.0)

        # Catastrophic shock spike on knee (60 Nm > 45 Nm threshold)
        state.tau_ext[L_KNEE_PITCH] = 60.0
        cmd_shock = self.humanoid.evaluate(state, dt=0.005)

        # Martingale breaches stopping barrier and trips E-STOP
        self.assertTrue(cmd_shock.fall_e_stop_active)
        self.assertEqual(cmd_shock.cmd_qd[0], 0.0)
        self.assertGreaterEqual(cmd_shock.martingale_wealth, 1000.0)

    def test_clbf_joint_limit_invariance(self):
        state = HumanoidState()
        # Push knee to upper limit
        state.q[L_KNEE_PITCH] = 2.19 # Near 2.2 max limit
        cmd = self.humanoid.evaluate(state, dt=0.005)

        self.assertLessEqual(cmd.clbf_barrier_value, 0.05)

    def test_128d_tensor_ipc_encoding(self):
        state = HumanoidState()
        state.payload_mass = 12.0
        state.is_payload_grasped = True
        kf = self.humanoid.forward_kinematics(state)
        cmd = self.humanoid.evaluate(state, dt=0.005)

        tensor = self.humanoid.extract_128d_tensor(state, kf, cmd)
        self.assertEqual(len(tensor), 128)
        self.assertEqual(tensor[88], 12.0) # Payload mass
        self.assertEqual(tensor[89], 1.0)  # Payload grasped flag
        self.assertGreater(tensor[66], 0.8) # Pelvis z


if __name__ == "__main__":
    unittest.main()
