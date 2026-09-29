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

# ==============================================================================
# TYPED QUESTION DECISION PRIMITIVES (JEV & LAYA PARITY + BARE-METAL SUPERIORITY)
# ==============================================================================

class ChoiceResult(BaseModel):
    """Discrete 1-of-N classification with calibrated posterior probabilities."""
    choice_id: int = 0
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Platt/Brier-calibrated probability")
    probabilities: Dict[str, float] = Field(default_factory=dict, description="Full calibrated probability distribution over options")
    conformal_set: List[str] = Field(default_factory=list, description="Guaranteed prediction set at 1 - alpha coverage")
    is_singleton: bool = True

class ScoreResult(BaseModel):
    """Continuous rubric scoring bounded in [0.0, 1.0] with predictive variance."""
    score: float = Field(..., description="Continuous score scalar")
    variance: float = 0.0
    rubric: str = ""
    is_calibrated: bool = True

class NoulResult(BaseModel):
    """Boolean predicate outcome with calibrated P(True) and ambiguity null-check."""
    value: bool = Field(..., description="Boolean decision state")
    probability: float = Field(..., ge=0.0, le=1.0, description="Calibrated P(True)")
    is_null: bool = Field(default=False, description="True if predictive entropy exceeds ambiguity threshold")
    confidence_guarantee: float = 0.99
    martingale_safety_certified: bool = True

class TypedQuestion(BaseModel):
    """Schema declaration for typed machine-native questions."""
    question_type: str = Field(..., description="'choice' | 'score' | 'noul'")
    question: str
    options: Optional[List[str]] = None
    rubric: Optional[str] = None
    threshold: float = 0.50

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
    
    # First-class Typed Decision Primitives
    choice: Optional[ChoiceResult] = None
    score: Optional[ScoreResult] = None
    noul: Optional[NoulResult] = None
    
    calibrated_brier_score: float = 0.0
    martingale_safety_certified: bool = True

    feedback: Optional[FeedbackOutput] = None
    latency_us: float
    latency_l1_us: float = 0.0
    latency_l2_us: float = 0.0
    latency_l3_us: float = 0.0
