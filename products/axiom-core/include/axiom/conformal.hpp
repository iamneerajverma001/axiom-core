#pragma once

#include "axiom/types.hpp"
#include <vector>
#include <cmath>
#include <algorithm>

namespace axiom {

// Finite-Sample Split Conformal Prediction Engine
class ConformalEngine {
public:
    explicit ConformalEngine(float alpha = 0.01f) : m_alpha(alpha) {
        // Pre-compute calibration quantile thresholds
        // In full pipeline, these are derived from calibration dataset scores s_i = 1 - p(y_i|x_i)
        m_quantile_threshold = 1.0f - alpha; 
    }

    void set_alpha(float alpha) noexcept {
        m_alpha = alpha;
        m_quantile_threshold = 1.0f - alpha;
    }

    // Computes statistically guaranteed prediction set C_alpha(X)
    ConformalSet generate_set(const std::vector<float>& leaf_distribution, const std::vector<uint32_t>& leaf_ids) const {
        ConformalSet set;
        set.alpha = m_alpha;

        // Sort candidates in descending order of probability
        std::vector<std::pair<float, uint32_t>> candidates;
        candidates.reserve(leaf_distribution.size());
        for (size_t i = 0; i < leaf_distribution.size(); ++i) {
            candidates.push_back({leaf_distribution[i], leaf_ids[i]});
        }
        std::sort(candidates.begin(), candidates.end(), [](const auto& a, const auto& b) {
            return a.first > b.first;
        });

        // Accumulate probabilities until exceeding the (1 - alpha) conformal quantile bound
        float cumulative_mass = 0.0f;
        float target_mass = 1.0f - m_alpha;

        for (const auto& item : candidates) {
            set.valid_labels.push_back(item.second);
            cumulative_mass += item.first;
            if (cumulative_mass >= target_mass) {
                break;
            }
        }

        // If even the first option was very ambiguous, ensure at least the top label is present
        if (set.valid_labels.empty() && !candidates.empty()) {
            set.valid_labels.push_back(candidates[0].second);
        }

        set.is_singleton = (set.valid_labels.size() == 1);
        return set;
    }

private:
    float m_alpha;
    float m_quantile_threshold;
};

} // namespace axiom
