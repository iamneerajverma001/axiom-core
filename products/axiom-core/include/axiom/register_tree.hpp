#pragma once

#include "axiom/types.hpp"
#include "axiom/memory_arena.hpp"
#include "axiom/stopwords.hpp"
#include "axiom/simd_math.hpp"
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <cstring>
#include <sstream>
#include <iostream>

namespace axiom {

static constexpr size_t EMBEDDING_DIM = 256;

// Cache-aligned leaf node inside contiguous register matrix
struct alignas(64) LeafRegister {
    uint32_t leaf_id;
    uint32_t sector_id;
    char name[32];
    alignas(16) float weight_vector[EMBEDDING_DIM]; // Compressed projection weights (256 dims)
};

// Macro Sector Branch Header
struct alignas(64) MacroBranchSector {
    uint32_t sector_id;
    char name[32];
    uint32_t leaf_count;
    uint32_t leaf_offset; // Offset into the contiguous LeafRegister array
    alignas(16) float sector_centroid[EMBEDDING_DIM]; // 256 dims
};

// Evaluation result from Layer 2
struct Layer2Evaluation {
    uint32_t macro_sector_id{0};
    std::string macro_sector_name{"UNMAPPED"};
    uint32_t selected_leaf_id{0};
    std::string selected_leaf_name{"UNMAPPED"};
    float max_probability{0.0f};
    float shannon_entropy{1.0f};
    float confidence_variance{0.0f};
    std::vector<float> leaf_distribution;
    std::vector<uint32_t> leaf_ids;
    bool fast_path_eligible{false};
};

// Layer 2: Hierarchical Memory-Pointer Register Tree
class HierarchicalRegisterTree {
public:
    HierarchicalRegisterTree() = default;

    // Helper to project text tokens into 256-dim normalized embedding signature
    static void project_tokens_to_signature(const std::string& text, float* out_sig, size_t dim = EMBEDDING_DIM) {
        std::memset(out_sig, 0, sizeof(float) * dim);
        
        // Meaningful word extraction with stopword pruning & anti-collision hashing
        auto tokens = extract_meaningful_tokens(text);
        for (const auto& word : tokens) {
            uint64_t h1 = 0xcbf29ce484222325ULL;
            uint64_t h2 = 0x100000001b3ULL;
            for (char ch : word) {
                h1 = (h1 ^ static_cast<unsigned char>(ch)) * 0x100000001b3ULL;
                h2 = (h2 + static_cast<unsigned char>(ch)) * 0xcbf29ce484222325ULL;
            }
            size_t idx1 = h1 % dim;
            size_t idx2 = (h2 ^ (h1 >> 16)) % dim;
            out_sig[idx1] += 3.0f;
            out_sig[idx2] += 1.5f;
        }

        // L2 Unit Normalization via SIMD
        simd_l2_normalize(out_sig, dim);
    }

    // Compiles declarative schema into contiguous C++ memory arrays
    void compile_schema(const SchemaDefinition& schema) {
        m_schema = schema;
        m_sectors.clear();
        m_leaves.clear();

        uint32_t current_leaf_offset = 0;
        for (const auto& sec_def : schema.sectors) {
            MacroBranchSector sector;
            sector.sector_id = sec_def.sector_id;
            std::strncpy(sector.name, sec_def.name.c_str(), sizeof(sector.name) - 1);
            sector.name[sizeof(sector.name) - 1] = '\0';
            sector.leaf_count = static_cast<uint32_t>(sec_def.leaves.size());
            sector.leaf_offset = current_leaf_offset;

            // Build sector signature from sector name and leaf vocabulary
            std::string sector_corpus = sec_def.name;
            for (const auto& l : sec_def.leaves) {
                sector_corpus += " " + l.name + " " + l.description;
            }
            project_tokens_to_signature(sector_corpus, sector.sector_centroid);
            m_sectors.push_back(sector);

            // Populate contiguous leaf registers
            for (const auto& leaf_def : sec_def.leaves) {
                LeafRegister leaf;
                leaf.leaf_id = leaf_def.leaf_id;
                leaf.sector_id = sec_def.sector_id;
                std::strncpy(leaf.name, leaf_def.name.c_str(), sizeof(leaf.name) - 1);
                leaf.name[sizeof(leaf.name) - 1] = '\0';

                std::string leaf_corpus = leaf_def.name + " " + leaf_def.description;
                project_tokens_to_signature(leaf_corpus, leaf.weight_vector);

                m_leaves.push_back(leaf);
                current_leaf_offset++;
            }
        }
    }

    // Evaluates embedding against hierarchical pointer tree (Sub-microsecond execution with Two-Stage Gating)
    Layer2Evaluation evaluate(const float* embedding, size_t dim, MemoryFrame& frame) const {
        Layer2Evaluation eval;
        if (m_leaves.empty()) {
            eval.fast_path_eligible = false;
            eval.macro_sector_name = "EMPTY_SCHEMA";
            eval.selected_leaf_name = "NO_LEAVES_CONFIGURED";
            return eval;
        }

        uint32_t total_leaves = static_cast<uint32_t>(m_leaves.size());
        uint32_t total_sectors = static_cast<uint32_t>(m_sectors.size());
        float* leaf_dots = static_cast<float*>(frame.allocate(sizeof(float) * total_leaves));
        float* leaf_logits = static_cast<float*>(frame.allocate(sizeof(float) * total_leaves));
        float max_logit = -1e9f;
        float best_leaf_dot = -1e9f;
        size_t best_leaf_idx = 0;

        float adaptive_temp = 28.0f;

        // STAGE 1: Macro-Sector Centroid Gating (Hierarchical Pruning)
        bool use_sector_pruning = (total_sectors >= 4 && total_leaves >= 24);
        uint32_t max_sec_id = 0;
        for (const auto& sec : m_sectors) {
            if (sec.sector_id > max_sec_id) max_sec_id = sec.sector_id;
        }
        std::vector<bool> active_sectors(max_sec_id + 1, true);

        if (use_sector_pruning) {
            std::fill(active_sectors.begin(), active_sectors.end(), false);
            float max_s_dot = -1e9f;
            std::vector<float> s_dots(total_sectors, 0.0f);

            for (uint32_t s = 0; s < total_sectors; ++s) {
                const auto& sec = m_sectors[s];
                float s_dot = simd_dot_product(embedding, sec.sector_centroid, EMBEDDING_DIM);
                s_dots[s] = s_dot;
                if (s_dot > max_s_dot) {
                    max_s_dot = s_dot;
                }
            }

            // Keep sectors within 0.18 of best sector centroid, and guarantee top 2 sectors
            float threshold = max_s_dot - 0.18f;
            std::vector<std::pair<float, uint32_t>> ranked_sectors;
            for (uint32_t s = 0; s < total_sectors; ++s) {
                ranked_sectors.push_back({s_dots[s], m_sectors[s].sector_id});
                if (s_dots[s] >= threshold) {
                    active_sectors[m_sectors[s].sector_id] = true;
                }
            }
            std::sort(ranked_sectors.rbegin(), ranked_sectors.rend());
            if (ranked_sectors.size() >= 1) active_sectors[ranked_sectors[0].second] = true;
            if (ranked_sectors.size() >= 2) active_sectors[ranked_sectors[1].second] = true;
        }

        // STAGE 2: Local Leaf Evaluation within Gated Sectors
        for (uint32_t l = 0; l < total_leaves; ++l) {
            const LeafRegister& leaf = m_leaves[l];

            // Pruning check: skip leaves not in the active candidate sectors
            if (use_sector_pruning && (leaf.sector_id >= active_sectors.size() || !active_sectors[leaf.sector_id])) {
                leaf_dots[l] = -1.0f;
                leaf_logits[l] = -1e6f;
                continue;
            }

            float dot = simd_dot_product(embedding, leaf.weight_vector, EMBEDDING_DIM);
            leaf_dots[l] = dot;
            if (dot > best_leaf_dot) {
                best_leaf_dot = dot;
                best_leaf_idx = l;
            }
            leaf_logits[l] = dot * adaptive_temp;
            if (leaf_logits[l] > max_logit) {
                max_logit = leaf_logits[l];
            }
        }

        // STEP 2: Calibrated Softmax across leaves
        float sum_exp = 0.0f;
        for (uint32_t l = 0; l < total_leaves; ++l) {
            if (leaf_logits[l] <= -1e5f) {
                leaf_logits[l] = 0.0f;
                continue;
            }
            leaf_logits[l] = std::exp(leaf_logits[l] - max_logit);
            sum_exp += leaf_logits[l];
        }

        eval.leaf_distribution.resize(total_leaves);
        eval.leaf_ids.resize(total_leaves);
        float best_leaf_prob = 0.0f;

        for (uint32_t l = 0; l < total_leaves; ++l) {
            float p = (sum_exp > 0.0f) ? (leaf_logits[l] / sum_exp) : (1.0f / total_leaves);
            eval.leaf_distribution[l] = p;
            eval.leaf_ids[l] = m_leaves[l].leaf_id;

            if (p > best_leaf_prob) {
                best_leaf_prob = p;
            }
        }

        eval.selected_leaf_id = m_leaves[best_leaf_idx].leaf_id;
        eval.selected_leaf_name = m_leaves[best_leaf_idx].name;
        eval.macro_sector_id = m_leaves[best_leaf_idx].sector_id;
        eval.macro_sector_name = "Sector_OS_Hardware";

        for (const auto& sec : m_sectors) {
            if (sec.sector_id == eval.macro_sector_id) {
                eval.macro_sector_name = sec.name;
                break;
            }
        }

        eval.max_probability = best_leaf_prob;

        // STEP 3: Normalized Shannon Entropy
        float entropy = 0.0f;
        for (float p : eval.leaf_distribution) {
            if (p > 1e-7f) {
                entropy -= p * std::log(p);
            }
        }
        if (total_leaves > 1) {
            entropy /= std::log(static_cast<float>(total_leaves));
        }
        eval.shannon_entropy = entropy;

        // Variance metric
        float mean_p = 1.0f / total_leaves;
        float var_sum = 0.0f;
        for (float p : eval.leaf_distribution) {
            float diff = p - mean_p;
            var_sum += diff * diff;
        }
        eval.confidence_variance = var_sum / total_leaves;

        // STEP 4: Genuine Geometric Alignment Gate
        // Best leaf dot product must exceed confidence barrier
        const bool genuine_alignment = (best_leaf_dot >= 0.28f);
        eval.fast_path_eligible = genuine_alignment &&
                                  (eval.max_probability >= m_schema.confidence_threshold) &&
                                  (eval.shannon_entropy <= m_schema.entropy_threshold);

        return eval;
    }

    struct RLCDResult {
        RLCDLearningType type{RLCDLearningType::NONE};
        uint32_t leaf_id{0};
        std::string leaf_name{""};
        uint32_t sector_id{0};
    };

    // Self-Learning RLCD: Reinforces existing leaf or dynamically expands new leaf with collision prevention
    RLCDResult hot_register_or_reinforce(
        const std::string& phrase,
        uint32_t target_leaf_id,
        uint32_t target_sector_id,
        const std::string& optional_leaf_name = ""
    ) {
        RLCDResult res;
        if (phrase.empty() || m_sectors.empty()) return res;

        // Compute 256-dim unit-normalized signature of new phrase
        alignas(16) float new_sig[EMBEDDING_DIM];
        project_tokens_to_signature(phrase, new_sig, EMBEDDING_DIM);

        // 1. Direct Leaf Reinforcement if target_leaf_id exists
        if (target_leaf_id != 0) {
            for (auto& leaf : m_leaves) {
                if (leaf.leaf_id == target_leaf_id) {
                    // Blend weights: 80% existing + 20% novel phrase vector
                    for (size_t i = 0; i < EMBEDDING_DIM; ++i) {
                        leaf.weight_vector[i] = 0.80f * leaf.weight_vector[i] + 0.20f * new_sig[i];
                    }
                    float sq = 0.0f;
                    for (size_t i = 0; i < EMBEDDING_DIM; ++i) sq += leaf.weight_vector[i] * leaf.weight_vector[i];
                    if (sq > 1e-8f) {
                        float inv = 1.0f / std::sqrt(sq);
                        for (size_t i = 0; i < EMBEDDING_DIM; ++i) leaf.weight_vector[i] *= inv;
                    }

                    // Reinforce sector centroid
                    for (auto& sec : m_sectors) {
                        if (sec.sector_id == leaf.sector_id) {
                            for (size_t i = 0; i < EMBEDDING_DIM; ++i) {
                                sec.sector_centroid[i] = 0.85f * sec.sector_centroid[i] + 0.15f * new_sig[i];
                            }
                            float csq = 0.0f;
                            for (size_t i = 0; i < EMBEDDING_DIM; ++i) csq += sec.sector_centroid[i] * sec.sector_centroid[i];
                            if (csq > 1e-8f) {
                                float inv = 1.0f / std::sqrt(csq);
                                for (size_t i = 0; i < EMBEDDING_DIM; ++i) sec.sector_centroid[i] *= inv;
                            }
                            break;
                        }
                    }

                    res.type = RLCDLearningType::REINFORCED_EXISTING_LEAF;
                    res.leaf_id = leaf.leaf_id;
                    res.leaf_name = leaf.name;
                    res.sector_id = leaf.sector_id;
                    return res;
                }
            }
        }

        // 2. Anti-Collision Scan: check cosine similarity against leaves in target sector
        float highest_sim = -1.0f;
        size_t best_match_idx = 0;
        bool found_leaf_in_sector = false;

        for (size_t idx = 0; idx < m_leaves.size(); ++idx) {
            if (m_leaves[idx].sector_id == target_sector_id) {
                found_leaf_in_sector = true;
                float dot = 0.0f;
                for (size_t i = 0; i < EMBEDDING_DIM; ++i) {
                    dot += new_sig[i] * m_leaves[idx].weight_vector[i];
                }
                if (dot > highest_sim) {
                    highest_sim = dot;
                    best_match_idx = idx;
                }
            }
        }

        // If similarity >= 0.70f, reinforce that existing leaf to avoid duplicate collision!
        if (found_leaf_in_sector && highest_sim >= 0.70f) {
            auto& leaf = m_leaves[best_match_idx];
            for (size_t i = 0; i < EMBEDDING_DIM; ++i) {
                leaf.weight_vector[i] = 0.80f * leaf.weight_vector[i] + 0.20f * new_sig[i];
            }
            float sq = 0.0f;
            for (size_t i = 0; i < EMBEDDING_DIM; ++i) sq += leaf.weight_vector[i] * leaf.weight_vector[i];
            if (sq > 1e-8f) {
                float inv = 1.0f / std::sqrt(sq);
                for (size_t i = 0; i < EMBEDDING_DIM; ++i) leaf.weight_vector[i] *= inv;
            }

            res.type = RLCDLearningType::REINFORCED_EXISTING_LEAF;
            res.leaf_id = leaf.leaf_id;
            res.leaf_name = leaf.name;
            res.sector_id = leaf.sector_id;
            return res;
        }

        // 3. Novel Intent: Safely Expand New Leaf in target sector
        LeafRegister new_leaf;
        uint32_t new_id = (target_leaf_id != 0) ? target_leaf_id : (target_sector_id * 100 + 50 + static_cast<uint32_t>(m_leaves.size() % 50));
        new_leaf.leaf_id = new_id;
        new_leaf.sector_id = target_sector_id;

        std::string final_name = optional_leaf_name.empty() ? ("Auto_Leaf_" + std::to_string(new_id)) : optional_leaf_name;
        std::strncpy(new_leaf.name, final_name.c_str(), sizeof(new_leaf.name) - 1);
        new_leaf.name[sizeof(new_leaf.name) - 1] = '\0';

        std::memcpy(new_leaf.weight_vector, new_sig, sizeof(float) * EMBEDDING_DIM);

        m_leaves.push_back(new_leaf);

        // Update sector leaf count and centroid
        for (auto& sec : m_sectors) {
            if (sec.sector_id == target_sector_id) {
                sec.leaf_count++;
                for (size_t i = 0; i < EMBEDDING_DIM; ++i) {
                    sec.sector_centroid[i] = 0.88f * sec.sector_centroid[i] + 0.12f * new_sig[i];
                }
                float csq = 0.0f;
                for (size_t i = 0; i < EMBEDDING_DIM; ++i) csq += sec.sector_centroid[i] * sec.sector_centroid[i];
                if (csq > 1e-8f) {
                    float inv = 1.0f / std::sqrt(csq);
                    for (size_t i = 0; i < EMBEDDING_DIM; ++i) sec.sector_centroid[i] *= inv;
                }
                break;
            }
        }

        res.type = RLCDLearningType::EXPANDED_NEW_LEAF;
        res.leaf_id = new_id;
        res.leaf_name = new_leaf.name;
        res.sector_id = target_sector_id;
        return res;
    }

    // Microsecond Online Hebbian/Oja Weight Adaptation (Zero-Heap Allocation)
    // Formula: Delta w_i = eta * y * (x_i - y * w_i) where y = w^T * x
    bool adapt_leaf_weights_hebbian(
        uint32_t leaf_id,
        const float* input_embedding,
        size_t dim,
        float learning_rate = 0.01f
    ) {
        if (!input_embedding || dim == 0) return false;
        size_t eff_dim = std::min(dim, EMBEDDING_DIM);

        for (auto& leaf : m_leaves) {
            if (leaf.leaf_id == leaf_id) {
                float y = simd_dot_product(leaf.weight_vector, input_embedding, eff_dim);
                simd_oja_update(leaf.weight_vector, input_embedding, learning_rate, y, eff_dim);
                simd_l2_normalize(leaf.weight_vector, EMBEDDING_DIM);

                // Update parent sector centroid with damped plasticity
                for (auto& sec : m_sectors) {
                    if (sec.sector_id == leaf.sector_id) {
                        float sec_y = simd_dot_product(sec.sector_centroid, input_embedding, eff_dim);
                        simd_oja_update(sec.sector_centroid, input_embedding, learning_rate * 0.5f, sec_y, eff_dim);
                        simd_l2_normalize(sec.sector_centroid, EMBEDDING_DIM);
                        break;
                    }
                }
                return true;
            }
        }
        return false;
    }

    const SchemaDefinition& get_schema() const noexcept { return m_schema; }
    size_t get_leaf_count() const noexcept { return m_leaves.size(); }
    size_t get_sector_count() const noexcept { return m_sectors.size(); }

private:
    SchemaDefinition m_schema;
    std::vector<MacroBranchSector> m_sectors;
    std::vector<LeafRegister> m_leaves;
};

} // namespace axiom
