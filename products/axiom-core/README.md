# Axiom-Core: Bare-Metal Neuromorphic Decision Engine & C++20 SDK

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Latency](https://img.shields.io/badge/Fast--Path%20Latency-%3C15%C2%B5s-brightgreen.svg)]()
[![Throughput](https://img.shields.io/badge/Throughput-15%2C000%2B%20decisions%2Fsec-success.svg)]()
[![Safety](https://img.shields.io/badge/Conformal%20Safety-Martingale%20Ville's%20Inequality-blueviolet.svg)]()

**Axiom-Core** is a high-throughput, bare-metal C++20 neuromorphic decision engine and Python SDK engineered for mission-critical, sub-millisecond control systems. 

Unlike traditional LLM agents that require 500ms to 5,000ms per decision and incur high API token costs, Axiom-Core routes structured operational directives in **less than 15 microseconds** via zero-copy Win32 shared-memory IPC, with distribution-free Martingale safety guarantees.

---

## ⚡ Key Architectural Pillars

1. **Bare-Metal C++20 Fast Path:**
   - Evaluates a 3-tier sparse hierarchical register tree (`include/axiom/register_tree.hpp`).
   - AVX2-accelerated sparse tensor inner products (`sparse_tensor_loop.hpp`).
   - Zero dynamic heap allocations in the critical path using bump-pointer memory arenas (`memory_arena.hpp`).

2. **Sub-15 Microsecond Zero-Copy Shared Memory IPC:**
   - Connects Python processes directly to the native C++ daemon using Win32 memory-mapped files and named event semaphores (`Local\AxiomSharedMemoryPool`).
   - Over **15,000 decisions/second** on a single consumer CPU core.

3. **Martingale Conformal Safety Barrier:**
   - Formal mathematical safety control based on sequential betting martingales and Ville's inequality ($P(\max M_k \ge 1/\alpha) \le \alpha$).
   - Dynamically intercepts destructive operations (`rmdir /s /q`, SQL table drops, torque runaway) before hardware actuators execute.

4. **Closed-Loop System 2 Deliberative Escalation:**
   - In-distribution operational queries commit immediately on the fast path (0 cloud cost).
   - Ambiguous or novel inputs gracefully escalate to System 2 (local Ollama or OpenRouter/Claude) with RLCD muscle memory reinforcement.

---

## 🚀 Turnkey Enterprise Solutions

Axiom-Core includes 3 fully operational, production-ready enterprise reference solutions in `solutions/`:

| Solution | Industry | Problem Solved | Latency / SLA |
| :--- | :--- | :--- | :--- |
| **FinTech Pre-Trade Risk Firewall** | Algorithmic Trading | Fat-finger blocking, collar bands, margin checks | **< 20 µs** |
| **Zero-Trust Packet Guard** | CyberSecurity | SYN flood, NULL scan, stealth port-scan filtering | **< 15 µs** |
| **Robotics Motor Reflex Arc** | Autonomous Robotics | 1000Hz torque saturation clipping, collision E-STOP | **< 25 µs** (1000Hz) |

---

## 📦 Quickstart (Python SDK)

### Installation
```bash
cd products/axiom-core
pip install -e .
```

### 1. High-Speed Decision Routing
```python
from axiom_core import AxiomClient

client = AxiomClient()
result = client.decide("postgresql deadlock transaction lock timeout kill deadlocked pid")

print(f"Path: {result.execution_path}")        # FAST_PATH_COMMIT
print(f"Leaf: {result.choice_label}")          # Database_Deadlock_Resolve
print(f"Latency: {result.latency_us:.2f} µs")   # 12.40 µs
print(f"Conformal Set: {result.conformal_set}") # [201]
```

### 2. Martingale Safety Interlock
```python
from axiom_core import MartingaleSafetyGate

gate = MartingaleSafetyGate(alpha=0.01)

# Dangerous command intercepted mathematically:
risk = gate.evaluate_action_risk("rmdir /s /q C:\\Windows", confidence=0.99, entropy=0.1)
if risk["requires_human_barrier"]:
    print(f"BLOCKED: {risk['reason']}")
```

---

## 🛠️ Building C++ Binaries from Source

```bash
cd products/axiom-core
mkdir build && cd build
cmake ..
cmake --build . --config Release
```
This produces `bin/axiom_cli.exe` and `bin/axiom_benchmark.exe`.

---

## 🧪 Testing

```bash
python -m unittest discover -s tests
python -m unittest solutions/fintech_pretrade_firewall/test_firewall.py
python -m unittest solutions/cybersecurity_packet_guard/test_packet_guard.py
python -m unittest solutions/robotics_motor_reflex/test_motor_reflex.py
```
