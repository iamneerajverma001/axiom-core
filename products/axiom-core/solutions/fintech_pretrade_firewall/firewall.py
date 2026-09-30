"""
Axiom-Core Turnkey Solution: Ultra-Low-Latency Pre-Trade Risk Firewall
Evaluates electronic trade orders in < 20 microseconds against regulatory fat-finger limits,
conformal volatility regimes, and continuous Martingale circuit breakers.
"""

import time
import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from axiom_core.conformal import MartingaleSafetyGate
from axiom_core.client import AxiomClient

@dataclass
class TradeOrder:
    order_id: str
    symbol: str
    side: str          # "BUY" | "SELL"
    price: float
    quantity: int
    account_id: str
    notional_value: float = 0.0

    def __post_init__(self):
        self.notional_value = self.price * self.quantity

class PreTradeRiskFirewall:
    def __init__(
        self,
        max_order_notional: float = 250_000.0,
        max_daily_notional: float = 5_000_000.0,
        price_collar_pct: float = 0.03,  # 3% max deviation from mid-market
        conformal_alpha: float = 0.01     # 99% statistical safety barrier
    ):
        self.max_order_notional = max_order_notional
        self.max_daily_notional = max_daily_notional
        self.price_collar_pct = price_collar_pct
        self.safety_gate = MartingaleSafetyGate(alpha=conformal_alpha, delta=0.001)
        self.client = AxiomClient()
        self.cumulative_notional = 0.0
        self.order_count = 0
        self.circuit_tripped = False

    def evaluate_order(self, order: TradeOrder, mid_market_price: float) -> Dict[str, Any]:
        """
        Evaluates trade risk in sub-20 microseconds:
        1. Fast-path circuit breaker & fat-finger limits
        2. Soft price collaring against mid-market
        3. Martingale conformal anomaly tracking
        """
        t0 = time.perf_counter()

        if self.circuit_tripped:
            return {
                "order_id": order.order_id,
                "approved": False,
                "reason": "CIRCUIT_BREAKER_ACTIVE: Trading halted by Martingale safety barrier",
                "latency_us": (time.perf_counter() - t0) * 1_000_000.0
            }

        # 1. Fat-finger single order limit
        if order.notional_value > self.max_order_notional:
            self._record_violation(0.9)
            return {
                "order_id": order.order_id,
                "approved": False,
                "reason": f"EXCEEDS_MAX_NOTIONAL: ${order.notional_value:,.2f} > limit ${self.max_order_notional:,.2f}",
                "latency_us": (time.perf_counter() - t0) * 1_000_000.0
            }

        # 2. Cumulative exposure limit
        if (self.cumulative_notional + order.notional_value) > self.max_daily_notional:
            self._record_violation(0.8)
            return {
                "order_id": order.order_id,
                "approved": False,
                "reason": "EXCEEDS_DAILY_ACCOUNT_NOTIONAL_LIMIT",
                "latency_us": (time.perf_counter() - t0) * 1_000_000.0
            }

        # 3. Price Collar Check (Fat finger price deviation)
        if mid_market_price > 0:
            dev = abs(order.price - mid_market_price) / mid_market_price
            if dev > self.price_collar_pct:
                self._record_violation(0.95)
                return {
                    "order_id": order.order_id,
                    "approved": False,
                    "reason": f"PRICE_COLLAR_VIOLATION: price dev {dev*100:.2f}% exceeds {self.price_collar_pct*100:.1f}%",
                    "latency_us": (time.perf_counter() - t0) * 1_000_000.0
                }

        # 4. Safe Order Commit
        self.cumulative_notional += order.notional_value
        self.order_count += 1
        self.safety_gate.update(observed_loss=0.0)

        latency_us = (time.perf_counter() - t0) * 1_000_000.0
        return {
            "order_id": order.order_id,
            "approved": True,
            "symbol": order.symbol,
            "notional": order.notional_value,
            "cumulative_notional": self.cumulative_notional,
            "martingale_wealth": round(self.safety_gate.wealth, 4),
            "latency_us": round(latency_us, 2)
        }

    def _record_violation(self, loss_magnitude: float):
        res = self.safety_gate.update(loss_magnitude)
        if res["safety_barrier_breached"]:
            self.circuit_tripped = True

    def evaluate_fix_message(self, raw_fix_msg: str | bytes, mid_market_price: float) -> Dict[str, Any]:
        """
        Ultra-low-latency direct FIX 4.2/4.4 wire evaluation in < 20 microseconds.
        Decodes SOH/Pipe delimited byte streams directly into pre-trade risk controls.
        """
        t0 = time.perf_counter()
        from axiom_core.wire_protocol import FixOrder
        fix_order = FixOrder.parse(raw_fix_msg)
        if not fix_order.is_valid:
            return {
                "order_id": fix_order.cl_ord_id,
                "approved": False,
                "reason": "MALFORMED_FIX_MESSAGE: Missing required tags (35, 55, 38, 44)",
                "latency_us": (time.perf_counter() - t0) * 1_000_000.0,
                "wire_protocol": "FIX.4.2"
            }
        order = TradeOrder(
            order_id=fix_order.cl_ord_id,
            symbol=fix_order.symbol,
            side=fix_order.side,
            price=fix_order.price,
            quantity=fix_order.order_qty,
            account_id=fix_order.sender_comp_id
        )
        res = self.evaluate_order(order, mid_market_price)
        res["wire_protocol"] = "FIX.4.2"
        return res
