import subprocess
import json
import os

env = os.environ.copy()
env["AXIOM_NO_SOCKET"] = "1"

queries = [
    "Free port 3000 occupied by zombie node process",
    "Clean temp files and build cache",
    "Lock my workstation",
    "Turn on battery ecoqos mode",
    "Immediate refund dispute on unauthorized charge #9401",
    "Reset my 2fa authentication token",
    "TradingView buy alert on BTCUSDT volume breakout",
    "Write a 3-line python function to calculate Fibonacci numbers"
]

print("=== AXIOM-OS MULTI-SECTOR ROUTING TEST ===")
for q in queries:
    res = subprocess.run(["axiom_cli.exe", q], capture_output=True, text=True, env=env)
    out = res.stdout.strip()
    j_start = out.find('{')
    j_end = out.rfind('}')
    if j_start != -1 and j_end != -1:
        data = json.loads(out[j_start:j_end+1])
        path = data.get("execution_path")
        label = data.get("choice_label")
        conf = data.get("confidence", 0.0) * 100
        singleton = data.get("is_singleton")
        cset = data.get("conformal_set")
        print(f"[{path:18}] Singleton={singleton} Conf={conf:5.1f}% Set={cset} Leaf={label} <- '{q}'")
    else:
        print("FAILED TO PARSE:", out)
