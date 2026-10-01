#pragma once

#ifdef _WIN32
#include <windows.h>
#else
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <semaphore.h>
#include <cerrno>
#include <ctime>
#endif

#include <cstdint>
#include <cstring>
#include <string>
#include <iostream>
#include <functional>
#include "axiom/types.hpp"

namespace axiom {

#ifdef _WIN32
constexpr const char* IPC_SHARED_MEM_NAME = "Local\\AxiomSharedMemoryPool";
constexpr const char* IPC_REQ_EVENT_NAME  = "Local\\AxiomReqEvent";
constexpr const char* IPC_RESP_EVENT_NAME = "Local\\AxiomRespEvent";
#else
constexpr const char* IPC_SHARED_MEM_NAME = "/axiom_shm_pool";
constexpr const char* IPC_REQ_SEM_NAME    = "/axiom_req_sem";
constexpr const char* IPC_RESP_SEM_NAME   = "/axiom_resp_sem";
#endif

constexpr uint32_t IPC_MAGIC = 0x4158494F; // "AXIO"
constexpr uint32_t IPC_VERSION = 1;

#pragma pack(push, 8)
struct alignas(64) AxiomIpcBuffer {
    uint32_t magic;           // 0x4158494F
    uint32_t version;         // 1
    uint32_t status;          // 0: IDLE, 1: REQ_READY, 2: RESP_READY, 3: SHUTDOWN, 4: HEBBIAN_ADAPT
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
    AxiomIpcServer()
        : m_buffer(nullptr), m_running(false)
#ifdef _WIN32
        , m_hMapFile(nullptr), m_hReqEvent(nullptr), m_hRespEvent(nullptr)
#else
        , m_shmFd(-1), m_reqSem(SEM_FAILED), m_respSem(SEM_FAILED)
#endif
    {}

    ~AxiomIpcServer() {
        stop();
    }

    bool initialize() {
#ifdef _WIN32
        m_hMapFile = CreateFileMappingA(
            INVALID_HANDLE_VALUE,
            nullptr,
            PAGE_READWRITE,
            0,
            sizeof(AxiomIpcBuffer),
            IPC_SHARED_MEM_NAME
        );
        if (!m_hMapFile) {
            std::cerr << "[Axiom IPC] Failed to create Win32 file mapping. Error: " << GetLastError() << std::endl;
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
            m_hMapFile = nullptr;
            return false;
        }

        std::memset(m_buffer, 0, sizeof(AxiomIpcBuffer));
        m_buffer->magic = IPC_MAGIC;
        m_buffer->version = IPC_VERSION;
        m_buffer->status = 0; // IDLE

        m_hReqEvent = CreateEventA(nullptr, FALSE, FALSE, IPC_REQ_EVENT_NAME);
        m_hRespEvent = CreateEventA(nullptr, FALSE, FALSE, IPC_RESP_EVENT_NAME);

        if (!m_hReqEvent || !m_hRespEvent) {
            std::cerr << "[Axiom IPC] Failed to create Win32 synchronization events." << std::endl;
            return false;
        }

        m_running = true;
        std::cout << "[Axiom IPC] Win32 Shared Memory Buffer initialized (" << sizeof(AxiomIpcBuffer) << " bytes, 64-byte aligned)." << std::endl;
        return true;
#else
        m_shmFd = shm_open(IPC_SHARED_MEM_NAME, O_CREAT | O_RDWR, 0666);
        if (m_shmFd < 0) {
            std::cerr << "[Axiom IPC] Failed POSIX shm_open. Errno: " << errno << std::endl;
            return false;
        }

        if (ftruncate(m_shmFd, sizeof(AxiomIpcBuffer)) != 0) {
            std::cerr << "[Axiom IPC] Failed POSIX ftruncate. Errno: " << errno << std::endl;
            close(m_shmFd);
            m_shmFd = -1;
            return false;
        }

        void* ptr = mmap(nullptr, sizeof(AxiomIpcBuffer), PROT_READ | PROT_WRITE, MAP_SHARED, m_shmFd, 0);
        if (ptr == MAP_FAILED) {
            std::cerr << "[Axiom IPC] Failed POSIX mmap. Errno: " << errno << std::endl;
            close(m_shmFd);
            m_shmFd = -1;
            return false;
        }

        m_buffer = static_cast<AxiomIpcBuffer*>(ptr);
        std::memset(m_buffer, 0, sizeof(AxiomIpcBuffer));
        m_buffer->magic = IPC_MAGIC;
        m_buffer->version = IPC_VERSION;
        m_buffer->status = 0; // IDLE

        sem_unlink(IPC_REQ_SEM_NAME);
        sem_unlink(IPC_RESP_SEM_NAME);
        m_reqSem = sem_open(IPC_REQ_SEM_NAME, O_CREAT, 0666, 0);
        m_respSem = sem_open(IPC_RESP_SEM_NAME, O_CREAT, 0666, 0);

        if (m_reqSem == SEM_FAILED || m_respSem == SEM_FAILED) {
            std::cerr << "[Axiom IPC] Failed POSIX sem_open. Errno: " << errno << std::endl;
            return false;
        }

        m_running = true;
        std::cout << "[Axiom IPC] POSIX Shared Memory Buffer initialized (" << sizeof(AxiomIpcBuffer) << " bytes)." << std::endl;
        return true;
#endif
    }

    template <typename DeciderFunc, typename TensorDeciderFunc>
    void run_service_loop(DeciderFunc decider, TensorDeciderFunc tensor_decider) {
        if (!m_running || !m_buffer) {
            std::cerr << "[Axiom IPC] Server not initialized." << std::endl;
            return;
        }
        std::cout << "[Axiom IPC] Daemon active: servicing sub-15us zero-copy text and tensor requests..." << std::endl;

#ifdef _WIN32
        HANDLE req_event = static_cast<HANDLE>(m_hReqEvent);
        HANDLE resp_event = static_cast<HANDLE>(m_hRespEvent);

        while (m_running) {
            DWORD dwWait = WaitForSingleObject(req_event, 500);
            if (dwWait == WAIT_OBJECT_0) {
                if (m_buffer->status == 1) { // REQ_READY
                    if (m_buffer->feature_dim > 0 && m_buffer->input_len == 0) {
                        // Direct Binary Feature Tensor Fast Path
                        auto res = tensor_decider(m_buffer->feature_vector, m_buffer->feature_dim);
                        write_response(res);
                    } else {
                        // Text Directive Fast Path
                        uint32_t len = (m_buffer->input_len < sizeof(m_buffer->input_text) - 1) ? m_buffer->input_len : (sizeof(m_buffer->input_text) - 1);
                        std::string input(m_buffer->input_text, len);
                        auto res = decider(input);
                        write_response(res);
                    }
                    m_buffer->status = 2; // RESP_READY
                    SetEvent(resp_event);
                }
            } else if (dwWait == WAIT_TIMEOUT) {
                continue;
            } else {
                break;
            }
        }
#else
        while (m_running) {
            struct timespec ts;
            clock_gettime(CLOCK_REALTIME, &ts);
            ts.tv_nsec += 500000000; // 500ms
            if (ts.tv_nsec >= 1000000000) {
                ts.tv_sec += 1;
                ts.tv_nsec -= 1000000000;
            }
            int s = sem_timedwait(m_reqSem, &ts);
            if (s == 0) {
                if (m_buffer->status == 1) { // REQ_READY
                    if (m_buffer->feature_dim > 0 && m_buffer->input_len == 0) {
                        auto res = tensor_decider(m_buffer->feature_vector, m_buffer->feature_dim);
                        write_response(res);
                    } else {
                        uint32_t len = (m_buffer->input_len < sizeof(m_buffer->input_text) - 1) ? m_buffer->input_len : (sizeof(m_buffer->input_text) - 1);
                        std::string input(m_buffer->input_text, len);
                        auto res = decider(input);
                        write_response(res);
                    }
                    m_buffer->status = 2; // RESP_READY
                    sem_post(m_respSem);
                }
            } else if (errno == ETIMEDOUT) {
                continue;
            } else {
                break;
            }
        }
#endif
    }

    template <typename DeciderFunc>
    void run_service_loop(DeciderFunc decider) {
        run_service_loop(decider, [decider](const float*, size_t) {
            return decider("binary_tensor_fallback");
        });
    }

    void stop() {
        m_running = false;
#ifdef _WIN32
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
#else
        if (m_buffer) {
            m_buffer->status = 3;
            munmap(m_buffer, sizeof(AxiomIpcBuffer));
            m_buffer = nullptr;
        }
        if (m_shmFd >= 0) {
            close(m_shmFd);
            m_shmFd = -1;
        }
        shm_unlink(IPC_SHARED_MEM_NAME);
        if (m_reqSem != SEM_FAILED) {
            sem_close(m_reqSem);
            sem_unlink(IPC_REQ_SEM_NAME);
            m_reqSem = SEM_FAILED;
        }
        if (m_respSem != SEM_FAILED) {
            sem_close(m_respSem);
            sem_unlink(IPC_RESP_SEM_NAME);
            m_respSem = SEM_FAILED;
        }
#endif
    }

    AxiomIpcBuffer* get_buffer() noexcept { return m_buffer; }
    bool is_running() const noexcept { return m_running; }

private:
    template <typename ResT>
    void write_response(const ResT& res) {
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
    }

    AxiomIpcBuffer* m_buffer;
    bool m_running;

#ifdef _WIN32
    void* m_hMapFile;
    void* m_hReqEvent;
    void* m_hRespEvent;
#else
    int m_shmFd;
    sem_t* m_reqSem;
    sem_t* m_respSem;
#endif
};

} // namespace axiom
