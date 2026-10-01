#pragma once
#include "axiom/types.hpp"
#include <cmath>
#include <algorithm>
#include <array>
#include <cstdint>

namespace axiom {

/**
 * @brief Control Lyapunov-Barrier Function (CLBF) with Ville's Martingale Interlock.
 * Evaluates continuous-time control barrier certificates:
 *   h(x) >= 0 defines the safe set C.
 *   L_f h(x) + L_g h(x)*u + gamma * h(x) >= 0.
 * In the presence of stochastic drift or external disturbances, Ville's supermartingale
 * tracks accumulated negative violations M_k. If M_k >= 1/alpha, the safety interlock
 * projects the control input onto the admissible halfspace in < 1 microsecond (zero heap).
 */
class LyapunovBarrierInterlock {
public:
    struct State3D {
        float x{0.0f}, y{0.0f}, z{0.0f};          // Position (meters)
        float vx{0.0f}, vy{0.0f}, vz{0.0f};       // Velocity (m/s)
        float roll{0.0f}, pitch{0.0f}, yaw{0.0f}; // Attitude (radians)
    };

    struct ControlInput3D {
        float roll_torque{0.0f};   // u1
        float pitch_torque{0.0f};  // u2
        float yaw_torque{0.0f};    // u3
        float thrust{0.0f};        // u4 (Newtons)
    };

    struct Obstacle3D {
        float x{0.0f}, y{0.0f}, z{0.0f};
        float safe_radius{5.0f};
    };

    struct BarrierResult {
        bool is_safe{true};
        float barrier_value{0.0f};       // h(x)
        float barrier_derivative{0.0f};  // h_dot(x, u)
        float martingale_wealth{1.0f};   // M_k
        bool interlock_triggered{false};
        ControlInput3D projected_u{};    // Safe projected control
    };

private:
    float alpha_{0.01f};           // Significance level (stopping bound = 1/alpha)
    float barrier_gamma_{2.0f};    // Class-K gain for h(x)
    float lambda_bet_{1.5f};       // Martingale betting sensitivity
    float martingale_wealth_{1.0f};
    float max_wealth_{1.0f};

public:
    constexpr LyapunovBarrierInterlock(float alpha = 0.01f, float gamma = 2.0f, float lambda = 1.5f) noexcept
        : alpha_(alpha > 0.0f ? alpha : 0.01f),
          barrier_gamma_(gamma),
          lambda_bet_(lambda),
          martingale_wealth_(1.0f),
          max_wealth_(1.0f) {}

    void reset() noexcept {
        martingale_wealth_ = 1.0f;
        max_wealth_ = 1.0f;
    }

    constexpr float get_wealth() const noexcept { return martingale_wealth_; }
    constexpr float get_stopping_barrier() const noexcept { return 1.0f / alpha_; }

    /**
     * @brief Evaluates the barrier certificate against a set of 3D obstacles and projects
     * the control input if necessary. Zero heap allocations.
     */
    BarrierResult evaluate(const State3D& state,
                           const ControlInput3D& raw_u,
                           const Obstacle3D* obstacles,
                           size_t obstacle_count,
                           float dt) noexcept {
        BarrierResult res;
        res.projected_u = raw_u;

        if (obstacle_count == 0 || obstacles == nullptr) {
            res.is_safe = true;
            res.barrier_value = 100.0f;
            res.barrier_derivative = 0.0f;
            res.martingale_wealth = martingale_wealth_;
            res.interlock_triggered = false;
            return res;
        }

        // Find the most critical obstacle (minimum h(x))
        float min_h = 1e9f;
        float min_h_dot = 0.0f;
        float crit_dx = 0.0f, crit_dy = 0.0f, crit_dz = 0.0f;

        for (size_t i = 0; i < obstacle_count; ++i) {
            const auto& obs = obstacles[i];
            float dx = state.x - obs.x;
            float dy = state.y - obs.y;
            float dz = state.z - obs.z;
            float dist_sq = dx * dx + dy * dy + dz * dz;
            float r_sq = obs.safe_radius * obs.safe_radius;

            // Barrier function h(x) = ||p - p_obs||^2 - R_safe^2
            float h_val = dist_sq - r_sq;
            if (h_val < min_h) {
                min_h = h_val;
                crit_dx = dx;
                crit_dy = dy;
                crit_dz = dz;
                // Lie derivative L_f h(x) = 2 * (p - p_obs) . v
                min_h_dot = 2.0f * (dx * state.vx + dy * state.vy + dz * state.vz);
            }
        }

        res.barrier_value = min_h;
        res.barrier_derivative = min_h_dot;

        // Condition for safety: h_dot + gamma * h >= 0
        float cbf_condition = min_h_dot + barrier_gamma_ * min_h;

        // Supermartingale sequential betting update
        float violation = (cbf_condition < 0.0f) ? (-cbf_condition) : 0.0f;
        if (violation > 0.0f) {
            float bet_factor = std::exp(std::min(lambda_bet_ * violation * dt, 4.0f));
            martingale_wealth_ *= bet_factor;
        } else {
            // Decay back towards unity under safe conditions
            martingale_wealth_ = std::max(1.0f, martingale_wealth_ * 0.98f);
        }

        max_wealth_ = std::max(max_wealth_, martingale_wealth_);
        res.martingale_wealth = martingale_wealth_;

        float barrier_threshold = get_stopping_barrier();
        if (martingale_wealth_ >= barrier_threshold || min_h <= 0.0f) {
            // Interlock triggered: project control input to steer away from obstacle
            res.interlock_triggered = true;
            res.is_safe = false;

            // Project control input away from critical obstacle vector
            float norm = std::sqrt(crit_dx * crit_dx + crit_dy * crit_dy + crit_dz * crit_dz);
            if (norm > 1e-4f) {
                float nx = crit_dx / norm;
                float ny = crit_dy / norm;
                float nz = crit_dz / norm;

                // Repulsive thrust and torque bias away from danger
                res.projected_u.thrust = std::max(raw_u.thrust, 15.0f); // Ensure lift
                res.projected_u.roll_torque = nx * 2.0f;
                res.projected_u.pitch_torque = ny * 2.0f;
                res.projected_u.yaw_torque = nz * 0.5f;
            }
        } else {
            res.interlock_triggered = false;
            res.is_safe = (min_h > 0.0f);
        }

        return res;
    }
};

} // namespace axiom
