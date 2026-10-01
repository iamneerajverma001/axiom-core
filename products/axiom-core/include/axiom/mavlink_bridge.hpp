#pragma once
#include <cstdint>
#include <cstring>
#include <array>
#include <vector>

namespace axiom {

/**
 * @brief MAVLink 2.0 High-Throughput Wire Protocol Bridge.
 * Implements microsecond-scale serial/UDP packet parsing and serialization
 * for PX4 Autopilot, ArduPilot, and robotic UAV flight systems.
 * Zero dynamic heap allocations in critical path.
 */
class MavlinkBridge {
public:
    static constexpr uint8_t MAVLINK_STX_V2 = 0xFD; // MAVLink 2.0 packet start byte
    static constexpr size_t MAX_PAYLOAD_SIZE = 255;
    static constexpr size_t HEADER_LEN_V2 = 10;
    static constexpr size_t CRC_LEN = 2;

    enum MessageId : uint32_t {
        MSG_HEARTBEAT = 0,
        MSG_ATTITUDE = 30,
        MSG_LOCAL_POSITION_NED = 32,
        MSG_SET_ATTITUDE_TARGET = 82,
        MSG_ACTUATOR_CONTROL_TARGET = 140
    };

    struct MavlinkHeader {
        uint8_t magic{MAVLINK_STX_V2};
        uint8_t payload_len{0};
        uint8_t incompat_flags{0};
        uint8_t compat_flags{0};
        uint8_t seq{0};
        uint8_t sys_id{1};
        uint8_t comp_id{1};
        uint32_t msg_id{0}; // 24-bit integer
    };

    struct AttitudePayload {
        uint32_t time_boot_ms{0};
        float roll{0.0f};
        float pitch{0.0f};
        float yaw{0.0f};
        float rollspeed{0.0f};
        float pitchspeed{0.0f};
        float yawspeed{0.0f};
    };

    struct LocalPositionNedPayload {
        uint32_t time_boot_ms{0};
        float x{0.0f};
        float y{0.0f};
        float z{0.0f};
        float vx{0.0f};
        float vy{0.0f};
        float vz{0.0f};
    };

    struct AttitudeTargetPayload {
        uint32_t time_boot_ms{0};
        float q[4]{1.0f, 0.0f, 0.0f, 0.0f}; // Attitude quaternion
        float body_roll_rate{0.0f};
        float body_pitch_rate{0.0f};
        float body_yaw_rate{0.0f};
        float thrust{0.0f}; // 0.0 to 1.0 (or normalized Newtons)
        uint8_t type_mask{0};
    };

private:
    static uint16_t crc_accumulate(uint8_t data, uint16_t crcAccum) noexcept {
        uint8_t tmp = data ^ static_cast<uint8_t>(crcAccum & 0xff);
        tmp ^= (tmp << 4);
        return (crcAccum >> 8) ^ (static_cast<uint16_t>(tmp) << 8) ^ (static_cast<uint16_t>(tmp) << 3) ^ (static_cast<uint16_t>(tmp) >> 4);
    }

    static uint16_t crc_calculate(const uint8_t* pBuffer, size_t length) noexcept {
        uint16_t crc = 0xFFFF;
        for (size_t i = 0; i < length; ++i) {
            crc = crc_accumulate(pBuffer[i], crc);
        }
        return crc;
    }

public:
    /**
     * @brief Serializes an Attitude Target command into a MAVLink 2.0 packet buffer.
     * Zero-heap, writes into target buffer and returns byte count.
     */
    static size_t serialize_attitude_target(uint8_t sys_id, uint8_t comp_id, uint8_t seq,
                                           const AttitudeTargetPayload& payload,
                                           uint8_t* out_buffer, size_t max_buffer_len) noexcept {
        constexpr uint8_t payload_len = sizeof(AttitudeTargetPayload);
        constexpr size_t total_len = HEADER_LEN_V2 + payload_len + CRC_LEN;
        if (max_buffer_len < total_len) return 0;

        out_buffer[0] = MAVLINK_STX_V2;
        out_buffer[1] = payload_len;
        out_buffer[2] = 0; // incompat
        out_buffer[3] = 0; // compat
        out_buffer[4] = seq;
        out_buffer[5] = sys_id;
        out_buffer[6] = comp_id;
        out_buffer[7] = static_cast<uint8_t>(MSG_SET_ATTITUDE_TARGET & 0xFF);
        out_buffer[8] = static_cast<uint8_t>((MSG_SET_ATTITUDE_TARGET >> 8) & 0xFF);
        out_buffer[9] = static_cast<uint8_t>((MSG_SET_ATTITUDE_TARGET >> 16) & 0xFF);

        std::memcpy(out_buffer + HEADER_LEN_V2, &payload, payload_len);

        // CRC calculated over bytes 1 to (HEADER_LEN_V2 + payload_len - 1)
        uint16_t crc = crc_calculate(out_buffer + 1, HEADER_LEN_V2 - 1 + payload_len);
        out_buffer[HEADER_LEN_V2 + payload_len] = static_cast<uint8_t>(crc & 0xFF);
        out_buffer[HEADER_LEN_V2 + payload_len + 1] = static_cast<uint8_t>((crc >> 8) & 0xFF);

        return total_len;
    }

    /**
     * @brief Deserializes a MAVLink 2.0 packet and extracts attitude telemetry if present.
     */
    static bool parse_attitude_packet(const uint8_t* buffer, size_t len,
                                      AttitudePayload& out_attitude, uint8_t& out_sys_id) noexcept {
        if (len < HEADER_LEN_V2 + sizeof(AttitudePayload) + CRC_LEN) return false;
        if (buffer[0] != MAVLINK_STX_V2) return false;

        uint8_t payload_len = buffer[1];
        uint32_t msg_id = static_cast<uint32_t>(buffer[7]) |
                         (static_cast<uint32_t>(buffer[8]) << 8) |
                         (static_cast<uint32_t>(buffer[9]) << 16);

        if (msg_id != MSG_ATTITUDE || payload_len < sizeof(AttitudePayload)) return false;

        out_sys_id = buffer[5];
        std::memcpy(&out_attitude, buffer + HEADER_LEN_V2, sizeof(AttitudePayload));
        return true;
    }
};

} // namespace axiom
