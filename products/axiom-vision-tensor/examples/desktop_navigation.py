"""
Axiom Vision-Tensor Desktop Navigation Example
Performs direct visual mouse interactions on native Windows elements.
"""

import sys
import os

pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from axiom_vision import default_vision_engine, capture_screen_gdi, render_ascii_heatmap

def run_navigation():
    print("--- Desktop Visual Spatial Targeting Demo ---")
    screen = capture_screen_gdi()
    w, h = screen.size
    print(f"Captured screen buffer: {w}x{h}")

    targets = ["start menu", "search box", "close window button", "system tray clock"]

    for t in targets:
        pred = default_vision_engine.predict_click_coordinates(screen, t, screen_w=w, screen_h=h)
        print(f"\nTarget: {t}")
        print(f"  Coordinates: ({pred['phys_x']}, {pred['phys_y']})")
        print(f"  Confidence:  {pred['confidence']*100:.1f}%")
        print(f"  Latency:     {pred['elapsed_ms']:.2f} ms")

if __name__ == "__main__":
    run_navigation()
