"""
Axiom Vision-Tensor Standalone Test Suite
Validates soft-argmax regression, luminance tensor downsampling, and spatial priors.
"""

import sys
import os
import unittest
import numpy as np
from PIL import Image

pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from axiom_vision.engine import VisualSpatialTensorEngine
from axiom_vision.visualizer import render_ascii_heatmap, render_heatmap_overlay

class TestVisionTensorEngine(unittest.TestCase):
    def setUp(self):
        self.engine = VisualSpatialTensorEngine(tensor_size=128, temperature=0.05)
        # Create a synthetic 1366x768 test canvas with a simulated bright button
        self.img = Image.new("RGB", (1366, 768), color=(40, 40, 40))
        # Draw a bright mock window with a close button
        img_arr = np.array(self.img)
        img_arr[50:600, 100:1200] = 200 # Window area
        img_arr[55:85, 1150:1190] = 255 # Close button highlight
        self.test_img = Image.fromarray(img_arr)

    def test_luminance_tensor_shape_and_range(self):
        tensor = self.engine.image_to_luminance_tensor(self.test_img)
        self.assertEqual(tensor.shape, (128, 128))
        self.assertGreaterEqual(np.min(tensor), 0.0)
        self.assertLessEqual(np.max(tensor), 1.0)

    def test_saliency_edge_detection(self):
        tensor = self.engine.image_to_luminance_tensor(self.test_img)
        edges = self.engine.compute_saliency_and_edges(tensor)
        self.assertEqual(edges.shape, (128, 128))
        self.assertGreater(np.max(edges), 0.0)

    def test_close_button_spatial_bias(self):
        res = self.engine.predict_click_coordinates(
            self.test_img,
            "close button",
            screen_w=1366,
            screen_h=768
        )
        self.assertTrue(res["success"])
        self.assertGreater(res["rel_x"], 0.70) # Biased towards top-right
        self.assertLess(res["rel_y"], 0.30)
        self.assertGreater(res["confidence"], 0.50)
        self.assertLess(res["elapsed_ms"], 50.0) # Sub-50ms cold-start SLA

    def test_start_menu_spatial_bias(self):
        res = self.engine.predict_click_coordinates(
            self.test_img,
            "start menu taskbar",
            screen_w=1366,
            screen_h=768
        )
        self.assertTrue(res["success"])
        self.assertLess(res["rel_x"], 0.30)  # Biased towards bottom-left
        self.assertGreater(res["rel_y"], 0.70)

    def test_ascii_heatmap_rendering(self):
        tensor = self.engine.image_to_luminance_tensor(self.test_img)
        ascii_map = render_ascii_heatmap(tensor, width=20, height=10)
        self.assertIsInstance(ascii_map, str)
        self.assertEqual(len(ascii_map.splitlines()), 10)

    def test_refine_patch_soft_argmax(self):
        # Around our simulated button at x=1170, y=70
        refined_x, refined_y, conf = self.engine.refine_patch_soft_argmax(
            self.test_img, coarse_x=1160, coarse_y=65, patch_size=100
        )
        self.assertGreater(refined_x, 1100)
        self.assertLess(refined_x, 1250)
        self.assertGreater(refined_y, 40)
        self.assertLess(refined_y, 100)
        self.assertGreater(conf, 0.5)

    def test_verify_visual_state_transition(self):
        before = Image.new("RGB", (200, 200), color=(50, 50, 50))
        # After click: button turns bright green/white
        after_arr = np.full((200, 200, 3), 50, dtype=np.uint8)
        after_arr[80:120, 80:120] = 240
        after = Image.fromarray(after_arr)

        res = self.engine.verify_visual_state_transition(before, after, 100, 100, radius=50)
        self.assertTrue(res["ui_transition_verified"])
        self.assertGreater(res["local_pixel_diff"], 1.0)
        self.assertGreater(res["max_local_diff"], 50.0)

    def test_calculator_keypad_prior(self):
        res = self.engine.predict_click_coordinates(
            self.test_img,
            "calculator button 7",
            screen_w=1000,
            screen_h=1000
        )
        self.assertTrue(res["success"])
        self.assertIn("phys_x", res)
        self.assertIn("phys_y", res)
        self.assertGreater(res["confidence"], 0.70)

    def test_execute_click_sequence_dry_run(self):
        # Mock execute_direct_click to avoid moving mouse during automated test
        orig_click = self.engine.execute_direct_click
        try:
            self.engine.execute_direct_click = lambda t, click=True, verify=False, **kwargs: {
                "phys_x": 500, "phys_y": 500, "confidence": 0.9, "total_elapsed_ms": 2.5
            }
            res = self.engine.execute_click_sequence(["button 7", "button 8"], delay_between_s=0.01)
            self.assertTrue(res["success"])
            self.assertEqual(res["total_clicks"], 2)
            self.assertEqual(len(res["sequence"]), 2)
        finally:
            self.engine.execute_direct_click = orig_click

    def test_extract_128d_feature_vector(self):
        mock_map = np.ones((128, 128), dtype=np.float32)
        vec = self.engine.extract_128d_feature_vector(mock_map)
        self.assertEqual(len(vec), 128)
        self.assertTrue(all(isinstance(x, float) for x in vec))
        self.assertAlmostEqual(sum(vec[:64]), 1.0, places=3)
        self.assertAlmostEqual(sum(vec[64:]), 1.0, places=3)

    def test_predict_contains_128d_feature_vector(self):
        res = self.engine.predict_click_coordinates(self.test_img, "close button", screen_w=1200, screen_h=800)
        self.assertIn("feature_vector_128d", res)
        self.assertEqual(len(res["feature_vector_128d"]), 128)

    def test_ocr_semantic_text_grounding(self):
        from PIL import ImageDraw
        test_canvas = Image.new("RGB", (1000, 600), color="#1e1e2e")
        draw = ImageDraw.Draw(test_canvas)
        draw.rectangle([(700, 300), (850, 360)], fill="#a6e3a1")
        draw.text((720, 320), "Submit Order", fill="black")

        res = self.engine.predict_click_coordinates(test_canvas, "Submit Order", screen_w=1000, screen_h=600)
        self.assertTrue(res["success"])
        # Coordinates should land squarely inside the button rectangle [700..850, 300..360]
        self.assertGreaterEqual(res["phys_x"], 680)
        self.assertLessEqual(res["phys_x"], 870)
        self.assertGreaterEqual(res["phys_y"], 280)
        self.assertLessEqual(res["phys_y"], 380)
        self.assertGreater(res["confidence"], 0.85)

    def test_ui_element_contour_detection(self):
        from PIL import ImageDraw
        canvas = Image.new("RGB", (800, 600), color=(240, 240, 240))
        d = ImageDraw.Draw(canvas)
        # Mock button
        d.rectangle([100, 100, 250, 150], fill=(50, 120, 240), outline=(20, 80, 200), width=2)
        # Mock input field
        d.rectangle([100, 200, 400, 240], fill=(255, 255, 255), outline=(150, 150, 150), width=2)

        elems = self.engine.detect_ui_elements(canvas, screen_w=800, screen_h=600, include_ocr=False)
        self.assertGreaterEqual(len(elems), 2)
        button_elem = next((e for e in elems if e["type"] in ("button", "ui_control")), None)
        self.assertIsNotNone(button_elem)
        self.assertIn("bbox", button_elem)
        self.assertIn("cx", button_elem)
        self.assertIn("cy", button_elem)

    def test_render_set_of_marks(self):
        from PIL import ImageDraw
        canvas = Image.new("RGB", (600, 400), color=(240, 240, 240))
        d = ImageDraw.Draw(canvas)
        d.rectangle([50, 50, 150, 90], fill=(50, 120, 240))
        som_img, ledger, elems = self.engine.render_set_of_marks(canvas, max_marks=10)
        self.assertEqual(som_img.size, (600, 400))
        self.assertIn("[Interactive UI Set-of-Marks Ledger]", ledger)
        self.assertGreaterEqual(len(elems), 1)

    def test_predict_with_routing_tiers(self):
        # Tier 1 reflex check
        tier1_res = self.engine.predict_with_routing("close button", self.test_img)
        self.assertEqual(tier1_res["routing_tier"], 1)
        self.assertIn("Tier-1", tier1_res["routing_tier_name"])

        # Tier 2 text search check
        tier2_res = self.engine.predict_with_routing("search bar", self.test_img)
        self.assertIn(tier2_res["routing_tier"], (2, 3))
        self.assertIn("routing_tier_name", tier2_res)

if __name__ == "__main__":
    unittest.main()


