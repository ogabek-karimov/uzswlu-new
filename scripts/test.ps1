# Hamma testlar (Windows): backend (Django) + frontend (Node) + admin (tur tekshiruvi, node_modules bo'lsa).
#   .\scripts\test.ps1          — to'liq
#   .\scripts\test.ps1 -Fast    — sekin (`slow`) testlarsiz
param([switch]$Fast)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$flags = @('--parallel'); if ($Fast) { $flags += '--exclude-tag=slow' }

Write-Host '▶ backend';  Push-Location "$root\backend";  python manage.py test @flags; if ($LASTEXITCODE) { exit $LASTEXITCODE }; Pop-Location
Write-Host '▶ frontend (server/utils)'; Push-Location "$root\frontend"; npm run --silent test:last-good; if ($LASTEXITCODE) { exit $LASTEXITCODE }; Pop-Location
if (Test-Path "$root\admin\node_modules") { Write-Host '▶ admin (vue-tsc)'; Push-Location "$root\admin"; npm run --silent typecheck; if ($LASTEXITCODE) { exit $LASTEXITCODE }; Pop-Location }
else { Write-Host "· admin: node_modules yo'q — tur tekshiruvi o'tkazib yuborildi (cd admin; npm ci)" }
Write-Host "✔ hammasi o'tdi"
