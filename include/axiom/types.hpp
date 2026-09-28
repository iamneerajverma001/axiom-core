#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <array>
#include <memory>
#include <functional>

namespace axiom {

// Execution mode of a decision
enum class ExecutionPath : uint8_t {
    FAST_PATH_COMMIT = 0,    // Cleared in Layer 1 & 2 in <5ms
    SYSTEM2_FALLBACK = 1,    // High entropy triggered Layer 3 deliberative fallback
    TIMEOUT_ESCALATE = 2     // Circuit breaker tripped (safe degradation)
};

// Typed Decision Primitives
struct ChoiceResult {
    uint32_t choice_id{0};
    std::string label{""};
    float confidence{0.0f};        // Calibrated probability
};

struct ScoreResult {
    float score{0.0f};             // Continuous bounded scalar [0.0, 1.0]
    float variance{0.0f};          // Uncertainty estimate
};

struct NoulResult {
    bool value{false};             // Boolean state (True / False)
    float probability{0.0f};       // P(True)
    bool is_null{false};           // True if uncertainty exceeds ambiguity threshold
};

// Mathematically Guaranteed Conformal Prediction Set
struct ConformalSet {
    float alpha{0.01f};                   // Error tolerance (e.g. 0.01 for 99% coverage)
    std::vector<uint32_t> valid_labels;   // Labels guaranteed to contain true class with >= 1 - alpha probability
    bool is_singleton{false};             // True if set size == 1 (high decisive certainty)
};

// Action Execution Hook callback signature for Tier 1 Fast-Path
using ActionExecutionHook = std::function<bool(uint32_t leaf_id, const std::string& context, std::string& out_status)>;

// Self-Learning RLCD (Reinforcement Learning from Conformal Deliberation) status
enum class RLCDLearningType : uint8_t {
    NONE = 0,
    REINFORCED_EXISTING_LEAF = 1,  // High cosine similarity: updated/reinforced existing weight vector
    EXPANDED_NEW_LEAF = 2         // Novel operational intent: safely spawned new leaf in sector
};

// Closed-Loop Tier 3 -> Tier 1 Execution & Learning Feedback
struct ExecutionFeedback {
    bool tier3_to_tier1_dispatched{false};
    bool action_executed{false};
    uint32_t executed_leaf_id{0};
    std::string execution_status{""};
    RLCDLearningType rlcd_learning{RLCDLearningType::NONE};
    std::string target_leaf_name{""};
    uint32_t target_sector_id{0};
};

// Unified Output Package
struct alignas(64) DecisionResult {
    uint32_t request_id{0};
    ExecutionPath path{ExecutionPath::FAST_PATH_COMMIT};
    
    // Core decision primitives
    ChoiceResult choice;
    ScoreResult score;
    NoulResult noul;
    
    // Rigorous statistical calibration
    float shannon_entropy{0.0f};
    ConformalSet conformal_set;
    
    // Closed-loop Tier 3 -> Tier 1 and RLCD learning telemetry
    ExecutionFeedback feedback;

    // Microsecond telemetry profiling
    double latency_layer1_us{0.0};
    double latency_layer2_us{0.0};
    double latency_layer3_us{0.0};
    double latency_total_us{0.0};

    bool is_successful() const {
        return path == ExecutionPath::FAST_PATH_COMMIT || path == ExecutionPath::SYSTEM2_FALLBACK;
    }
};

// Schema Definition Primitives
struct LeafDefinition {
    uint32_t leaf_id;
    std::string name;
    std::string description;
};

struct SectorDefinition {
    uint32_t sector_id;
    std::string name;
    std::vector<LeafDefinition> leaves;
};

struct SchemaDefinition {
    std::string schema_id;
    std::string domain;
    std::vector<SectorDefinition> sectors;
    float entropy_threshold = 0.15f;     // Normalized Shannon entropy threshold
    float confidence_threshold = 0.85f;  // Minimum leaf probability for fast-path commit
    float conformal_alpha = 0.01f;       // 99% statistical coverage
};

} // namespace axiom
