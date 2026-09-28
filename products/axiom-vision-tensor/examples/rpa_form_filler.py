"""
Axiom Vision-Tensor RPA Example: Zero-DOM Form Automation
Navigates and submits web or desktop forms without CSS selectors, XPath, or slow OCR.
"""

import time
import sys
import os

pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from axiom_vision import default_vision_engine

def simulate_form_workflow():
    print("--- Starting Zero-DOM Visual RPA Workflow ---")

    steps = [
        ("search bar", "Focusing on search input field"),
        ("center dialog content", "Focusing on main form content"),
        ("submit button", "Submitting form"),
        ("close button", "Dismissing completion modal")
    ]

    for target, action_desc in steps:
        print(f"\n[RPA Step] {action_desc} -> Targeting '{target}'...")
        res = default_vision_engine.click_target(target, dry_run=True)
        print(f"  -> Predicted Location: ({res['phys_x']}, {res['phys_y']})")
        print(f"  -> Saliency Confidence: {res['confidence']*100:.1f}%")
        print(f"  -> Execution Latency: {res['elapsed_ms']:.2f} ms")
        time.sleep(0.1)

    print("\n--- Visual RPA Workflow Completed Successfully! ---")

if __name__ == "__main__":
    simulate_form_workflow()
