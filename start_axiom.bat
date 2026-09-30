@echo off
title Axiom Neuromorphic Workstation
echo =====================================================================
echo                 AXIOM NEUROMORPHIC WORKSTATION
echo                  Unified Multi-Product Suite
echo =====================================================================
echo.
cd /d "%~dp0products\axiom-os"
call start_axiom_os.bat %*
