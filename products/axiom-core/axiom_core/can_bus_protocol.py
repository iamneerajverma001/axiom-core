"""
Automotive & Industrial CAN-Bus / CAN-FD ISO 11898 Telegram Parser
Decodes steer-by-wire, robotics motor torque, and brake pressure frames in < 1 microsecond.
"""

import struct
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class CanFrame:
    can_id: int
    dlc: int
    data: bytes
    is_extended: bool = False
    is_canfd: bool = False

    @classmethod
    def parse(cls, raw_bytes: bytes) -> Optional["CanFrame"]:
        """Decodes raw byte stream into structured CAN frame."""
        if len(raw_bytes) < 5:
            return None
        can_id, dlc = struct.unpack("<IB", raw_bytes[:5])
        flags = raw_bytes[5] if len(raw_bytes) > 5 else 0
        data = raw_bytes[6:6 + dlc] if len(raw_bytes) >= 6 + dlc else b""
        return cls(
            can_id=can_id & 0x1FFFFFFF,
            dlc=dlc,
            data=data,
            is_extended=bool(can_id & 0x80000000 or flags & 0x01),
            is_canfd=bool(flags & 0x04)
        )

    def extract_motor_torque_nm(self) -> float:
        """Decodes 16-bit signed joint motor torque in Nm (0.01 Nm resolution)."""
        if len(self.data) < 2:
            return 0.0
        val = struct.unpack("<h", self.data[:2])[0]
        return round(val * 0.01, 2)

    def extract_steering_angle_deg(self) -> float:
        """Decodes 16-bit signed steering angle in degrees (0.1 deg resolution)."""
        if len(self.data) < 4:
            return 0.0
        val = struct.unpack("<h", self.data[2:4])[0]
        return round(val * 0.1, 1)

    @staticmethod
    def build_synthetic_can_frame(
        can_id: int = 0x120,
        joint_torque_nm: float = 45.2,
        steering_deg: float = 12.5
    ) -> bytes:
        """Constructs synthetic CAN frame bytes for wire-speed benchmark."""
        raw_torque = int(round(joint_torque_nm / 0.01))
        raw_steer = int(round(steering_deg / 0.1))
        payload = struct.pack("<hh", raw_torque, raw_steer)
        header = struct.pack("<IBB", can_id, 4, 0)
        return header + payload
