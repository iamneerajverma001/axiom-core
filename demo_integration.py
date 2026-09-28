#!/usr/bin/env python3
"""
Axiom-1: Quickstart Integration Example for Your Python Apps & Agents
Demonstrates how to route user intents with sub-5ms native speed and live Ollama fallback.
"""

import sys
import os

# Add bindings to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bindings"))
from axiom import AxiomClient

def main():
    print("==================================================================")
    print("      AXIOM-1 PYTHON SDK: AGENTIC COPILOT & ROUTER DEMO           ")
    print("==================================================================\n")

    client = AxiomClient()

    test_queries = [
        "Immediate refund dispute on invoice #9401",
        "Reset MFA token lost phone authenticate user",
        "Kubernetes CrashLoopBackOff container killed in prod",
        "Ambiguous user feedback regarding general system latency"
    ]

    for q in test_queries:
        print(f"[QUERY] \"{q}\"")
        decision = client.decide(q)
        
        print(f"   -> Path         : {decision.execution_path}")
        print(f"   -> Choice Label : {decision.choice_label} (ID: {decision.choice_id})")
        print(f"   -> Confidence   : {decision.confidence * 100:.1f}%")
        print(f"   -> Conformal Set: {decision.conformal_set} (Singleton: {decision.is_singleton})")
        print(f"   -> Total Time   : {decision.latency_us / 1000.0:.2f} ms")
        print("-" * 66)

if __name__ == "__main__":
    main()
