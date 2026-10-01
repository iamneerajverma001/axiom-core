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
from .manipulator_reflex import (
    ManipulatorReflexKernel,
    JointState,
    CartPose,
    ManipulatorResult
)
from .edge_daemon import (
    EdgeDaemonService,
    DaemonConfig,
    DaemonMetrics
)
from .seven_axis_arm import SevenAxisArm
from .full_humanoid import (
    FullHumanoidReflex,
    HumanoidState,
    KeypointFrames,
    WholeBodyCommand,
    HEAD_YAW, HEAD_PITCH,
    TORSO_YAW, TORSO_PITCH, TORSO_ROLL,
    L_SHOULDER_PITCH, L_SHOULDER_ROLL, L_SHOULDER_YAW,
    L_ELBOW_PITCH, L_FOREARM_ROLL, L_WRIST_PITCH, L_WRIST_ROLL,
    R_SHOULDER_PITCH, R_SHOULDER_ROLL, R_SHOULDER_YAW,
    R_ELBOW_PITCH, R_FOREARM_ROLL, R_WRIST_PITCH, R_WRIST_ROLL,
    L_HIP_YAW, L_HIP_ROLL, L_HIP_PITCH, L_KNEE_PITCH, L_ANKLE_PITCH, L_ANKLE_ROLL,
    R_HIP_YAW, R_HIP_ROLL, R_HIP_PITCH, R_KNEE_PITCH, R_ANKLE_PITCH, R_ANKLE_ROLL,
    PAYLOAD_GRIP, DOF as HUMANOID_DOF
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
    "ManipulatorReflexKernel",
    "JointState",
    "CartPose",
    "ManipulatorResult",
    "EdgeDaemonService",
    "DaemonConfig",
    "DaemonMetrics",
    "SevenAxisArm",
    "FullHumanoidReflex",
    "HumanoidState",
    "KeypointFrames",
    "WholeBodyCommand",
    "HUMANOID_DOF"
]

