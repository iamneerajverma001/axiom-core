#ifndef AXIOM_NANO_H
#define AXIOM_NANO_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stddef.h>

#define AXIOM_NANO_MAX_LEAVES 32
#define AXIOM_NANO_EMBED_DIM  64

// Embedded leaf structure fitting in 320 bytes
typedef struct {
    uint16_t leaf_id;
    char     name[16];
    float    weight[AXIOM_NANO_EMBED_DIM];
} AxiomNanoLeaf;

// Freestanding Embedded Neuromorphic Kernel Context (< 12KB RAM footprint)
typedef struct {
    uint8_t       num_leaves;
    float         alpha;
    float         martingale_wealth;
    float         rejection_threshold;
    AxiomNanoLeaf leaves[AXIOM_NANO_MAX_LEAVES];
} AxiomNanoContext;

// Initialize embedded micro-kernel
void axiom_nano_init(AxiomNanoContext* ctx, float alpha);

// Register leaf prototype into embedded SRAM table
int axiom_nano_register_leaf(AxiomNanoContext* ctx, uint16_t leaf_id, const char* name, const float* weights);

// Sub-microsecond bare-metal inference without malloc
uint16_t axiom_nano_decide(
    AxiomNanoContext* ctx,
    const float* telemetry_features,
    float* out_confidence,
    int* out_safety_tripped
);

#ifdef __cplusplus
}
#endif

#endif // AXIOM_NANO_H
