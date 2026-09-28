"""
Tests for FinTech Pre-Trade Risk Firewall
"""

import sys
import os
import unittest
import time

pkg_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from solutions.fintech_pretrade_firewall.firewall import PreTradeRiskFirewall, TradeOrder

class TestPreTradeRiskFirewall(unittest.TestCase):
    def setUp(self):
        self.firewall = PreTradeRiskFirewall(
            max_order_notional=100_000.0,
            max_daily_notional=500_000.0,
            price_collar_pct=0.05
        )

    def test_clean_order_approval(self):
        order = TradeOrder(
            order_id="ORD-001",
            symbol="NVDA",
            side="BUY",
            price=120.0,
            quantity=100,
            account_id="ACC-HFT-1"
        )
        res = self.firewall.evaluate_order(order, mid_market_price=120.5)
        self.assertTrue(res["approved"])
        self.assertLess(res["latency_us"], 50.0) # Sub-50us validation

    def test_fat_finger_rejection(self):
        # Order worth $200,000 (limit is $100,000)
        order = TradeOrder(
            order_id="ORD-FAT-FINGER",
            symbol="AAPL",
            side="BUY",
            price=200.0,
            quantity=1000,
            account_id="ACC-HFT-1"
        )
        res = self.firewall.evaluate_order(order, mid_market_price=200.0)
        self.assertFalse(res["approved"])
        self.assertIn("EXCEEDS_MAX_NOTIONAL", res["reason"])

    def test_price_collar_rejection(self):
        # Limit buy at $150 when market is $100 (50% collar deviation)
        order = TradeOrder(
            order_id="ORD-COLLAR-VIOLATION",
            symbol="MSFT",
            side="BUY",
            price=150.0,
            quantity=10,
            account_id="ACC-HFT-1"
        )
        res = self.firewall.evaluate_order(order, mid_market_price=100.0)
        self.assertFalse(res["approved"])
        self.assertIn("PRICE_COLLAR_VIOLATION", res["reason"])

    def test_throughput_benchmark(self):
        # Evaluate 5,000 orders in batch
        t0 = time.perf_counter()
        for i in range(5000):
            order = TradeOrder(
                order_id=f"ORD-BULK-{i}",
                symbol="SPY",
                side="BUY",
                price=500.0,
                quantity=1,
                account_id="ACC-HFT-BULK"
            )
            # Pass clean orders
            self.firewall.evaluate_order(order, mid_market_price=500.0)
        elapsed = time.perf_counter() - t0
        throughput = 5000 / elapsed
        print(f"\nFinTech Pre-Trade Firewall: 5,000 orders evaluated in {elapsed*1000:.2f}ms ({throughput:,.0f} orders/sec)")
        self.assertGreater(throughput, 10_000) # At least 10,000 orders/sec

if __name__ == "__main__":
    unittest.main()
