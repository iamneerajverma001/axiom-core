import urllib.request
import json
import time

def test_endpoint(goal):
    print(f"\n==========================================")
    print(f"TESTING LIVE GOAL: {goal}")
    print(f"==========================================")
    req_data = json.dumps({"goal": goal}).encode('utf-8')
    req = urllib.request.Request(
        "http://127.0.0.1:3000/api/omni/chat",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elapsed = time.time() - t0
            print(f"Response (HTTP {resp.status}, {elapsed:.2f}s):")
            print(json.dumps(data, indent=2))
            return data
    except Exception as e:
        print(f"Request failed: {e}")
        return None

if __name__ == "__main__":
    test_endpoint("search REC Sonbhadra")
    test_endpoint("launch REC Sonbhadra")
    test_endpoint("open browser and serch REC SONBHADRA ,and lauch it website")
