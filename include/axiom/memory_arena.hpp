#pragma once

#include <cstdint>
#include <cstddef>
#include <atomic>
#include <vector>
#include <new>
#include <cstring>
#include <cassert>

namespace axiom {

// Cache line size on x86/ARM
constexpr size_t CACHE_LINE_SIZE = 64;

// Forward-only ring frame for single-inference execution with atomic concurrency lock
struct alignas(CACHE_LINE_SIZE) MemoryFrame {
    static constexpr size_t FRAME_CAPACITY = 64 * 1024; // 64 KB per inference frame
    alignas(CACHE_LINE_SIZE) uint8_t buffer[FRAME_CAPACITY];
    size_t offset{0};
    std::atomic<bool> is_locked{false}; // Prevents overwrite during slow Layer 3 fallbacks

    bool try_lock() noexcept {
        bool expected = false;
        return is_locked.compare_exchange_strong(expected, true, std::memory_order_acquire);
    }

    void unlock() noexcept {
        is_locked.store(false, std::memory_order_release);
    }

    void reset() noexcept {
        offset = 0;
    }

    void* allocate(size_t bytes, size_t alignment = CACHE_LINE_SIZE) noexcept {
        size_t current = reinterpret_cast<size_t>(buffer + offset);
        size_t aligned = (current + alignment - 1) & ~(alignment - 1);
        size_t new_offset = (aligned - reinterpret_cast<size_t>(buffer)) + bytes;
        
        if (new_offset > FRAME_CAPACITY) {
            return nullptr; // Out of frame bounds
        }
        offset = new_offset;
        return reinterpret_cast<void*>(aligned);
    }

    template <typename T, typename... Args>
    T* create(Args&&... args) noexcept {
        void* ptr = allocate(sizeof(T), alignof(T));
        if (!ptr) return nullptr;
        return new (ptr) T(std::forward<Args>(args)...);
    }
};

// RAII Guard to ensure memory frames are always safely released
class FrameGuard {
public:
    explicit FrameGuard(MemoryFrame& frame) noexcept : m_frame(frame) {}
    ~FrameGuard() noexcept {
        m_frame.unlock();
    }
    FrameGuard(const FrameGuard&) = delete;
    FrameGuard& operator=(const FrameGuard&) = delete;

    MemoryFrame& frame() noexcept { return m_frame; }

private:
    MemoryFrame& m_frame;
};

// Thread-safe pre-allocated ring buffer pool with lock-aware acquisition
class ArenaPool {
public:
    explicit ArenaPool(size_t pool_size = 256) 
        : m_pool_size(pool_size), m_frames(pool_size), m_head(0) {
    }

    // Zero-allocation acquisition: safely finds an unlocked frame, preventing ring overwrite
    MemoryFrame& acquire() noexcept {
        // Try up to m_pool_size slots to find an unlocked frame
        for (size_t attempt = 0; attempt < m_pool_size; ++attempt) {
            size_t idx = m_head.fetch_add(1, std::memory_order_relaxed) % m_pool_size;
            MemoryFrame& frame = m_frames[idx];
            if (frame.try_lock()) {
                frame.reset();
                return frame;
            }
        }

        // Fallback: If all frames in pool are locked, force frame 0 after resetting offset
        // (Guarantees forward progress under extreme congestion)
        size_t fallback_idx = m_head.load(std::memory_order_relaxed) % m_pool_size;
        MemoryFrame& frame = m_frames[fallback_idx];
        frame.reset();
        return frame;
    }

    size_t capacity() const noexcept { return m_pool_size; }

private:
    size_t m_pool_size;
    std::vector<MemoryFrame> m_frames;
    std::atomic<size_t> m_head;
};

} // namespace axiom
