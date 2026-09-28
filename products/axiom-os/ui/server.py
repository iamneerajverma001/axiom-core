#!/usr/bin/env python3
"""
Axiom-1 Universal Integration Hub & High-Speed REST / OpenAI Gateway
Provides:
1. OpenAI-Compatible Gateway: POST /v1/chat/completions & GET /v1/models
2. TradingView Webhook Handler: POST /webhook/tradingview
3. Native Decision Engine: POST /api/decide & POST /v1/decide
4. Health & Status Telemetry: GET /api/health & GET /api/ollama_status
5. Static Web UI & Studio: GET /
"""

import http.server
import socketserver
import subprocess
import urllib.request
import urllib.error
import json
import os
import sys
import time
import uuid

PORT = 3000
UI_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(UI_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src import axiom_os_bridge as bridge
from src import omni_sensor
from src import omni_actuator
from src import omni_brain
from src import omni_reflex
from src.omni_sentinel import sentinel_manager
from src.omni_ldu import ldu_engine
from src.omni_vision_tensor import vision_tensor_engine
from src.omni_mcts_planner import mcts_planner
from src.omni_policy_optimizer import policy_optimizer
from src.omni_mesh_swarm import mesh_node
from src.axiom_ipc_bridge import ipc_bridge
from src.omni_catalog import app_catalog

CLI_EXE = os.path.join(PROJECT_ROOT, "axiom_cli.exe")
OLLAMA_BASE = "http://127.0.0.1:11434"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE}/v1/chat/completions"
OLLAMA_TAGS_URL = f"{OLLAMA_BASE}/api/tags"

# Ring buffer for remote executed task history
EXECUTION_HISTORY = []

def record_execution(goal, mode, latency_ms, success, message=""):
    global EXECUTION_HISTORY
    EXECUTION_HISTORY.insert(0, {
        "id": str(uuid.uuid4())[:8],
        "timestamp": time.strftime("%H:%M:%S"),
        "goal": goal,
        "mode": mode,
        "latency_ms": round(float(latency_ms), 1),
        "success": bool(success),
        "message": str(message)
    })
    if len(EXECUTION_HISTORY) > 60:
        EXECUTION_HISTORY.pop()

# Default action responses when Fast Path commits
# Comprehensive action responses when Fast Path commits (80 Leaves across 8 Desktop Sectors)
ACTION_RESPONSES = {
    # Sector 0: Windows OS & Hardware Control (401-410)
    401: "Process mitigation active: Target high-load CPU/RAM thread identified and throttled.",
    402: "Port liberation active: Scanning listening TCP connections and releasing bound sockets.",
    403: "Disk maintenance active: Temporary cache, stale lockfiles, and build artifacts purged.",
    404: "Battery EcoQoS active: CPU power throttling engaged and background indexing suspended.",
    405: "Workstation security active: Workstation locked securely via Win32 LockWorkStation API.",
    406: "Audio master volume control active: Volume level updated.",
    407: "Display brightness & resolution control active.",
    408: "Bluetooth radio cycle: Bluetooth adapters refreshed.",
    409: "Clipboard wipe active: Sensitive memory sanitized.",
    410: "Hardware telemetry snapshot captured.",

    # Sector 1: Dev & Terminal Engineering (501-510)
    501: "Git tree status: Working tree analyzed, auto-staged, and synced.",
    502: "Compiler diagnostic fix: Build syntax and template error analyzed.",
    503: "Self-healing terminal: Exit code and stderr analyzed.",
    504: "Container orchestration: Container state verified.",
    505: "Package manager dependency resolution active.",
    506: "Code linter & auto-formatter dispatched.",
    507: "Test runner and coverage report executed.",
    508: "Git branch and rebase operation dispatched.",
    509: "GDB/LLDB debugger trace attached.",
    510: "CMake build generator configured.",

    # Sector 2: Research & Memory (601-610)
    601: "Research ingest: Paper metadata, abstract, and citations parsed into local index.",
    602: "Codebase semantic index: Symbol graph and AST relationships refreshed.",
    603: "Mathematical computation: Formula solved and numeric bounds verified.",
    604: "Research memory: Breakthrough note appended to RESEARCH_LOG.md.",
    605: "BibTeX citation generated.",
    606: "Literature survey comparative map constructed.",
    607: "Dataset schema and distributions profiled.",
    608: "Notebook headless execution dispatched.",
    609: "Knowledge graph associative link registered.",
    610: "Benchmark plot and latency chart exported.",

    # Sector 3: Database & Local Storage (301-310)
    301: "PostgreSQL deadlock killer active: Blocking lock transactions resolved.",
    302: "Redis cache memory eviction active: Stale cache keys purged.",
    303: "Database schema migration applied.",
    304: "Connection pool parameters tuned.",
    305: "Slow query EXPLAIN ANALYZE profile computed.",
    306: "Database archive dump backup created.",
    307: "Search index reindex and shard balanced.",
    308: "SQLite WAL checkpoint and VACUUM executed.",
    309: "Storage IOPS saturation analyzed.",
    310: "Vector HNSW index built and compacted.",

    # Sector 4: Network & PC Security (201-210)
    201: "Windows Firewall security rule applied.",
    202: "MFA authentication token reset link issued.",
    203: "SSL/TLS certificate expiry inspected.",
    204: "DNS cache probe and flushdns executed.",
    205: "Credential stuffing brute-force attack blocked.",
    206: "Privilege audit: Escalation vectors inspected.",
    207: "Secret token exfiltration guard triggered.",
    208: "VPN secure tunnel connection restored.",
    209: "Packet sniffer and interface diagnostics active.",
    210: "SSH public key credentials distributed.",

    # Sector 5: Window & Workspace Orchestration (701-710)
    701: "Window Snapper active: Active window snapped or tiled via Win32 hardware keys.",
    702: "Show Desktop active: Minimized all open application windows (Win+D).",
    703: "Virtual desktop switch active: Switched virtual desktop workspace.",
    704: "Focus mode isolate active: Minimized all background windows; active window isolated.",
    705: "Multi-monitor move active: Window shifted to secondary display.",
    706: "Window find & activate: Target application brought to foreground.",
    707: "Always-on-Top active: Toggled HWND_TOPMOST pin for active window.",
    708: "Screen snip tool active: Win+Shift+S screen capture dispatched.",
    709: "Boss Key active: Emergency minimize all windows and mute master audio.",
    710: "Workspace layout restore: Multi-window desktop arrangement loaded.",

    # Sector 6: Multimedia, Display & Audio Cockpit (801-810)
    801: "Audio endpoint switch active: Toggled default playback between headphones and speakers.",
    802: "Microphone privacy guard active: Toggled hardware microphone mute.",
    803: "Master volume control active: Audio volume adjusted.",
    804: "Display night light active: Blue light filter and warm color temperature toggled.",
    805: "Multimedia controller active: Global media play/pause/track key dispatched.",
    806: "Screen recording trigger active: Screen recording session toggled.",
    807: "Webcam privacy guard active: Webcam driver shutter engaged.",
    808: "Display orientation switch active.",
    809: "Display HDR & vibrant color profile toggled.",
    810: "Ambient brightness synchronized.",

    # Sector 7: Desktop Automation & File Intelligence (901-910)
    901: "Duplicate file sweep active: Scanned for redundant large files wasting disk space.",
    902: "Downloads auto-organizer active: Categorized messy files into clean subdirectories.",
    903: "Bulk file rename active: Mass renamer executed.",
    904: "Archive compression/extraction active: Zip archive processed.",
    905: "Directory symlink created.",
    906: "Registry stale MRU keys swept and optimized.",
    907: "Startup apps audit active: Queried Windows Run keys.",
    908: "Windows background service restarted.",
    909: "File SHA256 integrity hash verified.",
    910: "Workspace backup active: Created timestamped compressed zip snapshot."
}

def execute_native_axiom(input_text: str) -> dict:
    """Executes the bare-metal C++ DirectML binary with given input."""
    # 1. Ultra-Low-Latency Zero-Copy Shared-Memory IPC Fast-Path (<15 microseconds)
    if ipc_bridge and ipc_bridge.is_ready():
        res = ipc_bridge.query_native(input_text)
        if res:
            return res

    # 2. Subprocess Fallback
    if not os.path.exists(CLI_EXE):
        return {
            "execution_path": "ERROR_NO_BINARY",
            "choice_label": "CLI_Not_Found",
            "confidence": 0.0,
            "error": f"Binary missing at {CLI_EXE}"
        }
    try:
        t0 = time.time()
        env = os.environ.copy()
        env["AXIOM_NO_SOCKET"] = "1"
        proc = subprocess.run(
            [CLI_EXE, input_text],
            capture_output=True,
            text=True,
            timeout=15,
            env=env
        )
        output_str = proc.stdout.strip()
        json_start = output_str.find('{')
        json_end = output_str.rfind('}')
        if json_start != -1 and json_end != -1:
            data = json.loads(output_str[json_start:json_end+1])
            data["wall_time_us"] = (time.time() - t0) * 1_000_000.0
            return data
        else:
            return {
                "execution_path": "SYSTEM2_FALLBACK",
                "choice_label": "Unparsed_Output",
                "confidence": 0.5,
                "raw_output": output_str
            }
    except Exception as e:
        return {
            "execution_path": "SYSTEM2_FALLBACK",
            "choice_label": "Exception_Fallback",
            "confidence": 0.0,
            "error": str(e)
        }

def query_cloud_system2(input_text, candidate_leaf, provider="openrouter", api_key="", model="anthropic/claude-3.5-sonnet", base_url="https://openrouter.ai/api/v1"):
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Axiom-1 Decision Engine"
    }
    prompt = (
        f"Axiom-1 System 2 Verification: An operational request arrived: \"{input_text[:1500]}\". "
        f"Target candidate category: {candidate_leaf}. "
        f"Answer concisely in under 20 words whether this category fits."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are Axiom-1 System 2 Cloud Verification Engine. Answer concisely with brief verification."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 32,
        "temperature": 0.1
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
    with urllib.request.urlopen(req, timeout=12) as resp:
        res_data = json.loads(resp.read().decode('utf-8'))
        return res_data['choices'][0]['message']['content'].strip()

def query_ollama_chat(messages, model="qwen2.5-coder:1.5b", max_tokens=128):
    """Forwards chat completion payload to local Ollama /v1/chat/completions with desktop agent system prompt."""
    has_system = any(m.get('role') == 'system' for m in messages)
    chat_messages = list(messages)
    if not has_system:
        chat_messages.insert(0, {
            "role": "system",
            "content": (
                "You are Axiom-1 Desktop Omni-Agent, an intelligent autonomous PC companion with native Win32 hardware control. "
                "Always assist the user directly with desktop commands, media playback, window management, files, or coding questions. "
                "Be direct, concise, and helpful. Never refuse desktop or computing control requests."
            )
        })
    payload = {
        "model": model,
        "messages": chat_messages,
        "temperature": 0.3,
        "max_tokens": max_tokens
    }
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(OLLAMA_CHAT_URL, data=data_bytes, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

class AxiomUniversalHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=UI_DIR, **kwargs)

    def do_OPTIONS(self):
        """Enable CORS preflight for all origins and headers."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, HEAD')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.end_headers()

    def do_HEAD(self):
        """Handle HEAD requests using GET handler logic."""
        self.do_GET()

    def _handle_webhook(self, raw_body=""):
        try:
            t0 = time.perf_counter()
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            body = json.loads(raw_body) if raw_body else {}

            goal = body.get("goal") or params.get("goal", [""])[0]
            action = body.get("action") or params.get("action", [""])[0]
            target = body.get("target") or params.get("target", [""])[0]
            query = body.get("query") or params.get("query", [""])[0]

            if not goal and action:
                if action in ("mute", "play", "play_music", "next", "prev", "volume_up", "volume_down"):
                    res = omni_actuator.media_control(action, query=query or target)
                elif action in ("lock", "sleep", "boss_key", "screenshot"):
                    res = omni_actuator.system_control(action, target=target)
                elif action in ("snap_left", "snap_right", "maximize", "minimize", "desktop_next", "desktop_new"):
                    res = omni_actuator.window_manager(action)
                elif action in ("dark_mode", "light_mode", "toggle_theme", "theme"):
                    res = omni_actuator.system_theme_control("toggle")
                elif action == "search":
                    res = omni_actuator.web_search(query or target, launch_website=False)
                elif action == "launch_website":
                    res = omni_actuator.web_search(query or target, launch_website=True)
                else:
                    res = omni_actuator.execute_tool(action, target=target, query=query)
                elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                record_execution(f"Webhook: {action}", "WEBHOOK_DIRECT", elapsed_ms, res.get("success", True), res.get("message", ""))
                self._send_json({"success": True, "mode": "WEBHOOK_DIRECT", "latency_ms": elapsed_ms, "result": res})
                return

            if goal:
                # Check compound query first
                sub_queries = omni_reflex.split_compound_query(goal)
                if len(sub_queries) > 1:
                    compound = omni_reflex.match_compound_reflex(goal)
                    if compound and len(compound) >= 2:
                        res = omni_reflex.execute_compound_reflex(compound, original_query=goal)
                        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                        record_execution(goal, "PARALLEL_REFLEX_PLAN", elapsed_ms, res.get("success", True), res.get("final_answer", ""))
                        self._send_json({"success": True, "mode": "PARALLEL_REFLEX_PLAN", "latency_ms": elapsed_ms, "result": res})
                        return

                matched = omni_reflex.match_reflex(goal)
                if matched and matched.get("confidence", 0) >= 0.70:
                    res = omni_reflex.execute_reflex_action(matched, goal)
                    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                    record_execution(goal, "FAST_REFLEX_COMMIT", elapsed_ms, res.get("success", True), res.get("message", ""))
                    self._send_json({"success": True, "mode": "FAST_REFLEX_COMMIT", "latency_ms": elapsed_ms, "result": res})
                    return
                clean_target = goal.lower()
                for prefix in ("open ", "launch ", "start ", "run "):
                    if clean_target.startswith(prefix):
                        clean_target = clean_target[len(prefix):].strip()
                        break
                catalog_match = app_catalog.resolve(clean_target) if app_catalog else None
                if catalog_match:
                    res = omni_actuator.app_control(action="launch", target=clean_target)
                    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                    record_execution(goal, "CATALOG_APP_LAUNCH", elapsed_ms, res.get("success", True), res.get("message", ""))
                    self._send_json({"success": True, "mode": "CATALOG_APP_LAUNCH", "latency_ms": elapsed_ms, "result": res})
                    return

                # Otherwise execute autonomous brain (never divert to Google search)
                brain_res = omni_brain.execute_autonomous_task(user_goal=goal, max_steps=4)
                elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                record_execution(goal, "AUTONOMOUS_BRAIN_REACT", elapsed_ms, brain_res.get("success", True), brain_res.get("final_answer", ""))
                self._send_json({"success": brain_res.get("success", True), "mode": "AUTONOMOUS_BRAIN_REACT", "latency_ms": elapsed_ms, "result": brain_res})
                return

            self._send_json({"success": False, "error": "No goal or action specified."}, status=400)
            return
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, status=500)
            return

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else ""
        req_path = urllib.parse.urlparse(self.path).path

        # ---------------------------------------------------------
        # 0. OMNI-AGENT AUTONOMOUS CHAT & EXECUTION: POST /api/omni/chat
        # ---------------------------------------------------------
        if req_path == '/api/omni/chat':
            try:
                body = json.loads(raw_body) if raw_body else {}
                goal = (body.get('goal') or body.get('message') or body.get('prompt') or '').strip()
                provider = body.get('provider', 'ollama')
                model = body.get('model', '')
                if provider == 'ollama':
                    if not model or '/' in model or 'claude' in model or 'gpt' in model:
                        model = 'qwen2.5-coder:1.5b'
                elif provider in ('openrouter', 'custom'):
                    if not model or model == 'qwen2.5-coder:1.5b':
                        model = 'anthropic/claude-3.5-sonnet'
                api_key = body.get('api_key') or os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY', '')
                base_url = body.get('base_url', 'https://openrouter.ai/api/v1')
                force_brain = body.get('force_brain', False)

                if not goal:
                    self._send_json({"success": False, "error": "Empty goal provided"}, status=400)
                    return

                t0 = time.perf_counter()

                # P2P Swarm Work-Stealing: Offload heavy deliberation if local node is CPU-congested (>80%)
                if mesh_node and not body.get("is_offloaded"):
                    best_peer = mesh_node.find_best_offload_node()
                    if best_peer:
                        try:
                            body["is_offloaded"] = True
                            peer_url = f"http://{best_peer['ip']}:{best_peer['port']}/api/omni/execute"
                            req = urllib.request.Request(
                                peer_url,
                                data=json.dumps(body).encode('utf-8'),
                                headers={"Content-Type": "application/json"}
                            )
                            with urllib.request.urlopen(req, timeout=12) as peer_resp:
                                peer_data = json.loads(peer_resp.read().decode('utf-8'))
                                peer_data["offloaded_to_peer"] = best_peer
                                self._send_json(peer_data)
                                return
                        except Exception:
                            pass
                
                # Layer 1: Latent Deliberation Unit (LDU) sub-5ms non-token deliberation
                try:
                    ldu_delib = ldu_engine.deliberate(goal)
                except Exception:
                    ldu_delib = None
                
                # Check Fast-Path Muscle Memory Reflex first (unless force_brain requested)
                # 1. Compound Multi-Reflex Plan Check (e.g. "open camera and shot a image for if a person face appear")
                sub_queries = omni_reflex.split_compound_query(goal)
                is_compound = len(sub_queries) > 1

                if not force_brain and is_compound:
                    compound_match = omni_reflex.match_compound_reflex(goal, threshold=0.70)
                    if compound_match and len(compound_match) >= 2:
                        res = omni_reflex.execute_compound_reflex(compound_match, original_query=goal)
                        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                        response_payload = {
                            "success": res.get("success", True),
                            "execution_mode": res.get("execution_mode", "MULTI_REFLEX_PLAN"),
                            "milestones_count": res.get("milestones_count", len(compound_match)),
                            "confidence": 0.98,
                            "latency_ms": elapsed_ms,
                            "tokens_consumed": 0,
                            "ldu_deliberation": ldu_delib,
                            "conformal_calibration": res.get("conformal_calibration", {}),
                            "mcts_speculation": res.get("mcts_speculation"),
                            "final_answer": res.get("final_answer", f"Executed multi-step compound plan: {goal}"),
                            "trace": res.get("trace", [])
                        }
                        self._send_json(response_payload)
                        return

                # 2. Single Fast-Path Muscle Memory Reflex (only if NOT a compound multi-step goal)
                matched = omni_reflex.match_reflex(goal, threshold=0.75) if (not force_brain and not is_compound) else None
                if matched and matched.get("confidence", 0.0) >= 0.75:
                    skill = matched["skill"]
                    res = omni_reflex.execute_reflex_action(matched, goal)
                    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                    
                    response_payload = {
                        "success": True if res.get("success", True) or res.get("exit_code", 0) == 0 else False,
                        "execution_mode": "FAST_REFLEX_COMMIT",
                        "skill_id": skill.get("skill_id"),
                        "skill_name": skill.get("name"),
                        "confidence": matched.get("confidence", 0.98),
                        "latency_ms": elapsed_ms,
                        "tokens_consumed": 0,
                        "ldu_deliberation": ldu_delib,
                        "final_answer": f"Executed instantly via Muscle Memory: {skill.get('name')}",
                        "trace": [
                            {
                                "step": 1,
                                "thought": f"Instant reflex pattern match ({matched.get('confidence')*100:.1f}%) for skill: {skill.get('name')}",
                                "action": skill.get("tool"),
                                "args": skill.get("args", {}),
                                "observation": res
                            }
                        ]
                    }
                    self._send_json(response_payload)
                    return

                # 3. System 1 Bare-Metal C++ Shared-Memory Fast-Path
                # Sub-15 microsecond zero-copy evaluation across 80 enterprise macro leaves
                if not force_brain:
                    try:
                        cpp_eval = execute_native_axiom(goal)
                        if cpp_eval and cpp_eval.get("execution_path") == "FAST_PATH_COMMIT" and cpp_eval.get("confidence", 0.0) >= 0.70:
                            choice_id = cpp_eval.get("choice_id", 0)
                            choice_label = cpp_eval.get("choice_label", "")
                            # If choice_id belongs to the 80 macro leaves (or recognized actions)
                            if choice_id in ACTION_RESPONSES or (401 <= choice_id <= 910):
                                exec_res = bridge.execute_axiom_action(choice_id, goal)
                                elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                                response_payload = {
                                    "success": exec_res.get("success", True),
                                    "execution_mode": "BARE_METAL_C_CPP_COMMIT",
                                    "choice_id": choice_id,
                                    "choice_label": choice_label,
                                    "confidence": cpp_eval.get("confidence", 0.98),
                                    "latency_ms": elapsed_ms,
                                    "ipc_latency_us": cpp_eval.get("ipc_latency_us", cpp_eval.get("latency_total_us", 0.0)),
                                    "tokens_consumed": 0,
                                    "conformal_set": cpp_eval.get("conformal_set", []),
                                    "ldu_deliberation": ldu_delib,
                                    "final_answer": exec_res.get("message") or f"Executed via Bare-Metal Axiom Leaf #{choice_id} ({choice_label})",
                                    "trace": [
                                        {
                                            "step": 1,
                                            "thought": f"Sub-15µs Bare-Metal C++ Fast-Path ({cpp_eval.get('confidence', 0)*100:.1f}%) committed to leaf #{choice_id}: {choice_label}",
                                            "action": "axiom_native_leaf",
                                            "args": {"choice_id": choice_id, "label": choice_label},
                                            "observation": exec_res
                                        }
                                    ]
                                }
                                self._send_json(response_payload)
                                return
                    except Exception as cpp_err:
                        pass

                # Otherwise: Escalate to System 2 Closed-Loop ReAct Autonomous Brain
                brain_res = omni_brain.execute_autonomous_task(
                    user_goal=goal,
                    provider=provider,
                    model=model,
                    api_key=api_key,
                    base_url=base_url,
                    max_steps=5,
                    ldu_deliberation=ldu_delib
                )

                # RLCD Muscle Memory Synthesis: If brain succeeded, distill trace into reflex
                distilled = None
                if brain_res.get("success") and brain_res.get("steps"):
                    try:
                        distilled = omni_reflex.distill_skill_from_trace(goal, brain_res)
                        if distilled:
                            policy_optimizer.record_feedback_and_update(
                                distilled.get("skill_id", ""), True, elapsed_ms, exit_code=0
                            )
                    except Exception:
                        pass

                elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                response_payload = {
                    "success": brain_res.get("success", True),
                    "execution_mode": "AUTONOMOUS_BRAIN_REACT",
                    "confidence": 0.99,
                    "latency_ms": elapsed_ms,
                    "ldu_deliberation": ldu_delib,
                    "final_answer": brain_res.get("final_answer", ""),
                    "trace": brain_res.get("steps", []),
                    "events": brain_res.get("events", []),
                    "distilled_skill": distilled
                }
                self._send_json(response_payload)
                return
            except Exception as e:
                import traceback
                traceback.print_exc()
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # EXECUTE DISTILLED SKILL: POST /api/omni/execute_skill
        # ---------------------------------------------------------
        # ---------------------------------------------------------
        # EXECUTE DISTILLED SKILL: POST /api/omni/execute_skill
        # ---------------------------------------------------------
        elif req_path == '/api/omni/execute_skill':
            try:
                body = json.loads(raw_body) if raw_body else {}
                skill_id = body.get('skill_id', '')
                override_args = body.get('args', {})
                skills = omni_reflex.load_skills()
                target_skill = next((s for s in skills if s.get("skill_id") == skill_id), None)
                if not target_skill:
                    self._send_json({"success": False, "error": f"Skill '{skill_id}' not found"}, status=404)
                    return

                t0 = time.perf_counter()
                skill_to_run = dict(target_skill)
                if override_args:
                    skill_to_run["args"] = override_args
                res = omni_reflex.execute_reflex_action({"skill": skill_to_run}, query=target_skill.get("name", ""))
                lat_us = (time.perf_counter() - t0) * 1_000_000.0
                self._send_json({"success": True, "skill_id": skill_id, "result": res, "latency_us": round(lat_us, 1)})
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # DELETE DISTILLED SKILL: POST /api/omni/delete_skill
        # ---------------------------------------------------------
        elif req_path == '/api/omni/delete_skill':
            try:
                body = json.loads(raw_body) if raw_body else {}
                skill_id = body.get('skill_id', '')
                ok = omni_reflex.delete_skill(skill_id)
                self._send_json({"success": ok, "skill_id": skill_id})
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # DIRECT HARDWARE TOOL EXECUTION: POST /api/omni/tool
        # ---------------------------------------------------------
        elif req_path == '/api/omni/tool':
            try:
                body = json.loads(raw_body) if raw_body else {}
                tool_name = body.get('tool', '')
                tool_args = body.get('args', {})
                res = omni_actuator.execute_tool(tool_name, **tool_args)
                self._send_json({"success": True, "tool": tool_name, "result": res})
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # TOGGLE AUTONOMOUS SENTINEL: POST /api/omni/sentinels/toggle
        # ---------------------------------------------------------
        elif req_path == '/api/omni/sentinels/toggle':
            try:
                body = json.loads(raw_body) if raw_body else {}
                sentinel_id = body.get('sentinel_id') or body.get('name', '')
                enable = body.get('enable')
                res = sentinel_manager.toggle(sentinel_id, enable)
                self._send_json(res)
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # LAUNCH FLOATING ORB DESKTOP BUTTON: POST /api/omni/floating_widget/start
        # ---------------------------------------------------------
        elif req_path == '/api/omni/floating_widget/start':
            try:
                import subprocess
                launcher_path = os.path.join(PROJECT_ROOT, "launch_floating_button.py")
                subprocess.Popen([sys.executable, launcher_path], cwd=PROJECT_ROOT)
                self._send_json({"success": True, "message": "Axiom omnipresent floating button launched on physical desktop."})
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        elif req_path == '/api/omni/floating_widget/stop':
            try:
                import psutil
                killed = 0
                for p in psutil.process_iter(['name', 'cmdline']):
                    cmd = " ".join(p.info.get('cmdline') or [])
                    if "omni_floating_widget" in cmd or "launch_floating_button" in cmd:
                        p.kill()
                        killed += 1
                self._send_json({"success": True, "killed": killed})
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # REMOTE PC MOUSE CLICK: POST /api/omni/remote_click
        # ---------------------------------------------------------
        elif req_path == '/api/omni/remote_click':
            try:
                import ctypes
                from ctypes import wintypes
                body = json.loads(raw_body) if raw_body else {}
                btn = body.get("button", "left").lower()
                user32 = ctypes.windll.user32
                omni_actuator.attach_to_default_desktop()
                
                x = body.get("x")
                y = body.get("y")
                sw = user32.GetSystemMetrics(0)
                sh = user32.GetSystemMetrics(1)
                
                if x is not None and y is not None:
                    if 0.0 <= float(x) <= 1.0 and 0.0 <= float(y) <= 1.0:
                        target_x = int(float(x) * sw)
                        target_y = int(float(y) * sh)
                    else:
                        target_x = int(float(x))
                        target_y = int(float(y))
                    target_x = max(0, min(sw - 1, target_x))
                    target_y = max(0, min(sh - 1, target_y))
                    # Set position via SetCursorPos and hardware absolute move
                    user32.SetCursorPos(target_x, target_y)
                    norm_x = int(target_x * 65535 / max(1, sw - 1))
                    norm_y = int(target_y * 65535 / max(1, sh - 1))
                    user32.mouse_event(0x8001, norm_x, norm_y, 0, 0) # MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_MOVE
                    time.sleep(0.01)
                
                if btn == "left":
                    user32.mouse_event(0x0002, 0, 0, 0, 0)
                    user32.mouse_event(0x0004, 0, 0, 0, 0)
                elif btn == "left_down":
                    user32.mouse_event(0x0002, 0, 0, 0, 0)
                elif btn == "left_up":
                    user32.mouse_event(0x0004, 0, 0, 0, 0)
                elif btn == "right":
                    user32.mouse_event(0x0008, 0, 0, 0, 0)
                    user32.mouse_event(0x0010, 0, 0, 0, 0)
                elif btn == "middle":
                    user32.mouse_event(0x0020, 0, 0, 0, 0)
                    user32.mouse_event(0x0040, 0, 0, 0, 0)
                elif btn == "double":
                    user32.mouse_event(0x0002, 0, 0, 0, 0)
                    user32.mouse_event(0x0004, 0, 0, 0, 0)
                    time.sleep(0.05)
                    user32.mouse_event(0x0002, 0, 0, 0, 0)
                    user32.mouse_event(0x0004, 0, 0, 0, 0)

                self._send_json({"success": True, "action": f"clicked_{btn}"})
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # MULTIMODAL VISUAL-SPATIAL SOFT-ARGMAX CLICK: POST /api/omni/vision/click
        # ---------------------------------------------------------
        elif req_path == '/api/omni/vision/click':
            try:
                body = json.loads(raw_body) if raw_body else {}
                target = body.get("target") or body.get("element", "center")
                btn = body.get("button", "left")
                click = bool(body.get("click", True))
                res = omni_actuator.visual_spatial_click(target=target, click=click, button=btn)
                self._send_json(res)
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # SPECULATIVE MCTS PLANNING: POST /api/omni/mcts/plan
        # ---------------------------------------------------------
        elif req_path == '/api/omni/mcts/plan':
            try:
                body = json.loads(raw_body) if raw_body else {}
                actions = body.get("actions", [])
                goal = body.get("goal", "")
                if not actions and goal:
                    sub_queries = omni_reflex.split_compound_query(goal)
                    for sq in sub_queries:
                        m = omni_reflex.match_reflex(sq, threshold=0.60)
                        if m:
                            actions.append({
                                "tool": m["skill"].get("tool"),
                                "skill_name": m["skill"].get("name"),
                                "args": m["skill"].get("args", {}),
                                "confidence": m.get("confidence", 0.85)
                            })
                plan = mcts_planner.plan_speculative_trajectory(actions, {})
                self._send_json(plan)
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # VOICE SPEECH TRIGGER (STT / LISTEN): POST /api/omni/voice/listen
        # ---------------------------------------------------------
        elif req_path == '/api/omni/voice/listen' or self.path.startswith('/api/omni/voice/listen'):
            try:
                body = json.loads(raw_body) if raw_body else {}
                dur = float(body.get('duration', 4.0))
                auto_execute = bool(body.get('auto_execute', True))
                t0 = time.perf_counter()
                res = omni_actuator.voice_speech("listen", duration=dur)
                elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                res["latency_ms"] = elapsed_ms

                if res.get("success") and res.get("transcription") and auto_execute:
                    t_goal = res["transcription"].strip()
                    matched = omni_reflex.match_reflex(t_goal, threshold=0.75)
                    if matched and matched.get("confidence", 0.0) >= 0.75:
                        exec_res = omni_reflex.execute_reflex_action(matched, t_goal)
                        record_execution(t_goal, "VOICE_FAST_REFLEX", elapsed_ms, exec_res.get("success", True), exec_res.get("message", ""))
                        res["execution"] = {
                            "mode": "FAST_REFLEX_COMMIT",
                            "skill_name": matched["skill"].get("name"),
                            "result": exec_res
                        }
                    else:
                        brain_res = omni_brain.execute_autonomous_task(user_goal=t_goal, max_steps=5)
                        record_execution(t_goal, "VOICE_AUTONOMOUS_BRAIN", elapsed_ms, brain_res.get("success", True), brain_res.get("final_answer", ""))
                        res["execution"] = {
                            "mode": "AUTONOMOUS_BRAIN_REACT",
                            "result": brain_res
                        }
                self._send_json(res)
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # VOICE SPEECH SYNTHESIS (TTS / SPEAK): POST /api/omni/voice/speak
        # ---------------------------------------------------------
        elif req_path == '/api/omni/voice/speak' or self.path.startswith('/api/omni/voice/speak'):
            try:
                body = json.loads(raw_body) if raw_body else {}
                text = body.get('text', '').strip()
                if not text:
                    self._send_json({"success": False, "error": "No text provided to speak"}, status=400)
                    return
                res = omni_actuator.voice_speech("speak", text=text)
                self._send_json(res)
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # REMOTE PC KEYBOARD & TRACKPAD INPUT: POST /api/omni/remote_input
        # ---------------------------------------------------------
        elif req_path == '/api/omni/remote_input' or self.path.startswith('/api/omni/remote_input'):
            try:
                import ctypes
                from ctypes import wintypes
                user32 = ctypes.windll.user32
                body = json.loads(raw_body) if raw_body else {}
                action = body.get("action", "text").lower()

                if action == "move":
                    dx = int(body.get("dx", 0))
                    dy = int(body.get("dy", 0))
                    omni_actuator.attach_to_default_desktop()
                    # MOUSEEVENTF_MOVE (0x0001) injects physical relative deltas directly into Windows driver queue
                    user32.mouse_event(0x0001, dx, dy, 0, 0)
                    self._send_json({"success": True, "dx": dx, "dy": dy})
                    return

                elif action == "scroll":
                    delta = int(body.get("delta", 0))
                    omni_actuator.attach_to_default_desktop()
                    # MOUSEEVENTF_WHEEL (0x0800)
                    user32.mouse_event(0x0800, 0, 0, delta * 120, 0)
                    self._send_json({"success": True, "delta": delta})
                    return

                elif action == "text":
                    text = body.get("text", "")
                    if text:
                        import win32clipboard, win32con
                        win32clipboard.OpenClipboard()
                        win32clipboard.EmptyClipboard()
                        win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
                        win32clipboard.CloseClipboard()
                        omni_actuator.send_key_combo([0x11, 0x56]) # Ctrl+V
                    self._send_json({"success": True, "chars": len(text)})
                    return

                elif action == "key":
                    key = body.get("key", "").lower()
                    KEY_MAP = {
                        "enter": [0x0D],
                        "backspace": [0x08],
                        "escape": [0x1B],
                        "esc": [0x1B],
                        "tab": [0x09],
                        "space": [0x20],
                        "delete": [0x2E],
                        "del": [0x2E],
                        "up": [0x26],
                        "down": [0x28],
                        "left": [0x25],
                        "right": [0x27],
                        "pageup": [0x21],
                        "pagedown": [0x22],
                        "home": [0x24],
                        "end": [0x23],
                        "f5": [0x74],
                        "f11": [0x7A],
                        "win": [0x5B],
                        "win_d": [0x5B, 0x44],
                        "alt_tab": [0x12, 0x09],
                        "alt_f4": [0x12, 0x73],
                        "ctrl_c": [0x11, 0x43],
                        "ctrl_v": [0x11, 0x56],
                        "ctrl_z": [0x11, 0x5A],
                        "ctrl_a": [0x11, 0x41],
                        "ctrl_s": [0x11, 0x53],
                        "ctrl_w": [0x11, 0x57],
                        "ctrl_t": [0x11, 0x54]
                    }
                    if key in KEY_MAP:
                        omni_actuator.send_key_combo(KEY_MAP[key])
                        self._send_json({"success": True, "key": key})
                        return
                    else:
                        self._send_json({"success": False, "error": f"Unknown key: {key}"}, status=400)
                        return

                self._send_json({"success": False, "error": "Unknown input action"}, status=400)
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # REMOTE FILE SYSTEM OPEN: POST /api/omni/fs/open
        # ---------------------------------------------------------
        elif req_path == '/api/omni/fs/open':
            try:
                body = json.loads(raw_body) if raw_body else {}
                target_p = body.get("path", "").strip()
                if not target_p or not os.path.exists(target_p):
                    self._send_json({"success": False, "error": f"Path not found: {target_p}"}, status=404)
                    return
                omni_actuator.launch_on_user_desktop(target_p)
                self._send_json({"success": True, "message": f"Opened '{os.path.basename(target_p)}' on physical PC desktop."})
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # REMOTE PROCESS TERMINATION: POST /api/omni/processes/kill
        # ---------------------------------------------------------
        elif req_path == '/api/omni/processes/kill':
            try:
                import psutil
                body = json.loads(raw_body) if raw_body else {}
                pid = int(body.get("pid", 0))
                if pid <= 4:
                    self._send_json({"success": False, "error": "Cannot terminate system PID <= 4"}, status=400)
                    return
                p = psutil.Process(pid)
                name = p.name()
                p.kill()
                self._send_json({"success": True, "message": f"Terminated {name} (PID {pid})."})
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
                return

        # ---------------------------------------------------------
        # UNIVERSAL WEBHOOK EXECUTION: POST /webhook/trigger
        # ---------------------------------------------------------
        elif req_path.startswith('/webhook/trigger'):
            self._handle_webhook(raw_body)
            return

        # ---------------------------------------------------------
        # 1. OPENAI-COMPATIBLE API: POST /v1/chat/completions
        # ---------------------------------------------------------
        elif req_path == '/v1/chat/completions':
            try:
                body = json.loads(raw_body) if raw_body else {}
                messages = body.get('messages', [])
                requested_model = body.get('model', 'axiom-hybrid')
                auto_execute = body.get('auto_execute', True)
                
                # Extract the last user message
                last_user_msg = ""
                for msg in reversed(messages):
                    if msg.get('role') == 'user':
                        last_user_msg = msg.get('content', '')
                        break
                
                if not last_user_msg:
                    last_user_msg = "Hello"

                t0 = time.perf_counter()
                matched = omni_reflex.match_reflex(last_user_msg, threshold=0.75)
                if matched and matched.get("confidence", 0.0) >= 0.75:
                    skill = matched["skill"]
                    res = omni_reflex.execute_reflex_action(matched, last_user_msg)
                    lat_us = (time.perf_counter() - t0) * 1_000_000.0
                    content = f"[Axiom-OS Reflex Commit: {skill.get('name')} (Confidence: {matched.get('confidence')*100:.1f}%)]\nExecuted grounded action: {skill.get('tool')}\n- Result: {res.get('message', res.get('stdout', 'Success'))}"
                    openai_resp = {
                        "id": f"chatcmpl-axiom-{uuid.uuid4().hex[:8]}",
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": requested_model,
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": content
                            },
                            "finish_reason": "stop"
                        }],
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                        "axiom_meta": {
                            "execution_path": "FAST_PATH_COMMIT",
                            "choice_label": skill.get("name"),
                            "confidence": matched.get("confidence"),
                            "latency_us": lat_us,
                            "cost_tokens": 0,
                            "os_execution": res
                        }
                    }
                    self._send_json(openai_resp, headers={"X-Axiom-Execution-Path": "FAST_PATH_COMMIT", "X-Axiom-Latency-Us": str(round(lat_us, 1))})
                    return

                # ReAct Autonomous Agent Execution
                brain_res = omni_brain.execute_autonomous_task(user_goal=last_user_msg, max_steps=5)
                if brain_res.get("success") and brain_res.get("steps"):
                    try:
                        omni_reflex.distill_skill_from_trace(last_user_msg, brain_res)
                    except Exception:
                        pass

                lat_us = (time.perf_counter() - t0) * 1_000_000.0
                openai_resp = {
                    "id": f"chatcmpl-axiom-{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": requested_model,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": brain_res.get("final_answer", "Goal executed on desktop.")
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {"prompt_tokens": 120, "completion_tokens": 40, "total_tokens": 160},
                    "axiom_meta": {
                        "execution_path": "AUTONOMOUS_BRAIN_REACT",
                        "choice_label": "Omni_Autonomous_Execution",
                        "confidence": 0.99,
                        "latency_us": lat_us,
                        "steps": brain_res.get("steps", [])
                    }
                }
                self._send_json(openai_resp, headers={"X-Axiom-Execution-Path": "AUTONOMOUS_BRAIN_REACT"})
                return
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
                return

        # ---------------------------------------------------------
        # 2. TRADINGVIEW & WEBHOOK ENDPOINT: POST /webhook/tradingview
        # ---------------------------------------------------------
        elif req_path == '/webhook/tradingview':
            try:
                body = json.loads(raw_body) if raw_body else {}
                # TradingView alerts often send: {"ticker": "AAPL", "action": "BUY", "message": "..."}
                ticker = body.get('ticker', body.get('symbol', 'UNKNOWN'))
                action = body.get('action', body.get('signal', 'ALERT'))
                msg_text = body.get('message', body.get('text', raw_body))
                eval_text = f"{action} signal on {ticker}: {msg_text}"

                # Run through Axiom-1
                t0 = time.perf_counter()
                res = execute_native_axiom(eval_text)
                elapsed_us = (time.perf_counter() - t0) * 1_000_000.0

                webhook_resp = {
                    "status": "PROCESSED",
                    "ticker": ticker,
                    "action": action,
                    "axiom_execution_path": res.get("execution_path"),
                    "category": res.get("choice_label"),
                    "confidence": res.get("confidence"),
                    "entropy": res.get("shannon_entropy"),
                    "conformal_set": res.get("conformal_set"),
                    "is_safe_to_execute": res.get("execution_path") == "FAST_PATH_COMMIT" or res.get("confidence", 0) > 0.85,
                    "latency_us": res.get("latency_total_us", elapsed_us)
                }
                self._send_json(webhook_resp)
                return
            except Exception as e:
                self._send_json({"status": "ERROR", "error": str(e)}, status=400)
                return

        # ---------------------------------------------------------
        # 3. NATIVE DECIDE ENDPOINT: POST /api/decide or /v1/decide
        # ---------------------------------------------------------
        elif req_path in ('/api/decide', '/v1/decide'):
            try:
                body = json.loads(raw_body) if raw_body else {}
                input_text = body.get('input', '').strip()
                provider = body.get('provider', 'ollama')
                auto_execute = body.get('auto_execute', True)
                api_key = body.get('api_key') or os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY', '')
                cloud_model = body.get('cloud_model', 'anthropic/claude-3.5-sonnet')
                base_url = body.get('base_url', 'https://openrouter.ai/api/v1')
            except Exception:
                input_text = raw_body.strip()
                provider = 'ollama'
                auto_execute = True
                api_key = ''
                cloud_model = 'anthropic/claude-3.5-sonnet'
                base_url = 'https://openrouter.ai/api/v1'

            if not input_text:
                input_text = "Immediate refund dispute on unauthorized charge #9401"

            result_data = execute_native_axiom(input_text)

            # Direct intent alignment override for clear desktop actions
            msg_lower = input_text.lower()
            if "youtube" in msg_lower or "spotify" in msg_lower or "play music" in msg_lower or "pause music" in msg_lower or "next song" in msg_lower:
                result_data["execution_path"] = "FAST_PATH_COMMIT"
                result_data["choice_id"] = 805
                result_data["choice_label"] = "Media_Playback_Control"
                result_data["confidence"] = 0.998
            elif "minimize" in msg_lower or "show desktop" in msg_lower or "hide windows" in msg_lower:
                result_data["execution_path"] = "FAST_PATH_COMMIT"
                result_data["choice_id"] = 702
                result_data["choice_label"] = "Window_Minimize_All"
                result_data["confidence"] = 0.995
            elif "snap" in msg_lower and ("window" in msg_lower or "left" in msg_lower or "right" in msg_lower or "screen" in msg_lower):
                result_data["execution_path"] = "FAST_PATH_COMMIT"
                result_data["choice_id"] = 701
                result_data["choice_label"] = "Window_Snap_Tile"
                result_data["confidence"] = 0.995
            elif "download" in msg_lower and ("organize" in msg_lower or "clean" in msg_lower or "sort" in msg_lower):
                result_data["execution_path"] = "FAST_PATH_COMMIT"
                result_data["choice_id"] = 902
                result_data["choice_label"] = "Downloads_Auto_Organize"
                result_data["confidence"] = 0.995
            elif ("volume" in msg_lower and ("up" in msg_lower or "down" in msg_lower or "increase" in msg_lower or "lower" in msg_lower or "adjust" in msg_lower)) or "mute sound" in msg_lower or "mute volume" in msg_lower:
                result_data["execution_path"] = "FAST_PATH_COMMIT"
                result_data["choice_id"] = 803
                result_data["choice_label"] = "Volume_Master_Adjust"
                result_data["confidence"] = 0.995
            elif "boss key" in msg_lower or ("panic" in msg_lower and "button" in msg_lower):
                result_data["execution_path"] = "FAST_PATH_COMMIT"
                result_data["choice_id"] = 709
                result_data["choice_label"] = "Private_Windows_Hide"
                result_data["confidence"] = 0.995
            elif "free port" in msg_lower or "kill port" in msg_lower:
                result_data["execution_path"] = "FAST_PATH_COMMIT"
                result_data["choice_id"] = 402
                result_data["choice_label"] = "Port_Free_Liberate"
                result_data["confidence"] = 0.995

            if result_data.get("execution_path") in ("FAST_PATH_COMMIT", "SYSTEM2_FALLBACK"):
                choice_id = result_data.get("choice_id", 0)
                if choice_id in ACTION_RESPONSES or (choice_id >= 401 and choice_id <= 910):
                    if auto_execute:
                        exec_result = bridge.execute_axiom_action(choice_id, input_text)
                        result_data["os_execution"] = exec_result
                    else:
                        result_data["is_preview"] = True
                        result_data["os_execution"] = {
                            "success": True,
                            "is_preview": True,
                            "message": f"Preview Mode: Intent '{result_data.get('choice_label')}' recognized. Awaiting confirmation.",
                            "pending_action": {
                                "choice_id": choice_id,
                                "choice_label": result_data.get('choice_label'),
                                "prompt": input_text
                            }
                        }

            # If System 2 was triggered and user configured Cloud Provider (OpenRouter / Custom API)
            if result_data.get("execution_path") == "SYSTEM2_FALLBACK" and provider in ("openrouter", "custom") and api_key:
                try:
                    cloud_start = time.time()
                    clean_cand = result_data.get("choice_label", "").split("[")[0].strip()
                    cloud_answer = query_cloud_system2(
                        input_text=input_text,
                        candidate_leaf=clean_cand,
                        provider=provider,
                        api_key=api_key,
                        model=cloud_model,
                        base_url=base_url
                    )
                    cloud_ms = (time.time() - cloud_start) * 1000.0
                    result_data["choice_label"] = f"{clean_cand} [Verified by {cloud_model}]"
                    result_data["cloud_verification"] = cloud_answer
                    result_data["latency_l3_us"] = cloud_ms * 1000.0
                    result_data["provider"] = provider
                    result_data["cloud_model"] = cloud_model
                except Exception as cloud_err:
                    result_data["cloud_error"] = str(cloud_err)

            self._send_json(result_data)
            return

        # ---------------------------------------------------------
        # 4. OS HARDWARE ACTIONS: POST /api/os_action
        # ---------------------------------------------------------
        elif req_path == '/api/os_action':
            try:
                body = json.loads(raw_body) if raw_body else {}
                action = body.get('action', '')
                target = body.get('target', '')
                
                # Hardware & System
                if action == 'execute_axiom_action':
                    choice_id = int(body.get('choice_id', 0))
                    prompt = body.get('prompt', '')
                    res = bridge.execute_axiom_action(choice_id, prompt)
                elif action == 'launch_app':
                    res = bridge.launch_application(str(target))
                elif action == 'free_port':
                    port_val = int(target) if str(target).isdigit() else 3000
                    res = bridge.free_port(port_val)
                elif action == 'kill_process':
                    res = bridge.kill_process(str(target))
                elif action == 'clean_temp':
                    res = bridge.clean_temp_files()
                elif action in ('lock_workstation', 'lock'):
                    res = bridge.lock_workstation()
                elif action in ('sleep_pc', 'sleep'):
                    res = bridge.sleep_pc()
                
                # Sector 5: Window & Workspace
                elif action == 'minimize_all':
                    res = bridge.minimize_all_windows()
                elif action == 'snap_window':
                    res = bridge.snap_window(str(target) if target else 'left')
                elif action == 'focus_mode':
                    res = bridge.focus_mode_isolate()
                elif action == 'toggle_topmost':
                    res = bridge.toggle_topmost_window()
                elif action == 'boss_key':
                    res = bridge.boss_key()
                elif action == 'screenshot':
                    res = bridge.take_screenshot(snip_tool=True)
                elif action == 'switch_desktop':
                    res = bridge.switch_virtual_desktop(str(target) if target else 'next')
                
                # Sector 6: Multimedia & Audio
                elif action == 'media_control':
                    res = bridge.media_playback_control(str(target) if target else 'toggle')
                elif action == 'volume_adjust':
                    res = bridge.volume_master_adjust(str(target) if target else 'mute')
                elif action == 'mute_mic':
                    res = bridge.toggle_microphone_privacy()
                elif action == 'night_light':
                    res = bridge.toggle_night_light()
                
                # Sector 7: Automation & File System
                elif action == 'organize_downloads':
                    res = bridge.organize_downloads()
                elif action == 'audit_startup':
                    res = bridge.audit_startup_apps()
                elif action == 'backup_project':
                    res = bridge.backup_project()
                elif action == 'find_duplicates':
                    res = bridge.find_duplicate_files()
                else:
                    res = {"success": False, "error": f"Unknown OS action: {action}"}
                
                self._send_json(res)
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
                return

        # ---------------------------------------------------------
        # 5. PHONE TELEPORT: POST /api/teleport_url
        # ---------------------------------------------------------
        elif req_path == '/api/teleport_url':
            try:
                body = json.loads(raw_body) if raw_body else {}
                url = body.get('url', '').strip()
                if not url:
                    self._send_json({"success": False, "error": "No URL provided"}, status=400)
                    return
                res = bridge.teleport_url(url)
                self._send_json(res)
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
                return

        # ---------------------------------------------------------
        # 6. RESEARCH IDEA LOGGER: POST /api/idea_log
        # ---------------------------------------------------------
        elif req_path == '/api/idea_log':
            try:
                body = json.loads(raw_body) if raw_body else {}
                text = body.get('text', body.get('idea', '')).strip()
                if not text:
                    self._send_json({"success": False, "error": "No idea content provided"}, status=400)
                    return
                res = bridge.append_idea(text)
                self._send_json(res)
                return
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=400)
                return

        else:
            self.send_error(404, "Endpoint not found")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        req_path = parsed.path

        # ---------------------------------------------------------
        # OMNIPRESENT PC SENSOR SNAPSHOT: GET /api/omni/sensors
        # ---------------------------------------------------------
        if req_path == '/api/omni/sensors':
            try:
                state = omni_sensor.get_comprehensive_pc_state()
                self._send_json(state)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        # ---------------------------------------------------------
        # LEARNED REFLEX SKILLS CATALOG: GET /api/omni/skills
        # ---------------------------------------------------------
        elif req_path == '/api/omni/skills':
            try:
                skills = omni_reflex.load_skills()
                self._send_json({"skills": skills, "count": len(skills)})
            except Exception as e:
                self._send_json({"skills": [], "error": str(e)}, status=500)
            return

        # ---------------------------------------------------------
        # GROUNDED PHYSICAL APPLICATION CATALOG: GET /api/omni/catalog
        # ---------------------------------------------------------
        elif req_path == '/api/omni/catalog':
            try:
                apps = app_catalog.list_installed_apps()
                self._send_json({"apps": apps, "count": len(apps)})
            except Exception as e:
                self._send_json({"apps": [], "error": str(e)}, status=500)
            return

        # ---------------------------------------------------------
        # SENTINEL TELEMETRY & STATUS: GET /api/omni/sentinels
        # ---------------------------------------------------------
        elif req_path == '/api/omni/sentinels':
            try:
                status = sentinel_manager.get_status()
                self._send_json(status)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        # ---------------------------------------------------------
        # SERVE CAPTURED WEBCAM IMAGES: GET /captures/...
        # ---------------------------------------------------------
        elif req_path.startswith('/captures/'):
            filename = os.path.basename(req_path)
            captures_dir = os.path.join(PROJECT_ROOT, "captures")
            file_path = os.path.join(captures_dir, filename)
            if os.path.exists(file_path):
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "Capture not found")
                return

        # ---------------------------------------------------------
        # 7. MOBILE TOUCH COCKPIT: GET /mobile
        # ---------------------------------------------------------
        elif req_path in ('/mobile', '/mobile.html'):
            mobile_file = os.path.join(UI_DIR, "mobile.html")
            if os.path.exists(mobile_file):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(mobile_file, 'rb') as f:
                    self.wfile.write(f.read())
                return

        # ---------------------------------------------------------
        # 8. HARDWARE & OS TELEMETRY: GET /api/system_telemetry
        # ---------------------------------------------------------
        elif req_path == '/api/system_telemetry':
            telemetry = bridge.get_system_telemetry()
            self._send_json(telemetry)
            return

        # ---------------------------------------------------------
        # 9. RESEARCH IDEAS FEED: GET /api/idea_log
        # ---------------------------------------------------------
        elif req_path == '/api/idea_log':
            ideas = bridge.get_recent_ideas(limit=25)
            self._send_json({"ideas": ideas})
            return

        # ---------------------------------------------------------
        # 10. OPENAI MODELS LIST: GET /v1/models
        # ---------------------------------------------------------
        elif req_path == '/v1/models':
            models = {
                "object": "list",
                "data": [
                    {
                        "id": "axiom-hybrid",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "axiom",
                        "permission": [],
                        "root": "axiom-hybrid",
                        "description": "Axiom-OS Hybrid Reflex & Reason Router (Microsecond Fast-Path + Ollama/Cloud Fallback)"
                    },
                    {
                        "id": "axiom-fast-path",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "axiom",
                        "permission": [],
                        "root": "axiom-fast-path",
                        "description": "Axiom Bare-Metal 960-Param Register Tree (<1ms execution)"
                    },
                    {
                        "id": "qwen2.5-coder:1.5b",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "ollama",
                        "permission": [],
                        "root": "qwen2.5-coder:1.5b",
                        "description": "Local Ollama System 2 Reasoning Engine"
                    }
                ]
            }
            self._send_json(models)
            return

        elif req_path == '/api/ollama_status':
            status = {
                "connected": False,
                "model": "None",
                "endpoint": OLLAMA_BASE
            }
            try:
                req = urllib.request.Request(OLLAMA_TAGS_URL, headers={'User-Agent': 'Axiom-1'})
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        models = data.get('models', [])
                        if models:
                            status["connected"] = True
                            status["model"] = models[0].get("name", "qwen2.5-coder:1.5b")
            except Exception as e:
                status["error"] = str(e)

            self._send_json(status)
            return

        elif req_path == '/api/omni/floating_widget/status':
            try:
                import psutil
                is_running = any(("launch_floating_button" in cmd or "omni_floating_widget" in cmd) for cmd in (" ".join(p.info.get('cmdline') or []) for p in psutil.process_iter(['name', 'cmdline'])))
                self._send_json({"running": is_running})
                return
            except Exception as e:
                self._send_json({"running": False, "error": str(e)})
                return

        elif req_path == '/api/omni/screen_capture':
            try:
                import io
                img, abs_path, w, h = omni_actuator.capture_screen_pixels()
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=65)
                jpeg_bytes = buf.getvalue()
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', str(len(jpeg_bytes)))
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('X-Screen-Resolution', f"{w}x{h}")
                self.end_headers()
                self.wfile.write(jpeg_bytes)
                return
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
                return

        elif req_path.startswith('/api/omni/fs/browse'):
            try:
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                browse_path = params.get('path', [PROJECT_ROOT])[0]
                target_path = os.path.abspath(browse_path)
                if not os.path.exists(target_path) or not os.path.isdir(target_path):
                    target_path = PROJECT_ROOT

                items = []
                parent = os.path.dirname(target_path) if os.path.dirname(target_path) != target_path else ""
                for entry in os.scandir(target_path):
                    try:
                        st = entry.stat()
                        items.append({
                            "name": entry.name,
                            "path": entry.path,
                            "is_dir": entry.is_dir(),
                            "size_kb": round(st.st_size / 1024, 1) if not entry.is_dir() else 0,
                            "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))
                        })
                    except Exception:
                        pass
                items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
                self._send_json({
                    "current_path": target_path,
                    "parent_path": parent,
                    "count": len(items),
                    "items": items
                })
                return
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
                return

        elif req_path.startswith('/api/omni/fs/read'):
            try:
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                read_target = params.get('path', [''])[0]
                if not read_target or not os.path.exists(read_target) or os.path.isdir(read_target):
                    self._send_json({"error": "File not found"}, status=404)
                    return
                with open(read_target, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read(50000)
                self._send_json({
                    "success": True,
                    "path": read_target,
                    "filename": os.path.basename(read_target),
                    "content": content,
                    "lines": len(content.splitlines())
                })
                return
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
                return

        elif req_path.startswith('/api/omni/processes'):
            try:
                import psutil
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                limit = int(params.get('limit', [40])[0])
                procs = []
                for p in psutil.process_iter(['pid', 'name', 'status']):
                    try:
                        mem_mb = round(p.memory_info().rss / (1024 * 1024), 1)
                        procs.append({
                            "pid": p.info['pid'],
                            "name": p.info['name'],
                            "ram_mb": mem_mb,
                            "status": p.info.get('status', 'running')
                        })
                    except Exception:
                        pass
                procs.sort(key=lambda x: x['ram_mb'], reverse=True)
                self._send_json({"count": len(procs), "processes": procs[:limit]})
                return
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
                return

        elif req_path == '/api/omni/history':
            self._send_json({"history": EXECUTION_HISTORY})
            return

        elif req_path.startswith('/api/omni/ldu/deliberate'):
            try:
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                text = params.get('text', [''])[0]
                res = ldu_engine.deliberate(text or "Axiom Operational Directive")
                self._send_json(res)
                return
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
                return

        elif req_path == '/api/omni/swarm/status':
            try:
                res = mesh_node.get_swarm_status()
                self._send_json(res)
                return
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
                return

        elif req_path == '/api/omni/policy/stats':
            try:
                self._send_json({
                    "baseline_reward": round(policy_optimizer.running_baseline_reward, 3),
                    "stats": policy_optimizer.stats
                })
                return
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
                return

        elif req_path.startswith('/webhook/trigger'):
            self._handle_webhook("")
            return

        elif req_path == '/api/health':
            lan_ip = bridge.get_lan_ip()
            swarm_st = mesh_node.get_swarm_status()
            status = {
                "status": "online",
                "backend": "DirectML Universal Windows Accelerator (C++)",
                "cli_binary_exists": os.path.exists(CLI_EXE),
                "lan_ip": lan_ip,
                "desktop_url": f"http://localhost:{PORT}/",
                "mobile_url": f"http://{lan_ip}:{PORT}/mobile",
                "swarm": swarm_st,
                "openai_compatible_endpoint": f"http://localhost:{PORT}/v1/chat/completions",
                "tradingview_webhook_endpoint": f"http://localhost:{PORT}/webhook/tradingview",
                "version": "3.5.0-axiom-peak"
            }
            self._send_json(status)
            return

        elif req_path in ('/v1', '/v1/chat/completions', '/api', '/webhook', '/webhook/tradingview'):
            doc_info = {
                "service": "Axiom-OS Omnipresent Workstation & Mobile Integration Gateway",
                "status": "online",
                "endpoints": {
                    "POST /v1/chat/completions": "OpenAI drop-in chat completion (fast reflex OS execution or LLM fallback)",
                    "POST /webhook/tradingview": "TradingView PineScript alert webhook processor",
                    "POST /api/decide": "Direct bare-metal C++ decision routing JSON with OS execution",
                    "POST /api/os_action": "Direct Win32 OS action (free_port, clean_temp, lock, etc.)",
                    "POST /api/teleport_url": "Teleport URL from phone to PC browser",
                    "POST /api/idea_log": "Append research breakthrough to RESEARCH_LOG.md",
                    "GET /mobile": "Mobile Touch Cockpit for smartphones on LAN",
                    "GET /api/system_telemetry": "Live RAM, CPU, Battery, Port telemetry",
                    "GET /api/idea_log": "Recent ideas list from RESEARCH_LOG.md",
                    "GET /v1/models": "OpenAI models catalog",
                    "GET /api/health": "Health and runtime status",
                    "GET /": "Visual Decision Studio & AI Chat Playground"
                },
                "instructions": "Open http://localhost:3000/ on your PC or http://<LAN-IP>:3000/mobile on your phone."
            }
            self._send_json(doc_info)
            return

        else:
            # SPA Fallback: If requesting a route like /chat, /studio, or any UI path, serve index.html
            local_file = os.path.join(UI_DIR, req_path.lstrip('/'))
            if not os.path.exists(local_file) or os.path.isdir(local_file):
                self.path = '/index.html'
            else:
                self.path = req_path
            super().do_GET()

    def _send_json(self, data: dict, status: int = 200, headers: dict = None):
        try:
            body = json.dumps(data).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
            if headers:
                for k, v in headers.items():
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception:
            pass

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def main():
    lan_ip = bridge.get_lan_ip()
    print("==================================================================")
    print("   AXIOM-OS: OMNIPRESENT WORKSTATION & MOBILE COPILOT             ")
    print(f"   Native Engine   : {CLI_EXE}")
    print(f"   Ollama Engine   : {OLLAMA_BASE} (qwen2.5-coder:1.5b)")
    print(f"   Desktop Studio  : http://localhost:{PORT}/")
    print(f"   Mobile Cockpit  : http://{lan_ip}:{PORT}/mobile")
    print(f"   OpenAI Gateway  : http://localhost:{PORT}/v1/chat/completions")
    print(f"   TradingView Hook: http://localhost:{PORT}/webhook/tradingview")
    print(f"   OS Telemetry    : http://localhost:{PORT}/api/system_telemetry")
    print(f"   Sentinel Daemon : ACTIVE (Hardware Governor, Presence, Port Guards)")
    print("==================================================================")
    sentinel_manager.start()
    mesh_node.start()
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    with http.server.ThreadingHTTPServer(("0.0.0.0", PORT), AxiomUniversalHandler) as httpd:
        httpd.daemon_threads = True
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == '__main__':
    main()
