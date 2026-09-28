#pragma once

#include "axiom/types.hpp"
#include "axiom/memory_arena.hpp"
#include <string>
#include <vector>

namespace axiom {

enum class DeviceType : uint8_t {
    DIRECTML_GPU = 0,   // Windows DirectML (Universal: NVIDIA, AMD, Intel, Qualcomm NPU)
    CUDA_NATIVE = 1,    // NVIDIA CUDA / TensorRT
    CPU_VECTORIZED = 2  // AVX2 / AVX-512 / ARM NEON
};

struct BackendProfile {
    DeviceType device;
    std::string device_name;
    size_t vram_available_mb;
    bool supports_fp8;
    bool supports_sparse_tensor;
};

// Abstract Hardware Backend Interface
class ITensorBackend {
public:
    virtual ~ITensorBackend() = default;

    virtual void initialize() = 0;
    
    // Executes Layer 1: Computes bidirectional linear-attention and sparse spike activations
    virtual void forward_sparse(
        const std::string& input_text,
        MemoryFrame& frame,
        float* out_embedding,
        size_t embedding_dim
    ) = 0;

    virtual BackendProfile get_profile() const = 0;
};

} // namespace axiom
