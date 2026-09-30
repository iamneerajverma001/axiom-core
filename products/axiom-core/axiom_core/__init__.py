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
    DecisionOutput,
    ChoiceResult,
    ScoreResult,
    NoulResult,
    TypedQuestion
)
from .conformal import MartingaleSafetyGate, BrierCalibrator
from .ipc_bridge import AxiomIpcBridge
from .client import AxiomClient
from .wire_protocol import FixOrder, RawPacket

__version__ = "1.2.0"
__all__ = [
    "AxiomClient",
    "AxiomIpcBridge",
    "MartingaleSafetyGate",
    "BrierCalibrator",
    "FixOrder",
    "RawPacket",
    "DecisionOutput",
    "FeedbackOutput",
    "ChoiceResult",
    "ScoreResult",
    "NoulResult",
    "TypedQuestion",
    "LeafDefinition",
    "SectorDefinition",
    "SchemaDefinition",
]
