"""
Axiom Continuous Online Policy Optimizer & Adaptive Reflex Pruner
Reinforces reflex leaves based on physical Windows execution telemetry
(CPU reduction, execution latency, exit codes) and automatically evicts deteriorating branches.
"""

import json
import math
import os
import tempfile
import time
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_FILE = os.path.join(PROJECT_ROOT, "skills", "learned_skills.json")
QUARANTINE_FILE = os.path.join(PROJECT_ROOT, "skills", "quarantined_skills.json")

def _atomic_write_json(file_path: str, data: Any):
    """Atomically saves data to disk using temporary file and atomic replacement."""
    dir_name = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(dir_name, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix=".tmp_axiom_", suffix=".json")
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise

class OnlinePolicyOptimizer:
    def __init__(
        self,
        learning_rate: float = 0.05,
        baseline_momentum: float = 0.90,
        half_life_days: float = 7.0
    ):
        self.lr = learning_rate
        self.momentum = baseline_momentum
        self.half_life_s = half_life_days * 86400.0
        self.decay_lambda = math.log(2.0) / self.half_life_s
        self.running_baseline_reward = 0.50
        self.stats = {
            "updates_count": 0,
            "reinforcements": 0,
            "penalties": 0,
            "pruned_count": 0
        }

    def compute_execution_reward(
        self,
        success: bool,
        latency_ms: float,
        cpu_delta_pct: float = 0.0,
        exit_code: int = 0
    ) -> float:
        """
        Calculates scalar reinforcement reward from physical Windows telemetry.
        Range: [-1.0, 1.5]
        """
        if not success or exit_code != 0:
            return -1.0

        r_exit = 0.50
        r_lat = 0.30 * min(1.0, math.log1p(1000.0 / max(1.0, latency_ms)) / 7.0)
        r_cpu = 0.20 * min(1.0, max(0.0, cpu_delta_pct) / 20.0)

        total_reward = r_exit + r_lat + r_cpu
        return float(min(1.5, max(-1.0, total_reward)))

    def record_feedback_and_update(
        self,
        skill_id: str,
        success: bool,
        latency_ms: float,
        cpu_delta_pct: float = 0.0,
        exit_code: int = 0
    ) -> Dict[str, Any]:
        """
        Performs REINFORCE online policy update on the matching leaf in learned_skills.json.
        """
        if not os.path.exists(SKILLS_FILE):
            return {"updated": False, "error": "No skills file found"}

        try:
            with open(SKILLS_FILE, 'r', encoding='utf-8') as f:
                skills = json.load(f)
        except Exception as e:
            return {"updated": False, "error": str(e)}

        target_skill = None
        for s in skills:
            if s.get("skill_id") == skill_id:
                target_skill = s
                break

        if not target_skill:
            return {"updated": False, "reason": "Skill not found in dynamic registry"}

        reward = self.compute_execution_reward(success, latency_ms, cpu_delta_pct, exit_code)
        advantage = reward - self.running_baseline_reward
        self.running_baseline_reward = (self.momentum * self.running_baseline_reward) + ((1.0 - self.momentum) * reward)

        old_conf = float(target_skill.get("confidence", 0.90))
        now = time.time()
        last_exec = float(target_skill.get("last_executed", target_skill.get("created_at", now)))
        dt = max(0.0, now - last_exec)
        # Continuous Policy Optimization: Stale skills regress exponentially toward baseline
        if dt > 3600.0:
            decay_factor = math.exp(-self.decay_lambda * dt)
            old_conf = 0.50 + (old_conf - 0.50) * decay_factor

        # REINFORCE policy step
        new_conf = old_conf + (self.lr * advantage)
        new_conf = max(0.10, min(0.999, new_conf))
        target_skill["confidence"] = round(new_conf, 4)

        target_skill["success_count"] = target_skill.get("success_count", 0) + (1 if success else 0)
        target_skill["failure_count"] = target_skill.get("failure_count", 0) + (0 if success else 1)
        target_skill["last_executed"] = time.time()

        # Latency exponential moving average
        old_lat = float(target_skill.get("avg_latency_us", 30))
        new_lat_us = latency_ms * 1000.0
        target_skill["avg_latency_us"] = int(round((0.85 * old_lat) + (0.15 * new_lat_us)))

        self.stats["updates_count"] += 1
        if advantage >= 0:
            self.stats["reinforcements"] += 1
        else:
            self.stats["penalties"] += 1

        # Check for Pruning / Quarantine
        pruned = False
        if target_skill["failure_count"] >= 3 and target_skill["confidence"] < 0.25:
            skills = [s for s in skills if s.get("skill_id") != skill_id]
            self._quarantine_skill(target_skill)
            self.stats["pruned_count"] += 1
            pruned = True

        # Save back to file atomically
        try:
            _atomic_write_json(SKILLS_FILE, skills)
        except Exception:
            pass

        return {
            "updated": True,
            "skill_id": skill_id,
            "skill_name": target_skill.get("name"),
            "reward": round(reward, 3),
            "advantage": round(advantage, 3),
            "old_confidence": old_conf,
            "new_confidence": round(new_conf, 4),
            "pruned": pruned,
            "baseline_reward": round(self.running_baseline_reward, 3)
        }

    def apply_time_decay_sweep(self) -> int:
        """Sweeps entire skill database and applies half-life decay to stale skills."""
        if not os.path.exists(SKILLS_FILE):
            return 0
        try:
            with open(SKILLS_FILE, 'r', encoding='utf-8') as f:
                skills = json.load(f)
        except Exception:
            return 0
        now = time.time()
        decayed_count = 0
        for s in skills:
            last_exec = float(s.get("last_executed", s.get("created_at", now)))
            dt = max(0.0, now - last_exec)
            if dt > 86400.0: # older than 1 day
                conf = float(s.get("confidence", 0.90))
                factor = math.exp(-self.decay_lambda * dt)
                new_conf = 0.50 + (conf - 0.50) * factor
                s["confidence"] = round(max(0.10, min(0.99, new_conf)), 4)
                decayed_count += 1
        if decayed_count > 0:
            try:
                _atomic_write_json(SKILLS_FILE, skills)
            except Exception:
                pass
        return decayed_count

    def _quarantine_skill(self, skill_obj: dict):
        quarantined = []
        if os.path.exists(QUARANTINE_FILE):
            try:
                with open(QUARANTINE_FILE, 'r', encoding='utf-8') as f:
                    quarantined = json.load(f)
            except Exception:
                quarantined = []
        quarantined.append(skill_obj)
        try:
            _atomic_write_json(QUARANTINE_FILE, quarantined)
        except Exception:
            pass

# Global Singleton
policy_optimizer = OnlinePolicyOptimizer()
