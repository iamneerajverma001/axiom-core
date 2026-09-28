"""
Axiom Vision-Tensor Visualizer
Renders spatial activation heatmaps, target crosshairs, and terminal ASCII density maps.
"""

import numpy as np
from PIL import Image, ImageDraw
from typing import Dict, Any, Optional

def render_heatmap_overlay(
    image: Image.Image,
    prediction: Dict[str, Any],
    output_path: Optional[str] = None
) -> Image.Image:
    """Draws target crosshairs and confidence circle onto the image."""
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    x = prediction["phys_x"]
    y = prediction["phys_y"]
    r = 24

    # Red target crosshair
    draw.ellipse((x - r, y - r, x + r, y + r), outline="red", width=3)
    draw.line((x - r - 10, y, x + r + 10, y), fill="red", width=2)
    draw.line((x, y - r - 10, x, y + r + 10), fill="red", width=2)

    # Label text
    conf_pct = int(prediction.get("confidence", 1.0) * 100)
    label = f"{prediction.get('target', 'Target')} ({conf_pct}% conf)"
    draw.text((x + r + 5, y - 10), label, fill="red")

    if output_path:
        img_copy.save(output_path)

    return img_copy

def render_ascii_heatmap(activation_grid: np.ndarray, width: int = 40, height: int = 20) -> str:
    """Renders small ASCII heatmap into terminal for quick inspection."""
    import math
    chars = " .:-=+*#%@"
    # Downsample
    gh, gw = activation_grid.shape
    lines = []
    norm = (activation_grid - np.min(activation_grid)) / (np.max(activation_grid) - np.min(activation_grid) + 1e-6)
    
    for r in range(height):
        row_str = ""
        orig_r = int(r * gh / height)
        for c in range(width):
            orig_c = int(c * gw / width)
            val = norm[orig_r, orig_c]
            char_idx = int(val * (len(chars) - 1))
            row_str += chars[char_idx]
        lines.append(row_str)
    return "\n".join(lines)
