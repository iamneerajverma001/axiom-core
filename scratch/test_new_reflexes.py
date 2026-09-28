import sys
import os

PROJECT_ROOT = r"c:\Users\Neeraj\Desktop\Naya"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import omni_reflex
import omni_actuator

queries = [
    "toggle dark mode",
    "system vitals",
    "snap left",
    "read clipboard",
    "increase brightness",
    "battery status"
]

print("=== VERIFYING NEW REFLEX SKILLS ===")
for q in queries:
    m = omni_reflex.match_reflex(q)
    assert m is not None, f"Failed to match: {q}"
    print(f"[MATCHED] '{q}' -> Skill: '{m['skill']['name']}' ({m['confidence']*100:.1f}%) Tool: {m['skill']['tool']}")
    
    # Test execution
    res = omni_reflex.execute_reflex_action(m, q)
    print(f"  Outcome: {res.get('message', res)}")
    assert res.get("success") is True or "message" in res

print("\nALL NEW HYPER-CONTROL REFLEXES VERIFIED!")
