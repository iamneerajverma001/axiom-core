"""
Axiom Omni-Sensor: Omnipresent Windows Perception & Telemetry Engine
Captures active windows, media sessions, audio levels, processes, ports, and system state.
"""

import os
import sys
import ctypes
import ctypes.wintypes
import psutil
import subprocess
import json
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]

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

def get_foreground_window_info() -> dict:
    """Returns details of the currently focused foreground window on user's real desktop."""
    attach_to_default_desktop()
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return {"hwnd": 0, "title": "None", "process": "None", "pid": 0, "rect": {}}
    
    length = user32.GetWindowTextLengthW(hwnd)
    title = ""
    if length > 0:
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value.strip()

    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    proc_name = "unknown"
    if pid.value:
        try:
            proc_name = psutil.Process(pid.value).name()
        except Exception:
            pass

    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))

    return {
        "hwnd": hwnd,
        "title": title or "Untitled Window",
        "process": proc_name,
        "pid": pid.value,
        "rect": {
            "x": rect.left,
            "y": rect.top,
            "width": max(0, rect.right - rect.left),
            "height": max(0, rect.bottom - rect.top)
        }
    }

def get_visible_windows(limit: int = 15) -> list:
    """Enumerates open visible top-level windows on user's interactive desktop."""
    windows = []
    h_def = attach_to_default_desktop()

    def enum_cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()
                # Filter out shell infrastructure windows
                if title and title not in ("Program Manager", "Settings", "Windows Shell Experience Host", "Taskbar", "Default IME", "MSCTFIME UI"):
                    pid = ctypes.wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    proc_name = "unknown"
                    if pid.value:
                        try:
                            proc_name = psutil.Process(pid.value).name()
                        except Exception:
                            pass
                    windows.append({
                        "hwnd": hwnd,
                        "title": title,
                        "process": proc_name,
                        "pid": pid.value
                    })
        return True

    cb_func = WNDENUMPROC(enum_cb)
    if h_def:
        user32.EnumDesktopWindows(h_def, cb_func, 0)
    else:
        user32.EnumWindows(cb_func, 0)
    return windows[:limit]

def get_media_session_status() -> dict:
    """
    Inspects Windows Global Media Transport sessions to determine what is playing,
    which app is active, and track metadata.
    """
    ps_cmd = (
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        "Add-Type -AssemblyName System.Runtime.WindowsRuntime; "
        "$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | "
        "  Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]; "
        "Function Await($WinRtTask, $ResultType) { "
        "  $asTask = $asTaskGeneric.MakeGenericMethod($ResultType); "
        "  $netTask = $asTask.Invoke($null, @($WinRtTask)); "
        "  $netTask.Wait(1200) | Out-Null; "
        "  $netTask.Result "
        "}; "
        "[Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media, ContentType=WindowsRuntime] | Out-Null; "
        "$asyncOp = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync(); "
        "$mgr = Await $asyncOp ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]); "
        "$curr = $mgr.GetCurrentSession(); "
        "if ($curr) { "
        "  $infoAsync = $curr.TryGetMediaPropertiesAsync(); "
        "  $props = Await $infoAsync ([Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties]); "
        "  $playback = $curr.GetPlaybackInfo(); "
        "  @{ "
        "    app_id = $curr.SourceAppUserModelId; "
        "    title = $props.Title; "
        "    artist = $props.Artist; "
        "    status = $playback.PlaybackStatus.ToString(); "
        "    has_active_session = $true "
        "  } | ConvertTo-Json -Compress "
        "} else { "
        "  @{ has_active_session = $false } | ConvertTo-Json -Compress "
        "}"
    )
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=3
        )
        if proc.returncode == 0 and proc.stdout.strip():
            raw = proc.stdout.strip()
            # Find JSON
            s = raw.find('{')
            e = raw.rfind('}')
            if s != -1 and e != -1:
                return json.loads(raw[s:e+1])
    except Exception:
        pass

    # Fallback heuristic: check if known players are running
    spotify_running = any("spotify" in p.name().lower() for p in psutil.process_iter(['name']))
    vlc_running = any("vlc" in p.name().lower() for p in psutil.process_iter(['name']))
    chrome_running = any("chrome" in p.name().lower() for p in psutil.process_iter(['name']))
    
    return {
        "has_active_session": False,
        "spotify_running": spotify_running,
        "vlc_running": vlc_running,
        "chrome_running": chrome_running,
        "status": "Unknown"
    }

def get_audio_volume_level() -> dict:
    """Reads current Windows master audio volume percentage and mute state."""
    ps_cmd = (
        "try { "
        "  $audio = Get-AudioDevice -PlaybackVolume -ErrorAction SilentlyContinue; "
        "  if ($audio) { @{ volume = $audio; mute = $false } | ConvertTo-Json -Compress; return } "
        "} catch {}; "
        "@{ volume = -1; mute = $false } | ConvertTo-Json -Compress"
    )
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=2
        )
        if proc.returncode == 0 and proc.stdout.strip():
            raw = proc.stdout.strip()
            s = raw.find('{')
            e = raw.rfind('}')
            if s != -1 and e != -1:
                return json.loads(raw[s:e+1])
    except Exception:
        pass
    return {"volume": "Available via Win32", "mute": False}

def get_active_listening_ports() -> list:
    """Discovers all TCP ports currently listening on this PC."""
    ports = set()
    try:
        for conn in psutil.net_connections(kind='tcp'):
            if conn.status == psutil.CONN_LISTEN and conn.laddr:
                ports.add(conn.laddr.port)
    except Exception:
        pass
    return sorted(list(ports))

def get_system_hardware_telemetry() -> dict:
    """Captures CPU, RAM, Battery, and Display resolution metrics."""
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    battery = psutil.sensors_battery()
    
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)

    return {
        "cpu_percent": cpu,
        "ram_used_gb": round(mem.used / (1024**3), 2),
        "ram_total_gb": round(mem.total / (1024**3), 2),
        "ram_percent": mem.percent,
        "battery_percent": round(battery.percent, 1) if battery else 100,
        "is_charging": battery.power_plugged if battery else True,
        "screen_resolution": f"{screen_w}x{screen_h}"
    }

def get_clipboard_text(max_len: int = 500) -> str:
    """Safely retrieves current text on the Windows clipboard."""
    try:
        CF_UNICODETEXT = 13
        user32.OpenClipboard.argtypes = [ctypes.wintypes.HWND]
        user32.OpenClipboard.restype = ctypes.wintypes.BOOL
        user32.GetClipboardData.argtypes = [ctypes.wintypes.UINT]
        user32.GetClipboardData.restype = ctypes.wintypes.HANDLE
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = ctypes.wintypes.BOOL
        kernel32.GlobalLock.argtypes = [ctypes.wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = ctypes.c_wchar_p
        kernel32.GlobalUnlock.argtypes = [ctypes.wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = ctypes.wintypes.BOOL

        if user32.OpenClipboard(0):
            h_data = user32.GetClipboardData(CF_UNICODETEXT)
            if h_data:
                ptr = kernel32.GlobalLock(h_data)
                text = str(ptr) if ptr else ""
                kernel32.GlobalUnlock(h_data)
                user32.CloseClipboard()
                return text[:max_len]
            user32.CloseClipboard()
    except Exception:
        pass
    return ""

def get_visible_ui_labels(max_elements: int = 12) -> List[str]:
    """Scans desktop with native OCR and returns prominent visible text labels."""
    try:
        try:
            from omni_actuator import screen_ocr
        except ImportError:
            from src.omni_actuator import screen_ocr
        res = screen_ocr(action="read_screen")
        if res.get("success") and res.get("elements"):
            seen = set()
            labels = []
            for el in res["elements"]:
                txt = el["text"].strip()
                if len(txt) >= 2 and txt.lower() not in seen:
                    seen.add(txt.lower())
                    labels.append(txt)
                if len(labels) >= max_elements:
                    break
            return labels
    except Exception:
        pass
    return []

def get_ui_element_ledger(max_elements: int = 15) -> Tuple[List[str], str]:
    """
    Scans screen with native UI contour & WinOCR extractor (Native OmniParser).
    Returns prominent visible text labels and compact Set-of-Marks ledger lines.
    """
    labels = []
    ledger_str = ""
    try:
        try:
            from omni_vision_tensor import vision_tensor_engine, capture_screen_fast
        except ImportError:
            from src.omni_vision_tensor import vision_tensor_engine, capture_screen_fast

        img, w, h = capture_screen_fast()
        elements = vision_tensor_engine.detect_ui_elements(img, screen_w=w, screen_h=h)
        if elements:
            seen = set()
            for el in elements:
                t = el.get("text", "").strip()
                if t and len(t) >= 2 and t.lower() not in seen:
                    seen.add(t.lower())
                    labels.append(t)
                if len(labels) >= max_elements:
                    break

            lines = []
            for el in elements[:max_elements]:
                txt = el.get("text")
                typ = el.get("type", "elem").upper()
                role = el.get("role", "")
                desc = f"'{txt}'" if txt else (f"role={role}" if role else "")
                lines.append(f"[{el['id']}] {typ} {desc} at ({el['cx']}, {el['cy']})")
            if lines:
                ledger_str = "- Screen UI Elements (Set-of-Marks):\n  " + "\n  ".join(lines)
    except Exception:
        pass
    return labels, ledger_str

def get_comprehensive_pc_state(include_visual_labels: bool = True) -> dict:
    """
    Returns an omnipresent 360-degree snapshot of the entire PC environment,
    including live on-screen text elements, ready to feed directly into the agent's context.
    """
    fg = get_foreground_window_info()
    windows = get_visible_windows(8)
    media = get_media_session_status()
    telemetry = get_system_hardware_telemetry()
    ports = get_active_listening_ports()
    clip = get_clipboard_text(200)

    ui_labels, som_ledger = get_ui_element_ledger() if include_visual_labels else ([], "")
    if not ui_labels and include_visual_labels:
        ui_labels = get_visible_ui_labels()

    # Format human-readable perception string for LLM grounding
    win_list_str = ", ".join([f"'{w['title']}' ({w['process']})" for w in windows]) or "No active user windows"
    
    media_str = "No active media session"
    if media.get("has_active_session"):
        media_str = f"Playing '{media.get('title', 'Unknown')}' by '{media.get('artist', 'Unknown')}' via {media.get('app_id', 'App')} (Status: {media.get('status', 'Playing')})"
    elif media.get("spotify_running"):
        media_str = "Spotify is running (idle or background)"
    elif media.get("chrome_running"):
        media_str = "Chrome is running (browser active)"

    clip_str = f"- Clipboard Preview: '{clip}'" if clip else "- Clipboard: (Empty)"
    ui_str = f"- Visible Screen UI Text: {', '.join([repr(l) for l in ui_labels])}\n" if ui_labels else ""
    som_str = f"{som_ledger}\n" if som_ledger else ""

    prompt_context = (
        f"[CURRENT PC PERCEPTION SNAPSHOT]\n"
        f"- Foreground Active Window: '{fg['title']}' (Process: {fg['process']}, PID: {fg['pid']})\n"
        f"- Visible Windows: {win_list_str}\n"
        f"{ui_str}"
        f"{som_str}"
        f"- Media Playback State: {media_str}\n"
        f"- System Health: CPU {telemetry['cpu_percent']}%, RAM {telemetry['ram_used_gb']}/{telemetry['ram_total_gb']} GB ({telemetry['ram_percent']}%), Battery {telemetry['battery_percent']}% ({'AC Charging' if telemetry['is_charging'] else 'Battery'})\n"
        f"- Active Listening Ports: {ports[:10]}\n"
        f"- Display Resolution: {telemetry['screen_resolution']}\n"
        f"{clip_str}"
    )

    return {
        "foreground_window": fg,
        "visible_windows": windows,
        "visible_ui_labels": ui_labels,
        "media_session": media,
        "telemetry": telemetry,
        "active_ports": ports,
        "clipboard_preview": clip,
        "prompt_context": prompt_context
    }

if __name__ == "__main__":
    print(get_comprehensive_pc_state()["prompt_context"])
