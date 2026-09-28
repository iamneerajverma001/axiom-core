import sys
import os

PROJECT_ROOT = r"c:\Users\Neeraj\Desktop\Naya"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

import omni_reflex

q = "open browser and serch REC SONBHADRA ,and lauch it website"
parts = omni_reflex.split_compound_query(q)
print("Parts:", parts)
matched = omni_reflex.match_reflex(q, threshold=0.75)
print("Matched:", matched)
assert matched is None, f"Matched should be None but got: {matched}"
print("ASSERTION PASSED: Matched is None!")
