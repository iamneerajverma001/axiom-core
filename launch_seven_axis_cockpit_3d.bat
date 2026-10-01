@echo off
setlocal
echo =====================================================================
echo    AXIOM-CORE v3.0: 7-AXIS REDUNDANT ROBOTIC ARM MISSION CONTROL     
echo =====================================================================
echo.
echo [*] Initializing 7-DOF Kinematic Reflex Kernel...
echo [*] Sub-Millimeter Insertion Trajectory & Dynamic Obstacle Evasion...
echo [*] Nullspace Swiveling & Ville's Martingale Shock Shield...
echo.

python "%~dp0examples\axiom_seven_axis_cockpit_3d.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Cockpit exited with error code %ERRORLEVEL%
    pause
)
