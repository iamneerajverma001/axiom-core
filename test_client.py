import urllib.request
import urllib.error
import json
import time

def test_endpoint(name, url, method="GET", payload=None, timeout=25):
    print(f"\n=======================================================")
    print(f"Testing: {name}")
    print(f"Target : {method} {url}")
    print(f"=======================================================")
    data = json.dumps(payload).encode('utf-8') if payload else None
    headers = {"Content-Type": "application/json"} if payload else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = (time.time() - t0) * 1000
            res = resp.read().decode('utf-8')
            print(f"-> HTTP Status: {resp.status} (Roundtrip: {elapsed_ms:.1f} ms)")
            try:
                parsed = json.loads(res)
                print("-> Response Body:")
                print(json.dumps(parsed, indent=2))
            except Exception:
                print("-> Response Body (raw text):", res[:300])
            return True
    except urllib.error.HTTPError as e:
        print(f"-> HTTPError {e.code}: {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"-> Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    # 1. Health
    test_endpoint("Health Check", "http://localhost:3000/api/health")

    # 2. System Telemetry
    test_endpoint("Real-Time Hardware & OS Telemetry", "http://localhost:3000/api/system_telemetry")

    # 3. Fast Path: Free Port 3000 (With Self-Protection)
    test_endpoint(
        "Chat Fast-Path: Free Port 3000",
        "http://localhost:3000/v1/chat/completions",
        method="POST",
        payload={"messages": [{"role": "user", "content": "Free port 3000"}]}
    )

    # 4. Fast Path: Clean Temp Files (With Real %TEMP% Disk Purge)
    test_endpoint(
        "Chat Fast-Path: Clean Temp Files & Cache",
        "http://localhost:3000/v1/chat/completions",
        method="POST",
        payload={"messages": [{"role": "user", "content": "Clean temp files and build cache"}]}
    )

    # 5. Idea Logger
    test_endpoint(
        "Mobile/PC Idea Logger",
        "http://localhost:3000/api/idea_log",
        method="POST",
        payload={"text": "Verified Axiom-OS sub-millisecond hardware reflex bridge on Windows 10/11"}
    )

    # 6. Read Recent Ideas
    test_endpoint("Research Memory Feed", "http://localhost:3000/api/idea_log")

    # 7. TradingView Webhook Sentinel
    test_endpoint(
        "TradingView Webhook Alert (PineScript)",
        "http://localhost:3000/webhook/tradingview",
        method="POST",
        payload={"ticker": "BTCUSDT", "action": "BUY", "message": "Volume breakout confirmed above 200 EMA"}
    )

    # 8. System 2 Fallback: Coding Query
    test_endpoint(
        "Chat System 2 Fallback: Coding Query (Escalation to Qwen2.5-Coder)",
        "http://localhost:3000/v1/chat/completions",
        method="POST",
        payload={"messages": [{"role": "user", "content": "Write a 3-line python function to calculate Fibonacci numbers"}]}
    )
