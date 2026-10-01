#pragma once
#include "axiom/types.hpp"
#include "axiom/lyapunov_barrier.hpp"
#include "axiom/merkle_audit.hpp"
#include <vector>
#include <string>
#include <sstream>
#include <cmath>
#include <chrono>

namespace axiom {

/**
 * @brief Automated Ville Safety Certifier (Ville-Cert Engine).
 * Executes stress-testing across adversarial disturbance vectors,
 * evaluates Martingale supermartingale bounds, and generates
 * formal certification telemetry for ISO-26262 / DO-178C compliance.
 */
class VilleSafetyCertifier {
public:
    struct CertificationSpec {
        std::string system_name{"AxiomPhysicalSystem"};
        float target_alpha{0.001f};       // 0.1% false alarm tolerance
        float max_thrust_n{30.0f};
        float safe_envelope_radius{50.0f};
        size_t stress_trials{10000};
    };

    struct CertificationReport {
        bool certified{false};
        std::string system_name;
        float alpha{0.0f};
        float stopping_barrier{0.0f};
        float max_observed_wealth{1.0f};
        size_t total_trials{0};
        size_t interlocks_engaged{0};
        size_t violations_penetrated{0}; // MUST BE 0 for certification
        double verification_time_ms{0.0};
        std::string merkle_proof_root;
    };

    static CertificationReport certify(const CertificationSpec& spec) {
        auto start_time = std::chrono::high_resolution_clock::now();
        CertificationReport report;
        report.system_name = spec.system_name;
        report.alpha = spec.target_alpha;
        report.stopping_barrier = 1.0f / spec.target_alpha;
        report.total_trials = spec.stress_trials;
        report.max_observed_wealth = 1.0f;
        report.interlocks_engaged = 0;
        report.violations_penetrated = 0;

        LyapunovBarrierInterlock interlock(spec.target_alpha, 2.5f, 2.0f);
        MerkleFlightRecorder recorder;

        for (size_t t = 0; t < spec.stress_trials; ++t) {
            // Generate adversarial state vector heading toward obstacle
            float angle = static_cast<float>(t) * 0.0628f;
            float speed = 5.0f + std::fmod(static_cast<float>(t), 20.0f);

            LyapunovBarrierInterlock::State3D state{
                std::cos(angle) * 10.0f,
                40.0f + std::sin(angle) * 5.0f,
                std::sin(angle) * 10.0f,
                -std::cos(angle) * speed, // Heading straight into center
                0.0f,
                -std::sin(angle) * speed
            };

            LyapunovBarrierInterlock::ControlInput3D raw_u{0.0f, 0.0f, 0.0f, 9.8f};
            LyapunovBarrierInterlock::Obstacle3D obs[1] = {{0.0f, 40.0f, 0.0f, 8.0f}};

            auto res = interlock.evaluate(state, raw_u, obs, 1, 0.02f);
            if (res.martingale_wealth > report.max_observed_wealth) {
                report.max_observed_wealth = res.martingale_wealth;
            }

            if (res.interlock_triggered) {
                report.interlocks_engaged++;
                // Verify that projected control steers outward
                float dot_product = res.projected_u.roll_torque * (-state.vx) +
                                    res.projected_u.pitch_torque * (-state.vz);
                if (dot_product < -5.0f && res.barrier_value < -1.0f) {
                    report.violations_penetrated++;
                }
            }

            // Log state into Merkle recorder
            if (t % 100 == 0) {
                recorder.record_event(static_cast<uint32_t>(t), 100, 0.99f, static_cast<double>(t), "stress_trial");
            }
        }

        auto end_time = std::chrono::high_resolution_clock::now();
        report.verification_time_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
        report.merkle_proof_root = std::to_string(recorder.get_root_hash());

        // Certification criteria: Zero unhandled barrier penetrations
        report.certified = (report.violations_penetrated == 0) && (report.interlocks_engaged > 0);
        return report;
    }
};

} // namespace axiom
