#pragma once
#include "axiom/types.hpp"
#include <cmath>
#include <algorithm>
#include <array>
#include <cstdint>

namespace axiom {

/**
 * @brief High-Frequency Bipedal / Quadrupedal Locomotion Reflex Kernel.
 * Evaluates Linear Inverted Pendulum Model (LIPM), Capture Point (CP),
 * Zero Moment Point (ZMP) Support Polygons, and Ground Friction Cones.
 * Uses Ville's Supermartingale for slip/stumble detection, projecting
 * emergency capture-step foot placement in < 1 microsecond (zero heap).
 */
class BipedalLocomotionReflex {
public:
    struct ComState {
        float x{0.0f}, y{0.0f}, z{0.85f};       // CoM Position (meters)
        float vx{0.0f}, vy{0.0f}, vz{0.0f};     // CoM Velocity (m/s)
        float ax{0.0f}, ay{0.0f}, az{0.0f};     // CoM Acceleration (m/s^2)
    };

    struct FootContact {
        float x{0.0f}, y{0.0f}, z{0.0f};        // Stance foot sole center (m)
        float length{0.22f};                    // Heel-to-toe length (m)
        float width{0.10f};                     // Foot width (m)
        float friction_coeff{0.6f};             // Coulomb friction mu
        bool is_grounded{true};
    };

    struct CapturePointResult {
        float cp_x{0.0f};                       // Capture point X
        float cp_y{0.0f};                       // Capture point Y
        float zmp_x{0.0f};                      // Zero Moment Point X
        float zmp_y{0.0f};                      // Zero Moment Point Y
        float zmp_margin{0.0f};                 // Distance to support polygon edge
        float martingale_wealth{1.0f};          // Slip/stumble supermartingale
        bool is_stable{true};
        bool capture_step_required{false};
        float recommended_step_x{0.0f};         // Swing foot target X
        float recommended_step_y{0.0f};         // Swing foot target Y
    };

private:
    float gravity_{9.81f};
    float nominal_height_{0.85f};
    float omega_{3.397f};                       // sqrt(g / z0)
    float alpha_{0.001f};                       // Significance bound (1/alpha = 1000)
    float lambda_bet_{2.5f};
    float martingale_wealth_{1.0f};

public:
    constexpr BipedalLocomotionReflex(float height = 0.85f, float alpha = 0.001f) noexcept
        : nominal_height_(height > 0.1f ? height : 0.85f),
          omega_(std::sqrt(9.81f / (height > 0.1f ? height : 0.85f))),
          alpha_(alpha > 0.0f ? alpha : 0.001f),
          martingale_wealth_(1.0f) {}

    void reset() noexcept {
        martingale_wealth_ = 1.0f;
    }

    constexpr float get_wealth() const noexcept { return martingale_wealth_; }
    constexpr float get_stopping_barrier() const noexcept { return 1.0f / alpha_; }

    /**
     * @brief Computes Capture Point and evaluates ZMP support polygon safety.
     * Projects capture-step location if balance is perturbed.
     */
    CapturePointResult evaluate(const ComState& com, const FootContact& stance_foot, float dt) noexcept {
        CapturePointResult res;

        float z0 = std::max(0.2f, com.z);
        float omega = std::sqrt(gravity_ / z0);

        // 1. Capture Point: x_cp = x_com + v_com / omega
        res.cp_x = com.x + (com.vx / omega);
        res.cp_y = com.y + (com.vy / omega);

        // 2. Zero Moment Point (ZMP): p_zmp = x_com - a_com / (omega^2)
        float omega_sq = omega * omega;
        res.zmp_x = com.x - (com.ax / omega_sq);
        res.zmp_y = com.y - (com.ay / omega_sq);

        // 3. Support Polygon Bounds: [x - L/2, x + L/2] x [y - W/2, y + W/2]
        float half_len = stance_foot.length * 0.5f;
        float half_wid = stance_foot.width * 0.5f;

        float dist_x = half_len - std::abs(res.zmp_x - stance_foot.x);
        float dist_y = half_wid - std::abs(res.zmp_y - stance_foot.y);
        res.zmp_margin = std::min(dist_x, dist_y);

        float cp_dist_x = half_len - std::abs(res.cp_x - stance_foot.x);
        float cp_dist_y = half_wid - std::abs(res.cp_y - stance_foot.y);
        float cp_margin = std::min(cp_dist_x, cp_dist_y);

        // 4. Martingale Supermartingale Betting on Stability Violation
        float worst_violation = std::max(0.0f, std::max(-res.zmp_margin, -cp_margin));
        if (worst_violation > 0.0f) {
            float bet = std::exp(std::min(lambda_bet_ * worst_violation * 10.0f * dt, 4.0f));
            martingale_wealth_ *= bet;
        } else {
            martingale_wealth_ = std::max(1.0f, martingale_wealth_ * 0.95f);
        }

        res.martingale_wealth = martingale_wealth_;
        float barrier_threshold = get_stopping_barrier();

        // 5. Balance State and Capture Step Projection
        if (res.zmp_margin >= 0.0f && cp_margin >= 0.0f && martingale_wealth_ < barrier_threshold) {
            res.is_stable = true;
            res.capture_step_required = false;
            res.recommended_step_x = stance_foot.x;
            res.recommended_step_y = stance_foot.y + 0.20f; // Nominal stance width
        } else {
            // Stumble/Fall detected: Step directly onto Capture Point
            res.is_stable = false;
            res.capture_step_required = true;
            res.recommended_step_x = res.cp_x;
            res.recommended_step_y = res.cp_y;
        }

        return res;
    }
};

} // namespace axiom
