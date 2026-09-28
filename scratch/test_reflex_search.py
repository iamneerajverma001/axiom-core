import sys
import os
import time

PROJECT_ROOT = r"c:\Users\Neeraj\Desktop\Naya"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from src import omni_reflex
from src import omni_actuator

print("Testing direct match on 'search REC Sonbhadra'...")
m1 = omni_reflex.match_reflex("search REC Sonbhadra")
print("Match 1:", m1)

print("\nTesting compound match on 'open browser and serch REC SONBHADRA ,and lauch it website'...")
m2 = omni_reflex.match_compound_reflex("open browser and serch REC SONBHADRA ,and lauch it website")
print("Match 2 (Compound):", m2)

print("\nExecuting compound reflex plan...")
t0 = time.time()
exec_res = omni_reflex.execute_compound_reflex(m2, "open browser and serch REC SONBHADRA ,and lauch it website")
elapsed_ms = (time.time() - t0) * 1000.0
print("Execution Result:", exec_res)
print(f"Elapsed Time: {elapsed_ms:.2f} ms")

