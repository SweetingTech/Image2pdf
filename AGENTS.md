# AGENTS.md

## Purpose

This repository uses a checkpointed GoalLite workflow. Work from the README contract, move one milestone at a time, and keep every change small enough to review.

## Required reading before work

Before making implementation changes, Codex must read:

1. `README.md`
2. `PLAN.md`
3. `PROGRESS.md`
4. `VALIDATION.md`
5. `TASK_BRIEF.md` if present
6. Relevant source files listed in `PLAN.md`

Treat `README.md` as the product contract. If another file conflicts with README.md, stop and ask for direction before changing behavior.

## Operating loop

For every turn:

1. Read `README.md`, `PLAN.md`, `PROGRESS.md`, and `VALIDATION.md`.
2. Identify the current milestone and next checkpoint from `PROGRESS.md`.
3. Work only on that milestone unless the user explicitly changes the plan.
4. Keep changes small, focused, and reviewable.
5. Run validation after each checkpoint.
6. Fix validation failures before moving to the next checkpoint.
7. Update `PROGRESS.md` every turn with files changed, validation results, blockers, and next action.
8. Stop at a natural checkpoint and summarize the result.

## Completion rule

Never claim completion unless:

- Every README acceptance behavior is implemented.
- Every acceptance criterion in `PLAN.md` passes.
- `./scripts/Validate-GoalLite.ps1` passes, or `VALIDATION.md` documents a real environment blocker.
- GUI manual validation is completed or documented as blocked.
- `PROGRESS.md` has final status and validation history.
- No unresolved blockers remain.

## Change discipline

- Do not rewrite unrelated files.
- Do not stage unrelated work.
- Do not introduce runtime dependencies beyond `img2pdf` and `Pillow` unless the user approves.
- Do not remove tests unless replacing them with stronger coverage.
- Do not ignore failing tests.
- Do not report validation as passing unless the command actually passed.
- Do not edit secrets or commit credentials.
- Do not change README.md behavior without explicit user approval.

## Ask before doing

Ask for human input before:

- destructive file operations or data deletion
- public CLI behavior changes not already described in README.md
- new runtime dependencies
- cloud, account, telemetry, OCR, or non-Tkinter GUI behavior
- architectural changes outside `PLAN.md`

## Project standards

- Language: Python 3.11+
- CLI: argparse
- Paths: pathlib
- GUI: Tkinter only
- Runtime dependencies: `img2pdf`, `Pillow`
- Test dependencies: `pytest`, `pypdf`
- Main validation command: `./scripts/Validate-GoalLite.ps1`
- Bash validation when available: `./scripts/validate.sh`

## Response format after each checkpoint

```text
Checkpoint complete: [milestone name]

Changed files:
- [file]: [what changed]

Validation:
- [command]: [pass/fail]

Result:
- [what now works]

Next:
- [next milestone or blocker]
```
