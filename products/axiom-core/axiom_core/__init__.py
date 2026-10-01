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
from .matrix_martingale import MatrixMartingaleShield
from .merkle_audit import MerkleAuditLog
from .can_bus_protocol import CanFrame
from .itch_protocol import ItchOrder
from .swarm_fabric import SwarmReflexFabric
from .crdt_register_tree import CrdtRegisterTree
from .compiler import AxiomPolicyCompiler
from .telemetry_hud import AxiomTelemetryHUD

__version__ = "2.0.0"
__all__ = [
    "AxiomClient",
    "AxiomIpcBridge",
    "MartingaleSafetyGate",
    "BrierCalibrator",
    "MatrixMartingaleShield",
    "MerkleAuditLog",
    "CanFrame",
    "ItchOrder",
    "SwarmReflexFabric",
    "CrdtRegisterTree",
    "AxiomPolicyCompiler",
    "AxiomTelemetryHUD",
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
