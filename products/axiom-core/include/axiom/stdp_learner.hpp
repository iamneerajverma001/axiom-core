#pragma once

#include <vector>
#include <cmath>
#include <cstdint>
#include <algorithm>

namespace axiom {

// Spike-Timing-Dependent Plasticity (STDP) Temporal Sequence Learner
// Learns causal temporal order across sequential operational events:
// - Strengthens synapse if Pre-synaptic neuron fires before Post-synaptic neuron (LTP)
// - Weakens synapse if Post-synaptic neuron fires before Pre-synaptic neuron (LTD)
class StdpLearner {
public:
    static constexpr size_t NUM_SYNAPSES = 256;

    StdpLearner(
        float a_plus = 0.015f,
        float a_minus = 0.018f,
        float tau_plus = 20.0f,
        float tau_minus = 20.0f
    ) : m_a_plus(a_plus),
        m_a_minus(a_minus),
        m_tau_plus(tau_plus),
        m_tau_minus(tau_minus)
    {
        reset_weights();
    }

    void reset_weights() {
        for (size_t i = 0; i < NUM_SYNAPSES; ++i) {
            m_weights[i] = 0.5f; // Initial neutral conductance
            m_last_pre_spike_time[i] = -1000.0f;
            m_last_post_spike_time[i] = -1000.0f;
        }
    }

    // Process pair of spike events with timestamp (milliseconds)
    // Updates synaptic strength based on causal delta_t = t_post - t_pre
    void update_synapse(size_t synapse_idx, float pre_time, float post_time) {
        if (synapse_idx >= NUM_SYNAPSES) return;

        float delta_t = post_time - pre_time;
        float delta_w = 0.0f;

        if (delta_t > 0.0f) {
            // Causal order: Pre precedes Post -> Long-Term Potentiation (LTP)
            delta_w = m_a_plus * std::exp(-delta_t / m_tau_plus);
        } else if (delta_t < 0.0f) {
            // Anti-causal order: Post precedes Pre -> Long-Term Depression (LTD)
            delta_w = -m_a_minus * std::exp(delta_t / m_tau_minus);
        }

        m_weights[synapse_idx] = std::max(0.0f, std::min(1.0f, m_weights[synapse_idx] + delta_w));
        m_last_pre_spike_time[synapse_idx] = pre_time;
        m_last_post_spike_time[synapse_idx] = post_time;
    }

    float get_weight(size_t synapse_idx) const noexcept {
        return (synapse_idx < NUM_SYNAPSES) ? m_weights[synapse_idx] : 0.0f;
    }

    const float* get_weight_array() const noexcept {
        return m_weights;
    }

private:
    float m_a_plus;
    float m_a_minus;
    float m_tau_plus;
    float m_tau_minus;

    float m_weights[NUM_SYNAPSES];
    float m_last_pre_spike_time[NUM_SYNAPSES];
    float m_last_post_spike_time[NUM_SYNAPSES];
};

} // namespace axiom
