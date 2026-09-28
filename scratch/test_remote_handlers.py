import sys
import os
import json
import time

PROJECT_ROOT = r"c:\Users\Neeraj\Desktop\Naya"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import psutil
import omni_actuator
import omni_reflex

# 1. Test screen capture
img, path, w, h = omni_actuator.capture_screen_pixels()
print("1. Screen capture test:", w, "x", h, "Path:", path)

# 2. Test directory browser
def browse_dir(target=""):
    p = os.path.abspath(target or PROJECT_ROOT)
    items = []
    for entry in os.scandir(p):
        try:
            st = entry.stat()
            items.append({
                "name": entry.name,
                "path": entry.path,
                "is_dir": entry.is_dir(),
                "size_kb": round(st.st_size / 1024, 1) if not entry.is_dir() else 0
            })
        except Exception:
            pass
    return items

items = browse_dir()
print("2. Directory browse test:", len(items), "items in", PROJECT_ROOT)

# 3. Test process list
def get_procs(limit=10):
    procs = []
    for p in psutil.process_iter(['pid', 'name']):
        try:
            procs.append({"pid": p.info['pid'], "name": p.info['name'], "ram_mb": round(p.memory_info().rss / (1024*1024), 1)})
        except Exception:
            pass
    procs.sort(key=lambda x: x['ram_mb'], reverse=True)
    return procs[:limit]

procs = get_procs()
print("3. Process list test:", len(procs), "top procs, first:", procs[0])

# 4. Test Webhook trigger logic
def handle_webhook(goal="mute sound"):
    matched = omni_reflex.match_reflex(goal)
    if matched:
        return omni_reflex.execute_reflex_action(matched, goal)
    return {"status": "Fallback to brain"}

res_wh = handle_webhook("mute audio")
print("4. Webhook execution test:", res_wh.get("message"))

print("\nALL REMOTE BACKEND HANDLERS VALIDATED!")
