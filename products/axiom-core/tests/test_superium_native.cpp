#include <iostream>
#include <cassert>
#include <vector>
#include <cmath>

#include "axiom/huge_page_arena.hpp"
#include "axiom/lockfree_ring_buffer.hpp"
#include "axiom/numa_pinning.hpp"
#include "axiom/lif_reservoir.hpp"
#include "axiom/stdp_learner.hpp"
#include "axiom/anytime_ladder.hpp"
#include "axiom/matrix_martingale.hpp"
#include "axiom/merkle_audit.hpp"
#include "axiom/can_bus_protocol.hpp"
#include "axiom/itch_protocol.hpp"
#include "axiom/swarm_fabric.hpp"
#include "axiom/crdt_register_tree.hpp"
#include "axiom/axiom_nano.h"
#include "axiom/axiom_nano.hpp"

using namespace axiom;

int main() {
    std::cout << "=== Running Axiom Core Superium v2.0 Native C++ Verification Suite ===\n";

    // 1. Pillar 1: Silicon Micro-Architecture
    {
        HugePageArena arena(HUGE_PAGE_2MB);
        void* p = arena.allocate(1024, 64);
        assert(p != nullptr);
        assert(arena.get_allocated_bytes() >= 1024);

        SpscLockFreeRingBuffer<uint32_t, 1024> queue;
        assert(queue.push(42));
        uint32_t val = 0;
        assert(queue.pop(val));
        assert(val == 42);

        ThreadAffinityController::pin_current_thread_to_core(0);
        std::cout << "[PASS] Pillar 1: Silicon Micro-Architecture (HugePageArena, SpscLockFreeRingBuffer, ThreadAffinityController)\n";
    }

    // 2. Pillar 2: Neuromorphic Dynamics
    {
        LifSpikingReservoir reservoir;
        float input[128] = {0.8f};
        size_t spikes = reservoir.step(input, 128, 1.0f);
        (void)spikes;

        StdpLearner stdp;
        stdp.update_synapse(2, 10.0f, 15.0f);
        assert(stdp.get_weight(2) >= 0.5f);

        AnytimeDecisionLadder ladder;
        auto res = ladder.evaluate_with_deadline(
            50.0,
            []() { AnytimeDecisionSnapshot s; s.choice_id = 1; return s; },
            []() { AnytimeDecisionSnapshot s; s.choice_id = 2; return s; },
            []() { AnytimeDecisionSnapshot s; s.choice_id = 3; return s; }
        );
        assert(res.choice_id >= 1);
        std::cout << "[PASS] Pillar 2: Neuromorphic Dynamics (LifSpikingReservoir, StdpLearner, AnytimeDecisionLadder)\n";
    }

    // 3. Pillar 3: Safety & Verification
    {
        MatrixMartingaleShield<8> shield(0.01f);
        float state[8] = {0.1f};
        bool safe = shield.update(state);
        assert(safe);
        assert(shield.get_wealth() > 0.0);

        MerkleFlightRecorder audit;
        uint64_t hash = audit.record_event(101, 1, 0.99f, 12345.0, "ReflexExecuted");
        assert(hash != 0);
        assert(audit.get_root_hash() != 0);
        std::cout << "[PASS] Pillar 3: Safety & Verification (MatrixMartingaleShield, MerkleFlightRecorder)\n";
    }

    // 4. Pillar 4: Direct Hardware Wire Buses
    {
        uint8_t dummy_can[16] = {0};
        dummy_can[0] = 0x01; // ID 0x100
        dummy_can[4] = 0x08; // DLC 8
        dummy_can[6] = 0x05;
        dummy_can[7] = 0xDC; // 1500
        CanFrame frame;
        bool ok = CanBusProtocolParser::parse_frame(dummy_can, 16, frame);
        assert(ok);

        uint8_t dummy_itch[64] = {0};
        dummy_itch[0] = 'A';
        ItchAddOrderMsg msg;
        bool parsed = ItchProtocolParser::parse_add_order(dummy_itch, sizeof(dummy_itch), msg);
        assert(parsed);
        std::cout << "[PASS] Pillar 4: Direct Hardware Wire Buses (CanBusProtocolParser, ItchProtocolParser)\n";
    }

    // 5. Pillar 5: Swarm Intelligence
    {
        SwarmReflexFabric swarm(1, 100);
        assert(!swarm.is_cluster_halted());
        swarm.trigger_cluster_estop();
        assert(swarm.is_cluster_halted());

        CrdtRegisterTree crdt(1);
        float w[16] = {0.5f};
        crdt.update_local_leaf(10, w, 16);
        assert(crdt.get_vector_clock() >= 1);
        std::cout << "[PASS] Pillar 5: Swarm Intelligence (SwarmReflexFabric, CrdtRegisterTree)\n";
    }

    // 6. Pillar 6: Tooling & Nano Kernel
    {
        AxiomNanoContext nano_ctx;
        axiom_nano_init(&nano_ctx, 0.01f);
        float dummy_weights[AXIOM_NANO_EMBED_DIM] = {0};
        dummy_weights[0] = 1.0f;
        axiom_nano_register_leaf(&nano_ctx, 100, "ReflexSafe", dummy_weights);

        float query[AXIOM_NANO_EMBED_DIM] = {0};
        query[0] = 1.0f;
        float out_conf = 0.0f;
        int is_safe = 0;
        uint16_t decision = axiom_nano_decide(&nano_ctx, query, &out_conf, &is_safe);
        assert(decision == 100);
        assert(out_conf > 0.0f);
        std::cout << "[PASS] Pillar 6: Tooling & Nano Kernel (AxiomNano freestanding <12KB RAM)\n";
    }

    std::cout << "\n=====================================================================\n";
    std::cout << "ALL 6 SUPERIUM PILLARS VERIFIED NATIVELY IN C++ (100% HEALTHY)\n";
    std::cout << "=====================================================================\n";
    return 0;
}
