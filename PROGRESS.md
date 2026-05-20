# PROGRESS.md

## Current status

- Overall status: `Milestone 4 blocked`
- Current milestone: `Milestone 4: Documentation and final validation`
- Current checkpoint: `Persistent settings window and logo added; final Bash validation still blocked by Python version`
- Last updated: `2026-05-20`

## Current hypothesis

Documentation and scaffold files match the README contract, and PowerShell validation passes. Final completion is blocked because Bash/WSL only exposes Python 3.10.12, below the required Python 3.11+ target.

The project now includes a PowerShell startup launcher that prefers an existing `.venv` or `venv`, creates `.venv` when neither exists, installs runtime dependencies, and starts the Tkinter GUI.

Folder-based input now uses deterministic natural ordering by default, and the GUI enables natural sorting by default so page files such as `page1`, `page2`, and `page10` are assembled in reading order.

The GUI now has a toolbar/drop-zone layout, a shared output folder, queued folder/image jobs, per-item status, progress tracking, default folder-name titles, title override for selected queue items, and Japanese/Unicode title coverage.

README.md now documents the startup script, GUI queue workflow, shared output folder behavior, folder-name output titles, Windows drag/drop fallback, and Japanese/Unicode filename support. `.gitignore` excludes local test folders/files and generated Python/cache/output artifacts; `tests/test_image2pdf.py` was removed from Git's index only so it remains available locally for validation without being included in future GitHub pushes.

The Settings toolbar button now opens a real settings window. Saved settings are written to local `image2pdf_settings.yaml`, loaded on GUI startup, and applied to output folder, output mode, page size, standardization, natural sort, overwrite, and skip-invalid behavior. The settings file is ignored by Git. A root `image2pdf_logo.png` app/logo asset was added and is used as the Tk window icon when supported.

## Completed milestones

- [x] Milestone 0: GoalLite scaffold alignment
- [x] Milestone 1: Shared conversion core
- [x] Milestone 2: CLI behavior
- [x] Milestone 3: Tkinter GUI
- [ ] Milestone 4: Documentation and final validation

## Current milestone detail

### Milestone 3: Tkinter GUI

Tasks:

- [x] Read README.md, PLAN.md, PROGRESS.md, VALIDATION.md, and AGENTS.md.
- [x] Inspect `image2pdf_gui.py` against README.md and Milestone 3 acceptance criteria.
- [x] Verify GUI controls for files, input folder, output folder, title, mode, page size, standardize, sort, overwrite, and skip-invalid.
- [x] Verify GUI uses shared conversion logic.
- [x] Run GUI import/construction and conversion validation.
- [x] Run Milestone 3 validation commands.
- [x] Record validation results.

Files touched this checkpoint:

- `image2pdf_gui.py` - removed unsafe worker-thread Tk calls and run conversion on the Tk event thread.
- `tests/test_image2pdf.py` - added a GUI conversion flow test that creates a PDF through the Tkinter app object.
- `PROGRESS.md` - recorded Milestone 3 verification, validation results, fix, and next action.

What passed:

- `python -m pytest tests/test_image2pdf.py`
- `python -m py_compile image2pdf_gui.py`
- GUI integration smoke with generated images for combined and split output.
- `./scripts/Validate-GoalLite.ps1`

What failed:

- Initial GUI integration smoke failed with `RuntimeError: main thread is not in main loop`.

What was fixed:

- `image2pdf_gui.py` no longer calls Tk methods from a background thread during conversion.

### Milestone 4: Documentation and final validation

Tasks:

- [x] Read README.md, PLAN.md, PROGRESS.md, VALIDATION.md, and AGENTS.md.
- [x] Verify README examples and limitations against the current implementation.
- [x] Verify TASK_BRIEF.md, PLAN.md, PROGRESS.md, VALIDATION.md, and scripts are current.
- [x] Tighten validation scripts to enforce Python 3.11+.
- [x] Run PowerShell final validation.
- [ ] Run Bash final validation with Python 3.11+.
- [ ] Record final completed status.

### Startup launcher checkpoint

Tasks:

- [x] Read README.md, PLAN.md, PROGRESS.md, VALIDATION.md, TASK_BRIEF.md, AGENTS.md, and startup-relevant source files.
- [x] Add a startup script that checks for a virtual environment before setup.
- [x] Reuse an existing `.venv` or `venv` when present.
- [x] Create `.venv` when no virtual environment is found.
- [x] Install runtime dependencies from `requirements.txt`.
- [x] Start the Tkinter GUI with the virtual environment Python.
- [x] Run validation and record results.

Files touched this checkpoint:

- `Start-Image2pdf.ps1` - added setup-and-launch script for the GUI.
- `PROGRESS.md` - recorded startup launcher work and validation results.

What passed:

- PowerShell parser validation for `Start-Image2pdf.ps1`.
- `./scripts/Validate-GoalLite.ps1`

What failed:

- None in this checkpoint.

What was fixed:

- Added a single startup command path for first-run setup and GUI launch.

### Ordering checkpoint

Tasks:

- [x] Read README.md, PLAN.md, PROGRESS.md, VALIDATION.md, TASK_BRIEF.md, AGENTS.md, and ordering-relevant source files.
- [x] Inspect shared input expansion and GUI sorting behavior.
- [x] Make folder ingestion deterministic with natural ordering.
- [x] Enable natural sorting by default in the GUI.
- [x] Add regression coverage for folder order and GUI default sorting.
- [x] Run focused and global validation.

Files touched this checkpoint:

- `image2pdf_core.py` - natural-sorts folder images before appending them to selected inputs.
- `image2pdf_gui.py` - defaults the Natural sort toggle to enabled.
- `tests/test_image2pdf.py` - added folder ordering regression coverage and checked the GUI default.
- `PROGRESS.md` - recorded ordering fix and validation results.

What passed:

- `.\\.venv\\Scripts\\python.exe -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py`
- `.\\.venv\\Scripts\\python.exe -m pytest tests/test_image2pdf.py -q`
- Settings YAML round-trip smoke
- `./scripts/Validate-GoalLite.ps1`

What failed:

- None in this checkpoint.

What was fixed:

- Folder input no longer depends on filesystem enumeration order.
- GUI conversions default to natural sorting for page-numbered image filenames.

### GUI queue checkpoint

Tasks:

- [x] Read README.md, PLAN.md, PROGRESS.md, VALIDATION.md, TASK_BRIEF.md, AGENTS.md, and GUI source/test files.
- [x] Refresh the Tkinter UI toward the provided toolbar/drop-zone reference without adding runtime dependencies.
- [x] Add a queue for multiple folder/image jobs using one shared output folder.
- [x] Default queued folder output titles to the folder name.
- [x] Allow selected queue item titles to be overridden.
- [x] Preserve Japanese/Unicode folder names in generated PDF titles.
- [x] Add queued item status/progress feedback.
- [x] Add Windows native file/folder drop handling through the standard library where available.
- [x] Run focused and global validation.

Files touched this checkpoint:

- `image2pdf_gui.py` - replaced the plain form with toolbar/drop zone, queue table, shared output folder, progress bar, title override, queue processing, and optional Windows file drop support.
- `tests/test_image2pdf.py` - added queue, async GUI conversion, title override, and Japanese folder-name coverage.
- `PROGRESS.md` - recorded queue UI work and validation results.

What passed:

- `.\\.venv\\Scripts\\python.exe -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py`
- `.\\.venv\\Scripts\\python.exe -m pytest tests/test_image2pdf.py -q`
- `./scripts/Validate-GoalLite.ps1`

What failed:

- Initial focused GUI test failed because conversion is now asynchronous; test was updated to wait for queue completion.

What was fixed:

- GUI can process multiple queued folders/images into the same output folder.
- Folder queue items use their folder name as the default output title, including Japanese names.
- Queue status and progress are visible while jobs run.

### README and ignore checkpoint

Tasks:

- [x] Read README.md, PLAN.md, PROGRESS.md, VALIDATION.md, TASK_BRIEF.md, and relevant project files.
- [x] Update README.md for startup script usage and the current GUI queue workflow.
- [x] Document shared output folder behavior, queued folder defaults, drag/drop fallback, and Japanese/Unicode filename support.
- [x] Add `.gitignore` rules for local test files, test folders, caches, virtual environments, and generated outputs.
- [x] Remove tracked test files from the Git index only so they stay local but do not go to GitHub.
- [x] Run focused and global validation.

Files touched this checkpoint:

- `README.md` - documented startup script, GUI queue behavior, shared output folder, default folder-name output titles, drag/drop fallback, and Unicode filename support.
- `.gitignore` - added ignore rules for `test/`, `tests/`, `test_*.py`, `*_test.py`, Python caches, virtual environments, and generated output folders/files.
- `tests/test_image2pdf.py` - removed from Git index only; local file remains for validation.
- `PROGRESS.md` - recorded README and ignore-policy work.

What passed:

- `.\\.venv\\Scripts\\python.exe -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py`
- `.\\.venv\\Scripts\\python.exe -m pytest tests/test_image2pdf.py -q`
- `./scripts/Validate-GoalLite.ps1`

What failed:

- None in this checkpoint.

What was fixed:

- Local test folders/files are ignored and should not be included in future GitHub pushes.
- README now matches the current startup and queued GUI behavior.

### Settings and logo checkpoint

Tasks:

- [x] Read README.md, PROGRESS.md, GUI source, ignore rules, and repository status.
- [x] Keep Settings toolbar button and make it open a real settings window.
- [x] Persist GUI settings to local `image2pdf_settings.yaml` without adding PyYAML or other runtime dependencies.
- [x] Load saved settings on GUI startup and apply them to future conversions.
- [x] Ignore user-specific settings in `.gitignore`.
- [x] Add root `image2pdf_logo.png` asset and use it as the window icon when Tkinter supports it.
- [x] Update README.md with settings and logo behavior.
- [x] Run focused and global validation.

Files touched this checkpoint:

- `image2pdf_gui.py` - added settings load/save helpers, Settings pop-out window, startup settings application, and logo icon loading.
- `.gitignore` - ignored `image2pdf_settings.yaml` as local user state.
- `README.md` - documented saved settings, local settings file, no PyYAML requirement, and root logo asset.
- `image2pdf_logo.png` - added root app/logo asset.
- `PROGRESS.md` - recorded settings/logo work and validation.

What passed:

- `.\\.venv\\Scripts\\python.exe -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py`
- `.\\.venv\\Scripts\\python.exe -m pytest tests/test_image2pdf.py -q`
- `./scripts/Validate-GoalLite.ps1`

What failed:

- None in this checkpoint.

What was fixed:

- Settings now open, save to disk, load on restart, and drive conversion defaults.
- The app now has a root logo asset and attempts to use it as the Tkinter window icon.

Files touched this checkpoint:

- `VALIDATION.md` - documented Python 3.11+ interpreter enforcement.
- `scripts/Validate-GoalLite.ps1` - added Python 3.11+ version check.
- `scripts/validate.sh` - added Python 3.11+ interpreter selection/version check.
- `PROGRESS.md` - recorded final validation state and Bash blocker.

What passed:

- `python -m pytest`
- `python -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py`
- `./scripts/Validate-GoalLite.ps1`

What failed:

- `bash ./scripts/validate.sh` failed with `Python 3.11 or newer is required.`

What was fixed:

- Validation scripts now reject interpreters older than Python 3.11 instead of accidentally validating under Python 3.10.

## Validation history

| Date | Command | Result | Notes |
|---|---|---|---|
| 2026-05-13 | `./scripts/Validate-GoalLite.ps1` | pass | Installed/verified dependencies, compiled modules, ran 17 pytest tests, ran CLI help, and ran generated-image combined/split smoke tests. |
| 2026-05-13 | `python -m pytest tests/test_image2pdf.py` | pass | Milestone 1 targeted test run: 17 tests passed. |
| 2026-05-13 | `./scripts/Validate-GoalLite.ps1` | pass | Milestone 1 global validation passed: dependencies, compile checks, pytest, CLI help, and generated-image smoke tests. |
| 2026-05-13 | `python image2pdf.py --help` | pass | Milestone 2 CLI help displayed documented arguments and options. |
| 2026-05-13 | `python -m pytest tests/test_image2pdf.py` | pass | Milestone 2 targeted test run: 17 tests passed. |
| 2026-05-13 | `./scripts/Validate-GoalLite.ps1` | pass | Milestone 2 global validation passed: dependencies, compile checks, pytest, CLI help, and generated-image smoke tests. |
| 2026-05-13 | GUI integration smoke | fail | Exposed unsafe Tk calls from a worker thread: `RuntimeError: main thread is not in main loop`. |
| 2026-05-13 | `python -m pytest tests/test_image2pdf.py` | pass | Milestone 3 targeted test run after fix: 18 tests passed. |
| 2026-05-13 | `python -m py_compile image2pdf_gui.py` | pass | GUI module compiled successfully. |
| 2026-05-13 | GUI integration smoke | pass | Tkinter app object created combined and split PDFs from generated images. |
| 2026-05-13 | `./scripts/Validate-GoalLite.ps1` | pass | Milestone 3 global validation passed: dependencies, compile checks, pytest, CLI help, and generated-image smoke tests. |
| 2026-05-13 | `python -m pytest` | pass | Final test run: 18 tests passed on Windows Python 3.13. |
| 2026-05-13 | `python -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py` | pass | Final compile check passed. |
| 2026-05-13 | `./scripts/Validate-GoalLite.ps1` | pass | Final PowerShell validation passed with Python 3.13. |
| 2026-05-13 | `bash ./scripts/validate.sh` | fail | Bash/WSL environment has Python 3.10.12 and no executable Python 3.11+ interpreter. |
| 2026-05-20 | PowerShell parser validation for `Start-Image2pdf.ps1` | pass | Startup script parses without PowerShell syntax errors. |
| 2026-05-20 | `./scripts/Validate-GoalLite.ps1` | pass | Dependencies installed, modules compiled, 18 pytest tests passed, CLI help and generated-image smoke tests passed. |
| 2026-05-20 | `.\\.venv\\Scripts\\python.exe -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py` | pass | Ordering fix compile check passed. |
| 2026-05-20 | `.\\.venv\\Scripts\\python.exe -m pytest tests/test_image2pdf.py -q` | pass | Ordering regression run: 19 tests passed. |
| 2026-05-20 | `./scripts/Validate-GoalLite.ps1` | pass | Dependencies verified, modules compiled, 19 pytest tests passed, CLI help and generated-image smoke tests passed. |
| 2026-05-20 | `.\\.venv\\Scripts\\python.exe -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py` | pass | Queue UI compile check passed. |
| 2026-05-20 | `.\\.venv\\Scripts\\python.exe -m pytest tests/test_image2pdf.py -q` | pass | Queue UI focused run: 21 tests passed. |
| 2026-05-20 | `./scripts/Validate-GoalLite.ps1` | pass | Dependencies verified, modules compiled, 21 pytest tests passed, CLI help and generated-image smoke tests passed. |
| 2026-05-20 | `.\\.venv\\Scripts\\python.exe -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py` | pass | README/gitignore checkpoint compile check passed. |
| 2026-05-20 | `.\\.venv\\Scripts\\python.exe -m pytest tests/test_image2pdf.py -q` | pass | Local ignored test run: 21 tests passed. |
| 2026-05-20 | `./scripts/Validate-GoalLite.ps1` | pass | Dependencies verified, modules compiled, 21 pytest tests passed from local ignored tests, CLI help and generated-image smoke tests passed. |
| 2026-05-20 | `.\\.venv\\Scripts\\python.exe -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py` | pass | Settings/logo checkpoint compile check passed. |
| 2026-05-20 | `.\\.venv\\Scripts\\python.exe -m pytest tests/test_image2pdf.py -q` | pass | Local ignored focused run: 20 passed, 1 skipped due local Tk availability check. |
| 2026-05-20 | Settings YAML round-trip smoke | pass | Saved and loaded settings with a Japanese output path using a temporary YAML file. |
| 2026-05-20 | `./scripts/Validate-GoalLite.ps1` | pass | Dependencies verified, modules compiled, 21 pytest tests passed, CLI help and generated-image smoke tests passed. |

## Known blockers

- Bash/WSL validation is blocked until Python 3.11+ is installed or a Bash environment with Python 3.11+ is used.

## Decisions made

| Decision | Reason | Date |
|---|---|---|
| README.md is the product contract. | User explicitly instructed this and README contains current feature requirements. | 2026-05-13 |
| Tkinter remains the only GUI framework. | README and hard constraints require built-in Tkinter only. | 2026-05-13 |
| Runtime dependencies stay limited to `img2pdf` and `Pillow`. | README and hard constraints prohibit unnecessary dependencies. | 2026-05-13 |

## Next action

Use `./Start-Image2pdf.ps1` to set up and launch the GUI. Add folders to the queue, configure defaults through Settings, keep the shared output folder set, and start the queue. Before pushing, confirm ignored local test folders remain untracked. For final project completion, install or expose Python 3.11+ in the Bash/WSL environment, then rerun `bash ./scripts/validate.sh` and final validation.

## Completion checklist based on README.md

- [x] Local-only utility with no cloud services, accounts, telemetry, or OCR.
- [x] Python 3.11+ documented and supported.
- [x] Runtime dependencies are `img2pdf` and `Pillow`.
- [x] CLI creates combined multi-page PDFs.
- [x] CLI creates split one-page-per-image PDFs.
- [x] CLI supports explicit files, glob patterns, and non-recursive input folders.
- [x] Output folder and title behavior works.
- [x] Output names without `.pdf` receive `.pdf`.
- [x] Page order is preserved unless natural sort is requested.
- [x] Natural sort orders `page1`, `page2`, `page10`.
- [x] A4, Letter, and original page sizes work.
- [x] A4/Letter standardization preserves aspect ratio and uses white margins.
- [x] Existing output protection works unless overwrite is enabled.
- [x] Invalid-file handling fails by default and skips with `--skip-invalid`.
- [x] Transparent PNG inputs produce a white background.
- [x] EXIF-rotated images convert correctly.
- [x] Tkinter GUI opens and exposes README controls.
- [x] Automated tests pass.
- [x] CLI smoke tests pass.
- [x] Manual GUI validation is recorded.
