#pragma once

#include <cstdint>
#include <cstring>
#include <atomic>
#include <vector>

namespace axiom {

constexpr size_t MAX_SWARM_NODES = 64;

#pragma pack(push, 8)
// Zero-Copy Swarm Telemetry & Emergency Reflex State Frame
struct alignas(64) SwarmNodeState {
    uint32_t node_id;
    uint32_t cluster_id;
    uint64_t sequence_num;
    uint32_t active_leaf_id;
    float    safety_wealth;
    uint8_t  emergency_halt; // 1 = Cluster-Wide E-STOP Active
    uint8_t  padding[3];
    double   heartbeat_timestamp_us;
    float    state_vector[32];
};
#pragma pack(pop)

// Swarm Reflex Fabric
// Coordinates decentralized emergency halts and state updates across a multi-robot / multi-agent cluster.
class SwarmReflexFabric {
public:
    SwarmReflexFabric(uint32_t local_node_id, uint32_t cluster_id)
        : m_local_id(local_node_id), m_cluster_id(cluster_id), m_halt_tripped(false) {
        std::memset(m_nodes, 0, sizeof(m_nodes));
    }

    // Trigger cluster-wide emergency halt (E-STOP) across all nodes in < 5 microseconds
    void trigger_cluster_estop() noexcept {
        m_halt_tripped.store(true, std::memory_order_release);
        m_nodes[m_local_id % MAX_SWARM_NODES].emergency_halt = 1;
    }

    // Check if any node in the cluster has signaled an emergency halt
    bool is_cluster_halted() const noexcept {
        if (m_halt_tripped.load(std::memory_order_acquire)) return true;
        for (size_t i = 0; i < MAX_SWARM_NODES; ++i) {
            if (m_nodes[i].emergency_halt == 1) return true;
        }
        return false;
    }

    // Ingest peer state heartbeat
    void update_peer_state(const SwarmNodeState& peer) noexcept {
        size_t idx = peer.node_id % MAX_SWARM_NODES;
        m_nodes[idx] = peer;
        if (peer.emergency_halt == 1) {
            m_halt_tripped.store(true, std::memory_order_release);
        }
    }

    SwarmNodeState get_local_state(uint32_t current_leaf, float wealth) const noexcept {
        SwarmNodeState s{};
        s.node_id = m_local_id;
        s.cluster_id = m_cluster_id;
        s.active_leaf_id = current_leaf;
        s.safety_wealth = wealth;
        s.emergency_halt = m_halt_tripped.load(std::memory_order_relaxed) ? 1 : 0;
        return s;
    }

private:
    uint32_t m_local_id;
    uint32_t m_cluster_id;
    std::atomic<bool> m_halt_tripped;
    SwarmNodeState m_nodes[MAX_SWARM_NODES];
};

} // namespace axiom
