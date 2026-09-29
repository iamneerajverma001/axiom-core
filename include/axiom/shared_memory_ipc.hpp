#pragma once

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#endif

#include <cstdint>
#include <cstring>
#include <string>
#include <iostream>

namespace axiom {

constexpr const char* IPC_SHARED_MEM_NAME = "Local\\AxiomSharedMemoryPool";
constexpr const char* IPC_REQ_EVENT_NAME  = "Local\\AxiomReqEvent";
constexpr const char* IPC_RESP_EVENT_NAME = "Local\\AxiomRespEvent";
constexpr uint32_t IPC_MAGIC = 0x4158494F; // "AXIO"
constexpr uint32_t IPC_VERSION = 1;

#pragma pack(push, 8)
struct alignas(64) AxiomIpcBuffer {
    uint32_t magic;           // 0x4158494F
    uint32_t version;         // 1
    uint32_t status;          // 0: IDLE, 1: REQ_READY, 2: RESP_READY, 3: SHUTDOWN
    uint32_t request_id;      // Unique sequence number
    uint32_t input_len;       // Bytes in input_text
    uint32_t choice_id;       // Winning leaf ID
    uint32_t sector_id;       // Winning sector ID
    uint32_t execution_path;  // 1: FAST_PATH_COMMIT, 2: SYSTEM2_FALLBACK
    float confidence;         // Model probability / score
    float shannon_entropy;    // Shannon entropy H(P)
    double latency_l1_us;     // Layer 1 Latency
    double latency_l2_us;     // Layer 2 Latency
    double latency_total_us;  // End-to-end microseconds
    char input_text[2048];    // Input prompt / directive
    char choice_label[256];   // Action name / label
    char output_json[4096];   // Full JSON diagnostic payload
    uint32_t feature_dim;     // Direct binary feature tensor dimension
    float feature_vector[128];// Direct AVX2 float register slot (zero-copy)
};
#pragma pack(pop)

class AxiomIpcServer {
public:
    AxiomIpcServer() : m_hMapFile(nullptr), m_buffer(nullptr), m_hReqEvent(nullptr), m_hRespEvent(nullptr), m_running(false) {}

    ~AxiomIpcServer() {
        stop();
    }

    bool initialize() {
#ifdef _WIN32
        // Create Shared Memory Mapping
        m_hMapFile = CreateFileMappingA(
            INVALID_HANDLE_VALUE,
            nullptr,
            PAGE_READWRITE,
            0,
            sizeof(AxiomIpcBuffer),
            IPC_SHARED_MEM_NAME
        );
        if (!m_hMapFile) {
            std::cerr << "[Axiom IPC] Failed to create file mapping. Error: " << GetLastError() << std::endl;
            return false;
        }

        m_buffer = static_cast<AxiomIpcBuffer*>(MapViewOfFile(
            m_hMapFile,
            FILE_MAP_ALL_ACCESS,
            0,
            0,
            sizeof(AxiomIpcBuffer)
        ));
        if (!m_buffer) {
            std::cerr << "[Axiom IPC] Failed to map view of file. Error: " << GetLastError() << std::endl;
            CloseHandle(m_hMapFile);
            return false;
        }

        // Initialize header
        std::memset(m_buffer, 0, sizeof(AxiomIpcBuffer));
        m_buffer->magic = IPC_MAGIC;
        m_buffer->version = IPC_VERSION;
        m_buffer->status = 0; // IDLE

        // Create Named Event Synchronization Primitives
        m_hReqEvent = CreateEventA(nullptr, FALSE, FALSE, IPC_REQ_EVENT_NAME);
        m_hRespEvent = CreateEventA(nullptr, FALSE, FALSE, IPC_RESP_EVENT_NAME);

        if (!m_hReqEvent || !m_hRespEvent) {
            std::cerr << "[Axiom IPC] Failed to create synchronization events." << std::endl;
            return false;
        }

        m_running = true;
        std::cout << "[Axiom IPC] Shared Memory Buffer initialized (" << sizeof(AxiomIpcBuffer) << " bytes, 64-byte aligned)." << std::endl;
        return true;
#else
        return false;
#endif
    }

    template <typename DeciderFunc>
    void run_service_loop(DeciderFunc decider) {
#ifdef _WIN32
        if (!m_running || !m_buffer || !m_hReqEvent || !m_hRespEvent) {
            std::cerr << "[Axiom IPC] Server not initialized." << std::endl;
            return;
        }
        HANDLE req_event = static_cast<HANDLE>(m_hReqEvent);
        HANDLE resp_event = static_cast<HANDLE>(m_hRespEvent);
        std::cout << "[Axiom IPC] Daemon active: servicing sub-15us zero-copy requests..." << std::endl;

        while (m_running) {
            DWORD dwWait = WaitForSingleObject(req_event, 500);
            if (dwWait == WAIT_OBJECT_0) {
                if (m_buffer->status == 1) { // REQ_READY
                    uint32_t len = (m_buffer->input_len < sizeof(m_buffer->input_text) - 1) ? m_buffer->input_len : (sizeof(m_buffer->input_text) - 1);
                    std::string input(m_buffer->input_text, len);
                    auto res = decider(input);

                    m_buffer->choice_id = res.choice.choice_id;
                    m_buffer->sector_id = res.feedback.target_sector_id;
                    m_buffer->execution_path = (res.path == ExecutionPath::FAST_PATH_COMMIT ? 1 : 2);
                    m_buffer->confidence = res.choice.confidence;
                    m_buffer->shannon_entropy = res.shannon_entropy;
                    m_buffer->latency_l1_us = res.latency_layer1_us;
                    m_buffer->latency_l2_us = res.latency_layer2_us;
                    m_buffer->latency_total_us = res.latency_total_us;

                    std::strncpy(m_buffer->choice_label, res.choice.label.c_str(), sizeof(m_buffer->choice_label) - 1);
                    m_buffer->choice_label[sizeof(m_buffer->choice_label) - 1] = '\0';

                    std::string json_str = "{\"request_id\":" + std::to_string(res.request_id) +
                                           ",\"execution_path\":\"" + (res.path == ExecutionPath::FAST_PATH_COMMIT ? "FAST_PATH_COMMIT" : "SYSTEM2_FALLBACK") + "\"" +
                                           ",\"choice_id\":" + std::to_string(res.choice.choice_id) +
                                           ",\"choice_label\":\"" + res.choice.label + "\"" +
                                           ",\"confidence\":" + std::to_string(res.choice.confidence) +
                                           ",\"shannon_entropy\":" + std::to_string(res.shannon_entropy) +
                                           ",\"latency_total_us\":" + std::to_string(res.latency_total_us) +
                                           "}";
                    std::strncpy(m_buffer->output_json, json_str.c_str(), sizeof(m_buffer->output_json) - 1);
                    m_buffer->output_json[sizeof(m_buffer->output_json) - 1] = '\0';

                    m_buffer->status = 2; // RESP_READY
                    SetEvent(resp_event);
                }
            } else if (dwWait == WAIT_TIMEOUT) {
                continue;
            } else {
                break;
            }
        }
#endif
    }

    void stop() {
#ifdef _WIN32
        m_running = false;
        if (m_buffer) {
            m_buffer->status = 3; // SHUTDOWN
            UnmapViewOfFile(m_buffer);
            m_buffer = nullptr;
        }
        if (m_hMapFile) {
            CloseHandle(m_hMapFile);
            m_hMapFile = nullptr;
        }
        if (m_hReqEvent) {
            CloseHandle(m_hReqEvent);
            m_hReqEvent = nullptr;
        }
        if (m_hRespEvent) {
            CloseHandle(m_hRespEvent);
            m_hRespEvent = nullptr;
        }
#endif
    }

    AxiomIpcBuffer* get_buffer() noexcept { return m_buffer; }
    void* get_req_event() noexcept { return m_hReqEvent; }
    void* get_resp_event() noexcept { return m_hRespEvent; }
    bool is_running() const noexcept { return m_running; }

private:
    void* m_hMapFile;
    AxiomIpcBuffer* m_buffer;
    void* m_hReqEvent;
    void* m_hRespEvent;
    bool m_running;
};

} // namespace axiom
