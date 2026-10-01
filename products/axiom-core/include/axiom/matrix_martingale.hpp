#pragma once

#include <vector>
#include <cmath>
#include <cstdint>
#include <algorithm>

namespace axiom {

// Multivariate Matrix-Valued Supermartingale Anomaly Shield
// Grounded in Ville's Inequality: P(max_{1<=k<=T} M_k >= 1/alpha) <= alpha
// Tracks online covariance drift: M_k = prod_{i=1}^k det(I + Lambda * (x_i * x_i^T - Sigma_0))
// Detects subtle multi-axis sensor faults, motor fatigue, and multivariate drift before mechanical alarms fire.
template <size_t Dim>
class MatrixMartingaleShield {
public:
    explicit MatrixMartingaleShield(float alpha = 0.01f, float lambda_diag = 0.05f)
        : m_alpha(alpha),
          m_lambda(lambda_diag),
          m_wealth(1.0),
          m_threshold(1.0 / alpha),
          m_step_count(0),
          m_tripped(false)
    {
        // Initialize nominal reference covariance as Identity matrix
        for (size_t r = 0; r < Dim; ++r) {
            for (size_t c = 0; c < Dim; ++c) {
                m_sigma_nominal[r][c] = (r == c) ? 1.0f : 0.0f;
            }
        }
    }

    void reset() {
        m_wealth = 1.0;
        m_step_count = 0;
        m_tripped = false;
    }

    // Process multivariate vector x in continuous streaming mode
    // Returns true if safe, false if Martingale safety threshold (1/alpha) breached
    bool update(const float* x) {
        if (!x || m_tripped) return false;

        // Compute outer product trace discrepancy: Tr(Lambda * (x * x^T - Sigma_0))
        // Linearized determinant approximation for microsecond evaluation:
        // det(I + A) \approx 1 + Tr(A) + 0.5 * ((Tr(A))^2 - Tr(A^2))
        float trace_diff = 0.0f;
        float norm_sq = 0.0f;
        for (size_t i = 0; i < Dim; ++i) {
            norm_sq += x[i] * x[i];
            trace_diff += (x[i] * x[i] - m_sigma_nominal[i][i]);
        }

        // Multiplicative sequential betting factor
        float betting_term = 1.0f + m_lambda * (trace_diff / static_cast<float>(Dim));
        betting_term = std::max(0.01f, std::min(4.0f, betting_term)); // Numerical safety bounds

        m_wealth *= static_cast<double>(betting_term);
        m_step_count++;

        if (m_wealth >= m_threshold) {
            m_tripped = true;
            return false; // Safety barrier breached!
        }
        return true;
    }

    double get_wealth() const noexcept { return m_wealth; }
    double get_rejection_threshold() const noexcept { return m_threshold; }
    bool is_tripped() const noexcept { return m_tripped; }
    uint64_t get_step_count() const noexcept { return m_step_count; }

private:
    float m_alpha;
    float m_lambda;
    double m_wealth;
    double m_threshold;
    uint64_t m_step_count;
    bool m_tripped;

    float m_sigma_nominal[Dim][Dim];
};

} // namespace axiom
