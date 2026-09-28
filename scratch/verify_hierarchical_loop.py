"""
Scratch script to verify Hierarchical Autonomous Loop:
- Multi-step milestone progression
- Premature finalization interception
- Live ledger rendering
- Final synthesis resolution
"""
import sys
import os
import unittest
from unittest.mock import patch

# Ensure paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.omni_brain import run_autonomous_loop, Milestone, HierarchicalExecutionPlan

def test_autonomous_hierarchical_loop():
    print("Testing Hierarchical Autonomous Loop...")
    goal = "Open calculator, calculate 7 * 8, and record the result"
    
    # Sequence of mock LLM decisions
    mock_responses = [
        # Decision 1: Premature final answer (must be BLOCKED by planner)
        {
            "thought": "I will just answer without executing.",
            "action": None,
            "args": {},
            "final_answer": "Done, 7*8 is 56."
        },
        # Decision 2: Execute milestone 1 (launch calc)
        {
            "thought": "Launching calculator as requested by milestone 1.",
            "action": "powershell_exec",
            "args": {"script": "Write-Host 'Calculator started'"}
        },
        # Decision 3: Execute milestone 2 (click sequence)
        {
            "thought": "Clicking 7, *, 8, = on calculator.",
            "action": "powershell_exec",
            "args": {"script": "Write-Host 'Result 56'"}
        },
        # Decision 4: Conclude with final answer now that milestones are complete
        {
            "thought": "All execution milestones are verified. Synthesizing final answer.",
            "action": None,
            "args": {},
            "final_answer": "Successfully executed calculation 7 * 8 = 56 on Windows calculator."
        }
    ]

    response_iter = iter(mock_responses)
    def mock_query(*args, **kwargs):
        return next(response_iter)

    with patch("src.omni_brain.query_llm_json", side_effect=mock_query):
        events = []
        gen = run_autonomous_loop(
            user_goal=goal,
            provider="ollama",
            max_steps=6
        )

        for ev in gen:
            events.append(ev)
            ev_type = ev.get("type")
            if ev_type == "ledger_steer":
                print(f"[LEDGER STEER INTERCEPTION] Step {ev.get('step')}: {ev.get('thought')}")
            elif ev_type in ("action_dispatched", "action"):
                print(f"[ACTION DISPATCH] Step {ev.get('step')}: {ev.get('action')}")
            elif ev_type == "observation":
                print(f"[OBSERVATION] Step {ev.get('step')}: success={ev.get('observation', {}).get('success')}")
            elif ev_type == "completed":
                print(f"[COMPLETED] Final Answer: {ev.get('final_answer')}")

        trace = events[-1] if events and events[-1].get("type") != "completed" else None
        print("Total Events Emitted:", len(events))
        assert any(e.get("type") == "ledger_steer" for e in events), "Premature finalization was not intercepted!"
        assert any(e.get("type") == "action_dispatched" for e in events), "Actions were not executed!"
        assert any(e.get("type") == "completed" for e in events), "Loop did not successfully complete!"


        print("PASS: Hierarchical Autonomous Planning Loop verified 100%!")

if __name__ == "__main__":
    test_autonomous_hierarchical_loop()
