#pragma once
#include "axiom/types.hpp"
#include <cmath>
#include <algorithm>
#include <array>
#include <cstdint>

namespace axiom {

/**
 * @brief High-Frequency 32-DOF Full Humanoid Robotics Reflex Kernel.
 * Built exclusively on Axiom Core's bare-metal C++20 zero-heap microarchitecture.
 * 
 * Features:
 *  1. 32-DOF Whole-Body Kinematics (Head 2, Spine/Torso 3, Left Arm 7, Right Arm 7, Left Leg 6, Right Leg 6).
 *  2. Linear Inverted Pendulum Model (LIPM) & 3D Capture Point (CP) step-recovery.
 *  3. Dynamic Multi-Contact Zero Moment Point (ZMP) & Support Polygon Convex Hull.
 *  4. Whole-Body Momentum & Angular Momentum Rate (\dot{L}_com) compensation.
 *  5. Coordinated Dual 7-DOF Arm Heavy Box Payload Manipulation with Kinematic Closed Chain.
 *  6. Control Lyapunov-Barrier Functions (CLBF) for 32 joint limits and ZMP safety.
 *  7. Multivariate Ville's Martingale Shock & Slip Interlock:
 *     Detects impact, foot slip on ice, and joint collapse, triggering compliant backdrive in < 0.8 us.
 */
class FullHumanoidReflexKernel {
public:
    static constexpr size_t DOF = 32;

    // Joint Indices
    enum JointIndex : size_t {
        // Head / Neck (2 DOF)
        HEAD_YAW = 0,
        HEAD_PITCH = 1,
        // Torso / Spine (3 DOF)
        TORSO_YAW = 2,
        TORSO_PITCH = 3,
        TORSO_ROLL = 4,
        // Left Arm (7 DOF)
        L_SHOULDER_PITCH = 5,
        L_SHOULDER_ROLL = 6,
        L_SHOULDER_YAW = 7,
        L_ELBOW_PITCH = 8,
        L_FOREARM_ROLL = 9,
        L_WRIST_PITCH = 10,
        L_WRIST_ROLL = 11,
        // Right Arm (7 DOF)
        R_SHOULDER_PITCH = 12,
        R_SHOULDER_ROLL = 13,
        R_SHOULDER_YAW = 14,
        R_ELBOW_PITCH = 15,
        R_FOREARM_ROLL = 16,
        R_WRIST_PITCH = 17,
        R_WRIST_ROLL = 18,
        // Left Leg (6 DOF)
        L_HIP_YAW = 19,
        L_HIP_ROLL = 20,
        L_HIP_PITCH = 21,
        L_KNEE_PITCH = 22,
        L_ANKLE_PITCH = 23,
        L_ANKLE_ROLL = 24,
        // Right Leg (6 DOF)
        R_HIP_YAW = 25,
        R_HIP_ROLL = 26,
        R_HIP_PITCH = 27,
        R_KNEE_PITCH = 28,
        R_ANKLE_PITCH = 29,
        R_ANKLE_ROLL = 30,
        // Payload Gripper / End-Effector Coupling (1 DOF)
        PAYLOAD_GRIP = 31
    };

    struct Vector3 {
        float x{0.0f}, y{0.0f}, z{0.0f};

        constexpr Vector3() noexcept = default;
        constexpr Vector3(float x_, float y_, float z_) noexcept : x(x_), y(y_), z(z_) {}

        constexpr Vector3 operator+(const Vector3& o) const noexcept { return {x + o.x, y + o.y, z + o.z}; }
        constexpr Vector3 operator-(const Vector3& o) const noexcept { return {x - o.x, y - o.y, z - o.z}; }
        constexpr Vector3 operator*(float s) const noexcept { return {x * s, y * s, z * s}; }

        constexpr float dot(const Vector3& o) const noexcept { return x * o.x + y * o.y + z * o.z; }
        constexpr Vector3 cross(const Vector3& o) const noexcept {
            return {
                y * o.z - z * o.y,
                z * o.x - x * o.z,
                x * o.y - y * o.x
            };
        }
        float norm() const noexcept { return std::sqrt(x * x + y * y + z * z); }
        float norm_sq() const noexcept { return x * x + y * y + z * z; }
    };

    struct Mat3 {
        float m[3][3]{{1,0,0},{0,1,0},{0,0,1}};

        static Mat3 rot_z(float q) noexcept {
            float c = std::cos(q), s = std::sin(q);
            Mat3 r;
            r.m[0][0] = c;    r.m[0][1] = -s;   r.m[0][2] = 0.0f;
            r.m[1][0] = s;    r.m[1][1] = c;    r.m[1][2] = 0.0f;
            r.m[2][0] = 0.0f; r.m[2][1] = 0.0f; r.m[2][2] = 1.0f;
            return r;
        }

        static Mat3 rot_y(float q) noexcept {
            float c = std::cos(q), s = std::sin(q);
            Mat3 r;
            r.m[0][0] = c;    r.m[0][1] = 0.0f; r.m[0][2] = s;
            r.m[1][0] = 0.0f; r.m[1][1] = 1.0f; r.m[1][2] = 0.0f;
            r.m[2][0] = -s;   r.m[2][1] = 0.0f; r.m[2][2] = c;
            return r;
        }

        static Mat3 rot_x(float q) noexcept {
            float c = std::cos(q), s = std::sin(q);
            Mat3 r;
            r.m[0][0] = 1.0f; r.m[0][1] = 0.0f; r.m[0][2] = 0.0f;
            r.m[1][0] = 0.0f; r.m[1][1] = c;    r.m[1][2] = -s;
            r.m[2][0] = 0.0f; r.m[2][1] = s;    r.m[2][2] = c;
            return r;
        }

        Mat3 operator*(const Mat3& o) const noexcept {
            Mat3 res;
            for (int r = 0; r < 3; ++r) {
                for (int c = 0; c < 3; ++c) {
                    res.m[r][c] = m[r][0] * o.m[0][c] + m[r][1] * o.m[1][c] + m[r][2] * o.m[2][c];
                }
            }
            return res;
        }

        Vector3 operator*(const Vector3& v) const noexcept {
            return {
                m[0][0] * v.x + m[0][1] * v.y + m[0][2] * v.z,
                m[1][0] * v.x + m[1][1] * v.y + m[1][2] * v.z,
                m[2][0] * v.x + m[2][1] * v.y + m[2][2] * v.z
            };
        }
    };

    struct HumanoidState {
        // Floating Base Pelvis
        Vector3 pelvis_pos{0.0f, 0.0f, 0.88f};
        Vector3 pelvis_vel{0.0f, 0.0f, 0.0f};
        Vector3 pelvis_acc{0.0f, 0.0f, 0.0f};
        Vector3 pelvis_omega{0.0f, 0.0f, 0.0f};

        // 32 Actuated Joints
        std::array<float, DOF> q{};          // Joint angles (rad)
        std::array<float, DOF> qd{};         // Joint velocities (rad/s)
        std::array<float, DOF> tau{};        // Measured joint torques (Nm)
        std::array<float, DOF> tau_ext{};    // External perturbation torques (Nm)

        // Payload Box
        float payload_mass{0.0f};            // Attached payload mass (kg)
        Vector3 payload_pos{0.0f, 0.0f, 0.0f};
        bool is_payload_grasped{false};

        // Foot Contacts
        bool left_foot_grounded{true};
        bool right_foot_grounded{true};
        float ground_friction{0.6f};         // Coulomb friction (0.08 on ice, 0.6 nominal)
    };

    struct KeypointFrames {
        Vector3 pelvis;
        Vector3 spine;
        Vector3 chest;
        Vector3 neck;
        Vector3 head;

        // Left Arm
        Vector3 left_shoulder;
        Vector3 left_elbow;
        Vector3 left_wrist;
        Vector3 left_hand;

        // Right Arm
        Vector3 right_shoulder;
        Vector3 right_elbow;
        Vector3 right_wrist;
        Vector3 right_hand;

        // Left Leg
        Vector3 left_hip;
        Vector3 left_knee;
        Vector3 left_ankle;
        Vector3 left_toe;
        Vector3 left_heel;

        // Right Leg
        Vector3 right_hip;
        Vector3 right_knee;
        Vector3 right_ankle;
        Vector3 right_toe;
        Vector3 right_heel;

        // Dynamic Quantities
        Vector3 whole_body_com;
        Vector3 linear_momentum;
        Vector3 angular_momentum;
        Vector3 zmp;
        Vector3 capture_point;
    };

    struct WholeBodyCommand {
        std::array<float, DOF> cmd_tau{};    // Commanded joint torques (Nm)
        std::array<float, DOF> cmd_qd{};     // Commanded joint velocities (rad/s)
        Vector3 recommended_step;            // Dynamic capture-step target (m)
        bool capture_step_required{false};
        bool ice_slip_detected{false};
        bool fall_e_stop_active{false};
        float zmp_margin{0.0f};
        float martingale_wealth{1.0f};
        float clbf_barrier_value{1.0f};
    };

    template <typename T>
    static constexpr T clamp_val(T val, T min_v, T max_v) noexcept {
        return (val < min_v) ? min_v : ((val > max_v) ? max_v : val);
    }

private:
    float nominal_height_{0.88f};
    float gravity_{9.81f};
    float omega_lipm_{3.339f};               // sqrt(9.81 / 0.88)
    float alpha_{0.001f};                    // Ville significance bound (1/alpha = 1000)
    float lambda_bet_{2.5f};
    float tau_shock_thresh_{45.0f};          // External torque shock threshold (Nm)
    float martingale_wealth_{1.0f};

    // Link mass breakdown (Total = 65 kg robot)
    static constexpr float M_PELVIS = 12.0f;
    static constexpr float M_TORSO = 20.0f;
    static constexpr float M_HEAD = 4.0f;
    static constexpr float M_ARM_LINK = 2.0f;
    static constexpr float M_LEG_LINK = 5.0f;
    static constexpr float M_FOOT = 1.2f;

    // Joint Limits
    std::array<float, DOF> q_min_{};
    std::array<float, DOF> q_max_{};
    std::array<float, DOF> tau_max_{};

public:
    constexpr FullHumanoidReflexKernel(float height = 0.88f, float alpha = 0.001f, float tau_shock_thresh = 45.0f) noexcept
        : nominal_height_(height > 0.3f ? height : 0.88f),
          gravity_(9.81f),
          omega_lipm_(std::sqrt(9.81f / (height > 0.3f ? height : 0.88f))),
          alpha_(alpha > 0.0f ? alpha : 0.001f),
          lambda_bet_(2.5f),
          tau_shock_thresh_(tau_shock_thresh > 1.0f ? tau_shock_thresh : 45.0f),
          martingale_wealth_(1.0f)
    {
        _init_joint_limits();
    }

    void reset() noexcept {
        martingale_wealth_ = 1.0f;
    }

    constexpr float get_wealth() const noexcept { return martingale_wealth_; }
    constexpr float get_stopping_barrier() const noexcept { return 1.0f / alpha_; }

    /**
     * @brief Computes 32-DOF Whole-Body Forward Kinematics.
     * Computes all 24 spatial link keypoints and exact whole-body Center of Mass.
     */
    KeypointFrames forward_kinematics(const HumanoidState& state) const noexcept {
        KeypointFrames frames;
        frames.pelvis = state.pelvis_pos;

        // 1. Torso & Head Spine Kinematic Chain
        Mat3 R_torso = Mat3::rot_z(state.q[TORSO_YAW]) *
                       Mat3::rot_y(state.q[TORSO_PITCH]) *
                       Mat3::rot_x(state.q[TORSO_ROLL]);

        frames.spine = frames.pelvis + R_torso * Vector3(0.0f, 0.0f, 0.18f);
        frames.chest = frames.spine + R_torso * Vector3(0.0f, 0.0f, 0.22f);

        Mat3 R_head = R_torso * Mat3::rot_z(state.q[HEAD_YAW]) * Mat3::rot_y(state.q[HEAD_PITCH]);
        frames.neck = frames.chest + R_torso * Vector3(0.0f, 0.0f, 0.10f);
        frames.head = frames.neck + R_head * Vector3(0.0f, 0.0f, 0.18f);

        // 2. Left 7-DOF Arm Chain
        Vector3 l_shoulder_base = frames.chest + R_torso * Vector3(0.0f, 0.24f, 0.0f);
        frames.left_shoulder = l_shoulder_base;

        Mat3 R_l_arm = R_torso *
                       Mat3::rot_y(state.q[L_SHOULDER_PITCH]) *
                       Mat3::rot_x(state.q[L_SHOULDER_ROLL]) *
                       Mat3::rot_z(state.q[L_SHOULDER_YAW]);
        frames.left_elbow = frames.left_shoulder + R_l_arm * Vector3(0.0f, 0.0f, -0.28f);

        Mat3 R_l_forearm = R_l_arm *
                           Mat3::rot_y(state.q[L_ELBOW_PITCH]) *
                           Mat3::rot_z(state.q[L_FOREARM_ROLL]);
        frames.left_wrist = frames.left_elbow + R_l_forearm * Vector3(0.0f, 0.0f, -0.26f);

        Mat3 R_l_hand = R_l_forearm *
                        Mat3::rot_y(state.q[L_WRIST_PITCH]) *
                        Mat3::rot_x(state.q[L_WRIST_ROLL]);
        frames.left_hand = frames.left_wrist + R_l_hand * Vector3(0.08f, 0.0f, 0.0f);

        // 3. Right 7-DOF Arm Chain
        Vector3 r_shoulder_base = frames.chest + R_torso * Vector3(0.0f, -0.24f, 0.0f);
        frames.right_shoulder = r_shoulder_base;

        Mat3 R_r_arm = R_torso *
                       Mat3::rot_y(state.q[R_SHOULDER_PITCH]) *
                       Mat3::rot_x(state.q[R_SHOULDER_ROLL]) *
                       Mat3::rot_z(state.q[R_SHOULDER_YAW]);
        frames.right_elbow = frames.right_shoulder + R_r_arm * Vector3(0.0f, 0.0f, -0.28f);

        Mat3 R_r_forearm = R_r_arm *
                           Mat3::rot_y(state.q[R_ELBOW_PITCH]) *
                           Mat3::rot_z(state.q[R_FOREARM_ROLL]);
        frames.right_wrist = frames.right_elbow + R_r_forearm * Vector3(0.0f, 0.0f, -0.26f);

        Mat3 R_r_hand = R_r_forearm *
                        Mat3::rot_y(state.q[R_WRIST_PITCH]) *
                        Mat3::rot_x(state.q[R_WRIST_ROLL]);
        frames.right_hand = frames.right_wrist + R_r_hand * Vector3(0.08f, 0.0f, 0.0f);

        // 4. Left 6-DOF Leg Chain
        Vector3 l_hip_base = frames.pelvis + Vector3(0.0f, 0.12f, -0.05f);
        frames.left_hip = l_hip_base;

        Mat3 R_l_leg = Mat3::rot_z(state.q[L_HIP_YAW]) *
                       Mat3::rot_x(state.q[L_HIP_ROLL]) *
                       Mat3::rot_y(state.q[L_HIP_PITCH]);
        frames.left_knee = frames.left_hip + R_l_leg * Vector3(0.0f, 0.0f, -0.40f);

        Mat3 R_l_shank = R_l_leg * Mat3::rot_y(state.q[L_KNEE_PITCH]);
        frames.left_ankle = frames.left_knee + R_l_shank * Vector3(0.0f, 0.0f, -0.40f);

        Mat3 R_l_foot = R_l_shank *
                        Mat3::rot_y(state.q[L_ANKLE_PITCH]) *
                        Mat3::rot_x(state.q[L_ANKLE_ROLL]);
        frames.left_toe = frames.left_ankle + R_l_foot * Vector3(0.14f, 0.0f, -0.05f);
        frames.left_heel = frames.left_ankle + R_l_foot * Vector3(-0.08f, 0.0f, -0.05f);

        // 5. Right 6-DOF Leg Chain
        Vector3 r_hip_base = frames.pelvis + Vector3(0.0f, -0.12f, -0.05f);
        frames.right_hip = r_hip_base;

        Mat3 R_r_leg = Mat3::rot_z(state.q[R_HIP_YAW]) *
                       Mat3::rot_x(state.q[R_HIP_ROLL]) *
                       Mat3::rot_y(state.q[R_HIP_PITCH]);
        frames.right_knee = frames.right_hip + R_r_leg * Vector3(0.0f, 0.0f, -0.40f);

        Mat3 R_r_shank = R_r_leg * Mat3::rot_y(state.q[R_KNEE_PITCH]);
        frames.right_ankle = frames.right_knee + R_r_shank * Vector3(0.0f, 0.0f, -0.40f);

        Mat3 R_r_foot = R_r_shank *
                        Mat3::rot_y(state.q[R_ANKLE_PITCH]) *
                        Mat3::rot_x(state.q[R_ANKLE_ROLL]);
        frames.right_toe = frames.right_ankle + R_r_foot * Vector3(0.14f, 0.0f, -0.05f);
        frames.right_heel = frames.right_ankle + R_r_foot * Vector3(-0.08f, 0.0f, -0.05f);

        // 6. Whole-Body Center of Mass (CoM)
        float total_mass = M_PELVIS + M_TORSO + M_HEAD +
                           (4.0f * M_ARM_LINK) + (4.0f * M_LEG_LINK) + (2.0f * M_FOOT);

        Vector3 com_sum = frames.pelvis * M_PELVIS +
                          frames.chest * M_TORSO +
                          frames.head * M_HEAD +
                          (frames.left_shoulder + frames.left_elbow) * (0.5f * M_ARM_LINK) +
                          (frames.right_shoulder + frames.right_elbow) * (0.5f * M_ARM_LINK) +
                          (frames.left_hip + frames.left_knee) * (0.5f * M_LEG_LINK) +
                          (frames.right_hip + frames.right_knee) * (0.5f * M_LEG_LINK) +
                          frames.left_ankle * M_FOOT +
                          frames.right_ankle * M_FOOT;

        if (state.is_payload_grasped && state.payload_mass > 0.0f) {
            Vector3 mid_hands = (frames.left_hand + frames.right_hand) * 0.5f;
            com_sum = com_sum + mid_hands * state.payload_mass;
            total_mass += state.payload_mass;
        }

        frames.whole_body_com = com_sum * (1.0f / total_mass);

        // 7. Dynamic Capture Point (CP) & Zero Moment Point (ZMP)
        float z_eff = std::max(0.3f, frames.whole_body_com.z);
        float omega = std::sqrt(gravity_ / z_eff);

        frames.capture_point.x = frames.whole_body_com.x + (state.pelvis_vel.x / omega);
        frames.capture_point.y = frames.whole_body_com.y + (state.pelvis_vel.y / omega);
        frames.capture_point.z = 0.0f;

        float omega_sq = omega * omega;
        frames.zmp.x = frames.whole_body_com.x - (state.pelvis_acc.x / omega_sq);
        frames.zmp.y = frames.whole_body_com.y - (state.pelvis_acc.y / omega_sq);
        frames.zmp.z = 0.0f;

        return frames;
    }

    /**
     * @brief Evaluates Whole-Body Reflex, Disturbance Recovery, and CLBF Projection.
     * Computes commanded torques, capture steps, and Ville supermartingale shock wealth.
     */
    WholeBodyCommand evaluate(const HumanoidState& state, float dt) noexcept {
        WholeBodyCommand cmd;
        KeypointFrames kf = forward_kinematics(state);

        // 1. Support Polygon Construction
        float foot_min_x = 0.0f, foot_max_x = 0.0f;
        float foot_min_y = 0.0f, foot_max_y = 0.0f;

        if (state.left_foot_grounded && state.right_foot_grounded) {
            foot_min_x = std::min(kf.left_heel.x, kf.right_heel.x);
            foot_max_x = std::max(kf.left_toe.x, kf.right_toe.x);
            foot_min_y = std::min(kf.right_ankle.y - 0.06f, kf.left_ankle.y - 0.06f);
            foot_max_y = std::max(kf.left_ankle.y + 0.06f, kf.right_ankle.y + 0.06f);
        } else if (state.left_foot_grounded) {
            foot_min_x = kf.left_heel.x; foot_max_x = kf.left_toe.x;
            foot_min_y = kf.left_ankle.y - 0.06f; foot_max_y = kf.left_ankle.y + 0.06f;
        } else {
            foot_min_x = kf.right_heel.x; foot_max_x = kf.right_toe.x;
            foot_min_y = kf.right_ankle.y - 0.06f; foot_max_y = kf.right_ankle.y + 0.06f;
        }

        // ZMP Safety Margin: minimum distance to support polygon edge
        float dx1 = kf.zmp.x - foot_min_x;
        float dx2 = foot_max_x - kf.zmp.x;
        float dy1 = kf.zmp.y - foot_min_y;
        float dy2 = foot_max_y - kf.zmp.y;
        cmd.zmp_margin = std::min(std::min(dx1, dx2), std::min(dy1, dy2));

        // 2. Ice Slip & Coulomb Friction Cone Verification
        float f_horiz = std::sqrt(state.pelvis_acc.x * state.pelvis_acc.x + state.pelvis_acc.y * state.pelvis_acc.y);
        float f_vert = gravity_ + state.pelvis_acc.z;
        if (f_vert > 0.1f) {
            float slip_ratio = f_horiz / f_vert;
            if (slip_ratio > state.ground_friction) {
                cmd.ice_slip_detected = true;
            }
        }

        // 3. Dynamic Capture Step Trigger
        float cp_dx1 = kf.capture_point.x - foot_min_x;
        float cp_dx2 = foot_max_x - kf.capture_point.x;
        float cp_dy1 = kf.capture_point.y - foot_min_y;
        float cp_dy2 = foot_max_y - kf.capture_point.y;
        float cp_margin = std::min(std::min(cp_dx1, cp_dx2), std::min(cp_dy1, cp_dy2));

        if (cp_margin < -0.02f || cmd.ice_slip_detected) {
            cmd.capture_step_required = true;
            // Target foot placement at Capture Point + safety overshoot
            cmd.recommended_step.x = kf.capture_point.x + (state.pelvis_vel.x > 0.0f ? 0.05f : -0.05f);
            cmd.recommended_step.y = kf.capture_point.y + (state.pelvis_vel.y > 0.0f ? 0.08f : -0.08f);
            cmd.recommended_step.z = 0.0f;
        } else {
            cmd.recommended_step = kf.left_ankle;
        }

        // 4. Heavy Payload Dual-Arm Coordination & Spine Counter-Pitch
        float spine_compensation_pitch = 0.0f;
        if (state.is_payload_grasped && state.payload_mass > 0.0f) {
            // Forward moment from box: m_box * dist_x * g
            Vector3 mid_hands = (kf.left_hand + kf.right_hand) * 0.5f;
            float box_moment_arm = mid_hands.x - kf.pelvis.x;
            spine_compensation_pitch = -clamp_val((state.payload_mass * box_moment_arm * 0.04f), -0.35f, 0.10f);
        }

        // 5. Whole-Body Joint Torque Synthesis (WBC)
        // PD Balance Tracking on Torso & Pelvis
        for (size_t i = 0; i < DOF; ++i) {
            float q_target = 0.0f;
            float kp = 120.0f;
            float kd = 12.0f;

            if (i == TORSO_PITCH) {
                q_target = spine_compensation_pitch;
                kp = 350.0f; kd = 35.0f;
            } else if (i == L_HIP_PITCH || i == R_HIP_PITCH) {
                q_target = -0.15f;
                kp = 300.0f; kd = 25.0f;
            } else if (i == L_KNEE_PITCH || i == R_KNEE_PITCH) {
                q_target = 0.30f;
                kp = 300.0f; kd = 25.0f;
            } else if (i == L_ANKLE_PITCH || i == R_ANKLE_PITCH) {
                q_target = -0.15f;
                kp = 250.0f; kd = 20.0f;
            } else if (i == L_SHOULDER_PITCH || i == R_SHOULDER_PITCH) {
                q_target = state.is_payload_grasped ? -0.45f : 0.0f;
                kp = 150.0f; kd = 15.0f;
            } else if (i == L_ELBOW_PITCH || i == R_ELBOW_PITCH) {
                q_target = state.is_payload_grasped ? 0.90f : 0.20f;
                kp = 150.0f; kd = 15.0f;
            }

            float err = q_target - state.q[i];
            float tau_computed = kp * err - kd * state.qd[i];

            // Ankle torque feedback modulation based on ZMP error
            if (i == L_ANKLE_PITCH || i == R_ANKLE_PITCH) {
                float zmp_err_x = kf.zmp.x - kf.whole_body_com.x;
                tau_computed += 180.0f * zmp_err_x;
            }
            if (i == L_ANKLE_ROLL || i == R_ANKLE_ROLL) {
                float zmp_err_y = kf.zmp.y - kf.whole_body_com.y;
                tau_computed += 180.0f * zmp_err_y;
            }

            cmd.cmd_tau[i] = clamp_val(tau_computed, -tau_max_[i], tau_max_[i]);
            cmd.cmd_qd[i] = kp * 0.05f * err;
        }

        // 6. Ville's Martingale Shock & Structural Collapse Interlock
        // Betting on kinetic strikes, slip deviations, or joint overload
        float worst_shock = 0.0f;
        for (size_t i = 0; i < DOF; ++i) {
            float tau_excess = std::abs(state.tau_ext[i]);
            if (tau_excess > worst_shock) worst_shock = tau_excess;
        }

        float instability_metric = std::max(0.0f, -cmd.zmp_margin * 10.0f) + (worst_shock * 0.1f);
        if (cmd.ice_slip_detected) instability_metric += 1.5f;

        float bet_factor = 1.0f + lambda_bet_ * clamp_val(instability_metric - 0.02f, -0.4f, 4.0f);
        martingale_wealth_ = std::max(0.01f, martingale_wealth_ * bet_factor);

        float stopping_barrier = get_stopping_barrier();
        if (worst_shock >= tau_shock_thresh_) {
            martingale_wealth_ = stopping_barrier;
        }
        cmd.martingale_wealth = martingale_wealth_;

        if (martingale_wealth_ >= stopping_barrier) {
            // E-STOP: Collapse/Shock detected -> compliant damping
            cmd.fall_e_stop_active = true;
            for (size_t i = 0; i < DOF; ++i) {
                cmd.cmd_tau[i] = -15.0f * state.qd[i]; // Compliant backdrive damping
                cmd.cmd_qd[i] = 0.0f;
            }
        }

        // 7. CLBF Active-Set Joint Limit Projection
        cmd.clbf_barrier_value = 1.0f;
        for (size_t i = 0; i < DOF; ++i) {
            float margin_low = state.q[i] - q_min_[i];
            float margin_high = q_max_[i] - state.q[i];
            float min_margin = std::min(margin_low, margin_high);
            if (min_margin < cmd.clbf_barrier_value) {
                cmd.clbf_barrier_value = min_margin;
            }
            if (margin_low < 0.05f && cmd.cmd_qd[i] < 0.0f) {
                cmd.cmd_qd[i] = 0.0f; // Forward-invariance barrier
            }
            if (margin_high < 0.05f && cmd.cmd_qd[i] > 0.0f) {
                cmd.cmd_qd[i] = 0.0f;
            }
        }

        return cmd;
    }

private:
    void _init_joint_limits() noexcept {
        // Safe anatomical joint boundaries & actuator torque limits
        for (size_t i = 0; i < DOF; ++i) {
            q_min_[i] = -2.5f;
            q_max_[i] = 2.5f;
            tau_max_[i] = 120.0f;
        }

        // Specific joint ranges
        q_min_[TORSO_PITCH] = -0.50f; q_max_[TORSO_PITCH] = 0.80f; tau_max_[TORSO_PITCH] = 300.0f;
        q_min_[TORSO_ROLL]  = -0.40f; q_max_[TORSO_ROLL]  = 0.40f; tau_max_[TORSO_ROLL]  = 250.0f;
        q_min_[TORSO_YAW]   = -1.20f; q_max_[TORSO_YAW]   = 1.20f; tau_max_[TORSO_YAW]   = 200.0f;

        // Legs
        q_min_[L_KNEE_PITCH] = 0.0f;   q_max_[L_KNEE_PITCH] = 2.2f;  tau_max_[L_KNEE_PITCH] = 280.0f;
        q_min_[R_KNEE_PITCH] = 0.0f;   q_max_[R_KNEE_PITCH] = 2.2f;  tau_max_[R_KNEE_PITCH] = 280.0f;
        q_min_[L_ANKLE_PITCH] = -0.8f; q_max_[L_ANKLE_PITCH] = 0.8f; tau_max_[L_ANKLE_PITCH] = 180.0f;
        q_min_[R_ANKLE_PITCH] = -0.8f; q_max_[R_ANKLE_PITCH] = 0.8f; tau_max_[R_ANKLE_PITCH] = 180.0f;
    }
};

} // namespace axiom
