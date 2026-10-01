#pragma once

#include <cstdint>
#include <iostream>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <pthread.h>
#include <sched.h>
#include <unistd.h>
#endif

namespace axiom {

// Cross-Platform Thread Affinity & Core Isolation Controller
// Pins execution threads to dedicated physical cores to eliminate OS scheduler jitter,
// avoid L1/L2 cache evictions, and ensure strictly deterministic microsecond response times.
class ThreadAffinityController {
public:
    // Pin the current calling thread to a specific CPU core ID
    static bool pin_current_thread_to_core(uint32_t core_id) noexcept {
#ifdef _WIN32
        HANDLE thread = GetCurrentThread();
        DWORD_PTR mask = static_cast<DWORD_PTR>(1ULL << (core_id % 64));
        DWORD_PTR result = SetThreadAffinityMask(thread, mask);
        if (result == 0) {
            std::cerr << "[Axiom NUMA] Failed to set thread affinity for core " << core_id << std::endl;
            return false;
        }
        return true;
#else
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(core_id % CPU_SETSIZE, &cpuset);
        pthread_t current_thread = pthread_self();
        int rc = pthread_setaffinity_np(current_thread, sizeof(cpu_set_t), &cpuset);
        if (rc != 0) {
            std::cerr << "[Axiom NUMA] Failed to set pthread affinity for core " << core_id << std::endl;
            return false;
        }
        return true;
#endif
    }

    // Set priority to high-realtime critical priority
    static bool set_realtime_priority() noexcept {
#ifdef _WIN32
        HANDLE thread = GetCurrentThread();
        return SetThreadPriority(thread, THREAD_PRIORITY_TIME_CRITICAL) != FALSE;
#else
        struct sched_param param;
        param.sched_priority = 80; // High FIFO priority
        int policy = SCHED_FIFO;
        return pthread_setschedparam(pthread_self(), policy, &param) == 0;
#endif
    }

    // Yield CPU time slice to prevent thread starving while maintaining low latency
    static void spin_pause() noexcept {
#if defined(__x86_64__) || defined(_M_X64) || defined(i386) || defined(_M_IX86)
        #if defined(_MSC_VER)
        _mm_pause();
        #else
        __builtin_ia32_pause();
        #endif
#elif defined(__aarch64__) || defined(_M_ARM64)
        asm volatile("yield" ::: "memory");
#else
        // Fallback
#endif
    }
};

} // namespace axiom
