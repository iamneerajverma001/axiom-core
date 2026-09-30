# Axiom Monorepo Architecture

> **Ultra-Low-Latency Neuromorphic Intelligence & Autonomous PC Operating System**  
> *The True Successor to Jev, Laya, and Laya-MLX.*

---

## 🏛️ Monorepo Products Architecture

```
Naya/
├── products/
│   ├── axiom-core/          # Universal Foundational Decision Engine (C++20 & Python SDK)
│   ├── axiom-os/            # Autonomous Neuromorphic Desktop Copilot & Agent OS
│   └── axiom-vision-tensor/ # Sub-16ms Soft-Argmax Visual-Spatial Click Tensor Library
├── examples/                # Quickstart & Integration Examples (SDK, OpenAI, TradingView)
├── tests/                   # Monorepo Unified Test Runner & Verification Suite
├── start_axiom.bat          # 1-Click Desktop Launcher for Axiom OS
└── .gitignore               # Clean monorepo ignore rules
```

---

## 📦 Products Overview

### 1. [Axiom Core](file:///products/axiom-core/README.md) (`products/axiom-core/`)
* **Role**: Universal, product-agnostic foundational engine.
* **Technology**: Cache-aligned C++20 kernel (`alignas(64)`), zero-heap memory arena, Martingale conformal safety bounds ($1 - \alpha$), and Brier/Platt calibration.
* **Turnkey Enterprise Solutions**:
  * **FinTech Pre-Trade Risk Firewall** (`>115,000` orders/sec, sub-20µs fat-finger & price collar guard).
  * **Cybersecurity Packet Guard** (`>100,000` packets/sec line-rate SYN scrub & port filtering).
  * **Robotics Motor Reflex Arc** (`>50,000` Hz deterministic torque clipping & collision avoidance).
* **Package**: `axiom_core` Python SDK with typed decision queries (`ask_choice`, `ask_boolean`, `score`, `batch_decide`).

### 2. [Axiom OS](file:///products/axiom-os/README.md) (`products/axiom-os/`)
* **Role**: Autonomous desktop workstation companion with native Win32 hardware control.
* **Technology**: Dual-speed System 1 (sub-16ms reflex muscle memory) + System 2 (hierarchical DAG planner & ReAct brain).
* **Key Capabilities**:
  * **Win32 Actuator**: Direct typing (`VkKeyScanW`), multi-window orchestration, audio, files, and processes.
  * **Hardware Hotkey Reflex**: Win32 background message pump binding `Win + Alt + V`.
  * **Web HUD Studio**: Interactive Vision-Tensor Laboratory with 128-dim canvas visualizer and real-time enterprise benchmarks.
  * **Mobile Touch Cockpit**: Offline LAN touch controller with QR code pairing.
  * **Autonomous Sentinels**: CPU thermal governor, port guardian, lock guard, and temp hygiene.

### 3. [Axiom Vision Tensor](file:///products/axiom-vision-tensor/README.md) (`products/axiom-vision-tensor/`)
* **Role**: Zero-OCR, zero-cloud visual spatial localization library.
* **Technology**: 2D marginal soft-argmax regression producing 128-dimensional continuous float feature vectors (`64-bin P_X` + `64-bin P_Y`).

---

## ⚡ Quickstart

### 1. Launch Axiom OS
To start the unified server and open the Web Studio:
```cmd
start_axiom.bat
```
* **Desktop Studio**: `http://localhost:3000`
* **Mobile Cockpit**: `http://localhost:3000/mobile`
* **Vision & Enterprise Studio**: Open the **Vision & Enterprise Studio** tab in the HUD.

### 2. Run the Unified Test Suite
Run tests across all products with a single command:
```cmd
python tests/test_all.py
```

### 3. Run Individual Product Test Suites
```cmd
# Axiom Core
python -m unittest discover products/axiom-core/tests

# Axiom OS
python -m unittest discover products/axiom-os/tests

# Axiom Vision Tensor
python -m unittest discover products/axiom-vision-tensor/tests
```

---

## 💡 Developer Examples (`examples/`)

* [`examples/python_sdk_example.py`](file:///examples/python_sdk_example.py): Direct Python SDK integration with `AxiomClient`.
* [`examples/openai_dropin_example.py`](file:///examples/openai_dropin_example.py): OpenAI API drop-in compatibility for existing agent frameworks.
* [`examples/tradingview_example.py`](file:///examples/tradingview_example.py): Webhook alert ingestion for high-speed algorithmic execution.
* [`examples/cloud_fallback_demo.py`](file:///examples/cloud_fallback_demo.py): Hybrid fallback routing to cloud LLMs (Claude, GPT-4, OpenRouter).
