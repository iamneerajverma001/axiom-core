"""
Axiom-Core: Bare-Metal Neuromorphic Decision Engine & C++20 SDK
Sub-15 microsecond decisions, 15,000 decisions/sec, zero-copy shared memory IPC,
and distribution-free Martingale conformal safety barriers.
"""

from .models import (
    LeafDefinition,
    SectorDefinition,
    SchemaDefinition,
    FeedbackOutput,
    DecisionOutput
)
from .conformal import MartingaleSafetyGate
from .ipc_bridge import AxiomIpcBridge
from .client import AxiomClient

__version__ = "1.0.0"
__all__ = [
    "AxiomClient",
    "AxiomIpcBridge",
    "MartingaleSafetyGate",
    "DecisionOutput",
    "FeedbackOutput",
    "LeafDefinition",
    "SectorDefinition",
    "SchemaDefinition",
]
