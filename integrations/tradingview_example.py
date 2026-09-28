"""
Axiom-1 TradingView Webhook & Risk Filter Example
Demonstrates how TradingView alerts (PineScript alerts) post directly to Axiom-1
for microsecond risk validation, sentiment filtering, and instant trade authorization.
"""

import urllib.request
import json
import time

AXIOM_WEBHOOK_URL = "http://localhost:3000/webhook/tradingview"

def send_tradingview_alert(ticker: str, action: str, signal_message: str):
    payload = {
        "ticker": ticker,
        "action": action,
        "message": signal_message,
        "timestamp": int(time.time()),
        "timeframe": "15m"
    }

    print(f"\n[TRADINGVIEW ALERT DISPATCHED] -> {action} {ticker}: \"{signal_message}\"")
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        AXIOM_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            res = json.loads(resp.read().decode('utf-8'))
            
            print(f"  |-- Axiom Path    : {res.get('axiom_execution_path')}")
            print(f"  |-- Category      : {res.get('category')}")
            print(f"  |-- Safe to Trade : {res.get('is_safe_to_execute')}")
            print(f"  |-- Latency       : {elapsed_ms:.2f} ms ({res.get('latency_us', 0):.1f} us)")
            print(f"  |-- Conformal Set : {res.get('conformal_set')}")
    except Exception as e:
        print(f"  |-- Webhook Error : {e}")

if __name__ == "__main__":
    print("Testing TradingView Webhook Integration with Axiom-1...")

    # Simulated PineScript alert 1
    send_tradingview_alert("BTCUSDT", "BUY", "Bullish RSI divergence + Volume breakout confirmed")

    # Simulated PineScript alert 2
    send_tradingview_alert("SPY", "SELL", "Critical support breakdown on 1h chart stop loss triggered")

    # Simulated PineScript alert 3 (Ambiguous / Noise)
    send_tradingview_alert("TSLA", "ALERT", "Random chop within sideways range no clear trend")
