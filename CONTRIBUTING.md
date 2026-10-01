# Contributing to Axiom Core

Thank you for your interest in contributing to **Axiom Core**! 

Axiom Core is a mission-critical reflex engine designed for physical robots, aerospace vehicles, and synthesizable silicon. Because physical safety and sub-microsecond determinism are paramount, every contribution must adhere to strict architectural invariants.

---

## 🏛️ The 4 Non-Negotiable Architectural Invariants

### Invariant 1: Zero Dynamic Heap Allocations on Critical Paths
* **Rule:** On the fast decision path, calls to `malloc`, `free`, `new`, `delete`, `std::vector::push_back`, `std::string` concatenation, or any dynamically-resizing data structure are **strictly forbidden**.
* **Reasoning:** Memory allocators incur unpredictable OS syscalls, heap fragmentation, and non-deterministic latency spikes ($10\ \mu\text{s} - 100\ \mu\text{s}$).
* **Requirement:** Use fixed-capacity arrays, stack-allocated primitives, or bump-pointer memory arenas ([`huge_page_arena.hpp`](products/axiom-core/include/axiom/huge_page_arena.hpp)).

### Invariant 2: Mathematical Safety & Bounded Loops
* **Rule:** All safety mechanisms must be backed by formal mathematical invariants (e.g., Ville's Martingale inequalities, Control Lyapunov-Barrier Functions, or Linear Inverted Pendulum equations).
* **Reasoning:** Heuristic "if-else" bounds and soft penalty functions fail under out-of-distribution physical shocks.
* **Requirement:** Loops must have static upper bounds (e.g., `#pragma unroll`, `for (int i = 0; i < 128; ++i)`). Unbounded `while (true)` loops without watchdog breaks are rejected.

### Invariant 3: Pure ASCII Code Generators
* **Rule:** All code generators and CLI outputs in `compiler.py` and `certifier.py` must use pure ASCII characters (e.g., `alpha`, `us`, `Real`, `Nat` instead of Greek or Unicode symbols).
* **Reasoning:** Ensures 100% crash-free compilation across diverse global terminal environments (Windows CP1252, embedded RTOS serial consoles, CI runners).

### Invariant 4: Standalone Header Compilability
* **Rule:** Every header in [`products/axiom-core/include/axiom/`](products/axiom-core/include/axiom/) must be self-contained and compile standalone without missing include dependencies.
* **Verification:** `g++ -O3 -std=c++17 -fsyntax-only <header_path>` must succeed with zero warnings.

---

## 🛠️ Development & Verification Workflow

### 1. Set Up Your Environment
Ensure you have Python 3.10+ and a standard C++ compiler (`g++`, `clang++`, or `cl.exe`):
```powershell
python --version
g++ --version
```

### 2. Verify Baseline Tests
Before making any changes, confirm that all 69 tests pass:
```powershell
python tests/test_all.py
```

### 3. Build & Run Native C++ Verification
Run the one-click native build script:
```powershell
.\build_native.bat
```

### 4. Adding a New Robot Kinematic Model or Sensor Bus
When introducing a new robotic model (e.g., a quadruped locomotion kernel or an EtherCAT bus):
1. **Define C++ Header:** Create `include/axiom/<your_subsystem>.hpp` with zero dynamic allocations and 64-byte aligned structs.
2. **Add Native Test:** Add a test case in [`products/axiom-core/tests/test_superium_native.cpp`](products/axiom-core/tests/test_superium_native.cpp) and verify it with `build_native.bat`.
3. **Define Python Bridge:** Create `products/axiom-core/axiom_core/<your_subsystem>.py` with typed APIs and error checking.
4. **Add Automated Test:** Register unit tests in `products/axiom-core/tests/test_physical_machine_era.py`.
5. **Run Full Verification:** Execute `python tests/test_all.py` and ensure the pass rate remains 100%.

---

## 📋 Pull Request Checklist

Before submitting a Pull Request, ensure every item below is checked:

- [ ] `python tests/test_all.py` passes 100% of test cases.
- [ ] `build_native.bat` compiles cleanly with zero errors.
- [ ] No dynamic heap allocations (`new`, `malloc`, `std::vector`) introduced on the critical fast path.
- [ ] All code generators use pure ASCII strings.
- [ ] Any new safety gate includes a Ville martingale or Lyapunov-barrier certificate.
- [ ] Code formatting adheres to PEP 8 (Python) and ISO C++17/C++20 standards.

---

## 💬 Community & Discussion

For research collaborations, formal proof extensions, or silicon synthesis support, open an issue or pull request in the repository. We welcome contributions that advance the frontier of provably safe physical machines.
