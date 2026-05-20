# VALIDATION.md

## Purpose

This file defines how to prove Image2pdf works. Codex must use this as the validation contract and record results in `PROGRESS.md`.

## Environment setup

Use Python 3.11 or newer. Prefer the local virtual environment if it exists. Validation scripts must fail if the selected interpreter is older than Python 3.11.

PowerShell:

```powershell
if (Test-Path .\.venv\Scripts\python.exe) { .\.venv\Scripts\python.exe -m pip install -r requirements.txt } else { python -m pip install -r requirements.txt }
if (Test-Path .\.venv\Scripts\python.exe) { .\.venv\Scripts\python.exe -m pip install pytest pypdf } else { python -m pip install pytest pypdf }
```

Bash:

```bash
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; elif command -v python3.11 >/dev/null 2>&1; then PY=python3.11; else PY=python3; fi
"$PY" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required.")
PY
"$PY" -m pip install -r requirements.txt
"$PY" -m pip install pytest pypdf
```

## Validation commands

### 1. Import and compile checks

PowerShell:

```powershell
python -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py
```

Expected result:

- All project modules compile without syntax errors.

If it fails:

- Fix the syntax/import issue before running tests.

### 2. Unit and acceptance tests

```powershell
python -m pytest
```

Expected result:

- All tests pass.

If it fails:

- Read the failure, fix the smallest relevant issue, rerun the failed test, then rerun the full suite.

### 3. CLI help smoke test

```powershell
python image2pdf.py --help
```

Expected result:

- Command exits successfully and displays documented CLI options.

If it fails:

- Fix argparse/import/runtime setup before continuing.

### 4. CLI generated-image smoke tests

Create temporary images with Pillow, then run:

```powershell
python image2pdf.py .\tmp\page2.jpg .\tmp\page10.jpg .\tmp\page1.png --sort --output .\tmp\combined
python image2pdf.py --input-dir .\tmp --mode split --output-dir .\tmp\out --title page --overwrite
```

Expected result:

- Combined mode creates a valid PDF.
- Split mode creates one PDF per valid generated image.
- Output names without `.pdf` are accepted.

If it fails:

- Fix CLI/conversion behavior and rerun the smoke tests.

### 5. Global validation script

PowerShell:

```powershell
./scripts/Validate-GoalLite.ps1
```

Bash:

```bash
./scripts/validate.sh
```

Expected result:

- Dependencies install if needed, compile checks pass, pytest passes, and CLI smoke tests pass.

If it fails:

- Fix the reported issue before moving to the next milestone.

## Manual GUI validation

Manual GUI validation is required because automated Tkinter display checks vary by environment.

1. Run:

   ```powershell
   python image2pdf_gui.py
   ```

2. Confirm the window opens.
3. Select at least two images or an input folder.
4. Select an output folder and title.
5. Create a combined PDF.
6. Create split PDFs.
7. Confirm status/log output reports success.
8. Record the result in `PROGRESS.md`.

## Validation repair policy

When validation fails:

1. Read the error.
2. Identify the smallest likely fix.
3. Apply the fix.
4. Rerun the failed command.
5. Rerun `./scripts/Validate-GoalLite.ps1` if the failed command passes.
6. Update `PROGRESS.md`.

Stop if the same failure repeats after two repair attempts.
