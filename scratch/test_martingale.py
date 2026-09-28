import sys
import os

PROJECT_ROOT = r"c:\Users\Neeraj\Desktop\Naya"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import omni_reflex

chain = omni_reflex.match_compound_reflex("mute sound and show desktop")
print("Chain:", chain)
conformal = omni_reflex.compute_trajectory_conformal_risk(chain)
print("Conformal:", conformal)
res = omni_reflex.execute_compound_reflex(chain, "mute sound and show desktop")
print("Res:", res)
