"""
Axiom Vision-Tensor: Fast Screen & Window Capture Engine
Provides high-speed screen acquisition using Win32 GDI BitBlt with PIL ImageGrab fallback.
"""

import sys
from typing import Optional, Tuple
from PIL import Image

def capture_screen_gdi() -> Image.Image:
    """Captures entire primary desktop screen."""
    if sys.platform == 'win32':
        try:
            import win32gui
            import win32ui
            import win32con

            hdesktop = win32gui.GetDesktopWindow()
            width = win32gui.GetSystemMetrics(win32con.SM_CXSCREEN)
            height = win32gui.GetSystemMetrics(win32con.SM_CYSCREEN)

            desktop_dc = win32gui.GetWindowDC(hdesktop)
            img_dc = win32ui.CreateDCFromHandle(desktop_dc)
            mem_dc = img_dc.CreateCompatibleDC()

            screenshot = win32ui.CreateBitmap()
            screenshot.CreateCompatibleBitmap(img_dc, width, height)
            mem_dc.SelectObject(screenshot)

            mem_dc.BitBlt((0, 0), (width, height), img_dc, (0, 0), win32con.SRCCOPY)

            bmpinfo = screenshot.GetInfo()
            bmpstr = screenshot.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )

            mem_dc.DeleteDC()
            img_dc.DeleteDC()
            win32gui.ReleaseDC(hdesktop, desktop_dc)
            win32gui.DeleteObject(screenshot.GetHandle())
            return img
        except Exception:
            pass

    # Fallback to PIL ImageGrab
    try:
        from PIL import ImageGrab
        return ImageGrab.grab()
    except Exception:
        pass

    # Safe headless fallback canvas (1366x768)
    return Image.new("RGB", (1366, 768), color=(30, 30, 30))

def capture_active_window_gdi() -> Tuple[Image.Image, Tuple[int, int, int, int]]:
    """Captures active foreground window and returns (image, rect)."""
    if sys.platform == 'win32':
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                from PIL import ImageGrab
                # Ensure valid bbox
                if rect[2] > rect[0] and rect[3] > rect[1]:
                    img = ImageGrab.grab(bbox=rect)
                    return img, rect
        except Exception:
            pass

    full = capture_screen_gdi()
    return full, (0, 0, full.width, full.height)
