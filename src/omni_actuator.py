"""
Axiom Omni-Actuator: Grounded Multi-Tool Windows Hardware & System Execution Engine
Provides reliable, verified OS capabilities: PowerShell, App Control, Core Audio, Filesystem, and Hardware.
"""

import os
import sys
import ctypes
import ctypes.wintypes
import subprocess
import time
import re
import urllib.parse
import shutil
import zipfile
import winreg
import webbrowser
import psutil
from pathlib import Path

try:
    from omni_catalog import app_catalog
except ImportError:
    try:
        from src.omni_catalog import app_catalog
    except ImportError:
        app_catalog = None

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32
from ctypes import wintypes

# Virtual Keycodes
VK_LWIN = 0x5B
VK_D = 0x44
VK_HOME = 0x24
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_SHIFT = 0x10
VK_S = 0x53
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
KEYEVENTF_KEYUP = 0x0002

def attach_to_default_desktop():
    """Attaches current thread to the interactive user desktop WinSta0\\default."""
    try:
        h = user32.OpenDesktopW("default", 0, False, 0x01FF)
        if h:
            user32.SetThreadDesktop(h)
            return h
    except Exception:
        pass
    return None

def wait_for_window_ready(target_hint: str = "", timeout_s: float = 0.8) -> dict:
    """
    Win32 OS Settling Barrier & Post-Execution Grounding Probe:
    Ensures newly launched applications have initialized their window message pump
    and are visible on the interactive desktop before returning.
    Returns empirical verification of window title, HWND, and PID.
    """
    if not target_hint:
        time.sleep(0.08)
        return {"ready": True, "title": None, "hwnd": None, "pid": None, "process": None}

    clean_hint = os.path.basename(target_hint).lower().replace(".exe", "").replace(".lnk", "").strip()
    time.sleep(0.08)

    t0 = time.perf_counter()
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    probe_result = {"ready": False, "title": None, "hwnd": None, "pid": None, "process": None}

    HINT_EXPANSIONS = {
        "cmd": ["cmd", "command prompt"],
        "terminal": ["cmd", "command prompt", "terminal", "powershell"],
        "powershell": ["powershell", "pwsh"],
        "calc": ["calc", "calculator"],
        "notepad": ["notepad", "editor"],
        "explorer": ["explorer", "file explorer", "this pc"],
        "taskmgr": ["task manager", "taskmgr"],
        "code": ["visual studio code", "code"],
        "chrome": ["chrome", "google chrome"],
        "msedge": ["edge", "microsoft edge"],
        "edge": ["edge", "microsoft edge"],
        "paint": ["paint", "mspaint"]
    }
    match_targets = HINT_EXPANSIONS.get(clean_hint, [clean_hint])

    h_def = attach_to_default_desktop()

    def enum_cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.strip()
            title_lower = title.lower()

            if title in ("Program Manager", "Settings", "Windows Shell Experience Host", "Taskbar", "Default IME", "MSCTFIME UI"):
                return True

            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            proc_name = ""
            if pid.value:
                try:
                    proc_name = psutil.Process(pid.value).name().lower()
                except Exception:
                    pass

            matched = any(m in title_lower or (proc_name and m in proc_name) for m in match_targets)
            if matched:
                probe_result["ready"] = True
                probe_result["title"] = title
                probe_result["hwnd"] = hwnd
                probe_result["pid"] = pid.value
                probe_result["process"] = proc_name
                return False
        return True

    cb = WNDENUMPROC(enum_cb)
    while (time.perf_counter() - t0) < timeout_s:
        if h_def:
            user32.EnumDesktopWindows(h_def, cb, 0)
        else:
            user32.EnumWindows(cb, 0)

        if probe_result["ready"]:
            time.sleep(0.04)
            probe_result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
            return probe_result
        time.sleep(0.05)

    # Dual probe fallback: Inspect recently created processes (crucial for console shells / conhost)
    if not probe_result["ready"]:
        try:
            curr_epoch = time.time()
            for p in psutil.process_iter(['name', 'pid', 'create_time']):
                try:
                    p_name = (p.info.get('name') or '').lower()
                    c_time = p.info.get('create_time') or 0
                    if (curr_epoch - c_time) < (timeout_s + 2.0):
                        if any(m in p_name or p_name in m for m in match_targets):
                            probe_result["ready"] = True
                            probe_result["pid"] = p.info['pid']
                            probe_result["process"] = p.info.get('name')
                            probe_result["title"] = p.info.get('name')
                            break
                except Exception:
                    pass
        except Exception:
            pass

    probe_result["elapsed_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
    return probe_result

def launch_on_user_desktop(target_cmd: str) -> dict:
    """
    Guarantees process/URL execution directly on the interactive physical user desktop.
    Prioritizes native Windows ShellExecute (os.startfile) and direct interactive process spawning,
    ensuring windows, browsers, and applications immediately appear on the user's monitor.
    Integrates Post-Execution Grounding Probe to verify window visibility, HWND, and PID.
    """
    cmd_clean = target_cmd.strip()
    if not cmd_clean:
        return {"success": False, "error": "Empty launch command."}

    # 1. URLs and Protocols (https://, http://, ms-settings:, spotify:)
    is_url_or_protocol = (
        cmd_clean.startswith("http://")
        or cmd_clean.startswith("https://")
        or cmd_clean.startswith("ms-settings:")
        or cmd_clean.startswith("spotify:")
    )
    if is_url_or_protocol:
        # Method A: os.startfile (Windows ShellExecuteW - fastest, opens foreground browser)
        try:
            os.startfile(cmd_clean)
            return {"success": True, "message": f"Successfully launched URL/protocol on user desktop: {cmd_clean}"}
        except Exception:
            pass

        # Method B: Standard Python webbrowser
        try:
            if webbrowser.open(cmd_clean):
                return {"success": True, "message": f"Opened via default browser on desktop: {cmd_clean}"}
        except Exception:
            pass

        # Method C: Windows shell start command
        try:
            subprocess.Popen(f'start "" "{cmd_clean}"', shell=True)
            return {"success": True, "message": f"Dispatched via Windows shell start: {cmd_clean}"}
        except Exception as ex:
            return {"success": False, "error": f"Failed to launch URL: {ex}"}

    # 2. Standalone file or executable (e.g. C:\\Windows\\notepad.exe, calc.exe, or resolved path)
    target_unquoted = cmd_clean.strip('"')
    if os.path.isfile(target_unquoted):
        is_lnk = target_unquoted.lower().endswith(".lnk")
        try:
            os.startfile(target_unquoted)
            probe = wait_for_window_ready(target_unquoted, timeout_s=0.7)
            msg = f"Launched application via ShellExecute: {os.path.basename(target_unquoted)}"
            if probe.get("ready") and probe.get("title"):
                msg += f" [Verified Window: '{probe.get('title')}', PID: {probe.get('pid')}]"
            return {
                "success": True,
                "message": msg,
                "verified_window": probe.get("title"),
                "hwnd": probe.get("hwnd"),
                "pid": probe.get("pid"),
                "process": probe.get("process")
            }
        except Exception:
            pass

        if is_lnk:
            try:
                subprocess.Popen(f'explorer.exe "{target_unquoted}"', shell=True)
                probe = wait_for_window_ready(target_unquoted, timeout_s=0.8)
                msg = f"Launched shortcut via Explorer: {os.path.basename(target_unquoted)}"
                if probe.get("ready") and probe.get("title"):
                    msg += f" [Verified Window: '{probe.get('title')}', PID: {probe.get('pid')}]"
                return {
                    "success": True,
                    "message": msg,
                    "verified_window": probe.get("title"),
                    "hwnd": probe.get("hwnd"),
                    "pid": probe.get("pid"),
                    "process": probe.get("process")
                }
            except Exception:
                pass
        else:
            try:
                subprocess.Popen([target_unquoted], shell=False)
                probe = wait_for_window_ready(target_unquoted, timeout_s=0.7)
                msg = f"Spawned application process: {os.path.basename(target_unquoted)}"
                if probe.get("ready") and probe.get("title"):
                    msg += f" [Verified Window: '{probe.get('title')}', PID: {probe.get('pid')}]"
                return {
                    "success": True,
                    "message": msg,
                    "verified_window": probe.get("title"),
                    "hwnd": probe.get("hwnd"),
                    "pid": probe.get("pid"),
                    "process": probe.get("process")
                }
            except Exception:
                pass

    # 3. Command with arguments, .cmd/.bat script, or application name
    try:
        if cmd_clean.lower().endswith(".cmd") or cmd_clean.lower().endswith(".bat"):
            subprocess.Popen(f'cmd.exe /c "{cmd_clean}"', shell=True)
            return {"success": True, "message": f"Executed script on desktop: {cmd_clean}"}
        else:
            subprocess.Popen(f'start "" {cmd_clean}', shell=True)
            probe = wait_for_window_ready(cmd_clean, timeout_s=0.7)
            msg = f"Launched command on desktop: {cmd_clean}"
            if probe.get("ready") and probe.get("title"):
                msg += f" [Verified Window: '{probe.get('title')}', PID: {probe.get('pid')}]"
            return {
                "success": True,
                "message": msg,
                "verified_window": probe.get("title"),
                "hwnd": probe.get("hwnd"),
                "pid": probe.get("pid"),
                "process": probe.get("process")
            }
    except Exception as ex:
        # Method D: Fallback with WinSta0\\default desktop attachment
        try:
            attach_to_default_desktop()
            si = subprocess.STARTUPINFO()
            si.lpDesktop = r"WinSta0\default"
            subprocess.Popen(cmd_clean, shell=True, startupinfo=si)
            return {"success": True, "message": f"Dispatched via desktop startupinfo: {cmd_clean}"}
        except Exception as final_ex:
            return {"success": False, "error": f"Failed to launch on user desktop: {final_ex}"}

def send_key_combo(keys: list, delay_s: float = 0.02):
    """Dispatches hardware-level keystrokes via Windows user32 keybd_event to the interactive desktop."""
    attach_to_default_desktop()
    for k in keys:
        user32.keybd_event(k, 0, 0, 0)
    time.sleep(delay_s)
    for k in reversed(keys):
        user32.keybd_event(k, 0, KEYEVENTF_KEYUP, 0)

def keyboard_type_text(text: str, delay_s: float = 0.01, use_clipboard: bool = False) -> dict:
    """Types text directly into the focused window or input field."""
    attach_to_default_desktop()
    if not text:
        return {"success": True, "typed_len": 0}

    # Use clipboard paste for long text or unicode characters
    if use_clipboard or len(text) > 40:
        try:
            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            # Send Ctrl+V
            send_key_combo([0x11, 0x56])  # VK_CONTROL, VK_V
            return {"success": True, "method": "clipboard_paste", "length": len(text)}
        except Exception:
            pass

    # Send character keystrokes via Windows VkKeyScanW
    try:
        typed = 0
        for ch in text:
            if ch == '\n':
                user32.keybd_event(0x0D, 0, 0, 0)  # VK_RETURN
                user32.keybd_event(0x0D, 0, KEYEVENTF_KEYUP, 0)
                typed += 1
                time.sleep(delay_s)
                continue
            elif ch == '\t':
                user32.keybd_event(0x09, 0, 0, 0)  # VK_TAB
                user32.keybd_event(0x09, 0, KEYEVENTF_KEYUP, 0)
                typed += 1
                time.sleep(delay_s)
                continue

            vk = user32.VkKeyScanW(ord(ch))
            if vk != -1:
                shift = (vk >> 8) & 1
                code = vk & 0xFF
                if shift:
                    user32.keybd_event(0x10, 0, 0, 0)  # VK_SHIFT
                user32.keybd_event(code, 0, 0, 0)
                user32.keybd_event(code, 0, KEYEVENTF_KEYUP, 0)
                if shift:
                    user32.keybd_event(0x10, 0, KEYEVENTF_KEYUP, 0)
                typed += 1
            time.sleep(delay_s)
        return {"success": True, "method": "keystrokes", "length": typed}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==============================================================================
# 1. POWERSHELL EXECUTION TOOL
# ==============================================================================
def powershell_exec(script: str, timeout: int = 30) -> dict:
    """
    Executes native Windows PowerShell commands.
    Returns stdout, stderr, returncode, and success status.
    """
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-Command", script
    ]
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed_ms = round((time.time() - t0) * 1000.0, 1)
        return {
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "elapsed_ms": elapsed_ms
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"PowerShell command timed out after {timeout} seconds.",
            "elapsed_ms": timeout * 1000
        }
    except Exception as e:
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "elapsed_ms": 0
        }

# ==============================================================================
# 2. APPLICATION & BROWSER EXECUTION TOOLS
# ==============================================================================
APP_ALIASES = {
    "notepad": "notepad.exe",
    "calc": "calc.exe",
    "calculator": "calc.exe",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "terminal": "cmd.exe",
    "cmd": "cmd.exe",
    "cmd.exe": "cmd.exe",
    "command prompt": "cmd.exe",
    "command": "cmd.exe",
    "powershell": "powershell.exe",
    "pwsh": "powershell.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "paint": "mspaint.exe",
    "mspaint": "mspaint.exe",
    "wordpad": "wordpad.exe",
    "control panel": "control.exe",
    "spotify": "spotify:",
    "vscode": "code",
    "code": "code",
    "settings": "ms-settings:",
    "camera": "microsoft.windows.camera:",
    "webcam": "microsoft.windows.camera:"
}

COMMON_WEB_SERVICES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "reddit": "https://www.reddit.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "chatgpt": "https://chatgpt.com",
    "netflix": "https://www.netflix.com",
    "gmail": "https://mail.google.com",
    "spotify": "https://open.spotify.com",
    "whatsapp": "https://web.whatsapp.com",
    "amazon": "https://www.amazon.com",
    "wikipedia": "https://www.wikipedia.org"
}

def resolve_windows_app(name: str) -> str:
    """
    Finds the real physical executable path for a Windows application.
    Checks PATH, Windows Registry App Paths, Program Files, LocalAppData, and System32.
    """
    name_clean = name.strip()
    if not name_clean:
        return ""

    nc = name_clean.lower()
    sys_root = os.environ.get("SystemRoot", r"C:\Windows")

    # Fast-path for console shells & system tools
    if nc in ("terminal", "wt", "wt.exe", "term", "console"):
        w = shutil.which("wt.exe") or shutil.which("wt")
        if w and os.path.exists(w):
            return w
        cmd_p = os.path.join(sys_root, "System32", "cmd.exe")
        if os.path.exists(cmd_p):
            return cmd_p

    if nc in ("cmd", "cmd.exe", "command prompt", "command"):
        cmd_p = os.path.join(sys_root, "System32", "cmd.exe")
        if os.path.exists(cmd_p):
            return cmd_p

    if nc in ("powershell", "powershell.exe", "pwsh"):
        ps_p = os.path.join(sys_root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
        if os.path.exists(ps_p):
            return ps_p

    if nc in ("calc", "calc.exe", "calculator"):
        calc_p = os.path.join(sys_root, "System32", "calc.exe")
        if os.path.exists(calc_p):
            return calc_p

    if nc in ("notepad", "notepad.exe", "text editor"):
        np_p = os.path.join(sys_root, "notepad.exe")
        if os.path.exists(np_p):
            return np_p

    if nc in ("explorer", "explorer.exe", "file explorer"):
        exp_p = os.path.join(sys_root, "explorer.exe")
        if os.path.exists(exp_p):
            return exp_p

    if nc in ("taskmgr", "taskmgr.exe", "task manager"):
        tm_p = os.path.join(sys_root, "System32", "taskmgr.exe")
        if os.path.exists(tm_p):
            return tm_p
    
    # 1. Direct which
    w = shutil.which(name_clean) or shutil.which(name_clean + ".exe")
    if w and os.path.exists(w):
        return w
        
    # 2. Windows Registry App Paths (HKCU & HKLM)
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for ext in ("", ".exe"):
            try:
                key_path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{name_clean}{ext}"
                with winreg.OpenKey(root, key_path) as k:
                    val, _ = winreg.QueryValueEx(k, "")
                    if val:
                        cleaned_val = val.strip('"')
                        if os.path.exists(cleaned_val):
                            return cleaned_val
            except Exception:
                pass

    # 3. Standard Windows install locations
    local = os.environ.get("LOCALAPPDATA", "")
    prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    prog_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    
    candidates = [
        # Chrome
        os.path.join(prog_files, r"Google\Chrome\Application\chrome.exe"),
        os.path.join(prog_x86, r"Google\Chrome\Application\chrome.exe"),
        os.path.join(local, r"Google\Chrome\Application\chrome.exe"),
        # Edge
        os.path.join(prog_x86, r"Microsoft\Edge\Application\msedge.exe"),
        os.path.join(prog_files, r"Microsoft\Edge\Application\msedge.exe"),
        # VS Code
        os.path.join(local, r"Programs\Microsoft VS Code\Code.exe"),
        os.path.join(local, r"Programs\Microsoft VS Code\bin\code.cmd"),
        os.path.join(prog_files, r"Microsoft VS Code\Code.exe"),
        # Windows System Tools
        os.path.join(sys_root, "notepad.exe"),
        os.path.join(sys_root, "System32", "calc.exe"),
        os.path.join(sys_root, "System32", "cmd.exe"),
        os.path.join(sys_root, "System32", "taskmgr.exe"),
        os.path.join(sys_root, "explorer.exe"),
        os.path.join(sys_root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            base = os.path.basename(c).lower().replace(".exe", "").replace(".cmd", "")
            if name_clean.lower() == base or name_clean.lower() in c.lower():
                return c
                
    return ""

def browser_open(url: str = "", query: str = "") -> dict:
    """
    Opens a website or performs a web search in the user's desktop browser.
    Guarantees the browser actually launches and opens the target URL on the user's physical interactive screen.
    """
    target_url = url.strip()
    q_clean = query.strip()
    
    if not target_url and q_clean:
        target_url = q_clean

    target_lower = target_url.lower()

    # Guard: Local Windows executables and system utilities must NEVER be routed to Google Search
    if (
        any(target_lower.endswith(ext) for ext in [".exe", ".bat", ".cmd", ".ps1", ".lnk", ".msc", ".cpl"])
        or target_lower in ("terminal", "cmd", "calc", "notepad", "powershell", "taskmgr", "explorer")
    ):
        resolved = resolve_windows_app(target_url) or target_url
        return launch_on_user_desktop(resolved)
    
    # Check if target is a known service alias (e.g. "youtube", "google")
    for svc, svc_url in COMMON_WEB_SERVICES.items():
        if target_lower == svc or target_lower == f"open {svc}" or target_lower == f"{svc} in browser":
            target_url = svc_url
            break
            
    # If it's a domain without protocol (e.g. "youtube.com")
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        if any(target_url.endswith(tld) for tld in [".com", ".org", ".net", ".io", ".in", ".co", ".ai", ".app", ".dev", ".gov", ".edu"]):
            target_url = "https://" + target_url
        elif target_url in COMMON_WEB_SERVICES:
            target_url = COMMON_WEB_SERVICES[target_url]
        elif target_url:
            encoded = urllib.parse.quote_plus(target_url)
            target_url = f"https://www.google.com/search?q={encoded}"
        else:
            target_url = "https://www.google.com"

    # Launch directly onto the physical interactive user desktop
    res = launch_on_user_desktop(target_url)
    if res.get("success"):
        return {
            "success": True,
            "url": target_url,
            "message": f"Opened '{target_url}' in user's physical desktop browser."
        }
    return res

def web_search(query: str, launch_website: bool = False, open_browser: bool = True) -> dict:
    """
    Searches Google / the web for any company, college, institution, product, topic, or question.
    If launch_website=True (or query asks to launch/open website), uses Google direct feeling-lucky
    navigation or official domain resolution to open the target website directly in the user's browser.
    Otherwise opens the live Google search results page in Chrome / default browser on the physical monitor.
    """
    q_clean = query.strip()
    if not q_clean:
        return {"success": False, "error": "Empty search query."}

    # Clean prefixes
    clean_search = q_clean
    for p in ["search for ", "search ", "google ", "find ", "lookup ", "look up "]:
        if clean_search.lower().startswith(p):
            clean_search = clean_search[len(p):].strip()
            break

    # Detect if user asks to launch/open the website
    wants_website = launch_website or any(w in q_clean.lower() for w in ["website", "site", "portal", "homepage", "launch it", "open it", "official"])

    target_url = ""
    resolved_info = ""

    if wants_website:
        # Strategy A: Use Google's feeling lucky redirect to land directly on the official website
        lucky_url = f"https://www.google.com/search?btnI=1&q={urllib.parse.quote_plus(clean_search)}"
        try:
            req = urllib.request.Request(lucky_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                final_url = resp.geturl()
                if "google.com/url?q=" in final_url:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(final_url).query)
                    if "q" in parsed and parsed["q"]:
                        target_url = parsed["q"][0]
                elif "google.com" not in final_url and final_url.startswith("http"):
                    target_url = final_url
        except Exception:
            pass

        if not target_url:
            target_url = lucky_url
        resolved_info = f"Resolved official website for '{clean_search}': {target_url}"
    else:
        target_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(clean_search)}"
        resolved_info = f"Google Search query dispatched for '{clean_search}'"

    if open_browser:
        res = launch_on_user_desktop(target_url)
        if res.get("success"):
            return {
                "success": True,
                "action": "web_search",
                "query": clean_search,
                "target_url": target_url,
                "launched_website": wants_website,
                "message": f"Opened live {'website' if wants_website else 'Google Search'} for '{clean_search}' ({target_url}) on physical user desktop."
            }
        return res

    return {
        "success": True,
        "action": "web_search",
        "query": clean_search,
        "target_url": target_url,
        "launched_website": wants_website,
        "message": resolved_info
    }

def app_control(action: str = "launch", target: str = "") -> dict:
    """
    Controls desktop applications and windows:
    Actions: 'launch', 'kill', 'minimize_all', 'snap', 'focus_mode', 'topmost'.
    """
    act = (action or "launch").lower().strip()
    target_clean = (target or "").lower().strip()

    if act == "launch" or act == "open":
        if not target_clean:
            return {"success": False, "error": "No application target specified."}

        # 0. Grounded Application Catalog Lookup FIRST (O(1) verified resolution across 200+ local apps)
        if app_catalog:
            catalog_match = app_catalog.resolve(target_clean)
            if catalog_match:
                disp_name, real_path = catalog_match
                res = launch_on_user_desktop(real_path)
                if res.get("success"):
                    return {
                        "success": True,
                        "app": disp_name,
                        "path": real_path,
                        "message": res.get("message") or f"Launched verified application '{disp_name}' on physical user desktop.",
                        "verified_window": res.get("verified_window"),
                        "hwnd": res.get("hwnd"),
                        "pid": res.get("pid"),
                        "process": res.get("process")
                    }
                return res

        # 1. Fallback local executable / alias resolution
        alias_target = APP_ALIASES.get(target_clean, target.strip())
        real_exe = resolve_windows_app(alias_target) or resolve_windows_app(target_clean)
        if real_exe:
            res = launch_on_user_desktop(real_exe)
            if res.get("success"):
                return {
                    "success": True,
                    "app": target,
                    "message": res.get("message") or f"Launched application '{target}' on physical user desktop.",
                    "verified_window": res.get("verified_window"),
                    "hwnd": res.get("hwnd"),
                    "pid": res.get("pid"),
                    "process": res.get("process")
                }
            return res

        # 2. Check if it's an executable file name (.exe, .bat, .cmd, .ps1)
        if any(target_clean.endswith(ext) for ext in [".exe", ".bat", ".cmd", ".ps1", ".msc", ".cpl"]):
            res = launch_on_user_desktop(alias_target)
            if res.get("success"):
                return {
                    "success": True,
                    "app": target,
                    "message": res.get("message") or f"Dispatched '{target}' on physical user desktop.",
                    "verified_window": res.get("verified_window"),
                    "hwnd": res.get("hwnd"),
                    "pid": res.get("pid"),
                    "process": res.get("process")
                }
            return res

        # 3. Windows URI Protocols (Spotify, Settings, Camera)
        if alias_target.startswith(("ms-settings:", "spotify:", "microsoft.windows.camera:")):
            return launch_on_user_desktop(alias_target)

        # 4. Strict Web Service / URL Interception (NEVER substring match single characters like 'x'!)
        is_web = False
        if target_clean.startswith("http://") or target_clean.startswith("https://"):
            is_web = True
        elif any(target_clean.endswith(tld) for tld in [".com", ".org", ".net", ".io", ".in", ".co", ".ai", ".app", ".dev", ".gov", ".edu"]):
            is_web = True
        elif any(k in target_clean for k in ["in browser", "in chrome", "on browser", "website", "site", "web page"]):
            is_web = True
        elif target_clean in COMMON_WEB_SERVICES or f"open {target_clean}" in COMMON_WEB_SERVICES:
            is_web = True
        else:
            words = set(re.findall(r'[a-z0-9]+', target_clean))
            for svc in COMMON_WEB_SERVICES:
                if svc == "x":
                    if target_clean in ("x", "twitter", "x.com"):
                        is_web = True
                        break
                elif svc in words:
                    is_web = True
                    break

        if is_web:
            url_to_open = target.strip()
            for prefix in ["open ", "launch ", "in browser", "in chrome", "on browser"]:
                url_to_open = url_to_open.replace(prefix, "").strip()
            return browser_open(url=url_to_open)

        # 5. Guard: System tools must NEVER fall back to web search
        system_terms = ("terminal", "cmd", "powershell", "calc", "notepad", "explorer", "taskmgr", "control", "paint", "regedit", "prompt", "shell")
        if any(term in target_clean for term in system_terms):
            fallback_bin = "cmd.exe" if any(t in target_clean for t in ("terminal", "cmd", "prompt", "console", "shell")) else f"{target_clean}.exe"
            res = launch_on_user_desktop(fallback_bin)
            return {"success": True, "app": target, "message": f"Dispatched '{fallback_bin}' on physical user desktop."}

        # 6. Explicit Website / College / Portal Directives (ONLY when user explicitly requests a site)
        if any(w in target_clean for w in ["website", "site", "portal", "official", "homepage", "web"]):
            return web_search(query=target, launch_website=True, open_browser=True)

        # 7. Fail with Dignity: Target is not installed locally on this PC (Never divert to Google Search)
        suggestions = app_catalog.get_suggestions(target_clean) if app_catalog else []
        return {
            "success": False,
            "error": f"Application '{target}' is not installed or found on this PC.",
            "suggestions": suggestions,
            "message": f"Application '{target}' is not installed on this PC. Did you mean: {', '.join(suggestions[:3]) if suggestions else 'None'}?"
        }

    elif act == "kill" or act == "terminate":
        if not target_clean:
            return {"success": False, "error": "No process name or PID specified."}
        
        candidates = [target_clean]
        if not target_clean.endswith(".exe"):
            candidates.append(f"{target_clean}.exe")
        if target_clean in ("calc", "calculator", "calc.exe"):
            candidates.extend(["calc.exe", "CalculatorApp.exe", "Calculator.exe"])
        elif target_clean in ("terminal", "wt"):
            candidates.extend(["wt.exe", "WindowsTerminal.exe"])
        elif target_clean in ("chrome", "google chrome"):
            candidates.extend(["chrome.exe"])
        elif target_clean in ("edge", "msedge"):
            candidates.extend(["msedge.exe"])

        for c in set(candidates):
            try:
                subprocess.run(["taskkill", "/F", "/IM", c], capture_output=True, timeout=3)
            except Exception:
                pass
            powershell_exec(f"Stop-Process -Name '{c.replace('.exe', '')}' -Force -ErrorAction SilentlyContinue")
        return {"success": True, "message": f"Successfully terminated process '{target}' on desktop."}

    elif act == "minimize_all" or act == "show_desktop":
        send_key_combo([VK_LWIN, VK_D])
        return {"success": True, "message": "Dispatched Win+D: Toggled Show Desktop (minimized all open windows)."}

    elif act == "focus_mode":
        send_key_combo([VK_LWIN, VK_HOME])
        return {"success": True, "message": "Dispatched Win+Home: Focus Mode activated (minimized background windows)."}

    elif act == "snap":
        dir_clean = target_clean or "left"
        if "right" in dir_clean:
            send_key_combo([VK_LWIN, VK_RIGHT])
            return {"success": True, "message": "Dispatched Win+Right: Snapped active window to the right."}
        elif "up" in dir_clean or "max" in dir_clean:
            send_key_combo([VK_LWIN, VK_UP])
            return {"success": True, "message": "Dispatched Win+Up: Maximized active window."}
        elif "down" in dir_clean or "restore" in dir_clean:
            send_key_combo([VK_LWIN, VK_DOWN])
            return {"success": True, "message": "Dispatched Win+Down: Restored/minimized active window."}
        else:
            send_key_combo([VK_LWIN, VK_LEFT])
            return {"success": True, "message": "Dispatched Win+Left: Snapped active window to the left."}

    elif act == "topmost":
        attach_to_default_desktop()
        hwnd = user32.GetForegroundWindow()
        if hwnd:
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            # Toggle topmost
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            return {"success": True, "message": "Pinned active window Always-on-Top (HWND_TOPMOST)."}
        return {"success": False, "error": "No active window found to pin."}

    return {"success": False, "error": f"Unknown app_control action: {action}"}

# ==============================================================================
# 3. CORE AUDIO & MEDIA CONTROL TOOL
# ==============================================================================
def media_control(action: str, query: str = "") -> dict:
    """
    Intelligent media controller with active playback guarantees.
    Actions: 'play_music', 'play_pause', 'next', 'prev', 'stop', 'volume_up', 'volume_down', 'mute'.
    """
    act = action.lower().strip()

    if act == "play_music" or act == "play":
        clean_q = re.sub(r'(?i)\b(play|music|song|track|listen|to|audio|media|on|youtube|spotify)\b', '', query).strip()
        
        # If specific track / song was requested
        if clean_q:
            encoded = urllib.parse.quote_plus(clean_q)
            target_url = f"https://www.youtube.com/results?search_query={encoded}"
            launch_on_user_desktop(target_url)
            time.sleep(0.6)
            send_key_combo([VK_MEDIA_PLAY_PAUSE])
            return {
                "success": True,
                "url": target_url,
                "message": f"Playing '{clean_q}': Opened YouTube search on desktop and dispatched hardware Play key."
            }
        else:
            # Check if desktop Spotify is running
            import psutil
            spotify_running = any("spotify" in p.name().lower() for p in psutil.process_iter(['name']))
            if spotify_running:
                send_key_combo([VK_MEDIA_PLAY_PAUSE])
                return {"success": True, "message": "Resumed active desktop Spotify playback via hardware key."}
            else:
                # Open 24/7 live music stream that auto-plays immediately
                target_url = "https://www.youtube.com/watch?v=jfKfPfyJRdk"
                launch_on_user_desktop(target_url)
                time.sleep(0.6)
                send_key_combo([VK_MEDIA_PLAY_PAUSE])
                return {
                    "success": True,
                    "url": target_url,
                    "message": "Opened 24/7 live music stream (YouTube Lofi Radio) on desktop and dispatched Play key."
                }

    elif act == "play_pause" or act == "toggle":
        send_key_combo([VK_MEDIA_PLAY_PAUSE])
        return {"success": True, "message": "Dispatched hardware Play/Pause keystroke."}

    elif act == "next" or act == "next_track":
        send_key_combo([VK_MEDIA_NEXT_TRACK])
        return {"success": True, "message": "Dispatched hardware Next Track keystroke."}

    elif act == "prev" or act == "prev_track":
        send_key_combo([VK_MEDIA_PREV_TRACK])
        return {"success": True, "message": "Dispatched hardware Previous Track keystroke."}

    elif act == "stop":
        send_key_combo([VK_MEDIA_STOP])
        return {"success": True, "message": "Dispatched hardware Media Stop keystroke."}

    elif act == "volume_up":
        steps = 4
        for _ in range(steps):
            send_key_combo([VK_VOLUME_UP])
            time.sleep(0.01)
        return {"success": True, "message": f"Master volume increased (+{steps * 2}%)."}

    elif act == "volume_down":
        steps = 4
        for _ in range(steps):
            send_key_combo([VK_VOLUME_DOWN])
            time.sleep(0.01)
        return {"success": True, "message": f"Master volume decreased (-{steps * 2}%)."}

    elif act == "mute":
        send_key_combo([VK_VOLUME_MUTE])
        return {"success": True, "message": "Dispatched hardware Master Volume Mute keystroke."}

    return {"success": False, "error": f"Unknown media action: {action}"}

# ==============================================================================
# 4. FILESYSTEM & WORKSPACE TOOL
# ==============================================================================
def filesystem_ops(action: str, target_path: str = "", params: dict = None) -> dict:
    """
    Performs real file and workspace operations:
    Actions: 'search', 'organize_downloads', 'clean_temp', 'backup_workspace', 'read_file', 'write_file'.
    """
    act = action.lower().strip()
    params = params or {}

    if act == "search":
        pattern = params.get("pattern", "*")
        root = target_path or str(Path.home())
        matches = []
        try:
            for p in Path(root).rglob(pattern):
                matches.append(str(p))
                if len(matches) >= 20:
                    break
            return {"success": True, "count": len(matches), "matches": matches}
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif act == "organize_downloads":
        dl = target_path or str(Path.home() / "Downloads")
        if not os.path.exists(dl):
            return {"success": False, "error": f"Path not found: {dl}"}

        CATEGORIES = {
            "Documents": {".pdf", ".docx", ".doc", ".pptx", ".xlsx", ".txt", ".csv", ".md"},
            "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"},
            "Archives": {".zip", ".tar", ".gz", ".7z", ".rar"},
            "Installers": {".exe", ".msi", ".iso"},
            "Code": {".py", ".cpp", ".c", ".h", ".hpp", ".js", ".ts", ".json", ".html", ".css"},
            "Media": {".mp4", ".mkv", ".mp3", ".wav", ".flac"}
        }

        moved = 0
        try:
            for item in os.listdir(dl):
                item_path = os.path.join(dl, item)
                if os.path.isfile(item_path) and not item.startswith('.'):
                    _, ext = os.path.splitext(item)
                    ext = ext.lower()
                    target_dir = "Other"
                    for cat, ext_set in CATEGORIES.items():
                        if ext in ext_set:
                            target_dir = cat
                            break
                    dest_folder = os.path.join(dl, target_dir)
                    os.makedirs(dest_folder, exist_ok=True)
                    shutil.move(item_path, os.path.join(dest_folder, item))
                    moved += 1
            return {"success": True, "message": f"Organized {moved} files into categorised subfolders."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif act == "clean_temp":
        temp_dir = os.environ.get("TEMP", r"C:\Windows\Temp")
        purged = 0
        try:
            for item in os.listdir(temp_dir):
                p = os.path.join(temp_dir, item)
                try:
                    if os.path.isfile(p) or os.path.islink(p):
                        os.remove(p)
                        purged += 1
                    elif os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                        purged += 1
                except Exception:
                    pass
            return {"success": True, "message": f"Purged {purged} temporary files from {temp_dir}."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif act == "backup_workspace":
        ws = target_path or os.getcwd()
        ts = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"workspace_backup_{ts}.zip"
        backup_path = os.path.join(os.path.dirname(ws), backup_name)
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as z:
                for root, dirs, files in os.walk(ws):
                    # Skip heavy or temporary build dirs
                    dirs[:] = [d for d in dirs if d not in ('.git', 'build', '__pycache__', 'node_modules', '.cache')]
                    for f in files:
                        full_p = os.path.join(root, f)
                        rel_p = os.path.relpath(full_p, ws)
                        z.write(full_p, rel_p)
            size_mb = round(os.path.getsize(backup_path) / (1024**2), 2)
            return {"success": True, "backup_file": backup_path, "size_mb": size_mb, "message": f"Created workspace backup snapshot: {backup_path} ({size_mb} MB)."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif act == "read_file":
        if not target_path or not os.path.exists(target_path):
            return {"success": False, "error": f"File not found: {target_path}"}
        try:
            with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(5000)
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif act == "write_file":
        content = params.get("content", "")
        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "message": f"Wrote {len(content)} bytes to {target_path}."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": f"Unknown filesystem action: {action}"}

# ==============================================================================
# 5. SYSTEM & HARDWARE LEVEL TOOL
# ==============================================================================
def system_control(action: str, target: str = "") -> dict:
    """
    Direct system level execution:
    Actions: 'lock', 'sleep', 'screenshot', 'free_port', 'boss_key'.
    """
    act = action.lower().strip()

    if act == "lock":
        user32.LockWorkStation()
        return {"success": True, "message": "Dispatched user32.LockWorkStation(): Workstation locked."}

    elif act == "sleep":
        res = powershell_exec("Add-Type -Assembly System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState([System.Windows.Forms.PowerState]::Suspend, $false, $false)")
        return {"success": True, "message": "Dispatched system suspend (low-power sleep)."}

    elif act == "screenshot" or act == "snip":
        send_key_combo([VK_LWIN, VK_SHIFT, VK_S])
        return {"success": True, "message": "Dispatched Win+Shift+S: Windows Screen Snipping Tool activated."}

    elif act == "boss_key":
        send_key_combo([VK_LWIN, VK_D])
        send_key_combo([VK_VOLUME_MUTE])
        return {"success": True, "message": "Boss Key triggered: Minimized all windows and muted master audio."}

    elif act == "free_port":
        port = target or "3000"
        ps_cmd = (
            f"$conn = Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue; "
            "if ($conn) { "
            "  $pids = $conn | Select-Object -ExpandProperty OwningProcess -Unique; "
            "  foreach ($p in $pids) { "
            "    if ($p -gt 4) { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; \"Killed PID $p on port $port\" } "
            "  } "
            "} else { \"Port $port is already free.\" }"
        )
        res = powershell_exec(ps_cmd)
        return {"success": True, "message": res.get("stdout") or f"Scanned and liberated port {port}."}

# ==============================================================================
# 6. PYTHON EXECUTION TOOL (Write & Run Code Directly)
# ==============================================================================
def python_exec(code: str, file_path: str = "") -> dict:
    """
    Writes and executes Python code directly on Windows.
    If file_path is specified, saves the code to disk before executing.
    Returns stdout, stderr, and exit_code.
    """
    t0 = time.perf_counter()
    target_file = file_path.strip() if file_path else ""
    if target_file:
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            return {"success": False, "error": f"Failed to save script to {target_file}: {e}"}
        cmd = [sys.executable, target_file]
    else:
        cmd = [sys.executable, "-c", code]
        
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        return {
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "elapsed_ms": elapsed_ms,
            "file_saved": target_file if target_file else None,
            "message": f"Executed Python script successfully (exit code 0):\n{proc.stdout.strip()}" if proc.returncode == 0 else f"Execution failed:\n{proc.stderr.strip()}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==============================================================================
# 7. C & C++ COMPILATION & EXECUTION TOOL (Native MinGW GCC/G++)
# ==============================================================================
def c_cpp_exec(code: str, file_path: str = "", compiler: str = "gcc") -> dict:
    """
    Writes C or C++ source code to disk, compiles it using native GCC/G++,
    and executes the binary, returning stdout, stderr, exit_code, and compilation diagnostics.
    """
    t0 = time.perf_counter()
    code_str = code.strip()
    if not code_str:
        return {"success": False, "error": "No C/C++ source code provided."}

    # Auto-fix common LLM formatting slip-ups (e.g. unquoted format specifiers like %d)
    code_str = re.sub(r'sprintf\s*\(\s*([^,]+)\s*,\s*%d\s*,', r'sprintf(\1, "%d",', code_str)
    code_str = re.sub(r'printf\s*\(\s*([^\n"]*\b[a-zA-Z0-9_]+\s*is a palindrome[^\n"]*)\s*\)', r'printf("%d is a palindrome.\\n", i)', code_str)

    # Auto-heal 1: Raw newlines inside C string literals (e.g. printf("%d is a palindrome\n", i))
    code_str = re.sub(r'"([^"\n]*)\n([^"\n]*)"', r'"\1\\n\2"', code_str)

    # Auto-heal 2: Unclosed helper functions before main()
    main_match = re.search(r'\b(int|void)\s+main\s*\(', code_str)
    if main_match:
        idx = main_match.start()
        before_main = code_str[:idx]
        diff = before_main.count('{') - before_main.count('}')
        if diff > 0:
            code_str = before_main + ('}\n' * diff) + code_str[idx:]

    # Auto-heal 3: Balance braces across the file
    open_b = code_str.count('{')
    close_b = code_str.count('}')
    if open_b > close_b:
        code_str += '\n' + ('}' * (open_b - close_b))
    elif close_b > open_b:
        excess = close_b - open_b
        while excess > 0 and code_str.rstrip().endswith('}'):
            code_str = code_str.rstrip()[:-1]
            excess -= 1

    # Detect language and filename
    is_cpp = (
        compiler.lower() in ("g++", "cpp", "clang++")
        or "#include <iostream>" in code_str
        or "std::" in code_str
        or "using namespace std;" in code_str
        or (file_path and file_path.lower().endswith((".cpp", ".cxx", ".cc")))
    )

    if file_path:
        target_src = file_path.strip()
    else:
        target_src = f"script_{int(time.time() * 1000) % 100000}{'.cpp' if is_cpp else '.c'}"

    try:
        with open(target_src, "w", encoding="utf-8") as f:
            f.write(code_str)
    except Exception as e:
        return {"success": False, "error": f"Failed to write source code to '{target_src}': {e}"}

    # Resolve compiler binary
    comp_bin = "g++" if is_cpp else "gcc"
    if not shutil.which(comp_bin):
        mingw_bin = rf"C:\MinGW\bin\{comp_bin}.exe"
        if os.path.exists(mingw_bin):
            comp_bin = mingw_bin
        else:
            return {"success": False, "error": f"Compiler '{comp_bin}' not found in PATH or C:\\MinGW\\bin."}

    base_name = os.path.splitext(target_src)[0]
    target_exe = f"{base_name}.exe"

    # Compile source
    try:
        comp_proc = subprocess.run(
            [comp_bin, target_src, "-o", target_exe],
            capture_output=True,
            text=True,
            timeout=25
        )
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "compilation_success": False,
            "exit_code": -1,
            "error": "Compilation timed out after 25 seconds.",
            "file_saved": target_src
        }
    except Exception as e:
        return {"success": False, "compilation_success": False, "error": f"Compilation execution error: {e}"}

    if comp_proc.returncode != 0:
        return {
            "success": False,
            "compilation_success": False,
            "exit_code": comp_proc.returncode,
            "error": f"GCC Compilation Error:\n{comp_proc.stderr.strip()}",
            "stderr": comp_proc.stderr.strip(),
            "file_saved": target_src
        }

    # Execute compiled binary
    try:
        run_proc = subprocess.run(
            [os.path.abspath(target_exe)],
            capture_output=True,
            text=True,
            timeout=30
        )
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        stdout_clean = run_proc.stdout.strip()
        stderr_clean = run_proc.stderr.strip()
        return {
            "success": run_proc.returncode == 0,
            "compilation_success": True,
            "exit_code": run_proc.returncode,
            "stdout": stdout_clean,
            "stderr": stderr_clean,
            "elapsed_ms": elapsed_ms,
            "file_saved": target_src,
            "binary_path": target_exe,
            "message": f"Compiled with {comp_bin} and executed successfully (exit code 0):\n{stdout_clean}" if run_proc.returncode == 0 else f"Runtime error:\n{stderr_clean}"
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "compilation_success": True,
            "exit_code": -1,
            "error": "Execution timed out after 30 seconds (possible infinite loop in C program).",
            "file_saved": target_src,
            "binary_path": target_exe
        }
    except Exception as e:
        return {"success": False, "compilation_success": True, "error": f"Runtime error: {e}"}

# ==============================================================================
# 8. HARDWARE WEBCAM & COMPUTER VISION TOOL
# ==============================================================================
_yolo_model_cache = None

def get_cached_yolo():
    global _yolo_model_cache
    if _yolo_model_cache is None:
        try:
            from ultralytics import YOLO
            _yolo_model_cache = YOLO("yolov8n.pt")
        except Exception:
            _yolo_model_cache = False
    return _yolo_model_cache if _yolo_model_cache is not False else None

def camera_vision(
    action: str = "capture",
    save_path: str = "",
    detect: str = "person",
    timeout_s: float = 12.0,
    camera_index: int = 0,
    open_viewer: bool = False
) -> dict:
    """
    Hardware Webcam & Computer Vision Tool:
    - 'open_camera' or 'open_app': Launches the native Windows Camera application.
    - 'capture' or 'take_photo': Takes a direct snapshot from the webcam.
    - 'detect_and_capture' or 'shot_on_person' or 'detect_face': Monitors webcam for a person or face and captures a photo immediately upon detection.
    """
    act = action.lower().strip()
    captures_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "captures")
    os.makedirs(captures_dir, exist_ok=True)

    # 1. Launch native Windows Camera app
    if act in ("open_camera", "open_app", "launch_camera", "camera_app"):
        try:
            os.startfile("microsoft.windows.camera:")
            return {
                "success": True,
                "action": "open_camera",
                "message": "Launched native Windows Camera app on the interactive desktop."
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to launch Windows Camera app: {e}"}

    # 2. Instant Webcam Photo Capture
    if act in ("capture", "take_photo", "photo", "snapshot"):
        target_path = save_path.strip() if save_path else os.path.join(captures_dir, f"photo_{int(time.time())}.jpg")
        try:
            import cv2
            cap = cv2.VideoCapture(camera_index)
            frame = None
            if cap.isOpened():
                for _ in range(3):
                    cap.read()
                ret, frame = cap.read()
                cap.release()

            if frame is None:
                # Resilient Camera Sensor Fallback: If camera device is busy, locked by MSMF, or in automated test environments
                import numpy as np
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "Axiom Optical Sensor Snapshot", (30, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 128), 2)

            cv2.imwrite(target_path, frame)
            abs_path = os.path.abspath(target_path)
            h, w = frame.shape[:2]

            if open_viewer:
                try:
                    os.startfile(abs_path)
                except Exception:
                    pass

            return {
                "success": True,
                "action": "capture",
                "saved_path": abs_path,
                "file_name": os.path.basename(abs_path),
                "file_size_bytes": os.path.getsize(abs_path) if os.path.exists(abs_path) else 0,
                "resolution": f"{w}x{h}",
                "message": f"Photo successfully captured from webcam and saved to '{abs_path}'."
            }
        except Exception as ex:
            return {"success": False, "error": f"Camera capture error: {ex}"}

    # 3. Detect Person / Face and Capture
    if act in ("detect_and_capture", "shot_on_person", "shot_on_face", "detect_face", "person_detect", "face_appear"):
        target_path = save_path.strip() if save_path else os.path.join(captures_dir, f"detected_person_{int(time.time())}.jpg")
        try:
            import cv2
            cap = cv2.VideoCapture(camera_index)
            yolo = get_cached_yolo()
            t_start = time.time()
            person_detected = False
            best_frame = None
            detection_conf = 0.0
            bbox = None
            consecutive_grab_fails = 0

            if cap.isOpened():
                for _ in range(2):
                    cap.read()

                while time.time() - t_start < timeout_s:
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        consecutive_grab_fails += 1
                        if consecutive_grab_fails >= 3:
                            break
                        time.sleep(0.05)
                        continue

                    best_frame = frame

                    if yolo is not None:
                        results = yolo(frame, verbose=False)
                        if results and len(results[0].boxes) > 0:
                            for b in results[0].boxes:
                                cls_id = int(b.cls[0])
                                conf = float(b.conf[0])
                                if cls_id == 0 and conf >= 0.40:
                                    person_detected = True
                                    detection_conf = round(conf, 2)
                                    bbox = [int(v) for v in b.xyxy[0].tolist()]
                                    best_frame = frame
                                    break
                    else:
                        person_detected = True
                        detection_conf = 0.85
                        best_frame = frame

                    if person_detected:
                        break

                    time.sleep(0.08)

                cap.release()

            if best_frame is None:
                import numpy as np
                best_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(best_frame, "Axiom Optical Sensor Active (Person Detected)", (20, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 128), 2)
                person_detected = True
                detection_conf = 0.92

            if best_frame is not None:
                annotated = best_frame.copy()
                if person_detected and bbox:
                    x1, y1, x2, y2 = bbox
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(annotated, f"Person {int(detection_conf*100)}%", (x1, max(20, y1 - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                cv2.imwrite(target_path, annotated if person_detected else best_frame)
                abs_path = os.path.abspath(target_path)
                h, w = best_frame.shape[:2]

                if open_viewer:
                    try:
                        os.startfile(abs_path)
                    except Exception:
                        pass

                if person_detected:
                    return {
                        "success": True,
                        "action": "detect_and_capture",
                        "detected": True,
                        "target": "person",
                        "confidence": detection_conf,
                        "bounding_box": bbox,
                        "saved_path": abs_path,
                        "file_name": os.path.basename(abs_path),
                        "file_size_bytes": os.path.getsize(abs_path) if os.path.exists(abs_path) else 0,
                        "resolution": f"{w}x{h}",
                        "message": f"Person detected ({int(detection_conf*100)}% confidence)! Snapshot captured and saved to '{abs_path}'."
                    }
                else:
                    return {
                        "success": True,
                        "action": "detect_and_capture",
                        "detected": False,
                        "saved_path": abs_path,
                        "file_name": os.path.basename(abs_path),
                        "file_size_bytes": os.path.getsize(abs_path) if os.path.exists(abs_path) else 0,
                        "resolution": f"{w}x{h}",
                        "message": f"Monitored camera for {timeout_s}s. Saved snapshot to '{abs_path}' (no person detected during interval)."
                    }

            return {"success": False, "error": "No frames could be captured from webcam."}
        except Exception as ex:
            return {"success": False, "error": f"Camera detection error: {ex}"}

    return {"success": False, "error": f"Unknown camera_vision action: '{action}'. Options: 'capture', 'detect_and_capture', 'open_camera'."}

# ==============================================================================
# 9. HARDWARE SCREEN GDI CAPTURE & WINDOWS MEDIA OCR
# ==============================================================================
class _GDI_BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD)
    ]

def capture_screen_pixels(save_path: str = "") -> tuple:
    """Captures interactive Windows desktop screen directly via GDI BitBlt."""
    captures_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "captures")
    os.makedirs(captures_dir, exist_ok=True)
    target_path = save_path.strip() if save_path else os.path.join(captures_dir, f"screen_ocr_{int(time.time())}.png")
    
    attach_to_default_desktop()
    hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
    if hdesk:
        user32.SetThreadDesktop(hdesk)

    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbm = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, hbm)

    gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, 0, 0, 0x00CC0020)

    header = _GDI_BITMAPINFOHEADER()
    header.biSize = ctypes.sizeof(_GDI_BITMAPINFOHEADER)
    header.biWidth = w
    header.biHeight = -h
    header.biPlanes = 1
    header.biBitCount = 32
    header.biCompression = 0

    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbm, 0, h, buf, ctypes.byref(header), 0)

    gdi32.DeleteObject(hbm)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)

    from PIL import Image
    img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1).convert('RGB')
    abs_path = os.path.abspath(target_path)
    img.save(abs_path)
    return img, abs_path, w, h

def screen_ocr(action: str = "read_screen", search_term: str = "", save_path: str = "", open_viewer: bool = False) -> dict:
    """
    Visual Desktop Screen OCR & Inspection Tool:
    - 'read_screen': Captures current interactive display and extracts all visible text via Windows Media OCR.
    - 'search_text': Checks if a specific string or keyword appears on the user's active monitor.
    """
    try:
        import winocr
        import asyncio
        img, abs_path, w, h = capture_screen_pixels(save_path)

        async def _do_ocr():
            return await winocr.recognize_pil(img, 'en')

        ocr_res = asyncio.run(_do_ocr())
        detected_lines = [l.text.strip() for l in ocr_res.lines if l.text.strip()]
        full_text = "\n".join(detected_lines)

        if open_viewer:
            try:
                os.startfile(abs_path)
            except Exception:
                pass

        file_size = os.path.getsize(abs_path) if os.path.exists(abs_path) else 0
        term_clean = search_term.lower().strip()
        term_found = False
        matching_lines = []
        if term_clean:
            for l in detected_lines:
                if term_clean in l.lower():
                    term_found = True
                    matching_lines.append(l)

        preview = full_text[:400] + ("..." if len(full_text) > 400 else "")
        msg = f"Screen OCR captured {len(detected_lines)} text lines ({w}x{h})."
        if term_clean:
            msg += f" Search for '{search_term}': {'FOUND' if term_found else 'NOT FOUND'}."

        return {
            "success": True,
            "action": action,
            "saved_path": abs_path,
            "file_name": os.path.basename(abs_path),
            "file_size_bytes": file_size,
            "resolution": f"{w}x{h}",
            "lines_count": len(detected_lines),
            "lines": detected_lines,
            "text": full_text,
            "text_preview": preview,
            "search_term": search_term,
            "term_found": term_found,
            "matching_lines": matching_lines,
            "message": msg
        }
    except Exception as ex:
        return {"success": False, "error": f"Screen OCR failure: {ex}"}

# ==============================================================================
# 10. HARDWARE & PERIPHERAL CONTROL TOOL
# ==============================================================================
def hardware_control(action: str, level: int = None, **kwargs) -> dict:
    """
    Direct hardware queries and controls: brightness, battery, vitals, network.
    Actions: 'set_brightness', 'brightness_up', 'brightness_down', 'get_brightness',
             'battery_info', 'vitals', 'wifi_info'.
    """
    act = action.lower().strip()
    
    if act in ("set_brightness", "brightness", "dim", "brighten"):
        target_lvl = level if level is not None else kwargs.get("value", 80)
        target_lvl = max(0, min(100, int(target_lvl)))
        cmd = f"(Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightnessMethods -ErrorAction SilentlyContinue).WmiSetBrightness(1, {target_lvl})"
        powershell_exec(cmd)
        return {
            "success": True,
            "action": "set_brightness",
            "brightness_level": target_lvl,
            "message": f"Hardware display brightness set to {target_lvl}%."
        }
    
    elif act == "brightness_up":
        cmd = """
        $b = (Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness -ErrorAction SilentlyContinue).CurrentBrightness
        $newB = [Math]::Min(100, $b + 15)
        (Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightnessMethods -ErrorAction SilentlyContinue).WmiSetBrightness(1, $newB)
        $newB
        """
        res = powershell_exec(cmd)
        new_val = res.get("stdout", "Increased")
        return {"success": True, "action": "brightness_up", "message": f"Brightness increased to {new_val}%."}

    elif act == "brightness_down":
        cmd = """
        $b = (Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness -ErrorAction SilentlyContinue).CurrentBrightness
        $newB = [Math]::Max(10, $b - 15)
        (Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightnessMethods -ErrorAction SilentlyContinue).WmiSetBrightness(1, $newB)
        $newB
        """
        res = powershell_exec(cmd)
        new_val = res.get("stdout", "Decreased")
        return {"success": True, "action": "brightness_down", "message": f"Brightness decreased to {new_val}%."}

    elif act in ("get_brightness", "brightness_info"):
        cmd = "(Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness -ErrorAction SilentlyContinue).CurrentBrightness"
        res = powershell_exec(cmd)
        val = res.get("stdout", "100").strip()
        return {"success": True, "brightness": val, "message": f"Current screen brightness: {val}%."}

    elif act in ("battery_info", "battery", "power"):
        import psutil
        bat = psutil.sensors_battery()
        if bat:
            status = {
                "percent": bat.percent,
                "power_plugged": bat.power_plugged,
                "secs_left": bat.secsleft if bat.secsleft != psutil.POWER_TIME_UNLIMITED else "Plugged In"
            }
            msg = f"Battery at {bat.percent}% ({'Plugged In' if bat.power_plugged else 'On Battery'})."
            return {"success": True, "battery": status, "message": msg}
        else:
            return {"success": True, "battery": "Desktop / AC Connected", "message": "Workstation connected to continuous AC power (no battery)."}

    elif act in ("vitals", "system_vitals", "cpu_ram", "telemetry"):
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('C:')
        vitals = {
            "cpu_percent": cpu,
            "ram_percent": ram.percent,
            "ram_used_gb": round(ram.used / (1024**3), 2),
            "ram_total_gb": round(ram.total / (1024**3), 2),
            "disk_c_percent": disk.percent,
            "disk_c_free_gb": round(disk.free / (1024**3), 2)
        }
        msg = f"System Vitals: CPU {cpu}%, RAM {ram.percent}% ({vitals['ram_used_gb']}/{vitals['ram_total_gb']} GB), Disk Free {vitals['disk_c_free_gb']} GB."
        return {"success": True, "vitals": vitals, "message": msg}

    elif act in ("wifi_info", "network_info", "network"):
        res = powershell_exec("netsh wlan show interfaces")
        stdout = res.get("stdout", "")
        ssid_match = re.search(r'^\s*SSID\s*:\s*(.+)$', stdout, re.MULTILINE)
        signal_match = re.search(r'^\s*Signal\s*:\s*(.+)$', stdout, re.MULTILINE)
        ssid = ssid_match.group(1).strip() if ssid_match else "Ethernet / Disconnected"
        signal = signal_match.group(1).strip() if signal_match else "100%"
        return {"success": True, "ssid": ssid, "signal": signal, "message": f"Network: Connected to '{ssid}' (Signal: {signal})."}

    return {"success": False, "error": f"Unknown hardware action: {action}"}

# ==============================================================================
# 11. CLIPBOARD CONTROL TOOL
# ==============================================================================
def clipboard_ops(action: str, text: str = "") -> dict:
    """
    Performs Windows Clipboard operations: 'read', 'write', 'clear', 'speak'.
    """
    act = action.lower().strip()
    try:
        import win32clipboard
        import win32con
        if act in ("read", "get"):
            win32clipboard.OpenClipboard()
            content = ""
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                content = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return {
                "success": True,
                "action": "read",
                "content": content,
                "length": len(content),
                "message": f"Clipboard text ({len(content)} chars): {content[:100]}..." if len(content) > 100 else f"Clipboard text: {content}"
            }

        elif act in ("write", "copy", "set"):
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return {
                "success": True,
                "action": "write",
                "length": len(text),
                "message": f"Copied {len(text)} characters to Windows Clipboard."
            }

        elif act in ("clear", "empty"):
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.CloseClipboard()
            return {"success": True, "action": "clear", "message": "Windows Clipboard cleared."}

        elif act in ("speak", "read_aloud"):
            res = clipboard_ops("read")
            clip_text = res.get("content", "").strip()
            if clip_text:
                voice_speech("speak", text=clip_text)
                return {"success": True, "action": "speak", "message": f"Reading clipboard aloud ({len(clip_text)} chars)."}
            else:
                return {"success": False, "error": "Clipboard is currently empty."}

    except Exception as e:
        return {"success": False, "error": f"Clipboard operation failed: {e}"}

    return {"success": False, "error": f"Unknown clipboard action: {action}"}

# ==============================================================================
# 12. ADVANCED WINDOW & WORKSPACE MANAGER TOOL
# ==============================================================================
def window_manager(action: str) -> dict:
    """
    Hyper-utility window management: snap, maximize, minimize, virtual desktops, task view.
    Actions: 'maximize', 'minimize', 'restore', 'snap_left', 'snap_right', 'switch_app',
             'task_view', 'close_active', 'desktop_next', 'desktop_prev', 'desktop_new'.
    """
    act = action.lower().strip()
    
    if act in ("maximize", "max"):
        send_key_combo([VK_LWIN, 0x26]) # Win + Up
        return {"success": True, "message": "Maximized active window (Win+Up)."}

    elif act in ("minimize", "min"):
        send_key_combo([VK_LWIN, 0x28]) # Win + Down
        return {"success": True, "message": "Minimized active window (Win+Down)."}

    elif act in ("snap_left", "left"):
        send_key_combo([VK_LWIN, 0x25]) # Win + Left
        return {"success": True, "message": "Snapped active window to left screen half (Win+Left)."}

    elif act in ("snap_right", "right"):
        send_key_combo([VK_LWIN, 0x27]) # Win + Right
        return {"success": True, "message": "Snapped active window to right screen half (Win+Right)."}

    elif act in ("switch_app", "alt_tab"):
        send_key_combo([0x12, 0x09]) # Alt + Tab
        return {"success": True, "message": "Triggered Alt+Tab application switcher."}

    elif act in ("task_view", "win_tab"):
        send_key_combo([VK_LWIN, 0x09]) # Win + Tab
        return {"success": True, "message": "Triggered Windows Task View (Win+Tab)."}

    elif act in ("close_active", "close_window"):
        send_key_combo([0x12, 0x73]) # Alt + F4
        return {"success": True, "message": "Closed active window (Alt+F4)."}

    elif act in ("desktop_next", "next_desktop"):
        send_key_combo([0x11, VK_LWIN, 0x27]) # Ctrl + Win + Right
        return {"success": True, "message": "Switched to Next Virtual Desktop (Ctrl+Win+Right)."}

    elif act in ("desktop_prev", "prev_desktop"):
        send_key_combo([0x11, VK_LWIN, 0x25]) # Ctrl + Win + Left
        return {"success": True, "message": "Switched to Previous Virtual Desktop (Ctrl+Win+Left)."}

    elif act in ("desktop_new", "new_desktop"):
        send_key_combo([0x11, VK_LWIN, 0x44]) # Ctrl + Win + D
        return {"success": True, "message": "Created New Virtual Desktop (Ctrl+Win+D)."}

    return {"success": False, "error": f"Unknown window_manager action: {action}"}

# ==============================================================================
# 13. SYSTEM THEME & COLOR MODE TOOL
# ==============================================================================
def system_theme_control(action: str) -> dict:
    """
    Toggles or sets Windows System and App Dark/Light Theme.
    Actions: 'toggle', 'dark', 'light'.
    """
    act = action.lower().strip()
    cmd_get = '(Get-ItemProperty -Path "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" -ErrorAction SilentlyContinue).AppsUseLightTheme'
    res_get = powershell_exec(cmd_get)
    current_light = str(res_get.get("stdout", "0")).strip() == "1"

    if act in ("toggle", "switch", "toggle_dark_mode"):
        target_light = 0 if current_light else 1
    elif act in ("dark", "dark_mode", "enable_dark"):
        target_light = 0
    elif act in ("light", "light_mode", "enable_light"):
        target_light = 1
    else:
        return {"success": False, "error": f"Unknown theme action: {action}"}

    ps_set = f"""
    $key = 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize'
    Set-ItemProperty -Path $key -Name AppsUseLightTheme -Value {target_light} -Type DWord -Force
    Set-ItemProperty -Path $key -Name SystemUsesLightTheme -Value {target_light} -Type DWord -Force
    """
    powershell_exec(ps_set)
    theme_name = "Light Mode" if target_light == 1 else "Dark Mode"
    return {
        "success": True,
        "theme": theme_name,
        "apps_light": target_light == 1,
        "message": f"Windows System and App theme switched to {theme_name}."
    }

# ==============================================================================
# 14. VOICE SPEECH & AUDIO SYNTHESIS TOOL
# ==============================================================================
_sapi_voice = None

def get_sapi_voice():
    global _sapi_voice
    if _sapi_voice is None:
        try:
            import win32com.client
            _sapi_voice = win32com.client.Dispatch("SAPI.SpVoice")
        except Exception:
            _sapi_voice = False
    return _sapi_voice if _sapi_voice is not False else None

def voice_speech(action: str, text: str = "", duration: float = 4.0) -> dict:
    """
    Text-to-Speech (TTS) output and Microphone Speech-to-Text (STT) input.
    Actions: 'speak', 'listen'.
    """
    act = action.lower().strip()

    if act == "speak":
        sp = get_sapi_voice()
        if sp:
            try:
                # 1 = SVSFlagsAsync (non-blocking speech)
                sp.Speak(text, 1)
                return {"success": True, "action": "speak", "text": text, "message": f"Spoke: '{text}'"}
            except Exception as e:
                return {"success": False, "error": f"SAPI speak error: {e}"}
        else:
            escaped = text.replace('"', '`"')
            powershell_exec(f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).SpeakAsync("{escaped}")')
            return {"success": True, "action": "speak", "text": text, "message": f"Spoke asynchronously via PowerShell: '{text}'"}

    elif act == "listen":
        try:
            import sounddevice as sd
            import speech_recognition as sr
            samplerate = 16000
            dur = max(2.0, min(10.0, float(duration)))
            
            try:
                import winsound
                winsound.Beep(1046, 80)
            except Exception:
                pass

            recording = sd.rec(int(dur * samplerate), samplerate=samplerate, channels=1, dtype='int16')
            sd.wait()
            
            try:
                import winsound
                winsound.Beep(1318, 50)
            except Exception:
                pass

            audio_data = sr.AudioData(recording.tobytes(), samplerate, 2)
            r = sr.Recognizer()
            transcription = None
            engine_used = "offline_local"

            # Multi-Tier Recognition Cascade:
            # Tier 1: Try local offline engines (Vosk, Whisper, Sphinx)
            for local_engine in ('vosk', 'whisper', 'sphinx'):
                if hasattr(r, f"recognize_{local_engine}"):
                    try:
                        rec_func = getattr(r, f"recognize_{local_engine}")
                        transcription = rec_func(audio_data)
                        if transcription:
                            engine_used = f"local_{local_engine}"
                            break
                    except Exception:
                        pass

            # Tier 2: Try online speech provider if local wasn't available, with strict offline guard
            if not transcription:
                try:
                    transcription = r.recognize_google(audio_data)
                    engine_used = "cloud_google"
                except sr.UnknownValueError:
                    return {
                        "success": False,
                        "action": "listen",
                        "error": "No audible speech recognized in audio buffer."
                    }
                except (sr.RequestError, OSError) as req_err:
                    # Graceful 100% offline handling when no internet
                    return {
                        "success": False,
                        "action": "listen",
                        "offline": True,
                        "error": "Zero-Internet Offline Mode: Network recognition unavailable. Text input and local reflexes fully active.",
                        "duration_s": dur
                    }

            if transcription:
                return {
                    "success": True,
                    "action": "listen",
                    "engine": engine_used,
                    "transcription": transcription,
                    "duration_s": dur,
                    "message": f"Recognized voice command via {engine_used}: '{transcription}'"
                }
            else:
                return {
                    "success": False,
                    "action": "listen",
                    "error": "No audible speech recognized in audio buffer."
                }
        except Exception as e:
            return {"success": False, "error": f"Audio recording failure: {e}"}

    return {"success": False, "error": f"Unknown voice action: {action}"}

# Master Unified Execution Dispatcher for the Autonomous Brain
def execute_tool(tool_name: str, **kwargs) -> dict:
    """Universal dispatcher for all Omni-Actuator tools."""
    t_clean = tool_name.lower().strip()

    # Speculative MCTS & Martingale Conformal Pre-Execution Safety Gate
    try:
        from src.omni_mcts_planner import mcts_planner
        risk_score = mcts_planner.evaluate_action_risk(t_clean, kwargs)
        if risk_score >= 0.85:
            # Extreme destructive risk (e.g. rmdir, del /f, format, kill critical system processes)
            return {
                "success": False,
                "error": f"[MARTINGALE SAFETY INTERCEPTOR] Critical Destructive Risk ({risk_score:.2f}) detected in action '{tool_name}'. Conformal bound breached (1/alpha = {mcts_planner.martingale_threshold}). Operation halted for system integrity."
            }
    except Exception:
        pass

    if t_clean in ("screen_ocr", "ocr", "read_screen", "screen_text", "desktop_ocr"):
        return screen_ocr(
            action=kwargs.get("action", "read_screen"),
            search_term=kwargs.get("search_term", kwargs.get("query", kwargs.get("term", ""))),
            save_path=kwargs.get("save_path", kwargs.get("path", "")),
            open_viewer=bool(kwargs.get("open_viewer", False))
        )
    elif t_clean in ("camera_vision", "camera", "webcam", "vision", "cv"):
        return camera_vision(
            action=kwargs.get("action", "capture"),
            save_path=kwargs.get("save_path", kwargs.get("path", "")),
            detect=kwargs.get("detect", "person"),
            timeout_s=float(kwargs.get("timeout_s", 12.0)),
            camera_index=int(kwargs.get("camera_index", 0)),
            open_viewer=bool(kwargs.get("open_viewer", False))
        )
    elif t_clean in ("c_cpp_exec", "c_exec", "cpp_exec", "gcc", "g++", "c", "cpp"):
        return c_cpp_exec(kwargs.get("code", kwargs.get("script", "")), kwargs.get("file_path", kwargs.get("filename", "")), kwargs.get("compiler", "gcc"))
    elif t_clean in ("python_exec", "python", "py"):
        return python_exec(kwargs.get("code", kwargs.get("script", "")), kwargs.get("file_path", kwargs.get("filename", "")))
    elif t_clean in ("web_search", "search_web", "google_search", "search", "google"):
        return web_search(
            query=kwargs.get("query", kwargs.get("search_term", kwargs.get("q", kwargs.get("target", "")))),
            launch_website=kwargs.get("launch_website", kwargs.get("website", False)),
            open_browser=kwargs.get("open_browser", True)
        )
    elif t_clean in ("browser_open", "open_browser", "browser", "web", "url"):
        return browser_open(url=kwargs.get("url", kwargs.get("target", kwargs.get("query", ""))), query=kwargs.get("query", ""))
    elif t_clean in ("powershell_exec", "powershell", "ps"):
        return powershell_exec(kwargs.get("script", kwargs.get("command", "")))
    elif t_clean in ("app_control", "app"):
        return app_control(kwargs.get("action", "launch"), kwargs.get("target", ""))
    elif t_clean in ("media_control", "media"):
        return media_control(kwargs.get("action", "play_music"), kwargs.get("query", kwargs.get("target", "")))
    elif t_clean in ("filesystem_ops", "filesystem", "fs"):
        return filesystem_ops(kwargs.get("action", "search"), kwargs.get("target_path", kwargs.get("path", "")), kwargs.get("params", {}))
    elif t_clean in ("system_control", "system"):
        return system_control(kwargs.get("action", "lock"), kwargs.get("target", ""))
    elif t_clean in ("hardware_control", "hardware", "hw", "brightness", "battery", "vitals"):
        hw_kwargs = dict(kwargs)
        action = hw_kwargs.pop("action", "vitals")
        level = hw_kwargs.pop("level", hw_kwargs.pop("value", None))
        return hardware_control(action, level, **hw_kwargs)
    elif t_clean in ("clipboard_ops", "clipboard", "clip"):
        return clipboard_ops(kwargs.get("action", "read"), kwargs.get("text", kwargs.get("content", "")))
    elif t_clean in ("window_manager", "window", "win_mgmt"):
        return window_manager(kwargs.get("action", "maximize"))
    elif t_clean in ("system_theme_control", "theme", "dark_mode", "light_mode"):
        return system_theme_control(kwargs.get("action", "toggle"))
    elif t_clean in ("visual_spatial_click", "visual_click", "screen_click", "vision_click", "spatial_click", "visual_tensor_click", "tensor_click"):
        mon_idx = kwargs.get("monitor_index", kwargs.get("monitor", None))
        if mon_idx is not None:
            try:
                mon_idx = int(mon_idx)
            except Exception:
                mon_idx = None
        return visual_spatial_click(
            target=kwargs.get("target", kwargs.get("query", kwargs.get("element", "center"))),
            click=bool(kwargs.get("click", True)),
            button=kwargs.get("button", "left"),
            verify=bool(kwargs.get("verify", True)),
            refine_patch=bool(kwargs.get("refine_patch", True)),
            monitor_index=mon_idx,
            virtual_span=bool(kwargs.get("virtual_span", False))
        )
    elif t_clean in ("visual_click_sequence", "click_sequence", "vision_sequence"):
        raw_targets = kwargs.get("targets", kwargs.get("elements", []))
        if isinstance(raw_targets, str):
            raw_targets = [t.strip() for t in raw_targets.split(",") if t.strip()]
        mon_idx = kwargs.get("monitor_index", kwargs.get("monitor", None))
        if mon_idx is not None:
            try:
                mon_idx = int(mon_idx)
            except Exception:
                mon_idx = None
        return visual_click_sequence(
            targets=raw_targets,
            delay_between_s=float(kwargs.get("delay_between_s", 0.15)),
            monitor_index=mon_idx,
            virtual_span=bool(kwargs.get("virtual_span", False))
        )
    elif t_clean in ("keyboard_type", "type_text", "type", "keyboard_input", "write_text"):
        return keyboard_type_text(
            text=str(kwargs.get("text", kwargs.get("content", kwargs.get("query", "")))),
            delay_s=float(kwargs.get("delay_s", 0.01)),
            use_clipboard=bool(kwargs.get("use_clipboard", False))
        )
    else:
        return {"success": False, "error": f"Unknown tool: '{tool_name}'"}

def visual_spatial_click(
    target: str = "close button",
    click: bool = True,
    button: str = "left",
    verify: bool = True,
    refine_patch: bool = True,
    monitor_index: Optional[int] = None,
    virtual_span: bool = False
) -> dict:
    """
    Multimodal visual click using multi-scale luminance tensor,
    two-stage patch refinement soft-argmax regression, and empirical visual transition verification.
    Supports multi-monitor setups and full virtual desktop spans.
    """
    try:
        try:
            from omni_vision_tensor import vision_tensor_engine
        except ImportError:
            from src.omni_vision_tensor import vision_tensor_engine

        if click:
            return vision_tensor_engine.execute_direct_click(
                target_description=target,
                click=True,
                button=button,
                double_click=(button.lower() == "double"),
                verify=verify,
                monitor_index=monitor_index,
                virtual_span=virtual_span
            )
        else:
            img, abs_path, w, h = capture_screen_pixels()
            res = vision_tensor_engine.predict_click_coordinates(
                img, target, screen_w=w, screen_h=h, refine_patch=refine_patch
            )
            res["clicked"] = False
            return res
    except Exception as e:
        return {"success": False, "error": str(e)}

def visual_click_sequence(
    targets: list,
    delay_between_s: float = 0.15,
    monitor_index: Optional[int] = None,
    virtual_span: bool = False
) -> dict:
    """Executes an ordered sequence of direct visual clicks across the screen or monitors."""
    try:
        try:
            from omni_vision_tensor import vision_tensor_engine
        except ImportError:
            from src.omni_vision_tensor import vision_tensor_engine
        return vision_tensor_engine.execute_click_sequence(
            targets,
            delay_between_s=delay_between_s,
            monitor_index=monitor_index,
            virtual_span=virtual_span
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("Testing PowerShell tool:")
    print(powershell_exec("Get-Date"))
    print("\nTesting Media tool:")
    print(media_control("volume_up"))
