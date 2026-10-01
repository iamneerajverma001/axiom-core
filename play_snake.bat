@echo off
title Axiom Core - Real-Time Autonomous Neuromorphic Snake
echo =====================================================================
echo    LAUNCHING AXIOM CORE // REAL-TIME AUTONOMOUS SNAKE ENGINE
echo =====================================================================
echo.
echo Controls:
echo   - [SPACE] Toggle Autonomous Autopilot (Axiom Core vs Manual)
echo   - [W A S D / Arrows] Manual steer
echo   - [R] Reset Board
echo.
python examples/autonomous_snake_demo.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo GUI launch encountered an issue, launching Terminal ASCII HUD mode...
    python examples/autonomous_snake_demo.py --terminal
)
pause
