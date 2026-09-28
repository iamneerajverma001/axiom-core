import psutil

for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmd = ' '.join(p.info.get('cmdline') or [])
        if 'launch_floating' in cmd or 'omni_floating' in cmd:
            print(f"MATCH: PID={p.info['pid']} cmd={cmd}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
