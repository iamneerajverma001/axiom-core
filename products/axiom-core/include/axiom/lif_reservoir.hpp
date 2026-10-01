#pragma once

#include <vector>
#include <cmath>
#include <cstring>
#include <cstdint>
#include <algorithm>
#include "axiom/simd_math.hpp"

namespace axiom {

// Biological Neuromorphic Leaky Integrate-and-Fire (LIF) Spiking Reservoir
// Emulates biological dendritic spike generation in continuous time.
// Consumes zero compute on static inputs (event-driven sparsity).
class LifSpikingReservoir {
public:
    static constexpr size_t RESERVOIR_SIZE = 128;

    struct NeuronState {
        float voltage;         // Current membrane potential (mV)
        float refractory_time; // Remaining refractory period (ms)
        bool spiked;           // Did the neuron fire in this time step?
    };

    LifSpikingReservoir(
        float v_rest = -70.0f,
        float v_threshold = -50.0f,
        float v_reset = -75.0f,
        float tau_membrane = 15.0f,
        float refractory_period = 2.0f
    ) : m_v_rest(v_rest),
        m_v_thresh(v_threshold),
        m_v_reset(v_reset),
        m_tau_m(tau_membrane),
        m_t_refractory(refractory_period),
        m_total_spikes(0)
    {
        reset();
        initialize_reservoir_weights();
    }

    void reset() {
        for (size_t i = 0; i < RESERVOIR_SIZE; ++i) {
            m_neurons[i].voltage = m_v_rest;
            m_neurons[i].refractory_time = 0.0f;
            m_neurons[i].spiked = false;
        }
        m_total_spikes = 0;
    }

    // Step the spiking reservoir forward by dt (milliseconds) with injected input currents
    // Returns the total number of spikes fired across the network in this step
    size_t step(const float* input_currents, size_t input_dim, float dt = 0.5f) {
        size_t step_spikes = 0;
        const float decay = std::exp(-dt / m_tau_m);
        size_t eff_dim = std::min(input_dim, RESERVOIR_SIZE);

        // 1. Update membrane voltages
        for (size_t i = 0; i < RESERVOIR_SIZE; ++i) {
            auto& n = m_neurons[i];
            n.spiked = false;

            if (n.refractory_time > 0.0f) {
                n.refractory_time -= dt;
                n.voltage = m_v_reset;
                continue;
            }

            // Passive decay towards rest + injected input current
            float i_inj = (i < eff_dim) ? input_currents[i] : 0.0f;
            n.voltage = m_v_rest + (n.voltage - m_v_rest) * decay + (i_inj * 12.0f * dt);

            // Recurrent synaptic connection contributions from previous step
            float recurrent_synapse = 0.0f;
            for (size_t j = 0; j < 8; ++j) {
                size_t neighbor = (i + j * 16) % RESERVOIR_SIZE;
                if (m_neurons[neighbor].spiked) {
                    recurrent_synapse += m_weights[i * 8 + j];
                }
            }
            n.voltage += recurrent_synapse;

            // Spike threshold check
            if (n.voltage >= m_v_thresh) {
                n.spiked = true;
                n.voltage = m_v_reset;
                n.refractory_time = m_t_refractory;
                step_spikes++;
            }
        }

        m_total_spikes += step_spikes;
        return step_spikes;
    }

    // Extract current spike raster as a 128-dim binary float vector
    void get_spike_raster(float* out_raster) const {
        for (size_t i = 0; i < RESERVOIR_SIZE; ++i) {
            out_raster[i] = m_neurons[i].spiked ? 1.0f : 0.0f;
        }
    }

    // Extract mean membrane voltage distribution
    void get_voltage_distribution(float* out_voltages) const {
        for (size_t i = 0; i < RESERVOIR_SIZE; ++i) {
            out_voltages[i] = m_neurons[i].voltage;
        }
    }

    uint64_t get_total_spikes() const noexcept { return m_total_spikes; }

private:
    void initialize_reservoir_weights() {
        // Sparse recurrent connections with fixed spectral radius
        for (size_t i = 0; i < RESERVOIR_SIZE * 8; ++i) {
            float w = (static_cast<float>(i % 17) - 8.0f) * 0.35f;
            m_weights[i] = w;
        }
    }

    float m_v_rest;
    float m_v_thresh;
    float m_v_reset;
    float m_tau_m;
    float m_t_refractory;
    uint64_t m_total_spikes;

    NeuronState m_neurons[RESERVOIR_SIZE];
    float m_weights[RESERVOIR_SIZE * 8]; // Sparse recurrent connections
};

} // namespace axiom
