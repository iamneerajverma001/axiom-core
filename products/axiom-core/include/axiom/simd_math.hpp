#pragma once

#include <cstddef>
#include <cmath>
#include <algorithm>

#if defined(__AVX512F__)
#include <immintrin.h>
#elif defined(__AVX2__)
#include <immintrin.h>
#elif defined(__ARM_NEON) || defined(__ARM_NEON__)
#include <arm_neon.h>
#endif

namespace axiom {

// Ultra-fast multi-architecture SIMD inner product (AVX-512, AVX2, ARM NEON, Scalar)
inline float simd_dot_product(const float* a, const float* b, size_t dim) noexcept {
    if (!a || !b || dim == 0) return 0.0f;

#if defined(__AVX512F__)
    // 512-bit vectorization: 16 floats per instruction
    __m512 sum512 = _mm512_setzero_ps();
    size_t i = 0;
    for (; i + 16 <= dim; i += 16) {
        __m512 va = _mm512_loadu_ps(a + i);
        __m512 vb = _mm512_loadu_ps(b + i);
        sum512 = _mm512_fmadd_ps(va, vb, sum512);
    }
    float total = _mm512_reduce_add_ps(sum512);
    for (; i < dim; ++i) {
        total += a[i] * b[i];
    }
    return total;

#elif defined(__AVX2__)
    // 256-bit vectorization: 8 floats per instruction
    __m256 sum256 = _mm256_setzero_ps();
    size_t i = 0;
    for (; i + 8 <= dim; i += 8) {
        __m256 va = _mm256_loadu_ps(a + i);
        __m256 vb = _mm256_loadu_ps(b + i);
        sum256 = _mm256_fmadd_ps(va, vb, sum256);
    }
    // Horizontal add of 8 floats
    alignas(32) float tmp[8];
    _mm256_storeu_ps(tmp, sum256);
    float total = tmp[0] + tmp[1] + tmp[2] + tmp[3] + tmp[4] + tmp[5] + tmp[6] + tmp[7];
    for (; i < dim; ++i) {
        total += a[i] * b[i];
    }
    return total;

#elif defined(__ARM_NEON) || defined(__ARM_NEON__)
    // 128-bit ARM NEON vectorization: 4 floats per instruction
    float32x4_t sum128 = vdupq_n_f32(0.0f);
    size_t i = 0;
    for (; i + 4 <= dim; i += 4) {
        float32x4_t va = vld1q_f32(a + i);
        float32x4_t vb = vld1q_f32(b + i);
        sum128 = vfmaq_f32(sum128, va, vb);
    }
    float total = vaddvq_f32(sum128);
    for (; i < dim; ++i) {
        total += a[i] * b[i];
    }
    return total;

#else
    // Highly-unrolled scalar fallback
    float total0 = 0.0f, total1 = 0.0f, total2 = 0.0f, total3 = 0.0f;
    size_t i = 0;
    for (; i + 4 <= dim; i += 4) {
        total0 += a[i]     * b[i];
        total1 += a[i + 1] * b[i + 1];
        total2 += a[i + 2] * b[i + 2];
        total3 += a[i + 3] * b[i + 3];
    }
    float total = total0 + total1 + total2 + total3;
    for (; i < dim; ++i) {
        total += a[i] * b[i];
    }
    return total;
#endif
}

// In-place L2 Unit Normalization (Vectorized)
inline void simd_l2_normalize(float* vec, size_t dim) noexcept {
    if (!vec || dim == 0) return;
    float sq = simd_dot_product(vec, vec, dim);
    if (sq > 1e-8f) {
        float inv = 1.0f / std::sqrt(sq);
#if defined(__AVX2__)
        __m256 vinv = _mm256_set1_ps(inv);
        size_t i = 0;
        for (; i + 8 <= dim; i += 8) {
            __m256 v = _mm256_loadu_ps(vec + i);
            _mm256_storeu_ps(vec + i, _mm256_mul_ps(v, vinv));
        }
        for (; i < dim; ++i) vec[i] *= inv;
#elif defined(__ARM_NEON) || defined(__ARM_NEON__)
        float32x4_t vinv = vdupq_n_f32(inv);
        size_t i = 0;
        for (; i + 4 <= dim; i += 4) {
            float32x4_t v = vld1q_f32(vec + i);
            vst1q_f32(vec + i, vmulq_f32(v, vinv));
        }
        for (; i < dim; ++i) vec[i] *= inv;
#else
        for (size_t i = 0; i < dim; ++i) vec[i] *= inv;
#endif
    }
}

// Online Oja's Hebbian Weight Plasticity: w_new = w + eta * y * (x - y * w)
// Mathematically equivalent to: w_new = (1 - eta * y^2) * w + (eta * y) * x
inline void simd_oja_update(float* w, const float* x, float eta, float y, size_t dim) noexcept {
    if (!w || !x || dim == 0) return;
    float alpha = 1.0f - (eta * y * y);
    float beta  = eta * y;

#if defined(__AVX2__)
    __m256 valpha = _mm256_set1_ps(alpha);
    __m256 vbeta  = _mm256_set1_ps(beta);
    size_t i = 0;
    for (; i + 8 <= dim; i += 8) {
        __m256 vw = _mm256_loadu_ps(w + i);
        __m256 vx = _mm256_loadu_ps(x + i);
        // vw_new = valpha * vw + vbeta * vx
        __m256 vnew = _mm256_fmadd_ps(vbeta, vx, _mm256_mul_ps(valpha, vw));
        _mm256_storeu_ps(w + i, vnew);
    }
    for (; i < dim; ++i) {
        w[i] = alpha * w[i] + beta * x[i];
    }
#elif defined(__ARM_NEON) || defined(__ARM_NEON__)
    float32x4_t valpha = vdupq_n_f32(alpha);
    float32x4_t vbeta  = vdupq_n_f32(beta);
    size_t i = 0;
    for (; i + 4 <= dim; i += 4) {
        float32x4_t vw = vld1q_f32(w + i);
        float32x4_t vx = vld1q_f32(x + i);
        float32x4_t vnew = vfmaq_f32(vmulq_f32(valpha, vw), vbeta, vx);
        vst1q_f32(w + i, vnew);
    }
    for (; i < dim; ++i) {
        w[i] = alpha * w[i] + beta * x[i];
    }
#else
    for (size_t i = 0; i < dim; ++i) {
        w[i] = alpha * w[i] + beta * x[i];
    }
#endif
}

} // namespace axiom
