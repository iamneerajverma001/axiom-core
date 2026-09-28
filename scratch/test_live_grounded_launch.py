import urllib.request
import json

def test_tool_launch(target):
    req_data = json.dumps({
        "tool": "app_control",
        "args": {"action": "launch", "target": target}
    }).encode('utf-8')

    req = urllib.request.Request(
        "http://127.0.0.1:3000/api/omni/tool",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Target '{target}':")
        print(json.dumps(data, indent=2))
        return data

if __name__ == "__main__":
    test_tool_launch("cmd")
    test_tool_launch("calc")
