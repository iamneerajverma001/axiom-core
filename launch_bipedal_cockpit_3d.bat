@echo off
title Axiom-Core v3.0 // Humanoid Bipedal Reflex Cockpit
color 0B
echo =====================================================================
echo    AXIOM-CORE v3.0 // 1,000 Hz BIPEDAL HUMANOID BALANCE COCKPIT     
echo    - Linear Inverted Pendulum Model (LIPM) & Capture Point Dynamics 
echo    - Zero Moment Point (ZMP) Support Polygon Barrier Monitoring     
echo    - Ville's Martingale Stumble/Slip Interlock                      
echo    - Interactive Perturbation & Physical Kick Impulses              
echo =====================================================================
echo.
python examples\axiom_bipedal_cockpit_3d.py
pause
