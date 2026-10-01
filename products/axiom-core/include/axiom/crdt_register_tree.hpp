#pragma once

#include <cstdint>
#include <vector>
#include <cmath>
#include <algorithm>
#include "axiom/simd_math.hpp"

namespace axiom {

struct CrdtLeafEntry {
    uint32_t leaf_id;
    uint32_t node_origin;
    uint64_t vector_clock;
    float weight_vector[256];
};

// Conflict-Free Replicated Data Type (CRDT) Register Tree
// Guarantees deterministic, conflict-free prototype merges across distributed autonomous edge agents.
class CrdtRegisterTree {
public:
    explicit CrdtRegisterTree(uint32_t node_id) : m_node_id(node_id), m_local_clock(0) {}

    // Register or update a local leaf prototype with vector clock increment
    void update_local_leaf(uint32_t leaf_id, const float* weights, size_t dim) {
        m_local_clock++;
        size_t eff_dim = std::min(dim, size_t(256));

        for (auto& leaf : m_leaves) {
            if (leaf.leaf_id == leaf_id) {
                leaf.vector_clock = m_local_clock;
                leaf.node_origin = m_node_id;
                std::memcpy(leaf.weight_vector, weights, sizeof(float) * eff_dim);
                simd_l2_normalize(leaf.weight_vector, 256);
                return;
            }
        }

        CrdtLeafEntry new_leaf{};
        new_leaf.leaf_id = leaf_id;
        new_leaf.node_origin = m_node_id;
        new_leaf.vector_clock = m_local_clock;
        std::memcpy(new_leaf.weight_vector, weights, sizeof(float) * eff_dim);
        simd_l2_normalize(new_leaf.weight_vector, 256);
        m_leaves.push_back(new_leaf);
    }

    // Monotonic Join / Merge of a remote CRDT leaf state without conflicts
    void merge_remote_leaf(const CrdtLeafEntry& remote_leaf) {
        for (auto& leaf : m_leaves) {
            if (leaf.leaf_id == remote_leaf.leaf_id) {
                // If remote vector clock is strictly newer, adopt it
                if (remote_leaf.vector_clock > leaf.vector_clock) {
                    leaf = remote_leaf;
                } else if (remote_leaf.vector_clock == leaf.vector_clock && remote_leaf.node_origin != leaf.node_origin) {
                    // Convex combination merge of concurrent updates
                    for (size_t i = 0; i < 256; ++i) {
                        leaf.weight_vector[i] = 0.5f * (leaf.weight_vector[i] + remote_leaf.weight_vector[i]);
                    }
                    simd_l2_normalize(leaf.weight_vector, 256);
                    leaf.vector_clock++;
                }
                return;
            }
        }
        // Novel leaf from remote node
        m_leaves.push_back(remote_leaf);
    }

    const std::vector<CrdtLeafEntry>& get_leaves() const noexcept { return m_leaves; }
    uint64_t get_vector_clock() const noexcept { return m_local_clock; }

private:
    uint32_t m_node_id;
    uint64_t m_local_clock;
    std::vector<CrdtLeafEntry> m_leaves;
};

} // namespace axiom
