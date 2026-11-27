# Start the HarmonyMentor backend in fully local chatbot mode (no cloud, no API key).
#   LLM       : local QLoRA adapter on Qwen3-4B (WSL)
#   Retrieval : e5 embeddings + local Qdrant index (default: v4, 82 chunks L01-L08)
# Safe by design: uses a TEMP COPY of the Qdrant index, a TEMP SQLite database and a random JWT secret.
# It does not touch harmonymentor_dev.db, the index in outputs/, or any production service.
# Usage (PowerShell):  .\scripts\run_local_chatbot.ps1 [-Port 8000] [-Python <path to python.exe>]
param(
    [int]$Port = 8000,
    [string]$Index = "rag_L01_L08_index_20261127_v4",
    [string]$Collection = "hm_lessons_L01_L08_e5_v4",
    [string]$Python = ""
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$out = Join-Path $root "outputs"
if (-not $Python) { $Python = Join-Path $out "rag_l01_qdrant_pilot_20261125T154026Z\venv\Scripts\python.exe" }

$qdrantSrc = Join-Path $out "$Index\qdrant"
$e5 = Join-Path $out "rag_l01_qdrant_pilot_20261125T154026Z\e5"
$adapter = Join-Path $out "hm_m6_qlora_20261126\adapter"
foreach ($p in @($Python, $qdrantSrc, $e5, $adapter)) {
    if (-not (Test-Path $p)) { throw "Missing required path: $p" }
}

$work = Join-Path ([IO.Path]::GetTempPath()) ("hm_local_chatbot_" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $work | Out-Null
Copy-Item $qdrantSrc (Join-Path $work "qdrant") -Recurse
Get-ChildItem (Join-Path $work "qdrant") -Recurse -Force -Filter ".lock" | Remove-Item -Force

$rng = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($rng)

$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
$env:APP_ENV = "development"
$env:AI_ENABLED = "1"
$env:SHOW_DRAFT_CONTENT = "0"
$env:DATABASE_URL = "sqlite:///" + ((Join-Path $work "local_chatbot.db") -replace "\\", "/")
$env:JWT_SECRET = [Convert]::ToBase64String($rng)
$env:TUTOR_LLM_PROVIDER = "local_qlora"
$env:TUTOR_VECTOR_BACKEND = "qdrant"
$env:QDRANT_LOCAL_PATH = (Join-Path $work "qdrant")
$env:QDRANT_URL = ""
$env:QDRANT_COLLECTION = $Collection
$env:LOCAL_EMBED_DIR = $e5
$env:LOCAL_QLORA_ADAPTER_DIR = $adapter
$env:LOCAL_QLORA_SNAPSHOT_ROOT = "/home/thang/hm-qlora-resolve-guj5dVKF/verified-model-mhw5dy_8"
$env:LOCAL_QLORA_WSL_PYTHON = "/home/thang/hm-qlora-resolve-guj5dVKF/venv/bin/python"
$env:AI_DAILY_QUOTA = "200"
$env:AI_GLOBAL_DAILY_BUDGET = "400"

Write-Host "Index: $Index / $Collection"
Write-Host "Temp workspace: $work"
Write-Host "Starting backend on http://127.0.0.1:$Port (Ctrl+C to stop)"
Set-Location (Join-Path $root "backend")
& $Python -X utf8 -m uvicorn app.main:app --host 127.0.0.1 --port $Port
