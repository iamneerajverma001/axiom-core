import subprocess
import time
import sys
sys.path.insert(0, 'src')
import omni_sensor

CREATE_NEW_CONSOLE = 0x00000010
subprocess.Popen('cmd.exe /k "title Axiom Terminal && echo Welcome to Axiom Native Terminal"', creationflags=CREATE_NEW_CONSOLE)
time.sleep(1.0)
wins = omni_sensor.get_visible_windows(limit=30)
for w in wins:
    if any(k in w['title'].lower() or k in w['process'].lower() for k in ['cmd', 'terminal', 'conhost', 'console', 'axiom']):
        print("Found window:", w)
