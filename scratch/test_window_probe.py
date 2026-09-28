import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

count = [0]
def cb(hwnd, lp):
    if user32.IsWindowVisible(hwnd):
        l = user32.GetWindowTextLengthW(hwnd)
        if l > 0:
            b = ctypes.create_unicode_buffer(l + 1)
            user32.GetWindowTextW(hwnd, b, l + 1)
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if count[0] < 8:
                print(f"HWND: {hwnd:#010x}, PID: {pid.value}, Title: {b.value[:60]}")
                count[0] += 1
    return True

proc = WNDENUMPROC(cb)
user32.EnumWindows(proc, 0)

