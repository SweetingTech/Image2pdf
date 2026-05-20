<#
.SYNOPSIS
Sets up Image2pdf and starts the Tkinter GUI.

.DESCRIPTION
This script prefers an existing local virtual environment, creates .venv when
none is found, installs runtime dependencies from requirements.txt, and then
launches image2pdf_gui.py.
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Command
}

function Test-PythonVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Python,
        [string[]]$Arguments = @()
    )

    & $Python @Arguments -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" *> $null
    return $LASTEXITCODE -eq 0
}

function Get-SystemPython {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        if (Test-PythonVersion -Python "py" -Arguments @("-3.11")) {
            return @("py", "-3.11")
        }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        if (Test-PythonVersion -Python "python") {
            return @("python")
        }
    }

    throw "Python 3.11 or newer is required. Install Python 3.11+ and rerun this script."
}

$VenvCandidates = @(
    (Join-Path $RepoRoot ".venv"),
    (Join-Path $RepoRoot "venv")
)

$VenvDir = $null
foreach ($Candidate in $VenvCandidates) {
    if (Test-Path (Join-Path $Candidate "Scripts\python.exe")) {
        $VenvDir = $Candidate
        break
    }
}

if ($null -eq $VenvDir) {
    $VenvDir = Join-Path $RepoRoot ".venv"
    $SystemPython = @(Get-SystemPython)
    $PythonExe = $SystemPython[0]
    $PythonArgs = @()
    if ($SystemPython.Count -gt 1) {
        $PythonArgs = $SystemPython[1..($SystemPython.Count - 1)]
    }

    Invoke-Step "Create virtual environment" {
        & $PythonExe @PythonArgs -m venv $VenvDir
    }
}
else {
    Write-Host "Using existing virtual environment: $VenvDir" -ForegroundColor Green
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment Python was not found at $VenvPython."
}

Invoke-Step "Verify Python version" {
    & $VenvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 'Python 3.11 or newer is required.')"
}

Invoke-Step "Install runtime dependencies" {
    & $VenvPython -m pip install -r requirements.txt
}

Invoke-Step "Start Image2pdf GUI" {
    & $VenvPython image2pdf_gui.py
}
