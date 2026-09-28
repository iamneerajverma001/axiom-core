import sys
import os

PROJECT_ROOT = r"c:\Users\Neeraj\Desktop\Naya"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from src import omni_brain

print("Testing ReAct Brain on 'open browser and serch REC SONBHADRA ,and lauch it website'...")
for step in omni_brain.run_autonomous_loop(
    user_goal="open browser and serch REC SONBHADRA ,and lauch it website",
    provider="ollama",
    model="qwen2.5-coder:1.5b",
    max_steps=3
):
    print("STEP EVENT:", step)
