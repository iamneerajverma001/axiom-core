#pragma once

#include <atomic>
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <new>

namespace axiom {

// Cache-line size constant for modern x86/ARM processors
constexpr size_t CACHE_LINE_SIZE = 64;

// Single-Producer Single-Consumer (SPSC) Lock-Free Ring Buffer
// Designed for sub-100 nanosecond zero-contention IPC and thread communication.
// Both head and tail cursors are separated by 64-byte padding to eliminate False Sharing.
template <typename T, size_t Capacity>
class alignas(CACHE_LINE_SIZE) SpscLockFreeRingBuffer {
    static_assert((Capacity & (Capacity - 1)) == 0, "Capacity must be a power of 2 for fast bitmask modulo");

public:
    SpscLockFreeRingBuffer() : m_head(0), m_tail(0) {
        std::memset(m_storage, 0, sizeof(m_storage));
    }

    ~SpscLockFreeRingBuffer() = default;

    // Non-copyable, non-movable for cache-line and memory safety
    SpscLockFreeRingBuffer(const SpscLockFreeRingBuffer&) = delete;
    SpscLockFreeRingBuffer& operator=(const SpscLockFreeRingBuffer&) = delete;

    // Push item to the ring buffer (Producer thread only)
    // Returns true on success, false if buffer is full
    bool push(const T& item) noexcept {
        const size_t current_tail = m_tail.load(std::memory_order_relaxed);
        const size_t current_head = m_head.load(std::memory_order_acquire);

        if ((current_tail - current_head) >= Capacity) {
            return false; // Buffer full
        }

        m_storage[current_tail & MASK] = item;
        m_tail.store(current_tail + 1, std::memory_order_release);
        return true;
    }

    // Pop item from the ring buffer (Consumer thread only)
    // Returns true on success, false if buffer is empty
    bool pop(T& out_item) noexcept {
        const size_t current_head = m_head.load(std::memory_order_relaxed);
        const size_t current_tail = m_tail.load(std::memory_order_acquire);

        if (current_head == current_tail) {
            return false; // Buffer empty
        }

        out_item = m_storage[current_head & MASK];
        m_head.store(current_head + 1, std::memory_order_release);
        return true;
    }

    // Check if buffer is currently empty
    bool empty() const noexcept {
        return m_head.load(std::memory_order_relaxed) == m_tail.load(std::memory_order_relaxed);
    }

    // Check current number of items in buffer
    size_t size() const noexcept {
        const size_t h = m_head.load(std::memory_order_relaxed);
        const size_t t = m_tail.load(std::memory_order_relaxed);
        return (t >= h) ? (t - h) : 0;
    }

    // Get capacity
    constexpr size_t capacity() const noexcept {
        return Capacity;
    }

private:
    static constexpr size_t MASK = Capacity - 1;

    // Storage array for elements
    T m_storage[Capacity];

    // Producer cursor on its own cache-line
    alignas(CACHE_LINE_SIZE) std::atomic<size_t> m_tail;

    // Consumer cursor on its own separate cache-line (Zero False Sharing)
    alignas(CACHE_LINE_SIZE) std::atomic<size_t> m_head;

    // Trailing padding to isolate the structure in memory
    char m_trailing_pad[CACHE_LINE_SIZE - sizeof(std::atomic<size_t>)];
};

} // namespace axiom
