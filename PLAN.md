# PLAN.md

## Objective

Build and validate Image2pdf as a local Python 3.11+ utility that converts image files into PDF files through both CLI and Tkinter GUI workflows, using README.md as the product contract.

## Definition of done

- [ ] README.md requirements are implemented and remain documented.
- [ ] CLI supports combined and split PDF output.
- [ ] GUI supports file/folder input, output folder, title, mode, page size, sorting, overwrite, and skip-invalid options.
- [ ] Conversion handles natural sorting, A4/Letter/original sizing, overwrite protection, invalid inputs, transparent PNG white backgrounds, and EXIF rotation handling.
- [ ] Automated tests cover the README acceptance cases.
- [ ] `./scripts/Validate-GoalLite.ps1` passes on Windows PowerShell.
- [ ] `./scripts/validate.sh` passes on Bash-capable environments when available.
- [ ] PROGRESS.md is updated with final status and validation history.
- [ ] No unresolved blockers remain.

## In scope

- Shared Python conversion logic using `img2pdf` and Pillow.
- Argparse CLI entry point.
- Tkinter GUI entry point.
- README-aligned tests and validation scripts.
- GoalLite scaffold maintenance.

## Out of scope

- Cloud services, accounts, telemetry, or OCR.
- GUI frameworks other than Tkinter.
- Paid services or paid dependencies.
- Recursive folder ingestion.
- Guaranteed HEIC support by default.
- Multi-frame GIF/TIFF page expansion.
- Packaging installers or platform-specific app bundles unless separately requested.

## Constraints

- Python 3.11 or newer.
- Runtime dependencies must stay minimal: `img2pdf` and `Pillow`.
- Test-only dependencies may include `pytest` and `pypdf`.
- Use `pathlib` for path handling.
- Do not add unnecessary dependencies.
- Do not change README.md behavior without explicit user approval.
- Keep changes small and reviewable.

## Existing files to inspect first

- `README.md` - product contract and user-facing behavior.
- `TASK_BRIEF.md` - project objective and hard constraints.
- `PLAN.md` - milestone plan and acceptance criteria.
- `PROGRESS.md` - current milestone, blockers, and validation history.
- `VALIDATION.md` - validation commands and repair policy.
- `requirements.txt` - runtime dependency contract.
- `image2pdf_core.py` - shared conversion behavior.
- `image2pdf.py` - CLI behavior.
- `image2pdf_gui.py` - Tkinter GUI behavior.
- `tests/test_image2pdf.py` - automated acceptance coverage.
- `scripts/Validate-GoalLite.ps1` and `scripts/validate.sh` - project validation scripts.

## Milestones

### Milestone 0: GoalLite scaffold alignment

Goal:

- The scaffold files accurately describe the README contract and contain runnable validation commands.

Tasks:

- [ ] Update TASK_BRIEF.md from README.md.
- [ ] Update PLAN.md with milestones, acceptance criteria, validation, stop conditions, and risks.
- [ ] Update AGENTS.md with required operating rules.
- [ ] Update PROGRESS.md with current state and checklist.
- [ ] Update VALIDATION.md and validation scripts with real commands.

Validation:

```powershell
./scripts/Validate-GoalLite.ps1
```

Acceptance criteria:

- [ ] No placeholder scaffold commands remain.
- [ ] Validation scripts fail on first error.
- [ ] Validation scripts install dependencies if needed.
- [ ] Validation scripts run pytest and CLI smoke tests.

### Milestone 1: Shared conversion core

Goal:

- Shared conversion logic satisfies README behavior for input expansion, validation, preprocessing, and PDF creation.

Tasks:

- [ ] Implement or verify glob expansion and non-recursive folder ingestion.
- [ ] Implement or verify natural sorting.
- [ ] Implement or verify invalid-file handling and skip-invalid behavior.
- [ ] Implement or verify A4, Letter, and original page sizing.
- [ ] Implement or verify transparency flattening and EXIF-safe handling.

Validation:

```powershell
python -m pytest tests/test_image2pdf.py
./scripts/Validate-GoalLite.ps1
```

Acceptance criteria:

- [ ] Combined output creates one multi-page PDF.
- [ ] Split output creates one one-page PDF per image.
- [ ] Transparent PNG and EXIF-rotated images convert successfully.
- [ ] Missing/corrupt images fail or skip according to options.

### Milestone 2: CLI behavior

Goal:

- The argparse CLI matches README examples and options.

Tasks:

- [ ] Verify positional inputs, glob patterns, `--input-dir`, `--output`, `--output-dir`, and `--title`.
- [ ] Verify `--mode`, `--page-size`, `--sort`, `--overwrite`, and `--skip-invalid`.
- [ ] Verify clean user-facing errors and no normal stack traces.

Validation:

```powershell
python image2pdf.py --help
python -m pytest tests/test_image2pdf.py
./scripts/Validate-GoalLite.ps1
```

Acceptance criteria:

- [ ] README CLI examples work.
- [ ] Existing output protection works.
- [ ] Output names without `.pdf` receive `.pdf`.
- [ ] Page ordering follows README rules.

### Milestone 3: Tkinter GUI

Goal:

- The GUI exposes README features and uses the shared conversion logic.

Tasks:

- [ ] Verify GUI module imports and app can be constructed without starting the main loop.
- [ ] Verify controls exist for files, input folder, output folder, title, mode, page size, standardize, sort, overwrite, and skip-invalid.
- [ ] Manually verify the GUI opens and can run a conversion.

Validation:

```powershell
python -m pytest tests/test_image2pdf.py
python -m py_compile image2pdf_gui.py
./scripts/Validate-GoalLite.ps1
```

Acceptance criteria:

- [ ] GUI smoke test passes.
- [ ] Manual GUI launch works with `python image2pdf_gui.py`.
- [ ] GUI conversion produces expected PDFs.

### Milestone 4: Documentation and final validation

Goal:

- Documentation and validation fully match the implementation and README contract.

Tasks:

- [ ] Verify README examples and limitations.
- [ ] Verify TASK_BRIEF.md, PLAN.md, PROGRESS.md, VALIDATION.md, and scripts remain current.
- [ ] Run final validation and record results.

Validation:

```powershell
./scripts/Validate-GoalLite.ps1
```

Acceptance criteria:

- [ ] All automated validation passes.
- [ ] Manual GUI validation is recorded.
- [ ] PROGRESS.md marks all README checklist items complete.

## Final validation checklist

- [ ] `python -m pytest` passes.
- [ ] `python -m py_compile image2pdf.py image2pdf_core.py image2pdf_gui.py` passes.
- [ ] CLI combined smoke test creates a multi-page PDF.
- [ ] CLI split smoke test creates one PDF per image.
- [ ] Output overwrite protection is tested.
- [ ] GUI manual launch and conversion are tested.
- [ ] README limitations remain accurate.

## Stop conditions

Codex must stop and ask for human input if:

- README.md and user instructions conflict.
- A requested change would add cloud services, accounts, telemetry, OCR, or a non-Tkinter GUI framework.
- A destructive file operation or data deletion is required.
- A new runtime dependency beyond `img2pdf` and `Pillow` appears necessary.
- The same validation failure repeats after two repair attempts.
- Manual GUI validation cannot be completed because the desktop environment is unavailable.

## Risks and open questions

| Risk/Open question | Impact | Mitigation |
|---|---:|---|
| Tkinter display availability can vary by environment. | Medium | Keep automated GUI validation to import/construction and record manual GUI checks separately. |
| HEIC support varies by local Pillow/plugins. | Low | Document as optional and do not promise support by default. |
| Multi-frame image behavior can surprise users. | Low | Document v1 behavior as one input image per PDF page. |
| img2pdf API changes could affect layout behavior. | Medium | Keep tests and validation scripts covering A4, Letter, and original modes. |
