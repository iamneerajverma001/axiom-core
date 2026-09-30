"""
Axiom Vision-Tensor: Fast Screen & Window Capture Engine
Provides high-speed screen acquisition using Win32 GDI BitBlt with PIL ImageGrab fallback.
Supports DPI awareness, multi-monitor enumeration, and multi-display virtual desktop spans.
"""

import sys
import ctypes
from typing import Optional, Tuple, List, Dict, Any
from PIL import Image

try:
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    gdi32 = ctypes.windll.gdi32
except Exception:
    user32 = None
    kernel32 = None
    gdi32 = None

def init_dpi_awareness():
    """Activates Per-Monitor V2 DPI awareness."""
    if sys.platform == 'win32' and user32:
        try:
            user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except Exception:
            try:
                user32.SetProcessDPIAware()
            except Exception:
                pass

init_dpi_awareness()

class _RECT(ctypes.Structure):
    _fields_ = [
        ('left', wintypes.LONG if wintypes else ctypes.c_long),
        ('top', wintypes.LONG if wintypes else ctypes.c_long),
        ('right', wintypes.LONG if wintypes else ctypes.c_long),
        ('bottom', wintypes.LONG if wintypes else ctypes.c_long)
    ]

class _MONITORINFOEX(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD if wintypes else ctypes.c_uint32),
        ('rcMonitor', _RECT),
        ('rcWork', _RECT),
        ('dwFlags', wintypes.DWORD if wintypes else ctypes.c_uint32),
        ('szDevice', ctypes.c_wchar * 32)
    ]

def get_monitors_info() -> List[Dict[str, Any]]:
    """
    Enumerates all active physical and virtual display monitors.
    Returns list of dicts with device name, bounding rect, resolution, and is_primary flag.
    """
    monitors: List[Dict[str, Any]] = []
    if sys.platform == 'win32' and user32:
        try:
            def _enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
                mi = _MONITORINFOEX()
                mi.cbSize = ctypes.sizeof(_MONITORINFOEX)
                if user32.GetMonitorInfoW(hMonitor, ctypes.byref(mi)):
                    l = int(mi.rcMonitor.left)
                    t = int(mi.rcMonitor.top)
                    r = int(mi.rcMonitor.right)
                    b = int(mi.rcMonitor.bottom)
                    is_prim = bool(mi.dwFlags & 1)
                    monitors.append({
                        "index": len(monitors),
                        "device": str(mi.szDevice),
                        "left": l,
                        "top": t,
                        "right": r,
                        "bottom": b,
                        "width": max(1, r - l),
                        "height": max(1, b - t),
                        "is_primary": is_prim
                    })
                return 1

            _MONITORENUMPROC = ctypes.WINFUNCTYPE(
                ctypes.c_int,
                wintypes.HMONITOR if wintypes else ctypes.c_void_p,
                wintypes.HDC if wintypes else ctypes.c_void_p,
                ctypes.POINTER(_RECT),
                wintypes.LPARAM if wintypes else ctypes.c_long
            )
            user32.EnumDisplayMonitors(None, None, _MONITORENUMPROC(_enum_proc), 0)
        except Exception:
            pass

    if not monitors:
        w = user32.GetSystemMetrics(0) if user32 else 1366
        h = user32.GetSystemMetrics(1) if user32 else 768
        monitors.append({
            "index": 0,
            "device": "\\\\.\\DISPLAY1",
            "left": 0,
            "top": 0,
            "right": w,
            "bottom": h,
            "width": w,
            "height": h,
            "is_primary": True
        })
    return monitors

def capture_screen_gdi(
    monitor_index: Optional[int] = None,
    virtual_span: bool = False,
    include_offset: bool = False
) -> Any:
    """
    Captures desktop screen via Win32 GDI BitBlt.
    Supports primary screen, specific monitor index, or complete virtual multi-monitor desktop.
    """
    if sys.platform == 'win32' and user32 and gdi32:
        try:
            try:
                hwinsta = user32.OpenWindowStationW("WinSta0", False, 0x037F)
                if hwinsta:
                    user32.SetProcessWindowStation(hwinsta)
                hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
                if hdesk:
                    user32.SetThreadDesktop(hdesk)
            except Exception:
                pass

            if virtual_span:
                x = user32.GetSystemMetrics(76) # SM_XVIRTUALSCREEN
                y = user32.GetSystemMetrics(77) # SM_YVIRTUALSCREEN
                w = user32.GetSystemMetrics(78) # SM_CXVIRTUALSCREEN
                h = user32.GetSystemMetrics(79) # SM_CYVIRTUALSCREEN
            elif monitor_index is not None and monitor_index >= 0:
                monitors = get_monitors_info()
                target_mon = next((m for m in monitors if m["index"] == monitor_index), monitors[0])
                x = target_mon["left"]
                y = target_mon["top"]
                w = target_mon["width"]
                h = target_mon["height"]
            else:
                x = 0
                y = 0
                w = user32.GetSystemMetrics(0) # SM_CXSCREEN
                h = user32.GetSystemMetrics(1) # SM_CYSCREEN

            hdc_screen = user32.GetDC(0)
            hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
            hbm = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
            old_bm = gdi32.SelectObject(hdc_mem, hbm)
            gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, x, y, 0x00CC0020)
            gdi32.SelectObject(hdc_mem, old_bm)

            class _BITMAPINFOHEADER(ctypes.Structure):
                _fields_ = [
                    ('biSize', ctypes.c_uint32),
                    ('biWidth', ctypes.c_int32),
                    ('biHeight', ctypes.c_int32),
                    ('biPlanes', ctypes.c_uint16),
                    ('biBitCount', ctypes.c_uint16),
                    ('biCompression', ctypes.c_uint32),
                    ('biSizeImage', ctypes.c_uint32),
                    ('biXPelsPerMeter', ctypes.c_int32),
                    ('biYPelsPerMeter', ctypes.c_int32),
                    ('biClrUsed', ctypes.c_uint32),
                    ('biClrImportant', ctypes.c_uint32)
                ]

            header = _BITMAPINFOHEADER()
            header.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
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

            img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1).convert('RGB')
            if include_offset:
                return img, w, h, x, y
            return img
        except Exception:
            pass

    # Fallback to PIL ImageGrab
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        if include_offset:
            return img, img.width, img.height, 0, 0
        return img
    except Exception:
        fallback = Image.new("RGB", (1366, 768), color=(30, 30, 30))
        if include_offset:
            return fallback, 1366, 768, 0, 0
        return fallback

def capture_active_window_gdi() -> Tuple[Image.Image, Tuple[int, int, int, int]]:
    """Captures active foreground window and returns (image, rect)."""
    if sys.platform == 'win32':
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                from PIL import ImageGrab
                if rect[2] > rect[0] and rect[3] > rect[1]:
                    img = ImageGrab.grab(bbox=rect)
                    return img, rect
        except Exception:
            pass

    full = capture_screen_gdi()
    return full, (0, 0, full.width, full.height)
