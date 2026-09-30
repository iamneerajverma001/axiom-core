"""
Axiom-1 Universal OpenAI Drop-In Integration Example
Demonstrates how to connect ANY existing AI chat or agent framework (Open WebUI, LangChain,
LlamaIndex, Cursor, Continue.dev, or pure OpenAI SDK) to Axiom-1 with ZERO code rewrite.
Endpoint: http://localhost:3000/v1/chat/completions
"""

import os
import sys
import time
import json
import urllib.request

GATEWAY_URL = "http://localhost:3000/v1/chat/completions"

def query_axiom_chat(prompt: str):
    """Executes query over standard OpenAI chat completions endpoint."""
    payload = {
        "model": "axiom-hybrid",
        "messages": [
            {"role": "system", "content": "You are an intelligent enterprise assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        GATEWAY_URL,
        data=data,
        headers={"Content-Type": "application/json", "Authorization": "Bearer axiom-local"}
    )
    
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30) as resp:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        res = json.loads(resp.read().decode('utf-8'))
        return res, elapsed_ms

def test_chat(prompt: str):
    print(f"\n=======================================================")
    print(f"USER PROMPT: '{prompt}'")
    print(f"-------------------------------------------------------")
    
    try:
        response, elapsed_ms = query_axiom_chat(prompt)
        msg = response["choices"][0]["message"]["content"]
        model_used = response.get("model", "unknown")
        meta = response.get("axiom_meta", {})
        tokens_used = response.get("usage", {}).get("total_tokens", 0)

        print(f"EXEC PATH   : {meta.get('execution_path', 'SYSTEM2_FALLBACK')}")
        print(f"MODEL USED  : {model_used}")
        print(f"ROUNDTRIP   : {elapsed_ms:.2f} ms")
        print(f"TOKENS PAID : {tokens_used} tokens ($0.00 cost on fast path)")
        print(f"INTENT/TAG  : {meta.get('choice_label', 'Auto')}")
        print(f"RESPONSE    :\n{msg}")
    except Exception as e:
        print(f"Error querying Axiom Gateway: {e}")

if __name__ == "__main__":
    print("Testing Axiom-1 Drop-In OpenAI Gateway on http://localhost:3000/v1...")

    # Case 1: Fast Path Routine Task (Sub-millisecond reflex, 0 tokens!)
    test_chat("Lost my 2FA authentication phone, please reset my MFA token urgently")

    # Case 2: Fast Path Billing Dispute
    test_chat("Immediate refund dispute on unauthorized charge #9401")

    # Case 3: Complex / Creative Fallback (Automatically forwarded to Ollama / Cloud LLM)
    test_chat("Explain how an asynchronous event loop works in 2 sentences with an analogy")
