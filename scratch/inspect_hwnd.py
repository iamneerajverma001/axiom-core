import win32gui
import win32process

def enum_cb(hwnd, extra):
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    title = win32gui.GetWindowText(hwnd)
    cls = win32gui.GetClassName(hwnd)
    if "Axiom" in title or "Qt5QWindow" in cls:
        rect = win32gui.GetWindowRect(hwnd)
        vis = win32gui.IsWindowVisible(hwnd)
        print(f"FOUND: HWND={hwnd} PID={pid} Title='{title}' Class='{cls}' Rect={rect} Visible={vis}")

win32gui.EnumWindows(enum_cb, None)
