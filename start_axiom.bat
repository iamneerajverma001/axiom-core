@echo off
title Axiom-1 Universal Integration Hub
echo ================================================================
echo    AXIOM-1: UNIVERSAL INTEGRATION HUB & OPENAI GATEWAY
echo ================================================================
echo.

cd /d "%~dp0"

echo [1/3] Verifying Axiom Native Engine Binary...
if not exist "axiom_cli.exe" (
    echo [ERROR] axiom_cli.exe not found! Please build it first.
    pause
    exit /b 1
)
echo [OK] axiom_cli.exe is ready.

echo [2/3] Checking Ollama Local LLM Connection...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Ollama is not detected on port 11434. 
    echo System 2 Fallback will run in standalone mode or use Cloud AI API.
) else (
    echo [OK] Ollama is active on http://127.0.0.1:11434.
)

echo [3/3] Launching Axiom Integration Server on http://localhost:3000...
echo.
echo Available Endpoints:
echo   - OpenAI Drop-in API : http://localhost:3000/v1/chat/completions
echo   - TradingView Hook   : http://localhost:3000/webhook/tradingview
echo   - Decision REST API  : http://localhost:3000/api/decide
echo   - Interactive Studio : http://localhost:3000/
echo.
echo Press Ctrl+C to terminate server.
echo.

python ui/server.py
pause
