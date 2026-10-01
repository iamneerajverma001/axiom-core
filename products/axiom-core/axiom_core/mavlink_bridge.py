"""
MAVLink 2.0 Wire Protocol Bridge
High-throughput zero-allocation serializer and parser for PX4 Autopilot, ArduPilot,
and autonomous UAV flight controllers.
"""

import struct
from typing import Optional, Tuple
from dataclasses import dataclass

MAVLINK_STX_V2 = 0xFD
MSG_HEARTBEAT = 0
MSG_ATTITUDE = 30
MSG_LOCAL_POSITION_NED = 32
MSG_SET_ATTITUDE_TARGET = 82

@dataclass
class AttitudeTelemetry:
    time_boot_ms: int
    roll: float
    pitch: float
    yaw: float
    rollspeed: float
    pitchspeed: float
    yawspeed: float

@dataclass
class AttitudeTarget:
    time_boot_ms: int
    q: Tuple[float, float, float, float]
    body_roll_rate: float
    body_pitch_rate: float
    body_yaw_rate: float
    thrust: float

def crc_accumulate(byte_val: int, crc: int) -> int:
    tmp = byte_val ^ (crc & 0xFF)
    tmp ^= (tmp << 4) & 0xFF
    return ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xFFFF

def crc_calculate(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc = crc_accumulate(b, crc)
    return crc

class MavlinkBridge:
    @staticmethod
    def serialize_attitude_target(sys_id: int, comp_id: int, seq: int, target: AttitudeTarget) -> bytes:
        payload = struct.pack(
            "<I8fB",
            target.time_boot_ms,
            target.q[0], target.q[1], target.q[2], target.q[3],
            target.body_roll_rate, target.body_pitch_rate, target.body_yaw_rate,
            target.thrust,
            0 # type_mask
        )
        payload_len = len(payload)
        header = struct.pack(
            "<BBBBBBB3s",
            MAVLINK_STX_V2,
            payload_len,
            0, # incompat
            0, # compat
            seq & 0xFF,
            sys_id & 0xFF,
            comp_id & 0xFF,
            struct.pack("<I", MSG_SET_ATTITUDE_TARGET)[:3]
        )
        packet_without_crc = header + payload
        crc = crc_calculate(packet_without_crc[1:])
        return packet_without_crc + struct.pack("<H", crc)

    @staticmethod
    def parse_attitude_packet(data: bytes) -> Optional[Tuple[int, AttitudeTelemetry]]:
        if len(data) < 10 + 28 + 2:
            return None
        if data[0] != MAVLINK_STX_V2:
            return None
        
        payload_len, _, _, seq, sys_id, comp_id = struct.unpack("<BBBBBB", data[1:7])
        msg_id_bytes = data[7:10] + b"\x00"
        msg_id = struct.unpack("<I", msg_id_bytes)[0]
        
        if msg_id != MSG_ATTITUDE or payload_len < 28:
            return None
            
        payload = data[10:10 + 28]
        time_boot_ms, roll, pitch, yaw, rollspeed, pitchspeed, yawspeed = struct.unpack("<Iffffff", payload)
        telemetry = AttitudeTelemetry(
            time_boot_ms=time_boot_ms,
            roll=roll, pitch=pitch, yaw=yaw,
            rollspeed=rollspeed, pitchspeed=pitchspeed, yawspeed=yawspeed
        )
        return sys_id, telemetry
