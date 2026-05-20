<#
.SYNOPSIS
Runs Image2pdf validation for the GoalLite workflow.

.DESCRIPTION
This script fails on first error, prefers a local virtual environment when present,
installs runtime and test dependencies, runs compile checks, runs pytest, and runs
CLI smoke tests with generated temporary images.
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

& $Python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 'Python 3.11 or newer is required.')"

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
    Write-Host "    Passed: $Name" -ForegroundColor Green
}

Invoke-Step "Install runtime dependencies" {
    & $Python -m pip install -r requirements.txt
}

Invoke-Step "Install test dependencies" {
    & $Python -m pip install pytest pypdf
}

Invoke-Step "Compile project modules" {
    & $Python -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py
}

Invoke-Step "Run pytest" {
    & $Python -m pytest
}

Invoke-Step "Run CLI help smoke test" {
    & $Python image2pdf.py --help | Out-Null
}

Invoke-Step "Run generated-image CLI smoke tests" {
    $TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("image2pdf-validation-" + [System.Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $TempRoot | Out-Null
    try {
        $InputDir = Join-Path $TempRoot "images"
        $OutputDir = Join-Path $TempRoot "out"
        New-Item -ItemType Directory -Path $InputDir | Out-Null
        New-Item -ItemType Directory -Path $OutputDir | Out-Null

        $Generator = Join-Path $TempRoot "make_images.py"
        @'
from pathlib import Path
from PIL import Image

root = Path(__import__("sys").argv[1])
Image.new("RGB", (30, 20), (220, 30, 30)).save(root / "page2.jpg", dpi=(72, 72))
Image.new("RGB", (40, 20), (30, 220, 30)).save(root / "page10.jpg", dpi=(72, 72))
Image.new("RGBA", (20, 20), (30, 30, 220, 128)).save(root / "page1.png", dpi=(72, 72))
'@ | Set-Content -LiteralPath $Generator -Encoding UTF8

        & $Python $Generator $InputDir

        $CombinedBase = Join-Path $TempRoot "combined"
        & $Python image2pdf.py `
            (Join-Path $InputDir "page2.jpg") `
            (Join-Path $InputDir "page10.jpg") `
            (Join-Path $InputDir "page1.png") `
            --sort `
            --output $CombinedBase

        $CombinedPdf = Join-Path $TempRoot "combined.pdf"
        if (-not (Test-Path $CombinedPdf)) {
            throw "Combined smoke test did not create $CombinedPdf"
        }

        & $Python image2pdf.py --input-dir $InputDir --mode split --output-dir $OutputDir --title page --overwrite

        $SplitOutputs = Get-ChildItem -LiteralPath $OutputDir -Filter "page-*.pdf"
        if ($SplitOutputs.Count -ne 3) {
            throw "Split smoke test expected 3 PDFs but found $($SplitOutputs.Count)"
        }
    }
    finally {
        if (Test-Path $TempRoot) {
            Remove-Item -LiteralPath $TempRoot -Recurse -Force
        }
    }
}

Write-Host ""
Write-Host "==> All Image2pdf validation steps passed" -ForegroundColor Green
