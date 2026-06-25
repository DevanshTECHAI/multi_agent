# ═══════════════════════════════════════════════════════
#  MoA Setup — Sets environment variable for OpenRouter
# ═══════════════════════════════════════════════════════

Write-Host ""
Write-Host "  ╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║  MoA — Mixture of Agents Setup       ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Set for current session
$env:OPENROUTER_API_KEY = Read-Host "  Enter your OpenRouter API key"

# Persist for future sessions
[System.Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", $env:OPENROUTER_API_KEY, "User")

Write-Host ""
Write-Host "  ✓ API key set for current session and saved permanently!" -ForegroundColor Green
Write-Host ""
Write-Host "  Usage:" -ForegroundColor Yellow
Write-Host "    python moa.py `"your prompt here`"" -ForegroundColor White
Write-Host "    python moa.py --verbose `"your prompt`"" -ForegroundColor White
Write-Host "    python moa.py --mode judge `"your prompt`"" -ForegroundColor White
Write-Host "    python moa.py --list-models" -ForegroundColor White
Write-Host ""
