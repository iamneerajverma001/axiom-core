"""
Axiom-Core: Bare-Metal Neuromorphic Decision Engine & C++20 SDK
Physical Machine Era (v3.0.0): Sub-microsecond decisions, biological LIF dynamics,
Control Lyapunov-Barrier Martingales, MAVLink, DVS Event Ingestion, Silicon Verilog Synthesizer,
and 3D Swarm Fleet Coordination.
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

# Physical Machine Era v3.0 Components
from .lyapunov_barrier import (
    LyapunovBarrierInterlock,
    State3D,
    ControlInput3D,
    Obstacle3D,
    BarrierResult
)
from .mavlink_bridge import (
    MavlinkBridge,
    AttitudeTelemetry,
    AttitudeTarget
)
from .event_camera_dvs import (
    EventCameraDvs,
    DvsEvent
)
from .fpga_verilog_synth import (
    FpgaVerilogSynthesizer,
    SynthOptions
)
from .swarm_fleet import (
    SwarmFleetCoordinator,
    DroneAgent
)
from .certifier import (
    VilleSafetyCertifier,
    CertificationSpec,
    CertificationReport
)
from .sim2real_bridge import (
    Sim2RealBridge,
    SimState,
    SimCommand
)
from .bipedal_locomotion import (
    BipedalLocomotionReflex,
    ComState,
    FootContact,
    CapturePointResult
)

__version__ = "3.0.0"
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
    # Physical Machine Era v3.0
    "LyapunovBarrierInterlock",
    "State3D",
    "ControlInput3D",
    "Obstacle3D",
    "BarrierResult",
    "MavlinkBridge",
    "AttitudeTelemetry",
    "AttitudeTarget",
    "EventCameraDvs",
    "DvsEvent",
    "FpgaVerilogSynthesizer",
    "SynthOptions",
    "SwarmFleetCoordinator",
    "DroneAgent",
    "VilleSafetyCertifier",
    "CertificationSpec",
    "CertificationReport",
    "Sim2RealBridge",
    "SimState",
    "SimCommand",
    "BipedalLocomotionReflex",
    "ComState",
    "FootContact",
    "CapturePointResult",
]
