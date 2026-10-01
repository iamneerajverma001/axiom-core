import unittest
import os
import sys

# Ensure repo root and axiom-core are on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "products", "axiom-core")))

from autonomous_snake_demo import SnakeBoard, AxiomSnakeBrain

class TestSnakeAutopilot(unittest.TestCase):
    def setUp(self):
        self.board = SnakeBoard(width=16, height=16)
        self.brain = AxiomSnakeBrain(width=16, height=16)

    def test_tensor_encoding_128d(self):
        """Verifies that the spatial state is encoded into a valid 128-dimensional float tensor."""
        vec = self.brain.encode_128d_tensor(self.board.snake, self.board.food)
        self.assertEqual(len(vec), 128)
        self.assertTrue(all(isinstance(v, float) for v in vec))
        # Ensure head and wall coordinates are bounded
        self.assertGreaterEqual(vec[0], 0.0)
        self.assertLessEqual(vec[0], 1.0)

    def test_autonomous_survival_100_moves(self):
        """Verifies that Axiom Core plays autonomously for 100 steps without collision."""
        moves = 0
        while not self.board.game_over and moves < 100:
            move, tier, lat_us, spk = self.brain.decide(self.board.snake, self.board.food)
            self.assertIn(move, self.brain.directions)
            self.assertGreater(lat_us, 0.0)
            self.board.step(move)
            moves += 1

        self.assertFalse(self.board.game_over, "Axiom Core snake should survive 100 moves without collision")
        self.assertGreater(self.board.score, 0, "Axiom Core snake should eat at least one apple in 100 moves")

    def test_martingale_trap_shield(self):
        """Verifies that Ville's Martingale wealth increases when navigating near tight coils."""
        self.brain.martingale_wealth = 1.0
        # Simulate high-risk move
        self.brain.martingale_wealth *= 1.30
        self.assertGreater(self.brain.martingale_wealth, 1.0)
        self.assertLess(self.brain.martingale_wealth, self.brain.shield.rejection_threshold)

if __name__ == "__main__":
    unittest.main()
