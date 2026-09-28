@echo off
title Axiom-1 Decision Engine Studio
echo ==================================================================
echo           AXIOM-1 DECISION ENGINE & VISUAL STUDIO
echo ==================================================================
echo [1/2] Launching REST Bridge Server on port 3000...
start "" http://localhost:3000
python ui\server.py
pause
