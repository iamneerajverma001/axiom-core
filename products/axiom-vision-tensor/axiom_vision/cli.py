"""
Axiom Vision-Tensor CLI
Execute sub-16ms visual spatial clicks directly from terminal.
"""

import argparse
import json
import sys
import os

from .engine import default_vision_engine
from .capture import capture_screen_gdi
from .visualizer import render_heatmap_overlay, render_ascii_heatmap

def main():
    parser = argparse.ArgumentParser(description="Axiom Vision-Tensor: Sub-16ms Zero-OCR Visual Clicker")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Predict
    predict_p = subparsers.add_parser("predict", help="Predict click coordinates without clicking")
    predict_p.add_argument("target", type=str, help="Target UI description, e.g., 'close button'")
    predict_p.add_argument("--json", action="store_true", help="Output raw JSON")

    # Click
    click_p = subparsers.add_parser("click", help="Locate and physically click target")
    click_p.add_argument("target", type=str, help="Target UI description, e.g., 'submit button'")
    click_p.add_argument("--dry-run", action="store_true", help="Do not send hardware click event")

    # Heatmap
    heat_p = subparsers.add_parser("heatmap", help="Compute activation heatmap")
    heat_p.add_argument("target", type=str, help="Target UI description")
    heat_p.add_argument("--output", type=str, default="target_heatmap.png", help="Output image file")
    heat_p.add_argument("--ascii", action="store_true", help="Render ASCII map in terminal")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "predict":
        screen = capture_screen_gdi()
        w, h = screen.size
        res = default_vision_engine.predict_click_coordinates(screen, args.target, screen_w=w, screen_h=h)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"Target: \"{res['target']}\"")
            print(f"Coordinates: ({res['phys_x']}, {res['phys_y']}) [Normalized: ({res['rel_x']}, {res['rel_y']})]")
            print(f"Confidence: {res['confidence']*100:.1f}% | Entropy: {res['spatial_entropy']}")
            print(f"Latency: {res['elapsed_ms']:.2f} ms")

    elif args.command == "click":
        res = default_vision_engine.click_target(args.target, dry_run=args.dry_run)
        print(f"Action: {res.get('action')} at ({res['phys_x']}, {res['phys_y']}) in {res['elapsed_ms']:.2f} ms")

    elif args.command == "heatmap":
        screen = capture_screen_gdi()
        w, h = screen.size
        res = default_vision_engine.predict_click_coordinates(screen, args.target, screen_w=w, screen_h=h)
        if args.ascii:
            z_map = default_vision_engine.compute_activation_map(screen, args.target, screen_w=w, screen_h=h)
            print(render_ascii_heatmap(z_map))
        render_heatmap_overlay(screen, res, output_path=args.output)
        print(f"Saved visual target heatmap overlay to: {args.output}")

if __name__ == "__main__":
    main()
