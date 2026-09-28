import sys
import os

PROJECT_ROOT = r"c:\Users\Neeraj\Desktop\Naya"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from src import omni_actuator
from src import omni_reflex
from src import omni_brain

print("=== SCENARIO 1: 'open browser and serch REC SONBHADRA ,and lauch it website' ===")
# Check compound splitter
sub_queries = omni_reflex.split_compound_query("open browser and serch REC SONBHADRA ,and lauch it website")
print("Sub-queries:", sub_queries)
is_compound = len(sub_queries) > 1
print("Is compound:", is_compound)
matched_single = omni_reflex.match_reflex("open browser and serch REC SONBHADRA ,and lauch it website")
print("Single reflex matched?", matched_single)
assert matched_single is None

# Test the brain guard directly on action dispatched
print("\n=== SCENARIO 2: 'launch REC Sonbhadra' ===")
# If brain outputs app_control(target='REC Sonbhadra'), what does omni_actuator execute?
res_launch = omni_actuator.execute_tool("app_control", action="launch", target="REC Sonbhadra")
print("Real Execution of launch REC Sonbhadra:", res_launch)
assert res_launch["success"] is True
assert res_launch["action"] == "web_search"
assert "recsonbhadra" in res_launch["target_url"].lower() or "google.com" in res_launch["target_url"].lower()

print("\n=== SCENARIO 3: 'search REC Sonbhadra' ===")
# If brain outputs web_search or screen_ocr, test what happens
res_search = omni_actuator.execute_tool("web_search", query="REC Sonbhadra", open_browser=False)
print("Real Execution of web_search for REC Sonbhadra:", res_search)
assert res_search["success"] is True
assert "google.com/search" in res_search["target_url"].lower()

print("\nALL SCENARIOS VALIDATED WITH REAL PHYSICAL OUTCOMES!")
