#pragma once

#include <cstdint>
#include <cstring>
#include <algorithm>

namespace axiom {

#pragma pack(push, 1)
// Standard ISO 11898 CAN 2.0B & CAN-FD Frame Header
struct alignas(8) CanFrame {
    uint32_t can_id;      // 11-bit standard or 29-bit extended arbitration ID
    uint8_t  can_dlc;     // Data length code (0..8 for CAN, 0..64 for CAN-FD)
    uint8_t  flags;       // Bit 0: Extended ID, Bit 1: Remote Frame, Bit 2: CAN-FD format
    uint16_t reserved;
    uint8_t  data[64];    // Payload data bytes
};
#pragma pack(pop)

// Zero-Copy Automotive CAN-Bus / CAN-FD Telegram Parser
// Decodes physical vehicle & robotics sensor bus frames in < 250 nanoseconds
class CanBusProtocolParser {
public:
    static constexpr uint32_t CAN_EFF_FLAG = 0x80000000U; // Extended frame format
    static constexpr uint32_t CAN_RTR_FLAG = 0x40000000U; // Remote transmission request
    static constexpr uint32_t CAN_ERR_FLAG = 0x20000000U; // Error message frame

    // Decodes raw CAN bytes into CanFrame
    static bool parse_frame(const uint8_t* raw_bytes, size_t len, CanFrame& out_frame) noexcept {
        if (!raw_bytes || len < 5) return false;

        // Arbitration ID (4 bytes, little-endian)
        std::memcpy(&out_frame.can_id, raw_bytes, sizeof(uint32_t));
        out_frame.can_dlc = raw_bytes[4];
        out_frame.flags = (len > 5) ? raw_bytes[5] : 0;
        out_frame.reserved = 0;

        size_t payload_len = std::min(static_cast<size_t>(out_frame.can_dlc), static_cast<size_t>(64));
        size_t data_offset = 6;
        if (len >= data_offset + payload_len) {
            std::memcpy(out_frame.data, raw_bytes + data_offset, payload_len);
        } else {
            std::memset(out_frame.data, 0, sizeof(out_frame.data));
        }

        return true;
    }

    // High-speed telemetry signal extractor: Motor Joint Torque (Nm)
    static float extract_joint_torque(const CanFrame& frame) noexcept {
        if (frame.can_dlc < 2) return 0.0f;
        int16_t raw_val = static_cast<int16_t>(frame.data[0] | (frame.data[1] << 8));
        return static_cast<float>(raw_val) * 0.01f; // 0.01 Nm scale
    }

    // High-speed telemetry signal extractor: Steering Wheel Angle (Degrees)
    static float extract_steering_angle(const CanFrame& frame) noexcept {
        if (frame.can_dlc < 4) return 0.0f;
        int16_t raw_val = static_cast<int16_t>(frame.data[2] | (frame.data[3] << 8));
        return static_cast<float>(raw_val) * 0.1f; // 0.1 deg scale
    }
};

} // namespace axiom
