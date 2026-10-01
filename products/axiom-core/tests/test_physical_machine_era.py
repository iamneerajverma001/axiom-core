"""
Unit tests for Axiom Core Physical Machine Era (v3.0):
1. Control Lyapunov-Barrier Function Interlock (CLBF + Martingales)
2. MAVLink 2.0 Flight Controller Wire Serializer & Parser
3. Dynamic Vision Sensor (DVS) Event Camera Ingestor
4. Axiom Silicon Synthesizer (Axiom-V Verilog HDL)
5. Multi-Target Policy Compiler (C++20, C23, Verilog, Lean 4)
6. 3D Swarm Fleet Coordinator (Reynolds Flocking + CRDT Gossip)
"""

import os
import sys
import unittest
import struct
import math

pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from axiom_core import (
    LyapunovBarrierInterlock,
    State3D,
    ControlInput3D,
    Obstacle3D,
    MavlinkBridge,
    AttitudeTarget,
    AttitudeTelemetry,
    EventCameraDvs,
    DvsEvent,
    FpgaVerilogSynthesizer,
    SynthOptions,
    AxiomPolicyCompiler,
    SwarmFleetCoordinator,
    VilleSafetyCertifier,
    CertificationSpec,
    Sim2RealBridge,
    SimCommand,
    SimState,
    BipedalLocomotionReflex,
    ComState,
    FootContact,
    ManipulatorReflexKernel,
    JointState,
    CartPose,
    EdgeDaemonService,
    DaemonConfig
)

class TestPhysicalMachineEra(unittest.TestCase):
    def test_lyapunov_barrier_interlock_safe_flight(self):
        barrier = LyapunovBarrierInterlock(alpha=0.01, gamma=2.0, lambda_bet=1.5)
        state = State3D(x=0.0, y=50.0, z=0.0, vx=2.0, vy=0.0, vz=0.0)
        u = ControlInput3D(roll_torque=0.1, pitch_torque=0.0, yaw_torque=0.0, thrust=9.8)
        obstacles = [Obstacle3D(x=100.0, y=50.0, z=0.0, safe_radius=5.0)]

        res = barrier.evaluate(state, u, obstacles, dt=0.05)
        self.assertTrue(res.is_safe)
        self.assertFalse(res.interlock_triggered)
        self.assertAlmostEqual(res.projected_u.thrust, 9.8, places=2)

    def test_lyapunov_barrier_interlock_collision_evasion(self):
        barrier = LyapunovBarrierInterlock(alpha=0.01, gamma=2.0, lambda_bet=2.0)
        # Flying at high speed directly towards obstacle
        state = State3D(x=0.0, y=50.0, z=0.0, vx=20.0, vy=0.0, vz=0.0)
        u = ControlInput3D(roll_torque=0.0, pitch_torque=0.0, yaw_torque=0.0, thrust=9.8)
        obstacles = [Obstacle3D(x=3.0, y=50.0, z=0.0, safe_radius=5.0)] # Imminent penetration

        res = barrier.evaluate(state, u, obstacles, dt=0.05)
        # Should trigger interlock or increase wealth
        self.assertTrue(res.martingale_wealth > 1.0 or res.interlock_triggered)
        if res.interlock_triggered:
            # Thrust and repulsive torque must be actively engaged
            self.assertTrue(res.projected_u.thrust >= 15.0)

    def test_mavlink_bridge_serialization_and_parsing(self):
        target = AttitudeTarget(
            time_boot_ms=123456,
            q=(1.0, 0.0, 0.0, 0.0),
            body_roll_rate=0.05,
            body_pitch_rate=-0.08,
            body_yaw_rate=0.01,
            thrust=0.82
        )
        packet = MavlinkBridge.serialize_attitude_target(
            sys_id=1, comp_id=1, seq=10, target=target
        )
        self.assertEqual(packet[0], 0xFD) # MAVLink 2.0 Magic byte
        self.assertTrue(len(packet) > 30)

        # Build a valid synthetic ATTITUDE packet (MsgID = 30)
        # MsgID 30: time_boot_ms(I), roll(f), pitch(f), yaw(f), rollspeed(f), pitchspeed(f), yawspeed(f)
        att_payload = struct.pack("<Iffffff", 5000, 0.12, -0.05, 1.57, 0.01, -0.02, 0.005)
        header = struct.pack("<BBBBBBB3s", 0xFD, len(att_payload), 0, 0, 1, 2, 1, struct.pack("<I", 30)[:3])
        packet_no_crc = header + att_payload
        from axiom_core.mavlink_bridge import crc_calculate
        crc = crc_calculate(packet_no_crc[1:])
        full_att_packet = packet_no_crc + struct.pack("<H", crc)

        parsed = MavlinkBridge.parse_attitude_packet(full_att_packet)
        self.assertIsNotNone(parsed)
        sys_id, telem = parsed
        self.assertEqual(sys_id, 2)
        self.assertAlmostEqual(telem.roll, 0.12, places=2)
        self.assertAlmostEqual(telem.yaw, 1.57, places=2)

    def test_event_camera_dvs_ingestion(self):
        dvs = EventCameraDvs(tau_us=10000.0)
        events = [
            DvsEvent(x=100, y=100, timestamp_us=1000, polarity=1),
            DvsEvent(x=100, y=100, timestamp_us=1050, polarity=1),
            DvsEvent(x=500, y=400, timestamp_us=1100, polarity=-1),
        ]
        dvs.ingest_batch(events)
        tensor128 = dvs.extract_128d_tensor(current_time_us=2000)
        self.assertEqual(len(tensor128), 128)
        self.assertTrue(any(v > 0.0 for v in tensor128))
        self.assertTrue(all(-1.0 <= v <= 1.0 for v in tensor128))

    def test_fpga_verilog_synthesizer(self):
        synth = FpgaVerilogSynthesizer()
        opt = SynthOptions(module_name="axiom_test_silicon", neuron_count=128)
        verilog_code = synth.synthesize_lif_verilog(opt)
        self.assertIn("module axiom_test_silicon", verilog_code)
        self.assertIn("v_mem", verilog_code)
        self.assertIn("estop_tripwire", verilog_code)
        self.assertIn("BARRIER_THRESH", verilog_code)

        axi_code = synth.synthesize_axi_lite_wrapper("axiom_axi_test")
        self.assertIn("module axiom_axi_test", axi_code)
        self.assertIn("s_axi_aclk", axi_code)

    def test_multi_target_compiler(self):
        schema = {
            "domain": "AutonomousFlightGrid",
            "conformal_alpha": 0.005,
            "sectors": [
                {
                    "sector_id": 1,
                    "name": "KinematicSector",
                    "leaves": [
                        {"leaf_id": 101, "name": "Cruising", "description": "Normal cruising"},
                        {"leaf_id": 102, "name": "CollisionEvade", "description": "Emergency evasion"}
                    ]
                }
            ]
        }
        compiler = AxiomPolicyCompiler()

        # Target C++20
        cpp_code = compiler.compile(schema, target="cpp20")
        self.assertIn("#pragma once", cpp_code)
        self.assertIn("CONFORMAL_ALPHA = 0.005f", cpp_code)

        # Target C23
        c23_code = compiler.compile(schema, target="c23")
        self.assertIn("/* Pure Freestanding C23", c23_code)
        self.assertIn("AXIOM_CONFORMAL_ALPHA 0.005f", c23_code)

        # Target Verilog
        v_code = compiler.compile(schema, target="verilog")
        self.assertIn("module autonomousflightgrid_gate", v_code)
        self.assertIn("BARRIER_THRESH", v_code)

        # Target Lean 4
        lean_code = compiler.compile(schema, target="lean4")
        self.assertIn("import Mathlib.Probability.Martingale.Basic", lean_code)
        self.assertIn("villes_maximal_inequality", lean_code)

    def test_swarm_fleet_coordinator_dynamics(self):
        swarm = SwarmFleetCoordinator(drone_count=5)
        self.assertEqual(len(swarm.drones), 5)

        # Test initial V-Formation step
        step_res = swarm.step_simulation(dt=0.05)
        self.assertEqual(step_res["formation"], "V_FORMATION")
        self.assertEqual(step_res["drone_count"], 5)
        self.assertGreaterEqual(step_res["avg_martingale_wealth"], 1.0)

        # Switch to Orbital Shield
        swarm.set_formation_mode("ORBITAL_SHIELD")
        step_res_orbit = swarm.step_simulation(dt=0.05)
        self.assertEqual(step_res_orbit["formation"], "ORBITAL_SHIELD")

        # Switch to Dispersal
        swarm.set_formation_mode("DISPERSAL")
        step_res_disp = swarm.step_simulation(dt=0.05)
        self.assertEqual(step_res_disp["formation"], "DISPERSAL")

    def test_ville_safety_certifier_execution(self):
        spec = CertificationSpec(stress_trials=500)
        report = VilleSafetyCertifier.certify(spec)
        self.assertTrue(report.certified)
        self.assertEqual(report.violations_penetrated, 0)
        self.assertGreater(report.interlocks_engaged, 0)
        self.assertIn("ISO-26262 ASIL-D", report.compliance_standards)
        self.assertTrue(len(report.merkle_proof_root) > 0)

    def test_sim2real_bridge_packet_serialization(self):
        cmd = SimCommand(
            timestamp_ns=1000000,
            motor_torques=(0.8, 0.75, 0.75, 0.8),
            estop_engaged=False,
            safety_interlock_active=True,
            martingale_wealth=1.5,
            sequence_id=42
        )
        cmd_bytes = Sim2RealBridge.serialize_command(cmd)
        self.assertTrue(len(cmd_bytes) > 20)

        # Build synthetic state packet
        import struct
        state_bytes = struct.pack(
            Sim2RealBridge.STATE_FMT,
            0x53494D32, # SIM2
            2000000,    # ts_ns
            10.0, 20.0, 30.0, # pos
            1.0, 2.0, 3.0,    # lin_vel
            1.0, 0.0, 0.0, 0.0, # quat
            0.1, 0.2, 0.3,    # ang_vel
            *( [5.0] * 16 ),  # lidar
            101               # seq
        )
        sim_state = Sim2RealBridge.deserialize_state(state_bytes)
        self.assertIsNotNone(sim_state)
        self.assertEqual(sim_state.sequence_id, 101)
        self.assertAlmostEqual(sim_state.position[0], 10.0, places=2)
        self.assertEqual(len(sim_state.lidar_distances), 16)

    def test_fpga_verilog_synthesizer_testbench(self):
        opt = SynthOptions(module_name="axiom_tb_test")
        tb_code = FpgaVerilogSynthesizer.synthesize_testbench(opt)
        self.assertIn("module tb_axiom_tb_test", tb_code)
        self.assertIn("$finish", tb_code)

    def test_bipedal_locomotion_reflex(self):
        biped = BipedalLocomotionReflex(height=0.85, alpha=0.001)
        com = ComState(x=0.0, y=0.0, z=0.85, vx=0.0, vy=0.0, vz=0.0)
        foot = FootContact(x=0.0, y=0.0, z=0.0, length=0.24, width=0.12, friction_coeff=0.6)

        # Equilibrium stance
        res_eq = biped.evaluate(com, foot, dt=0.005)
        self.assertTrue(res_eq.is_stable)
        self.assertFalse(res_eq.capture_step_required)
        self.assertGreaterEqual(res_eq.zmp_margin, 0.0)

        # Severe push perturbation (kick Vx = 2.0 m/s)
        com.vx = 2.0
        res_kick = biped.evaluate(com, foot, dt=0.005)
        self.assertTrue(res_kick.capture_step_required)
        self.assertFalse(res_kick.is_stable)
        self.assertGreater(res_kick.recommended_step_x, 0.5) # Reaches out to intercept CoM fall

    def test_manipulator_reflex_kernel(self):
        arm = ManipulatorReflexKernel(alpha=0.001, contact_thresh=12.0)
        state = JointState(q=[0.0, 0.5, -0.5, 0.0, 0.0, 0.0], tau=[0.0] * 6)
        target = CartPose(x=0.5, y=0.1, z=0.4)

        # Free space trajectory
        res = arm.evaluate(state, target, dt=0.005)
        self.assertTrue(res.is_safe)
        self.assertFalse(res.collision_e_stop)
        self.assertEqual(len(res.cmd_torques), 6)

        # External human collision impact (tau1 = 35 Nm > 12 Nm)
        state.tau[1] = 35.0
        coll_res = arm.evaluate(state, target, dt=0.005)
        self.assertGreater(coll_res.martingale_wealth, 1.0)

    def test_edge_daemon_service(self):
        daemon = EdgeDaemonService(DaemonConfig(enable_watchdog=True))
        self.assertTrue(daemon.start())
        for _ in range(25):
            daemon.step_cycle(dt=0.001)

        m = daemon.get_metrics()
        self.assertEqual(m.total_decisions, 25)
        self.assertEqual(m.watchdog_heartbeats, 25)
        self.assertTrue(m.is_healthy)
        self.assertTrue(len(daemon.flight_recorder.root_hash) > 0)
        daemon.stop()

if __name__ == "__main__":
    unittest.main()
