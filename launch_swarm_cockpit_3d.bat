@echo off
title Axiom-Core v3.0 // Planetary 3D Swarm Fleet Command
color 0B
echo =====================================================================
echo    AXIOM-CORE v3.0 // PHYSICAL MACHINE ERA: 3D SWARM FLEET COMMAND   
echo    - 5 Autonomous 6-DOF Quadcopters in Coordinated 3D Airspace      
echo    - Control Lyapunov-Barrier Functions + Ville's Martingale Interlock
echo    - Decentralized CRDT Peer-to-Peer Gossip Mesh                    
echo    - Live MAVLink 2.0 & CAN-FD Wire Bus Telemetry Stream            
echo =====================================================================
echo.
python examples\axiom_swarm_cockpit_3d.py
pause
