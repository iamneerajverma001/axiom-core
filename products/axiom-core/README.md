# Axiom-Core: Universal Reflex Kernel & Formal Safety Substrate

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-69%2F69%20Passing-brightgreen.svg)](tests/)
[![Fast-Path Latency](https://img.shields.io/badge/Fast--Path%20Latency-70--120%20ns-brightgreen.svg)](include/axiom/)
[![Silicon Clock](https://img.shields.io/badge/FPGA%20Verilog-5.0%20ns%20(200%20MHz)-blueviolet.svg)](axiom_lif_core.v)
[![Throughput](https://img.shields.io/badge/Throughput-1%2C000%2C000%2B%20decisions%2Fsec-success.svg)](benchmarks/)
[![Safety](https://img.shields.io/badge/Safety-Ville's%20Martingale%20%26%20CLBF-red.svg)](axiom_core/lyapunov_barrier.py)
[![Targets](https://img.shields.io/badge/Targets-C%2B%2B20%20%7C%20C23%20%7C%20Verilog%20%7C%20Lean%204-orange.svg)](axiom_core/compiler.py)

**Axiom-Core** is a high-throughput, bare-metal C++20 neuromorphic reflex kernel and Python SDK engineered for mission-critical, sub-microsecond physical control systems, autonomous robotics, aerospace flight control, and synthesizable silicon.

While traditional cloud foundation models require 500ms to 5,000ms per decision and incur latency jitter and cloud failure risks, Axiom-Core routes structured operational directives and physical reflex actions in **70 to 120 nanoseconds natively in C++** and **less than 8.4 microseconds via zero-copy shared-memory IPC**, with non-asymptotic distribution-free Martingale safety bounds ($P(\sup M_t \ge 1/\alpha) \le \alpha$).

---

## ⚡ Key Architectural Pillars

1. **Bare-Metal C++20 Zero-Heap Engine:**
   - 36 standalone C++ headers with contiguous memory arenas and AVX2 SIMD sector trees.
   - Zero dynamic heap allocations in critical paths (`alignas(64)` cache-line alignment).
   - Fast-path execution in **$70 - 120\text{ ns}$**.

2. **Control Lyapunov-Barrier Functions (CLBF):**
   - Active-set quadratic programming projection enforcing safe invariant sets $\dot{h}(\mathbf{x}, \mathbf{u}) + \gamma(h(\mathbf{x})) \ge 0$.
   - Computes closed-form projection $\mathbf{u}^*$ in **$< 0.8\ \mu\text{s}$** without dynamic memory allocations.

3. **Ville's Martingale Maximal Stopping Bounds:**
   - Formal mathematical safety control based on non-negative supermartingales.
   - Non-asymptotic false alarm bounds $\mathbb{P}(\sup M_t \ge 1/\alpha) \le \alpha$ holding across arbitrary non-stationary and non-Gaussian distributions.

4. **Multi-Target Ahead-of-Time Compiler (`axiomc v3.0`):**
   - Compiles declarative JSON/`.axiom` policies to **C++20**, **Freestanding C23**, **Synthesizable Verilog HDL**, and **Lean 4 machine-checked proofs**.

5. **Physical Hardware & Sensor Protocol Bridges:**
   - **MAVLink 2.0**: Direct packet serialization for PX4 and ArduPilot flight controllers in **$< 0.4\ \mu\text{s}$**.
   - **DVS Event Camera**: Dynamic Vision Sensor microsecond spike ingestion into continuous time surfaces in **$< 1.2\ \mu\text{s}$**.
   - **CAN-FD / ISO 11898**: High-speed deterministic automotive and robot actuator bus.
   - **Sim2Real Bridge**: Binary UDP/SHM link for Isaac Sim, MuJoCo, and Gazebo in **$< 0.3\ \mu\text{s}$**.

6. **Terrestrial Bipedal & Cobot Kinematic Reflexes:**
   - **Bipedal Locomotion**: 1,000 Hz Linear Inverted Pendulum Model (LIPM), ZMP polygon monitoring, and dynamic Capture Point (CP) stumble recovery in **$< 1.1\ \mu\text{s}$**.
   - **6-DOF Manipulator**: Damped Least Squares (DLS) Jacobian pseudoinverse tracking and contact impedance compliant backdrive in **$< 0.9\ \mu\text{s}$**.

---

## 📦 Quickstart (Python SDK & Toolchain)

### Installation
```bash
cd products/axiom-core
pip install -e .
```

### 1. Compile Policies to Verilog Silicon, C++, and Lean 4
```bash
# Compile to Verilog HDL (axiom_lif_core.v):
python -m axiom_core.compiler examples/policies/quadcopter_defense.json --target verilog

# Compile to Formal Lean 4 Proof:
python -m axiom_core.compiler examples/policies/quadcopter_defense.json --target lean4

# Compile to Zero-Heap C++20 Header:
python -m axiom_core.compiler examples/policies/quadcopter_defense.json --target cpp20

# Compile to Freestanding C23 for Microcontrollers:
python -m axiom_core.compiler examples/policies/quadcopter_defense.json --target c23
```

### 2. Run Automated Ville Formal Safety Certification
```bash
python -m axiom_core.certifier
```
*Outputs cryptographically sealed certificate `axiom_safety_certificate.vcert.json` verifying 0 barrier violations over 5,000 adversarial stress trials.*

### 3. High-Speed Decision Client
```python
from axiom_core import AxiomClient

client = AxiomClient()
result = client.decide("postgresql deadlock transaction lock timeout kill deadlocked pid")

print(f"Path: {result.execution_path}")        # FAST_PATH_COMMIT
print(f"Leaf: {result.choice_label}")          # Database_Deadlock_Resolve
print(f"Latency: {result.latency_us:.2f} µs")   # 8.40 µs
```

### 4. Direct 128-Dim Continuous Spatial Tensor Reflex
```python
visual_features = [0.0] * 128
visual_features[42] = 0.95  # Anomaly activation peak

reflex = client.decide_visual_tensor(visual_features, fallback_label="Critical_Obstacle_Evasion")
print(f"Reflex: {reflex.choice_label} in {reflex.latency_us:.2f} µs")
```

---

## 🛠️ Verification & Tests

```bash
# Run all tests in Axiom Core:
python -m unittest discover tests

# Build and run native C++ verification benchmark:
../../build_native.bat
```
