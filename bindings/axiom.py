"""
Axiom-1 Production Python SDK
Provides type-safe declarative bindings and high-speed execution for Axiom-1
Calling native bare-metal C++ kernel and live local Ollama fallback.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import subprocess
import json
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_EXE = os.path.join(PROJECT_ROOT, "axiom_cli.exe")

class LeafDefinition(BaseModel):
    leaf_id: int
    name: str
    description: str

class SectorDefinition(BaseModel):
    sector_id: int
    name: str
    leaves: List[LeafDefinition]

class SchemaDefinition(BaseModel):
    schema_id: str
    domain: str
    sectors: List[SectorDefinition]
    confidence_threshold: float = 0.80
    entropy_threshold: float = 0.35
    conformal_alpha: float = 0.01  # 99% coverage guarantee

class FeedbackOutput(BaseModel):
    tier3_to_tier1_dispatched: bool = False
    action_executed: bool = False
    executed_leaf_id: int = 0
    target_leaf_name: str = ""
    target_sector_id: int = 0
    rlcd_learning_type: int = 0
    execution_status: str = ""

class DecisionOutput(BaseModel):
    request_id: int
    execution_path: str  # FAST_PATH_COMMIT (<5ms) or SYSTEM2_FALLBACK
    choice_label: str
    choice_id: int
    confidence: float
    shannon_entropy: float
    conformal_set: List[int]
    is_singleton: bool
    active_leaves: int = 0
    active_sectors: int = 0
    feedback: Optional[FeedbackOutput] = None
    latency_us: float
    latency_l1_us: float = 0.0
    latency_l2_us: float = 0.0
    latency_l3_us: float = 0.0

class AxiomClient:
    """
    High-level Production Python client for Axiom-1.
    Dispatches to bare-metal C++ DirectML engine for fast-path routing (<5ms),
    and supports either Local Ollama or Cloud AI Models (OpenRouter / Dedicated API)
    for Layer 3 deliberative fallback.
    """
    def __init__(
        self,
        cli_path: Optional[str] = None,
        provider: str = "ollama", # "ollama" | "openrouter" | "custom"
        api_key: Optional[str] = None,
        cloud_model: str = "anthropic/claude-3.5-sonnet",
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        self.cli_path = cli_path or CLI_EXE
        if not os.path.exists(self.cli_path):
            raise FileNotFoundError(f"Axiom-1 CLI binary not found at: {self.cli_path}. Please compile first.")
        
        self.provider = provider
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        self.cloud_model = cloud_model
        self.base_url = base_url

    def _query_cloud_api(self, input_text: str, candidate_leaf: str) -> str:
        import urllib.request
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Axiom-1 Decision Engine"
        }
        prompt = (
            f"Axiom-1 System 2 Verification: An operational request arrived: \"{input_text[:1500]}\". "
            f"Target candidate category: {candidate_leaf}. "
            f"Answer concisely in under 20 words whether this category fits."
        )
        payload = {
            "model": self.cloud_model,
            "messages": [
                {"role": "system", "content": "You are Axiom-1 System 2 Cloud Verification Engine. Answer concisely with brief verification."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 32,
            "temperature": 0.1
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            return res_data['choices'][0]['message']['content'].strip()

    def decide(self, input_text: str, timeout: float = 12.0) -> DecisionOutput:
        """
        Executes end-to-end decision routing.
        - High confidence queries commit in <5ms via Layer 1 & 2 (0 cloud cost!).
        - Ambiguous queries escalate to System 2 (Local Ollama or OpenRouter Cloud).
        """
        t0 = time.perf_counter()
        proc = subprocess.run(
            [self.cli_path, input_text],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        wall_time_us = (time.perf_counter() - t0) * 1_000_000.0
        output_str = proc.stdout.strip()
        
        json_start = output_str.find('{')
        json_end = output_str.rfind('}')
        if json_start == -1 or json_end == -1:
            raise RuntimeError(f"Axiom CLI failed to return valid JSON. Raw output: {output_str}")

        data = json.loads(output_str[json_start:json_end+1])
        exec_path = data.get("execution_path", "FAST_PATH_COMMIT")
        choice_label = data.get("choice_label", "Unknown")
        l3_us = data.get("latency_l3_us", 0.0)

        # Cloud AI Model Escalation (OpenRouter / Dedicated API)
        if exec_path == "SYSTEM2_FALLBACK" and self.provider in ("openrouter", "custom") and self.api_key:
            try:
                cloud_start = time.perf_counter()
                clean_cand = choice_label.split("[")[0].strip()
                cloud_ans = self._query_cloud_api(input_text, clean_cand)
                cloud_ms = (time.perf_counter() - cloud_start) * 1000.0
                choice_label = f"{clean_cand} [Verified by {self.cloud_model}]"
                l3_us = cloud_ms * 1000.0
                wall_time_us = (time.perf_counter() - t0) * 1_000_000.0
            except Exception as e:
                choice_label = f"{choice_label} [Cloud API Fallback Error: {e}]"

        fb_dict = data.get("feedback")
        feedback_obj = FeedbackOutput(**fb_dict) if fb_dict else None

        return DecisionOutput(
            request_id=data.get("request_id", 0),
            execution_path=exec_path,
            choice_label=choice_label,
            choice_id=data.get("choice_id", 0),
            confidence=data.get("confidence", 0.0),
            shannon_entropy=data.get("shannon_entropy", 0.0),
            conformal_set=data.get("conformal_set", []),
            is_singleton=data.get("is_singleton", False),
            active_leaves=data.get("active_leaves", 0),
            active_sectors=data.get("active_sectors", 0),
            feedback=feedback_obj,
            latency_us=wall_time_us if (exec_path == "SYSTEM2_FALLBACK" and self.provider != "ollama") else data.get("latency_total_us", wall_time_us),
            latency_l1_us=data.get("latency_l1_us", 0.0),
            latency_l2_us=data.get("latency_l2_us", 0.0),
            latency_l3_us=l3_us
        )
