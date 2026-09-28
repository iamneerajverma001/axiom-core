@echo off
title Axiom-OS Neuromorphic Workstation Copilot
echo =====================================================================
echo                  AXIOM-OS NEUROMORPHIC COPILOT
echo        System 1: Bare-Metal Microsecond Reflex Arc (<15us)
echo        System 2: ReAct Cognitive Multi-Step Planner & Actuator
echo =====================================================================

cd /d "%~dp0"

echo [1/3] Starting Axiom-OS Unified Gateway on Port 3000...
start /b python ui/server.py

echo [2/3] Waiting for server initialization...
timeout /t 2 /nobreak >nul

echo [3/3] Opening Axiom-OS Desktop Studio...
start http://localhost:3000

echo =====================================================================
echo Axiom-OS is LIVE!
echo Desktop Studio : http://localhost:3000
echo Mobile Cockpit : http://localhost:3000/mobile.html
echo Floating Orb   : http://localhost:3000/floating.html
echo =====================================================================
