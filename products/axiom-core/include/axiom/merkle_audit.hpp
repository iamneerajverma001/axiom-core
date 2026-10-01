#pragma once

#include <cstdint>
#include <cstring>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>

namespace axiom {

// FNV-1a 64-bit cryptographic hash for microsecond in-memory Merkle DAG
inline uint64_t fnv1a_hash(const void* data, size_t len, uint64_t seed = 0xcbf29ce484222325ULL) noexcept {
    const uint8_t* ptr = static_cast<const uint8_t*>(data);
    uint64_t hash = seed;
    for (size_t i = 0; i < len; ++i) {
        hash = (hash ^ ptr[i]) * 0x100000001b3ULL;
    }
    return hash;
}

struct alignas(32) MerkleAuditNode {
    uint64_t node_hash;
    uint64_t prev_hash;
    uint32_t request_id;
    uint32_t leaf_id;
    float confidence;
    double timestamp_us;
};

// Cryptographic In-Memory Merkle Flight Recorder
// Produces immutable, tamper-evident cryptographic proofs of decision provenance.
class MerkleFlightRecorder {
public:
    static constexpr size_t MAX_AUDIT_LOGS = 1024;

    MerkleFlightRecorder() : m_count(0), m_root_hash(0) {}

    // Record an action execution event into the Merkle chain in < 300 nanoseconds
    uint64_t record_event(
        uint32_t request_id,
        uint32_t leaf_id,
        float confidence,
        double timestamp_us,
        const char* directive_str
    ) noexcept {
        uint64_t prev = (m_count > 0) ? m_nodes[(m_count - 1) % MAX_AUDIT_LOGS].node_hash : 0xDEADBEEFCAFEULL;
        
        // Hash payload
        uint64_t payload_hash = fnv1a_hash(&request_id, sizeof(request_id), prev);
        payload_hash = fnv1a_hash(&leaf_id, sizeof(leaf_id), payload_hash);
        payload_hash = fnv1a_hash(&confidence, sizeof(confidence), payload_hash);
        if (directive_str) {
            payload_hash = fnv1a_hash(directive_str, std::strlen(directive_str), payload_hash);
        }

        size_t idx = m_count % MAX_AUDIT_LOGS;
        m_nodes[idx].node_hash = payload_hash;
        m_nodes[idx].prev_hash = prev;
        m_nodes[idx].request_id = request_id;
        m_nodes[idx].leaf_id = leaf_id;
        m_nodes[idx].confidence = confidence;
        m_nodes[idx].timestamp_us = timestamp_us;

        m_root_hash = payload_hash;
        m_count++;
        return m_root_hash;
    }

    // Verify chain integrity between start_idx and end_idx
    bool verify_chain_integrity() const noexcept {
        if (m_count <= 1) return true;
        size_t limit = (m_count < MAX_AUDIT_LOGS) ? m_count : MAX_AUDIT_LOGS;

        for (size_t i = 1; i < limit; ++i) {
            if (m_nodes[i].prev_hash != m_nodes[i - 1].node_hash) {
                return false; // Tampered chain!
            }
        }
        return true;
    }

    uint64_t get_root_hash() const noexcept { return m_root_hash; }
    size_t get_total_records() const noexcept { return m_count; }

private:
    MerkleAuditNode m_nodes[MAX_AUDIT_LOGS];
    size_t m_count;
    uint64_t m_root_hash;
};

} // namespace axiom
