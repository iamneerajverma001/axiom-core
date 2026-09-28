import sys
sys.path.insert(0, 'src')
import omni_sensor
wins = omni_sensor.get_visible_windows(limit=25)
print("Visible windows currently:")
for w in wins:
    if any(k in w['title'].lower() or k in w['process'].lower() for k in ['cmd', 'prompt', 'calc', 'python', 'terminal']):
        print(w)
