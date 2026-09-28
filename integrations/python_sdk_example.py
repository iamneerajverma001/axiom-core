"""
Axiom-1 Python SDK Direct Integration Example
Demonstrates using the native AxiomClient to route requests directly from any Python backend.
"""

import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bindings.axiom import AxiomClient

def main():
    print("================================================================")
    print("   AXIOM-1 PYTHON SDK DIRECT INTEGRATION DEMO                   ")
    print("================================================================")

    # Initialize client (Local Ollama or Cloud API)
    client = AxiomClient(provider="ollama")

    test_queries = [
        "Reset MFA token lost phone authenticate user",
        "Immediate refund request for unauthorized charge on invoice #9401",
        "Kubernetes worker node worker-prod-04 reporting MemoryPressure and OOMKill",
        "Can you write a python script to parse CSV files with pandas?"
    ]

    for q in test_queries:
        print(f"\n[QUERY] -> \"{q}\"")
        result = client.decide(q)
        print(f"  |-- Execution Path : {result.execution_path}")
        print(f"  |-- Selected Action: {result.choice_label} (ID: {result.choice_id})")
        print(f"  |-- Confidence     : {result.confidence * 100:.2f}%")
        print(f"  |-- Shannon Entropy: {result.shannon_entropy:.4f}")
        print(f"  |-- Latency        : {result.latency_us:.1f} us ({result.latency_us / 1000.0:.2f} ms)")

if __name__ == "__main__":
    main()
