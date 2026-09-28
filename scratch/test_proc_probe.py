import psutil
import time

t0 = time.time()
recent_procs = []
for p in psutil.process_iter(['name', 'pid', 'create_time']):
    try:
        if (t0 - p.info['create_time']) < 120.0:  # Created in last 2 mins
            recent_procs.append(p.info)
    except Exception:
        pass

print(f"Total recent processes (<2m): {len(recent_procs)}")
for p in recent_procs[-10:]:
    print(p)
