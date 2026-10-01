#pragma once
#include "axiom/types.hpp"
#include <cstdint>
#include <cstring>
#include <array>

namespace axiom {

/**
 * @brief Zero-Allocation Sim2Real High-Speed Telemetry Bridge.
 * Binds Axiom Core to robotics simulators (Isaac Sim, MuJoCo, Gazebo, AirSim)
 * over memory-mapped buffers or binary UDP sockets with sub-microsecond serialization.
 */
class Sim2RealBridge {
public:
    static constexpr uint32_t SIM2REAL_MAGIC = 0x53494D32; // "SIM2"

    #pragma pack(push, 1)
    struct StatePacket {
        uint32_t magic{SIM2REAL_MAGIC};
        uint64_t timestamp_ns{0};
        float position[3]{0.0f, 0.0f, 0.0f};      // x, y, z (m)
        float linear_vel[3]{0.0f, 0.0f, 0.0f};    // vx, vy, vz (m/s)
        float orientation_quat[4]{1.0f, 0.0f, 0.0f, 0.0f}; // w, x, y, z
        float angular_vel[3]{0.0f, 0.0f, 0.0f};   // wx, wy, wz (rad/s)
        float lidar_distances[16]{};              // 16-ray proximity radar
        uint32_t sequence_id{0};
    };

    struct CommandPacket {
        uint32_t magic{SIM2REAL_MAGIC};
        uint64_t timestamp_ns{0};
        float motor_torques[4]{0.0f, 0.0f, 0.0f, 0.0f}; // Normalized 0.0 to 1.0 or N*m
        uint8_t estop_engaged{0};
        uint8_t safety_interlock_active{0};
        float martingale_wealth{1.0f};
        uint32_t sequence_id{0};
    };
    #pragma pack(pop)

    static size_t serialize_command(const CommandPacket& cmd, uint8_t* out_buf, size_t max_len) noexcept {
        if (max_len < sizeof(CommandPacket) || out_buf == nullptr) return 0;
        std::memcpy(out_buf, &cmd, sizeof(CommandPacket));
        return sizeof(CommandPacket);
    }

    static bool deserialize_state(const uint8_t* in_buf, size_t len, StatePacket& out_state) noexcept {
        if (len < sizeof(StatePacket) || in_buf == nullptr) return false;
        std::memcpy(&out_state, in_buf, sizeof(StatePacket));
        return (out_state.magic == SIM2REAL_MAGIC);
    }
};

} // namespace axiom
