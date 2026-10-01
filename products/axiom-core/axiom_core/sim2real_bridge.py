"""
Zero-Allocation Sim2Real High-Speed Telemetry Bridge
Connects Axiom Core directly to robotics simulators (Isaac Sim, MuJoCo, Gazebo, AirSim, PX4 SITL)
over binary UDP sockets or memory-mapped files.
"""

import struct
from typing import Optional, Tuple, List
from dataclasses import dataclass

SIM2REAL_MAGIC = 0x53494D32 # "SIM2"

@dataclass
class SimState:
    timestamp_ns: int
    position: Tuple[float, float, float]
    linear_vel: Tuple[float, float, float]
    orientation_quat: Tuple[float, float, float, float]
    angular_vel: Tuple[float, float, float]
    lidar_distances: List[float]
    sequence_id: int

@dataclass
class SimCommand:
    timestamp_ns: int
    motor_torques: Tuple[float, float, float, float]
    estop_engaged: bool
    safety_interlock_active: bool
    martingale_wealth: float
    sequence_id: int

class Sim2RealBridge:
    # State format: magic(I), timestamp(Q), pos(3f), lin_vel(3f), quat(4f), ang_vel(3f), lidar(16f), seq(I)
    STATE_FMT = "<IQ3f3f4f3f16fI"
    # Command format: magic(I), timestamp(Q), torques(4f), estop(B), interlock(B), wealth(f), seq(I)
    CMD_FMT = "<IQ4fBBfI"

    @classmethod
    def serialize_command(cls, cmd: SimCommand) -> bytes:
        return struct.pack(
            cls.CMD_FMT,
            SIM2REAL_MAGIC,
            cmd.timestamp_ns,
            cmd.motor_torques[0], cmd.motor_torques[1], cmd.motor_torques[2], cmd.motor_torques[3],
            1 if cmd.estop_engaged else 0,
            1 if cmd.safety_interlock_active else 0,
            cmd.martingale_wealth,
            cmd.sequence_id
        )

    @classmethod
    def deserialize_state(cls, data: bytes) -> Optional[SimState]:
        expected_len = struct.calcsize(cls.STATE_FMT)
        if len(data) < expected_len:
            return None

        unpacked = struct.unpack(cls.STATE_FMT, data[:expected_len])
        magic = unpacked[0]
        if magic != SIM2REAL_MAGIC:
            return None

        ts_ns = unpacked[1]
        pos = (unpacked[2], unpacked[3], unpacked[4])
        lin_vel = (unpacked[5], unpacked[6], unpacked[7])
        quat = (unpacked[8], unpacked[9], unpacked[10], unpacked[11])
        ang_vel = (unpacked[12], unpacked[13], unpacked[14])
        lidar = list(unpacked[15:31])
        seq = unpacked[31]

        return SimState(
            timestamp_ns=ts_ns,
            position=pos,
            linear_vel=lin_vel,
            orientation_quat=quat,
            angular_vel=ang_vel,
            lidar_distances=lidar,
            sequence_id=seq
        )
