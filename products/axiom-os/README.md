# Axiom-OS: The Dual-Speed Neuromorphic Workstation & Mobile Copilot

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Architecture](https://img.shields.io/badge/Architecture-Dual--Speed%20(System%201%20%2B%20System%202)-blueviolet.svg)]()
[![Reflex Latency](https://img.shields.io/badge/System%201%20Reflex-%3C5ms-brightgreen.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%20%2B%20Mobile%20PWA-orange.svg)]()

**Axiom-OS** is the next-generation operating system copilot engineered around a dual-speed neuromorphic architecture. It unites bare-metal sub-millisecond C++ reflexes for 80 enterprise macros with an autonomous System 2 ReAct cognitive brain, real-time background sentinels, and peer-to-peer CRDT swarm synchronization between PC and mobile.

---

## ⚡ The Dual-Speed Architecture

```
                  USER OPERATIONAL DIRECTIVE
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       [SYSTEM 1: C++ FAST PATH]     [SYSTEM 2: COGNITIVE BRAIN]
       - Sub-15µs Shared Memory IPC   - ReAct Multi-Step Planner
       - 80 Enterprise Action Leaves  - Win32 Native Hardware Actuator
       - AVX2 Vector Similarity       - Soft-Argmax Visual Spatial Clicker
       - 0 Cloud Tokens / Cost        - Self-Correction & MCTS Search
               │                             │
               └──────────────┬──────────────┘
                              ▼
           [MARTINGALE CONFORMAL SAFETY GATE]
           - Ville's Inequality Stopping Rule
           - Intercepts destructive actions before execution
                              │
                              ▼
            [GROUNDED SYSTEM EXECUTION (WIN32)]
```

### 1. System 1 (C++ Neuromorphic Reflex Arc)
Directives such as *"clean temporary files"*, *"audit startup apps"*, or *"flush DNS cache"* execute in under 15 microseconds via `axiom-core` zero-copy shared-memory IPC. No LLM tokens or internet connection needed.

### 2. System 2 (ReAct Cognitive Brain & Grounded Actuators)
Complex multi-step directives (*"Find all PDF invoices on desktop, extract totals, and compile into an Excel report"*) dynamically trigger:
- **Grounded PowerShell & Win32 Process Control**
- **C/C++ Bare-Metal Compilation & Execution**
- **Sub-16ms Soft-Argmax Visual-Spatial Click Engine** (`axiom-vision-tensor`)
- **Camera Vision & Screen OCR**
- **Native Media & Window Management**

### 3. Latent Deliberation Unit (LDU)
Before calling cognitive models, a 3-timestep Spiking Neural Network (LIF) extracts domain priors in 0.5ms to focus the LLM's context window on the exact relevant subsystem.

### 4. Autonomous Sentinels
Background daemons continuously monitor:
- System Resource Pressure (CPU, RAM, Disk)
- Rogue Listening Ports & Network Anomalies
- Battery & Power Drain
- Audio/Media Session State

### 5. P2P Swarm CRDT Sync
Synchronizes skills, macros, and device clipboard seamlessly across multiple workstations and mobile devices on port 3001 using conflict-free replicated data types.

---

## 🖥️ Surfaces & Interfaces

1. **Desktop Studio (`http://localhost:3000`):** High-density cybernetic dashboard with terminal logs, telemetry gauges, and interactive skill catalog.
2. **Mobile Cockpit (`http://localhost:3000/mobile.html`):** Responsive touch-first web application for commanding your PC from any smartphone or tablet.
3. **Floating Cybernetic Orb (`start_floating_orb.bat`):** Draggable desktop HUD overlay for instant access and system status.

---

## 🚀 Quickstart

### Launch Axiom-OS
Double click `start_axiom_os.bat` or run:
```bash
python ui/server.py
```
Then navigate to `http://localhost:3000`.

### Launch Floating Desktop Widget
```bash
python -m src.omni_floating_widget
```

---

## 🧪 Testing

```bash
python -m unittest discover -s tests
```
