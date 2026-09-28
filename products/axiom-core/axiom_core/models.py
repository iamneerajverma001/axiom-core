"""
Axiom-Core Type Definitions & Pydantic Data Models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

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
