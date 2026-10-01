#pragma once
#include <cstdint>
#include <cmath>
#include <algorithm>
#include <array>

namespace axiom {

/**
 * @brief Dynamic Vision Sensor (DVS) / Event-Based Camera Neuromorphic Ingestor.
 * Ingests asynchronous microsecond pixel events (x, y, timestamp, polarity)
 * and computes an Exponential Decaying Time Surface (EDTS) mapped directly
 * into Axiom Core's 128-dimensional spatial input tensor. Zero-heap, AVX-friendly.
 */
class EventCameraDvs {
public:
    static constexpr size_t GRID_WIDTH = 32;
    static constexpr size_t GRID_HEIGHT = 32;
    static constexpr size_t TENSOR_DIMS = 128;

    struct DvsEvent {
        uint16_t x{0};          // 0 to 639
        uint16_t y{0};          // 0 to 479
        uint64_t timestamp_us{0};
        int8_t polarity{1};     // +1 (ON) or -1 (OFF)
    };

private:
    float decay_tau_us_{10000.0f}; // 10ms exponential decay constant
    uint64_t last_timestamp_us_{0};
    std::array<float, GRID_WIDTH * GRID_HEIGHT> surface_{};
    std::array<uint64_t, GRID_WIDTH * GRID_HEIGHT> last_pixel_ts_{};

public:
    explicit EventCameraDvs(float tau_us = 10000.0f) noexcept
        : decay_tau_us_(tau_us > 0.0f ? tau_us : 10000.0f) {
        reset();
    }

    void reset() noexcept {
        surface_.fill(0.0f);
        last_pixel_ts_.fill(0);
        last_timestamp_us_ = 0;
    }

    /**
     * @brief Ingests a single asynchronous neuromorphic event.
     */
    void ingest_event(const DvsEvent& ev, uint16_t sensor_w = 640, uint16_t sensor_h = 480) noexcept {
        if (ev.timestamp_us > last_timestamp_us_) {
            last_timestamp_us_ = ev.timestamp_us;
        }

        // Downsample to internal 32x32 spatial grid
        size_t gx = std::min(GRID_WIDTH - 1, static_cast<size_t>((ev.x * GRID_WIDTH) / sensor_w));
        size_t gy = std::min(GRID_HEIGHT - 1, static_cast<size_t>((ev.y * GRID_HEIGHT) / sensor_h));
        size_t idx = gy * GRID_WIDTH + gx;

        uint64_t prev_ts = last_pixel_ts_[idx];
        if (prev_ts > 0 && ev.timestamp_us >= prev_ts) {
            float dt = static_cast<float>(ev.timestamp_us - prev_ts);
            surface_[idx] = surface_[idx] * std::exp(-dt / decay_tau_us_);
        } else {
            surface_[idx] = 0.0f;
        }

        surface_[idx] += (ev.polarity > 0 ? 1.0f : -0.5f);
        surface_[idx] = std::max(-2.0f, std::min(10.0f, surface_[idx]));
        last_pixel_ts_[idx] = ev.timestamp_us;
    }

    /**
     * @brief Ingests a batch of raw DVS events.
     */
    void ingest_batch(const DvsEvent* events, size_t count, uint16_t sensor_w = 640, uint16_t sensor_h = 480) noexcept {
        for (size_t i = 0; i < count; ++i) {
            ingest_event(events[i], sensor_w, sensor_h);
        }
    }

    /**
     * @brief Projects the current 32x32 time surface into Axiom Core's continuous 128-dim tensor.
     * Divides 32x32 into 128 regional receptive fields (each 8 pixels).
     */
    void extract_128d_tensor(float* out_tensor, uint64_t current_time_us) const noexcept {
        constexpr size_t PIXELS_PER_BIN = (GRID_WIDTH * GRID_HEIGHT) / TENSOR_DIMS; // 1024 / 128 = 8

        for (size_t b = 0; b < TENSOR_DIMS; ++b) {
            float bin_energy = 0.0f;
            size_t start_idx = b * PIXELS_PER_BIN;
            for (size_t p = 0; p < PIXELS_PER_BIN; ++p) {
                size_t idx = start_idx + p;
                float val = surface_[idx];
                uint64_t pts = last_pixel_ts_[idx];
                if (pts > 0 && current_time_us >= pts) {
                    float dt = static_cast<float>(current_time_us - pts);
                    val *= std::exp(-dt / decay_tau_us_);
                }
                bin_energy += std::abs(val);
            }
            // Normalize with tanh activation for the LIF reservoir
            out_tensor[b] = std::tanh(bin_energy / static_cast<float>(PIXELS_PER_BIN));
        }
    }
};

} // namespace axiom
