# Axiom-1 PowerShell Launcher
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   AXIOM-1: UNIVERSAL INTEGRATION HUB & OPENAI GATEWAY" -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Check binary
if (Test-Path ".\axiom_cli.exe") {
    Write-Host "[OK] axiom_cli.exe native bare-metal engine ready." -ForegroundColor Green
} else {
    Write-Host "[ERROR] axiom_cli.exe not found!" -ForegroundColor Red
    exit 1
}

# Check Ollama
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 2 -ErrorAction Stop
    $modelName = $res.models[0].name
    Write-Host "[OK] Local Ollama detected: $modelName" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Ollama not detected on port 11434. Cloud API or fallback mode active." -ForegroundColor Yellow
}

Write-Host "`nLaunching Axiom Server on http://localhost:3000..." -ForegroundColor Cyan
Write-Host "  -> OpenAI Drop-In API : http://localhost:3000/v1/chat/completions" -ForegroundColor White
Write-Host "  -> TradingView Hook   : http://localhost:3000/webhook/tradingview" -ForegroundColor White
Write-Host "  -> Visual Studio UI   : http://localhost:3000/" -ForegroundColor White
Write-Host "Press Ctrl+C to terminate.`n" -ForegroundColor DarkGray

python ui/server.py
