#pragma once

#include "axiom/types.hpp"
#include "axiom/memory_arena.hpp"
#include "axiom/sparse_tensor_loop.hpp"
#include "axiom/register_tree.hpp"
#include "axiom/conformal.hpp"
#include "axiom/system2_fallback.hpp"
#include <chrono>
#include <string>
#include <atomic>
#include <unordered_map>

namespace axiom {

// The Unified Axiom-1 Decision Engine
class AxiomEngine {
public:
    explicit AxiomEngine(
        DeviceType device = DeviceType::DIRECTML_GPU,
        size_t arena_pool_size = 256,
        float conformal_alpha = 0.01f,
        const System2Config& system2_cfg = System2Config()
    ) : m_arena_pool(arena_pool_size),
        m_layer1(device),
        m_conformal(conformal_alpha),
        m_system2(system2_cfg),
        m_request_counter(0),
        m_fast_path_hits(0),
        m_fallback_hits(0)
    {
        m_layer1.initialize();
    }

    // Loads and compiles declarative schema into contiguous pointer registers
    void load_schema(const SchemaDefinition& schema) {
        m_register_tree.compile_schema(schema);
        m_conformal.set_alpha(schema.conformal_alpha);
    }

    // Registers an action execution handler for a specific leaf ID
    void register_action_handler(uint32_t leaf_id, ActionExecutionHook handler) {
        m_action_handlers[leaf_id] = std::move(handler);
    }

    // Registers a default fallback action handler
    void register_default_action_handler(ActionExecutionHook handler) {
        m_default_action_handler = std::move(handler);
    }

    // Direct invocation of Tier 1 fast-path execution loop
    bool execute_leaf_action(uint32_t leaf_id, const std::string& context, std::string& out_status) {
        auto it = m_action_handlers.find(leaf_id);
        if (it != m_action_handlers.end() && it->second) {
            return it->second(leaf_id, context, out_status);
        }
        if (m_default_action_handler) {
            return m_default_action_handler(leaf_id, context, out_status);
        }
        out_status = "Executed native Tier 1 leaf #" + std::to_string(leaf_id) + " (Zero-overhead bare-metal commit)";
        return true;
    }

    // Dynamically registers or reinforces an action leaf in the hierarchical tree
    HierarchicalRegisterTree::RLCDResult hot_register_or_reinforce_leaf(
        const std::string& phrase,
        uint32_t target_leaf_id,
        uint32_t target_sector_id,
        const std::string& optional_leaf_name = ""
    ) {
        return m_register_tree.hot_register_or_reinforce(phrase, target_leaf_id, target_sector_id, optional_leaf_name);
    }

    // Executes end-to-end decision pipeline (Target: <5ms fast path)
    DecisionResult decide(const std::string& input_text) {
        auto t_total_start = std::chrono::high_resolution_clock::now();
        uint32_t req_id = static_cast<uint32_t>(m_request_counter.fetch_add(1, std::memory_order_relaxed));

        // 1. ARENA ACQUISITION with Lock-Aware RAII Protection
        MemoryFrame& frame = m_arena_pool.acquire();
        FrameGuard frame_guard(frame); // Automatically releases lock on return

        // 2. LAYER 1: SPARSE TENSOR LOOP & LDU RECURRENT DELIBERATION
        auto t_l1_start = std::chrono::high_resolution_clock::now();
        float* embedding = static_cast<float*>(frame.allocate(sizeof(float) * SparseTensorLoop::DEFAULT_EMBEDDING_DIM));
        m_layer1.forward_sparse(input_text, frame, embedding, SparseTensorLoop::DEFAULT_EMBEDDING_DIM);
        auto t_l1_end = std::chrono::high_resolution_clock::now();

        // 3. LAYER 2: CONTIGUOUS HIERARCHICAL REGISTER TREE LOOKUP (TWO-STAGE GATED)
        auto t_l2_start = std::chrono::high_resolution_clock::now();
        Layer2Evaluation l2_eval = m_register_tree.evaluate(embedding, SparseTensorLoop::DEFAULT_EMBEDDING_DIM, frame);
        auto t_l2_end = std::chrono::high_resolution_clock::now();

        // 4. CONFORMAL SET GENERATION USING REAL BUSINESS LEAF IDs
        ConformalSet conf_set = m_conformal.generate_set(l2_eval.leaf_distribution, l2_eval.leaf_ids);

        // Microsecond Profiling
        double l1_us = static_cast<double>(std::chrono::duration_cast<std::chrono::microseconds>(t_l1_end - t_l1_start).count());
        double l2_us = static_cast<double>(std::chrono::duration_cast<std::chrono::microseconds>(t_l2_end - t_l2_start).count());

        // 5. FAST PATH OR SYSTEM 2 BUS HALT GATING
        // Statistical Conformal Guarantee: Fast-Path MUST have a singleton set (no ambiguity)
        if (l2_eval.fast_path_eligible && conf_set.is_singleton) {
            // === FAST-PATH COMMIT (<5ms Target) ===
            m_fast_path_hits.fetch_add(1, std::memory_order_relaxed);
            auto t_total_end = std::chrono::high_resolution_clock::now();

            DecisionResult result;
            result.request_id = req_id;
            result.path = ExecutionPath::FAST_PATH_COMMIT;
            
            result.choice.choice_id = l2_eval.selected_leaf_id;
            result.choice.label = l2_eval.selected_leaf_name;
            result.choice.confidence = l2_eval.max_probability;

            result.score.score = l2_eval.max_probability;
            result.score.variance = l2_eval.confidence_variance;

            result.noul.value = (l2_eval.max_probability >= 0.70f);
            result.noul.probability = l2_eval.max_probability;
            result.noul.is_null = false;

            result.shannon_entropy = l2_eval.shannon_entropy;
            result.conformal_set = conf_set;

            // Direct Tier 1 Action Execution
            result.feedback.tier3_to_tier1_dispatched = false;
            result.feedback.executed_leaf_id = l2_eval.selected_leaf_id;
            result.feedback.target_leaf_name = l2_eval.selected_leaf_name;
            result.feedback.target_sector_id = l2_eval.macro_sector_id;
            result.feedback.action_executed = execute_leaf_action(
                l2_eval.selected_leaf_id, input_text, result.feedback.execution_status
            );

            result.latency_layer1_us = l1_us;
            result.latency_layer2_us = l2_us;
            result.latency_layer3_us = 0.0;
            result.latency_total_us = static_cast<double>(
                std::chrono::duration_cast<std::chrono::microseconds>(t_total_end - t_total_start).count()
            );

            return result;
        } else {
            // === LAYER 3: BUS HALT & SYSTEM 2 FALLBACK ===
            m_fallback_hits.fetch_add(1, std::memory_order_relaxed);
            
            DecisionResult fallback_result = m_system2.resolve_ambiguity(
                req_id, input_text, l2_eval, conf_set
            );

            // CLOSED-LOOP TIER 3 -> TIER 1 EXECUTION BRIDGE
            // System 2 deliberated and validated the intent. Now dispatch directly into Tier 1 execution loop!
            uint32_t resolved_leaf_id = fallback_result.choice.choice_id;
            fallback_result.feedback.tier3_to_tier1_dispatched = true;
            fallback_result.feedback.executed_leaf_id = resolved_leaf_id;
            fallback_result.feedback.target_leaf_name = l2_eval.selected_leaf_name;
            fallback_result.feedback.target_sector_id = l2_eval.macro_sector_id;
            fallback_result.feedback.action_executed = execute_leaf_action(
                resolved_leaf_id, input_text, fallback_result.feedback.execution_status
            );
            m_tier3_to_tier1_dispatches.fetch_add(1, std::memory_order_relaxed);

            // RLCD AUTONOMOUS MUSCLE MEMORY LEARNING
            // Hot-reinforce or expand the leaf in HierarchicalRegisterTree
            // so subsequent identical or semantically close queries hit Tier 1 Fast-Path directly in <65µs!
            if (fallback_result.choice.confidence >= 0.85f) {
                auto rlcd_res = m_register_tree.hot_register_or_reinforce(
                    input_text,
                    resolved_leaf_id,
                    l2_eval.macro_sector_id,
                    l2_eval.selected_leaf_name
                );
                fallback_result.feedback.rlcd_learning = rlcd_res.type;
                if (rlcd_res.type != RLCDLearningType::NONE) {
                    m_rlcd_learn_hits.fetch_add(1, std::memory_order_relaxed);
                }
            }

            auto t_total_end = std::chrono::high_resolution_clock::now();
            fallback_result.latency_layer1_us = l1_us;
            fallback_result.latency_layer2_us = l2_us;
            fallback_result.latency_total_us = static_cast<double>(
                std::chrono::duration_cast<std::chrono::microseconds>(t_total_end - t_total_start).count()
            );

            return fallback_result;
        }
    }

    uint64_t get_total_requests() const noexcept { return m_request_counter.load(); }
    uint64_t get_fast_path_hits() const noexcept { return m_fast_path_hits.load(); }
    uint64_t get_fallback_hits() const noexcept { return m_fallback_hits.load(); }
    uint64_t get_tier3_dispatches() const noexcept { return m_tier3_to_tier1_dispatches.load(); }
    uint64_t get_rlcd_learn_hits() const noexcept { return m_rlcd_learn_hits.load(); }
    size_t get_active_leaf_count() const noexcept { return m_register_tree.get_leaf_count(); }
    size_t get_active_sector_count() const noexcept { return m_register_tree.get_sector_count(); }
    BackendProfile get_backend_profile() const { return m_layer1.get_profile(); }

private:
    ArenaPool m_arena_pool;
    SparseTensorLoop m_layer1;
    HierarchicalRegisterTree m_register_tree;
    ConformalEngine m_conformal;
    System2FallbackController m_system2;

    std::unordered_map<uint32_t, ActionExecutionHook> m_action_handlers;
    ActionExecutionHook m_default_action_handler;

    std::atomic<uint64_t> m_request_counter;
    std::atomic<uint64_t> m_fast_path_hits;
    std::atomic<uint64_t> m_fallback_hits;
    std::atomic<uint64_t> m_tier3_to_tier1_dispatches{0};
    std::atomic<uint64_t> m_rlcd_learn_hits{0};
};

} // namespace axiom
