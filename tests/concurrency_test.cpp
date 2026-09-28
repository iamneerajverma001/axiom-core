#include "axiom/engine.hpp"
#include <windows.h>
#include <iostream>
#include <vector>
#include <atomic>

using namespace axiom;

AxiomEngine* g_engine = nullptr;
std::atomic<uint64_t> g_success_count{0};
std::atomic<uint64_t> g_error_count{0};

DWORD WINAPI WorkerThread(LPVOID lpParam) {
    int thread_id = reinterpret_cast<intptr_t>(lpParam);
    std::string queries[4] = {
        "Immediate refund dispute on invoice #9921",
        "Multiple failed MFA token attempts",
        "Kubernetes container crash loop in namespace prod",
        "Ambiguous edge case query that needs escalation"
    };

    for (int i = 0; i < 2000; ++i) {
        try {
            DecisionResult res = g_engine->decide(queries[i % 4]);
            if (res.choice.label.empty() || std::isnan(res.choice.confidence)) {
                g_error_count.fetch_add(1);
            } else {
                g_success_count.fetch_add(1);
            }
        } catch (...) {
            g_error_count.fetch_add(1);
        }
    }
    return 0;
}

int main() {
    std::cout << "[Concurrency Audit] Testing 8 threads x 2,000 requests (16,000 total)..." << std::endl;
    
    SchemaDefinition schema;
    schema.confidence_threshold = 0.85f;
    schema.entropy_threshold = 0.20f;
    SectorDefinition sec;
    sec.sector_id = 0;
    sec.name = "Billing";
    sec.leaves = {{101, "Refund", "Desc"}, {102, "Tax", "Desc"}};
    schema.sectors = {sec};

    // Notice: pool size is set to 8, but we have 8 concurrent threads!
    AxiomEngine engine(DeviceType::DIRECTML_GPU, 8, 0.01f);
    engine.load_schema(schema);
    g_engine = &engine;

    const int NUM_THREADS = 8;
    HANDLE threads[NUM_THREADS];

    for (int i = 0; i < NUM_THREADS; ++i) {
        threads[i] = CreateThread(NULL, 0, WorkerThread, reinterpret_cast<LPVOID>(static_cast<intptr_t>(i)), 0, NULL);
    }

    WaitForMultipleObjects(NUM_THREADS, threads, TRUE, INFINITE);

    for (int i = 0; i < NUM_THREADS; ++i) {
        CloseHandle(threads[i]);
    }

    std::cout << "Success Count: " << g_success_count.load() << std::endl;
    std::cout << "Error Count:   " << g_error_count.load() << std::endl;
    return 0;
}
