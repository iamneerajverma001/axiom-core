@echo off
setlocal
title Axiom Vision-Tensor: Rigorous Physical Testing Suite
echo =====================================================================
echo           AXIOM VISION-TENSOR: PHYSICAL TESTING & STRESS BENCHMARK
echo =====================================================================
echo.
echo Launching rigorous physical mouse click testing and 50-query stress suite...
echo.

python "%~dp0tests\rigorous_vision_tensor_test.py"

echo.
echo =====================================================================
echo Test run complete. Report saved to reports\vision_tensor_physical_audit.json
echo =====================================================================
pause
