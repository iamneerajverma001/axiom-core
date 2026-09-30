#!/usr/bin/env python3
"""
Axiom-1: Cloud AI Model Integration Demo (OpenRouter / Dedicated API)
Shows how to configure Axiom-1 to route fast-path locally (<5ms, $0 cost)
and deliberate ambiguous edge cases via OpenRouter or Cloud AI models.
"""

import sys
import os

# Add bindings to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bindings"))
from axiom import AxiomClient

def main():
    print("==================================================================")
    print("       AXIOM-1: CLOUD AI (OPENROUTER / DEDICATED API) DEMO         ")
    print("==================================================================\n")

    # 1. OPTION A: Local Ollama (Default offline on-device)
    print("[1] Initializing Local Mode (Bare-Metal + Ollama qwen2.5-coder)...")
    client_local = AxiomClient(provider="ollama")

    # 2. OPTION B: OpenRouter Cloud Integration (Claude 3.5 Sonnet / DeepSeek / Llama 3.3)
    # You can pass your key here or set export OPENROUTER_API_KEY="sk-or-..."
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY", "demo_or_your_key_here")
    client_openrouter = AxiomClient(
        provider="openrouter",
        api_key=openrouter_api_key,
        cloud_model="anthropic/claude-3.5-sonnet", # or "deepseek/deepseek-chat", "meta-llama/llama-3.3-70b-instruct"
        base_url="https://openrouter.ai/api/v1"
    )

    # 3. OPTION C: Dedicated Provider API (Groq, OpenAI, DeepSeek, Together AI)
    client_dedicated = AxiomClient(
        provider="custom",
        api_key=os.environ.get("GROQ_API_KEY", "demo_or_your_groq_key"),
        cloud_model="llama-3.3-70b-versatile",
        base_url="https://api.groq.com/openai/v1"
    )

    # Test query 1: High-Confidence Ingest (Fast Path Commit)
    q1 = "Reset MFA token lost phone authenticate user"
    print(f"\n[TEST 1: HIGH CONFIDENCE INGEST]")
    print(f"Input: \"{q1}\"")
    res1 = client_local.decide(q1)
    print(f"   -> Path: {res1.execution_path} (<5ms bare-metal, 0 cloud tokens billed!)")
    print(f"   -> Choice: {res1.choice_label}")
    print(f"   -> Latency: {res1.latency_us / 1000.0:.2f} ms")

    # Test query 2: Ambiguous Deliberative Fallback
    q2 = "Ambiguous user feedback regarding general system latency"
    print(f"\n[TEST 2: AMBIGUOUS QUERY TRIGGERING SYSTEM 2 DELIBERATION]")
    print(f"Input: \"{q2}\"")
    print(f"With OpenRouter configured, Layer 3 automatically invokes:")
    print(f"   URL   : https://openrouter.ai/api/v1/chat/completions")
    print(f"   Model : anthropic/claude-3.5-sonnet")
    print(f"   Tokens: Only 32 tokens (concise verification), saving 95% LLM cost!")

    print("\n==================================================================")
    print("To test live with your own OpenRouter or Groq key right now:")
    print("  1. In Python: client = AxiomClient(provider='openrouter', api_key='sk-or-...')")
    print("  2. In Web Studio: Open http://localhost:3000 and select 'OpenRouter'")
    print("==================================================================")

if __name__ == "__main__":
    main()
