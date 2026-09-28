"""
Axiom Vision-Tensor: Sub-16ms Soft-Argmax Visual-Spatial Click Engine
Zero-OCR, zero-cloud visual spatial UI clicker and automation library.
"""

from .engine import VisualSpatialTensorEngine, default_vision_engine, vision_tensor_engine
from .capture import capture_screen_gdi, capture_active_window_gdi
from .visualizer import render_heatmap_overlay, render_ascii_heatmap

__version__ = "1.0.0"
__all__ = [
    "VisualSpatialTensorEngine",
    "default_vision_engine",
    "vision_tensor_engine",
    "capture_screen_gdi",
    "capture_active_window_gdi",
    "render_heatmap_overlay",
    "render_ascii_heatmap",
]

