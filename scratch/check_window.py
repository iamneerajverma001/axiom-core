import win32gui
import win32process
import psutil

target_pids = []
for p in psutil.process_iter(['pid', 'cmdline']):
    cmd = ' '.join(p.info.get('cmdline') or [])
    if 'launch_floating' in cmd:
        target_pids.append(p.info['pid'])

print(f"Target PIDs: {target_pids}")

def enum_cb(hwnd, extra):
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    if pid in target_pids:
        title = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        vis = win32gui.IsWindowVisible(hwnd)
        print(f"MATCH HWND {hwnd}: PID={pid} Title='{title}' Class='{cls}' Rect={rect} Visible={vis}")

win32gui.EnumWindows(enum_cb, None)
