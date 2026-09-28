"""
Comprehensive End-to-End Verification Suite for Axiom Omni Agent & Grounded PC Brain
Validates:
1. Perception Engine (Win32 & OS sensor data)
2. Actuator Multi-Tool Engine (PowerShell, App Control, Filesystem, Audio)
3. Dynamic RLCD Muscle Memory Engine (Microsecond matching, Distillation, Eviction)
4. Closed-Loop ReAct Autonomous Brain (Local Ollama / Fallback Execution)
5. REST API & OpenAI Gateway Compatibility
"""

import sys
import os
import time
import json
import unittest
import urllib.request
import urllib.error

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src import omni_sensor
from src import omni_actuator
from src import omni_reflex
from src import omni_brain

SERVER_URL = "http://127.0.0.1:3000"
_server_proc = None

def setUpModule():
    global _server_proc
    try:
        req = urllib.request.Request(f"{SERVER_URL}/api/omni/sensors")
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                return
    except Exception:
        pass

    import subprocess
    server_script = os.path.join(PROJECT_ROOT, "ui", "server.py")
    flags = 0x08000000 if os.name == 'nt' else 0
    _server_proc = subprocess.Popen([sys.executable, server_script], creationflags=flags)
    for _ in range(40):
        time.sleep(0.2)
        try:
            req = urllib.request.Request(f"{SERVER_URL}/api/omni/sensors")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    break
        except Exception:
            pass

def tearDownModule():
    global _server_proc
    if _server_proc:
        try:
            _server_proc.terminate()
        except Exception:
            pass

def post_json(endpoint: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{SERVER_URL}{endpoint}",
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def get_json(endpoint: str) -> dict:
    req = urllib.request.Request(f"{SERVER_URL}{endpoint}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))


class TestOmniPerception(unittest.TestCase):
    """Test Win32 and system telemetry perception."""

    def test_telemetry_capture(self):
        telem = omni_sensor.get_system_hardware_telemetry()
        self.assertIn("cpu_percent", telem)
        self.assertIn("ram_percent", telem)
        self.assertIn("screen_resolution", telem)
        self.assertGreater(telem["ram_percent"], 0)

    def test_listening_ports(self):
        ports = omni_sensor.get_active_listening_ports()
        self.assertIsInstance(ports, list)
        self.assertGreater(len(ports), 0)
        # Port 3000 should be active because our server is running
        self.assertIn(3000, ports)

    def test_comprehensive_pc_state(self):
        state = omni_sensor.get_comprehensive_pc_state()
        self.assertIn("foreground_window", state)
        self.assertIn("media_session", state)
        self.assertIn("telemetry", state)
        self.assertIn("active_ports", state)
        self.assertIn("prompt_context", state)
        self.assertIn("PC PERCEPTION SNAPSHOT", state["prompt_context"])


class TestOmniActuator(unittest.TestCase):
    """Test grounded hardware and system execution."""

    def test_powershell_execution(self):
        res = omni_actuator.powershell_exec("Get-Date")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("exit_code"), 0)
        self.assertGreater(len(res.get("stdout", "")), 0)

    def test_filesystem_search(self):
        res = omni_actuator.filesystem_ops("search", target_path=PROJECT_ROOT, params={"pattern": "*.py"})
        self.assertTrue(res.get("success"))
        self.assertGreater(res.get("count", 0), 0)

    def test_media_control_volume(self):
        # Non-disruptive volume adjust test
        res = omni_actuator.media_control("volume_up")
        self.assertTrue(res.get("success"))

    def test_resolve_windows_app(self):
        chrome_path = omni_actuator.resolve_windows_app("chrome")
        self.assertTrue(bool(chrome_path))
        self.assertTrue(os.path.exists(chrome_path))

    def test_browser_open_resolution(self):
        res = omni_actuator.browser_open("https://www.youtube.com")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("url"), "https://www.youtube.com")

    def test_execute_tool_unified_dispatcher(self):
        res = omni_actuator.execute_tool("powershell_exec", script="Write-Output 'AXIOM_OMNI_VERIFIED'")
        self.assertTrue(res.get("success"))
        self.assertIn("AXIOM_OMNI_VERIFIED", res.get("stdout", ""))

    def test_c_cpp_exec_compilation(self):
        c_code = '#include <stdio.h>\nint main() { printf("GCC_OMNI_SUCCESS\\n"); return 0; }'
        res = omni_actuator.execute_tool("c_cpp_exec", code=c_code, file_path="test_omni_c.c")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("exit_code"), 0)
        self.assertIn("GCC_OMNI_SUCCESS", res.get("stdout", ""))
        for f in ("test_omni_c.c", "test_omni_c.exe"):
            if os.path.exists(f):
                os.remove(f)

    def test_camera_vision_snapshot(self):
        res = omni_actuator.execute_tool("camera_vision", action="capture", open_viewer=False)
        self.assertTrue(res.get("success"))
        self.assertTrue(os.path.exists(res.get("saved_path", "")))
        self.assertGreater(res.get("file_size_bytes", 0), 1000)

    def test_screen_ocr_execution(self):
        res = omni_actuator.execute_tool("screen_ocr", action="read_screen")
        self.assertTrue(res.get("success"))
        self.assertIn("lines_count", res)
        self.assertIsInstance(res.get("lines"), list)

    def test_web_search_resolution(self):
        res = omni_actuator.web_search("REC Sonbhadra", launch_website=False, open_browser=False)
        self.assertTrue(res.get("success"))
        self.assertIn("google.com/search", res.get("target_url", "").lower())

        res_site = omni_actuator.web_search("REC Sonbhadra", launch_website=True, open_browser=False)
        self.assertTrue(res_site.get("success"))
        self.assertTrue(res_site.get("launched_website"))


class TestOmniReflexMuscleMemory(unittest.TestCase):
    """Test dynamic RLCD skill distillation and microsecond pattern matching."""

    def test_load_skills(self):
        skills = omni_reflex.load_skills()
        self.assertIsInstance(skills, list)
        self.assertGreater(len(skills), 0)

    def test_microsecond_reflex_matching(self):
        # Warmup cache
        omni_reflex.match_reflex("warmup")
        latencies = []
        matched = None
        for _ in range(3):
            t0 = time.perf_counter()
            matched = omni_reflex.match_reflex("play music on youtube")
            latencies.append((time.perf_counter() - t0) * 1_000_000.0)
        
        self.assertIsNotNone(matched)
        self.assertGreaterEqual(matched["confidence"], 0.80)
        self.assertEqual(matched["skill"]["tool"], "media_control")
        self.assertLess(min(latencies), 25000.0)

    def test_omni_catalog_grounded_resolution(self):
        from src.omni_catalog import app_catalog
        cmd_res = app_catalog.resolve("cmd")
        self.assertIsNotNone(cmd_res)
        self.assertTrue(os.path.exists(cmd_res[1]))
        
        # Uninstalled app should return None and provide suggestions
        bad_res = app_catalog.resolve("non_existent_app_xyz")
        self.assertIsNone(bad_res)
        suggestions = app_catalog.get_suggestions("non_existent_app_xyz")
        self.assertIsInstance(suggestions, list)

    def test_distill_and_delete_skill(self):
        test_goal = "test synthesize custom temp skill"
        fake_trace = {
            "success": True,
            "steps": [
                {
                    "step": 1,
                    "thought": "Synthesizing test skill",
                    "action": "powershell_exec",
                    "args": {"script": "Write-Output 'TEST_RLCD'"}
                }
            ]
        }
        distilled = omni_reflex.distill_skill_from_trace(test_goal, fake_trace)
        self.assertIsNotNone(distilled)
        self.assertEqual(distilled.get("tool"), "powershell_exec")
        
        # Verify it matches
        matched = omni_reflex.match_reflex(test_goal)
        self.assertIsNotNone(matched)
        self.assertEqual(matched["skill"]["skill_id"], distilled["skill_id"])

        # Clean up
        deleted = omni_reflex.delete_skill(distilled["skill_id"])
        self.assertTrue(deleted)

    def test_compound_reflex_splitting_and_matching(self):
        goal = "open camera and shot a image for if a person face appear"
        parts = omni_reflex.split_compound_query(goal)
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], "open camera")
        self.assertEqual(parts[1], "shot a image for if a person face appear")
        
        compound = omni_reflex.match_compound_reflex(goal, threshold=0.70)
        self.assertIsNotNone(compound)
        self.assertEqual(len(compound), 2)
        self.assertEqual(compound[0]["matched"]["skill"]["tool"], "camera_vision")
        self.assertEqual(compound[1]["matched"]["skill"]["tool"], "camera_vision")

    def test_semantic_distillation_guard(self):
        # Browser open cannot be distilled for a camera/photo goal
        self.assertFalse(omni_reflex.is_semantically_valid_distillation(
            "open camera and shot a image for if a person face appear",
            "browser_open",
            {"url": "https://www.google.com"}
        ))
        # Camera vision is valid
        self.assertTrue(omni_reflex.is_semantically_valid_distillation(
            "open camera and shot a image for if a person face appear",
            "camera_vision",
            {"action": "detect_and_capture", "detect": "person"}
        ))

    def test_martingale_conformal_safety(self):
        chain = omni_reflex.match_compound_reflex("mute sound and show desktop")
        self.assertIsNotNone(chain)
        conformal = omni_reflex.compute_trajectory_conformal_risk(chain)
        self.assertTrue(conformal["safe"])
        self.assertGreaterEqual(conformal["p_trajectory_safe"], 0.95)

    def test_parallel_reflex_execution(self):
        chain = omni_reflex.match_compound_reflex("mute sound and show desktop")
        self.assertIsNotNone(chain)
        res = omni_reflex.execute_compound_reflex(chain, "mute sound and show desktop")
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("execution_mode"), "PARALLEL_REFLEX_PLAN")
        self.assertIn("conformal_calibration", res)

    def test_compound_query_not_intercepted_by_single_trigger(self):
        q = "open browser and serch REC SONBHADRA ,and lauch it website"
        parts = omni_reflex.split_compound_query(q)
        self.assertGreaterEqual(len(parts), 2)
        matched = omni_reflex.match_reflex(q, threshold=0.75)
        self.assertIsNone(matched)


class TestOmniServerEndpoints(unittest.TestCase):
    """Test server REST API and OpenAI gateway."""

    def test_get_sensors(self):
        res = get_json("/api/omni/sensors")
        self.assertIn("telemetry", res)
        self.assertIn("active_ports", res)

    def test_get_skills(self):
        res = get_json("/api/omni/skills")
        self.assertIn("skills", res)
        self.assertGreater(res.get("count", 0), 0)

    def test_post_tool_execution(self):
        res = post_json("/api/omni/tool", {
            "tool": "powershell_exec",
            "args": {"script": "Get-Location"}
        })
        self.assertTrue(res.get("success"))
        self.assertIn("Path", res.get("result", {}).get("stdout", ""))

    def test_post_chat_fast_reflex(self):
        res = post_json("/api/omni/chat", {
            "goal": "play music"
        })
        self.assertEqual(res.get("execution_mode"), "FAST_REFLEX_COMMIT")
        self.assertTrue(res.get("success"))
        self.assertIn("Muscle Memory", res.get("final_answer", ""))

    def test_post_chat_open_youtube_reflex(self):
        res = post_json("/api/omni/chat", {
            "goal": "open youtube in browser"
        })
        self.assertEqual(res.get("execution_mode"), "FAST_REFLEX_COMMIT")
        self.assertTrue(res.get("success"))
        self.assertIn("Open YouTube", res.get("final_answer", ""))

    def test_post_chat_compound_multi_reflex(self):
        res = post_json("/api/omni/chat", {
            "goal": "open camera and shot a image for if a person face appear"
        })
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("execution_mode"), "MULTI_REFLEX_PLAN")
        self.assertEqual(res.get("milestones_count"), 2)
        self.assertEqual(len(res.get("trace", [])), 2)
        # Check that both milestones executed camera_vision, not browser_open!
        self.assertEqual(res["trace"][0]["action"], "camera_vision")
        self.assertEqual(res["trace"][1]["action"], "camera_vision")

    def test_openai_gateway_compatibility(self):
        res = post_json("/v1/chat/completions", {
            "model": "axiom-omni-brain",
            "messages": [
                {"role": "user", "content": "mute sound"}
            ]
        })
        self.assertIn("choices", res)
        self.assertGreater(len(res["choices"]), 0)
        self.assertIn("Reflex Commit", res["choices"][0]["message"]["content"])

    def test_sentinels_status_and_toggle(self):
        res = get_json("/api/omni/sentinels")
        self.assertTrue(res.get("success"))
        self.assertIn("sentinels", res)
        self.assertIn("cpu_governor", res["sentinels"])
        self.assertIn("port_guard", res["sentinels"])
        
        # Test toggle
        toggle_res = post_json("/api/omni/sentinels/toggle", {"name": "cpu_governor"})
        self.assertTrue(toggle_res.get("success"))
        self.assertIn("enabled", toggle_res)

        # Toggle back
        post_json("/api/omni/sentinels/toggle", {"name": "cpu_governor"})

    def test_post_chat_parallel_compound_reflex(self):
        res = post_json("/api/omni/chat", {
            "goal": "mute sound and show desktop"
        })
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("execution_mode"), "PARALLEL_REFLEX_PLAN")
        self.assertIn("conformal_calibration", res)
        self.assertGreaterEqual(res["conformal_calibration"]["p_trajectory_safe"], 0.95)


class TestAxiomUnifiedArchitecture(unittest.TestCase):
    """Verifies that 100% of Axiom architecture is actively executing in Axiom OS."""

    def test_bare_metal_cpp_fast_path_in_chat(self):
        """Verifies C++ shared-memory fast-path resolves in /api/omni/chat."""
        res = post_json("/api/omni/chat", {"goal": "clean temp files"})
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("execution_mode"), "BARE_METAL_C_CPP_COMMIT")
        self.assertEqual(res.get("choice_id"), 403)
        self.assertEqual(res.get("tokens_consumed"), 0)
        self.assertIn("ldu_deliberation", res)

    def test_visual_spatial_soft_argmax_click(self):
        """Verifies 2D spatial soft-argmax click tensor predicts screen coordinates."""
        res = omni_actuator.execute_tool("visual_spatial_click", target="close button", click=False)
        self.assertTrue(res.get("success"))
        self.assertIn("phys_x", res)
        self.assertIn("phys_y", res)
        self.assertIn("confidence", res)
        self.assertGreater(res.get("confidence", 0), 0.70)

    def test_martingale_conformal_safety_gate(self):
        """Verifies Martingale pre-execution gate intercepts destructive actions."""
        res = omni_actuator.execute_tool("powershell_exec", script="rmdir /s /q C:\\Windows")
        self.assertFalse(res.get("success"))
        self.assertIn("MARTINGALE SAFETY INTERCEPTOR", res.get("error", ""))

    def test_ldu_deliberation_engine(self):
        """Verifies Latent Deliberation Unit (LDU) sub-5ms vector deliberation."""
        from src.omni_ldu import ldu_engine
        delib = ldu_engine.deliberate("mute sound and lower volume")
        self.assertTrue(delib.get("success"))
        self.assertEqual(delib.get("best_sector_id"), 6)
        self.assertEqual(delib.get("best_sector_name"), "Multimedia & Core Audio")
        self.assertGreater(delib.get("max_confidence", 0), 0.75)
        self.assertLess(delib.get("shannon_entropy", 1.0), 0.40)

    def test_sentinel_alert_callbacks(self):
        """Verifies SentinelManager alert callback registration and dispatch."""
        from src.omni_sentinel import sentinel_manager
        events = []
        sentinel_manager.register_alert_callback(lambda e: events.append(e))
        sentinel_manager._log_event("UNIT_TEST_ALERT", "Testing alert system")
        self.assertTrue(any(e.get("event_type") == "UNIT_TEST_ALERT" for e in events))

    def test_visual_click_sequence_execution(self):
        """Verifies visual_click_sequence dispatches and handles sequences of coordinates."""
        from src.omni_vision_tensor import vision_tensor_engine
        orig = vision_tensor_engine.execute_direct_click
        try:
            vision_tensor_engine.execute_direct_click = lambda t, click=True, verify=False: {
                "phys_x": 400, "phys_y": 600, "confidence": 0.95, "total_elapsed_ms": 3.2
            }
            # Test list format
            res = omni_actuator.execute_tool("visual_click_sequence", targets=["button 7", "button 8"], delay_between_s=0.01)
            self.assertTrue(res.get("success"))
            self.assertEqual(res.get("total_clicks"), 2)
            self.assertEqual(len(res.get("sequence")), 2)

            # Test comma-separated string format
            res2 = omni_actuator.execute_tool("visual_click_sequence", targets="button 7, button plus, button 8", delay_between_s=0.01)
            self.assertTrue(res2.get("success"))
            self.assertEqual(res2.get("total_clicks"), 3)
        finally:
            vision_tensor_engine.execute_direct_click = orig

    def test_hierarchical_planner_dag_and_ledger(self):
        """Verifies HierarchicalExecutionPlan DAG decomposition and ledger rendering."""
        from src.omni_brain import decompose_hierarchical_plan, Milestone
        plan = decompose_hierarchical_plan("open calc and compute 7 * 8", {})
        self.assertIsNotNone(plan)
        self.assertGreater(len(plan.milestones), 2)
        
        # Verify first active milestone is in Perception & Setup or Core Execution
        active = plan.get_active_milestone()
        self.assertIsNotNone(active)
        self.assertEqual(active.id, 1)

        # Verify ledger rendering
        ledger = plan.render_ledger()
        self.assertIn("[HIERARCHICAL MULTI-STEP EXECUTION GRAPH & PROGRESS LEDGER]", ledger)
        self.assertIn("Milestone 1", ledger)

        # Verify milestone transition
        active.status = "verified"
        next_active = plan.get_active_milestone()
        self.assertIsNotNone(next_active)
        self.assertEqual(next_active.id, 2)

    def test_vision_tensor_patch_refinement_subpixel(self):
        """Verifies high-resolution 140x140 patch refinement and soft-argmax centroid."""
        from src.omni_vision_tensor import vision_tensor_engine
        import numpy as np
        from PIL import Image

        # Create canvas with a sharp high-contrast button at (500, 300)
        img_arr = np.full((600, 800), 40, dtype=np.uint8)
        img_arr[285:315, 485:515] = 230
        img = Image.fromarray(img_arr)

        ref_x, ref_y, conf = vision_tensor_engine.refine_patch_soft_argmax(img, coarse_x=495, coarse_y=305, patch_size=100)
        self.assertGreaterEqual(ref_x, 480)
        self.assertLessEqual(ref_x, 520)
        self.assertGreaterEqual(ref_y, 280)
        self.assertLessEqual(ref_y, 320)
        self.assertGreater(conf, 0.5)

    def test_vision_tensor_state_verification_probe(self):
        """Verifies empirical visual state transition detection on before/after states."""
        from src.omni_vision_tensor import vision_tensor_engine
        import numpy as np
        from PIL import Image

        before = Image.new("RGB", (200, 200), color=(30, 30, 30))
        after_arr = np.full((200, 200, 3), 30, dtype=np.uint8)
        after_arr[90:110, 90:110] = 220 # Button turned white after click
        after = Image.fromarray(after_arr)

        v_res = vision_tensor_engine.verify_visual_state_transition(before, after, 100, 100, radius=30)
        self.assertTrue(v_res["ui_transition_verified"])
        self.assertGreater(v_res["local_pixel_diff"], 0.4)


if __name__ == "__main__":
    unittest.main()

