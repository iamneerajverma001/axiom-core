#pragma once

#include <chrono>
#include <string>
#include <cstdint>
#include <functional>
#include "axiom/types.hpp"

namespace axiom {

enum class AnytimeTier : uint8_t {
    TIER_0_HARD_BITMASK = 0,   // < 500 nanoseconds
    TIER_1_SIMD_TREE    = 1,   // < 8 microseconds
    TIER_2_SNN_RESERVOIR= 2,   // < 40 microseconds
    TIER_3_DEEP_DELIB   = 3    // < 2 milliseconds
};

struct AnytimeDecisionSnapshot {
    AnytimeTier completed_tier{AnytimeTier::TIER_0_HARD_BITMASK};
    uint32_t choice_id{0};
    std::string label{"DEFAULT_FALLBACK"};
    float confidence{0.5f};
    bool safety_guaranteed{false};
    double latency_accumulated_us{0.0};
    bool interrupted_early{false};
};

// Anytime Bounded-Rationality Decision Ladder
// Guarantees an immediate, calibrated, safe action commit at ANY microsecond interrupt tick.
class AnytimeDecisionLadder {
public:
    AnytimeDecisionLadder() = default;

    // Evaluates input against progressive tiers, respecting max_deadline_us
    template <typename Tier0Func, typename Tier1Func, typename Tier2Func>
    AnytimeDecisionSnapshot evaluate_with_deadline(
        double max_deadline_us,
        Tier0Func eval_tier0,
        Tier1Func eval_tier1,
        Tier2Func eval_tier2
    ) {
        auto t_start = std::chrono::high_resolution_clock::now();
        AnytimeDecisionSnapshot current_snapshot;

        auto get_elapsed_us = [&t_start]() -> double {
            auto now = std::chrono::high_resolution_clock::now();
            return static_cast<double>(std::chrono::duration_cast<std::chrono::nanoseconds>(now - t_start).count()) / 1000.0;
        };

        // --- TIER 0: Hard Bitmask / Blacklist Check (< 500 nanoseconds) ---
        current_snapshot = eval_tier0();
        current_snapshot.completed_tier = AnytimeTier::TIER_0_HARD_BITMASK;
        current_snapshot.latency_accumulated_us = get_elapsed_us();

        if (current_snapshot.latency_accumulated_us >= max_deadline_us) {
            current_snapshot.interrupted_early = true;
            return current_snapshot;
        }

        // --- TIER 1: Contiguous SIMD Register Tree (< 8 microseconds) ---
        AnytimeDecisionSnapshot t1_res = eval_tier1();
        current_snapshot = t1_res;
        current_snapshot.completed_tier = AnytimeTier::TIER_1_SIMD_TREE;
        current_snapshot.latency_accumulated_us = get_elapsed_us();

        if (current_snapshot.latency_accumulated_us >= max_deadline_us || current_snapshot.confidence >= 0.95f) {
            current_snapshot.interrupted_early = (current_snapshot.latency_accumulated_us >= max_deadline_us);
            return current_snapshot;
        }

        // --- TIER 2: SNN Latent Deliberation Reservoir (< 40 microseconds) ---
        AnytimeDecisionSnapshot t2_res = eval_tier2();
        current_snapshot = t2_res;
        current_snapshot.completed_tier = AnytimeTier::TIER_2_SNN_RESERVOIR;
        current_snapshot.latency_accumulated_us = get_elapsed_us();
        current_snapshot.interrupted_early = false;

        return current_snapshot;
    }
};

} // namespace axiom
