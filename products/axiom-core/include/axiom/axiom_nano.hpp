#pragma once

#include "axiom/axiom_nano.h"
#include <cmath>
#include <cstring>

namespace axiom {

// Inline C/C++ embedded implementation of axiom-nano
inline void axiom_nano_init(AxiomNanoContext* ctx, float alpha) {
    if (!ctx) return;
    ctx->num_leaves = 0;
    ctx->alpha = (alpha > 0.0f) ? alpha : 0.01f;
    ctx->martingale_wealth = 1.0f;
    ctx->rejection_threshold = 1.0f / ctx->alpha;
    std::memset(ctx->leaves, 0, sizeof(ctx->leaves));
}

inline int axiom_nano_register_leaf(AxiomNanoContext* ctx, uint16_t leaf_id, const char* name, const float* weights) {
    if (!ctx || ctx->num_leaves >= AXIOM_NANO_MAX_LEAVES) return -1;
    AxiomNanoLeaf* l = &ctx->leaves[ctx->num_leaves++];
    l->leaf_id = leaf_id;
    if (name) {
        std::strncpy(l->name, name, sizeof(l->name) - 1);
        l->name[sizeof(l->name) - 1] = '\0';
    }
    if (weights) {
        float sq = 0.0f;
        for (size_t i = 0; i < AXIOM_NANO_EMBED_DIM; ++i) sq += weights[i] * weights[i];
        float inv = (sq > 1e-8f) ? (1.0f / std::sqrt(sq)) : 1.0f;
        for (size_t i = 0; i < AXIOM_NANO_EMBED_DIM; ++i) l->weight[i] = weights[i] * inv;
    }
    return 0;
}

inline uint16_t axiom_nano_decide(
    AxiomNanoContext* ctx,
    const float* telemetry_features,
    float* out_confidence,
    int* out_safety_tripped
) {
    if (!ctx || ctx->num_leaves == 0 || !telemetry_features) {
        if (out_safety_tripped) *out_safety_tripped = 1;
        return 0;
    }

    float best_dot = -1e9f;
    uint16_t best_leaf = 0;

    for (size_t l = 0; l < ctx->num_leaves; ++l) {
        float dot = 0.0f;
        for (size_t i = 0; i < AXIOM_NANO_EMBED_DIM; ++i) {
            dot += telemetry_features[i] * ctx->leaves[l].weight[i];
        }
        if (dot > best_dot) {
            best_dot = dot;
            best_leaf = ctx->leaves[l].leaf_id;
        }
    }

    float conf = (best_dot > 0.0f) ? std::min(1.0f, best_dot) : 0.0f;
    if (out_confidence) *out_confidence = conf;

    // Martingale safety check
    if (conf < 0.35f) {
        ctx->martingale_wealth *= 1.4f; // Penalize out-of-distribution observation
    } else {
        ctx->martingale_wealth *= 0.95f; // Decay wealth on safe operational commit
    }

    if (ctx->martingale_wealth >= ctx->rejection_threshold) {
        if (out_safety_tripped) *out_safety_tripped = 1;
    } else {
        if (out_safety_tripped) *out_safety_tripped = 0;
    }

    return best_leaf;
}

} // namespace axiom
