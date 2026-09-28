import urllib.request
import json
import time

def test_chat(goal):
    req = urllib.request.Request(
        'http://127.0.0.1:3000/api/omni/chat',
        data=json.dumps({'goal': goal}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode('utf-8'))
        dt = (time.time() - t0) * 1000.0
        print(f"GOAL: '{goal}'")
        print(f"  Execution Mode: {data.get('execution_mode')}")
        print(f"  Latency: {data.get('latency_ms')} ms (HTTP wall: {dt:.1f}ms)")
        print(f"  Tokens Consumed: {data.get('tokens_consumed', 'N/A')}")
        print(f"  Choice: #{data.get('choice_id')} ({data.get('choice_label')})")
        print(f"  Answer: {data.get('final_answer')}")
        ldu = data.get('ldu_deliberation')
        if ldu:
            print(f"  LDU Deliberation: Sector='{ldu.get('best_sector_name')}' Conf={ldu.get('max_confidence', 0)*100:.1f}% Entropy={ldu.get('shannon_entropy')}")
        print("-" * 60)

if __name__ == "__main__":
    print("Testing 80 C++ Leaves in Live Chat:\n")
    test_chat("audit startup apps")
    test_chat("organize downloads")
    test_chat("find duplicate files")
    test_chat("backup project")
    test_chat("night light")
