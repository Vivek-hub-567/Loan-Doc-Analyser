# start_all.ps1
# Launch LoanGuard backend and frontend in separate PowerShell windows,
# ensure model exists (train if missing), and poll the health endpoint.

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BackendDir = Join-Path $ScriptRoot 'loanguard-backend'
$FrontendDir = Join-Path $ScriptRoot 'loanguard-frontend'

Write-Host "Starting LoanGuard backend and frontend from:`n  $BackendDir`n  $FrontendDir"

# --- Backend: ensure model, then start uvicorn in new window ---
function Start-Backend {
    Push-Location $BackendDir
    if (-not (Test-Path (Join-Path $BackendDir 'ml\model.pkl'))) {
        Write-Host "Model not found at ml/model.pkl — training (this may take several minutes)..."
        python -m ml.train_classifier
    }
    $cmd = "cd `"$BackendDir`"; uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
    Start-Process -FilePath powershell -ArgumentList '-NoExit','-Command',$cmd -WindowStyle Normal
    Pop-Location
}

# --- Frontend: ensure env, then start dev server in new window ---
function Start-Frontend {
    Push-Location $FrontendDir
    if (-not (Test-Path (Join-Path $FrontendDir '.env.local'))) {
        if (Test-Path (Join-Path $FrontendDir '.env.local.example')) {
            Copy-Item -Path (Join-Path $FrontendDir '.env.local.example') -Destination (Join-Path $FrontendDir '.env.local') -Force
            Write-Host "Created .env.local from example. Ensure NEXT_PUBLIC_API_URL points to http://localhost:8000/api/v1 if needed."
        }
    }

    $cmd = "cd `"$FrontendDir`"; npm install; npm run dev"
    Start-Process -FilePath powershell -ArgumentList '-NoExit','-Command',$cmd -WindowStyle Normal
    Pop-Location
}

# --- Poll backend health endpoint ---
function Wait-For-Health {
    $url = 'http://localhost:8000/api/v1/health'
    $timeout = 60  # seconds
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        try {
            $resp = Invoke-RestMethod -Uri $url -TimeoutSec 5
            Write-Host "Backend health: $($resp | ConvertTo-Json -Depth 3)"
            return $true
        } catch {
            Write-Host "Waiting for backend (health)... ($elapsed/$timeout)"
            Start-Sleep -Seconds 2
            $elapsed += 2
        }
    }
    Write-Host "Backend did not become healthy within $timeout seconds."
    return $false
}

# --- Run ---
Start-Backend
Start-Sleep -Seconds 3
$ok = Wait-For-Health
Start-Frontend

if ($ok) {
    Write-Host "Opening frontend at http://localhost:3000"
    Start-Process "http://localhost:3000"
} else {
    Write-Host "Frontend will still start, but backend health check failed — please inspect backend window for errors."
}
