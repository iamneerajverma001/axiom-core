import sys
import os

PROJECT_ROOT = r"c:\Users\Neeraj\Desktop\Naya"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from src import omni_actuator
from src import omni_reflex

print("--- 1. Testing split_compound_query ---")
q1 = "open browser and serch REC SONBHADRA ,and lauch it website"
parts = omni_reflex.split_compound_query(q1)
print(f"Query: '{q1}'")
print(f"Parts: {parts}")
assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}"

print("\n--- 2. Testing web_search URL resolution ---")
res = omni_actuator.web_search("REC Sonbhadra", launch_website=True, open_browser=False)
print("web_search launch_website=True result:", res)
assert res["success"] is True
assert "recsonbhadra" in res["target_url"].lower() or "google.com" in res["target_url"].lower()

res2 = omni_actuator.web_search("REC Sonbhadra", launch_website=False, open_browser=False)
print("web_search search result:", res2)
assert res2["success"] is True
assert "google.com/search" in res2["target_url"].lower()

print("\n--- 3. Testing app_control fallback for non-apps ---")
res3 = omni_actuator.app_control("launch", target="REC Sonbhadra")
print("app_control launch REC Sonbhadra result:", res3)
assert res3["success"] is True
assert res3["action"] == "web_search"

print("\n--- 4. Testing match_reflex does NOT falsely match 'open browser' for compound queries ---")
m = omni_reflex.match_reflex(q1, threshold=0.75)
print(f"match_reflex on compound query: {m}")
assert m is None, "match_reflex should return None for compound query with unconsumed tokens!"

print("\nALL VERIFICATIONS PASSED!")
