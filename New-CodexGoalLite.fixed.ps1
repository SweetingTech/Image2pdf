<#
.SYNOPSIS
Creates a Codex goal-lite scaffold for checkpointed agent work when /goal is unavailable.

.DESCRIPTION
This script writes a small set of control files into a project directory:
- TASK_BRIEF.md
- PLAN.md
- AGENTS.md
- PROGRESS.md
- VALIDATION.md
- CODEX_APP_PROMPTS.md
- scripts/Validate-GoalLite.ps1
- scripts/validate.sh, unless -NoBashValidation is used

It does not call Codex, install dependencies, or modify your source code.
It only creates the harness files you can point Codex at from the app.

.EXAMPLE
./New-CodexGoalLite.ps1 -Path . -ProjectName "Tiny Markdown CLI" -Objective "Build a CLI that converts Markdown notes to JSON" -Language "Python" -AppType "CLI" -PackageManager "uv"

.EXAMPLE
./New-CodexGoalLite.ps1 -Path . -Force
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Path = (Get-Location).Path,
    [string]$ProjectName = "My Small Program",
    [string]$Objective = "Describe the small program, feature, or fix here.",
    [string]$Language = "TBD",
    [string]$AppType = "TBD",
    [string]$PackageManager = "TBD",
    [switch]$Force,
    [switch]$NoBashValidation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-TemplateTokens {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    $replacements = @{
        "%%PROJECT_NAME%%"    = $ProjectName
        "%%OBJECTIVE%%"       = $Objective
        "%%LANGUAGE%%"        = $Language
        "%%APP_TYPE%%"        = $AppType
        "%%PACKAGE_MANAGER%%" = $PackageManager
    }

    foreach ($key in $replacements.Keys) {
        $Text = $Text.Replace($key, [string]$replacements[$key])
    }

    return $Text
}

function Write-GoalLiteFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root,

        [Parameter(Mandatory = $true)]
        [string]$RelativePath,

        [Parameter(Mandatory = $true)]
        [string]$Content,

        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [System.Collections.Generic.List[string]]$Created,

        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [System.Collections.Generic.List[string]]$Skipped
    )

    $fullPath = Join-Path -Path $Root -ChildPath $RelativePath
    $parent = Split-Path -Path $fullPath -Parent

    if (-not (Test-Path -Path $parent)) {
        if ($PSCmdlet.ShouldProcess($parent, "Create directory")) {
            New-Item -Path $parent -ItemType Directory -Force | Out-Null
        }
    }

    if ((Test-Path -Path $fullPath) -and -not $Force) {
        $Skipped.Add($RelativePath)
        return
    }

    $resolvedContent = Resolve-TemplateTokens -Text $Content

    if ($PSCmdlet.ShouldProcess($fullPath, "Write goal-lite file")) {
        Set-Content -Path $fullPath -Value $resolvedContent -Encoding UTF8
        $Created.Add($RelativePath)
    }
}

$targetRoot = [System.IO.Path]::GetFullPath($Path)

if (-not (Test-Path -Path $targetRoot)) {
    if ($PSCmdlet.ShouldProcess($targetRoot, "Create target project directory")) {
        New-Item -Path $targetRoot -ItemType Directory -Force | Out-Null
    }
}

$createdFiles = [System.Collections.Generic.List[string]]::new()
$skippedFiles = [System.Collections.Generic.List[string]]::new()

$taskBrief = @'
# Task Brief

Use this file before asking Codex to plan. Keep it specific. Vague objectives create vague code, and vague code is how future-you develops a drinking problem.

## Project name

`%%PROJECT_NAME%%`

## One-sentence objective

`%%OBJECTIVE%%`

## Current project state

- Existing repo: `[yes/no]`
- Main language/framework: `%%LANGUAGE%%`
- App type: `%%APP_TYPE%%`
- Package manager: `%%PACKAGE_MANAGER%%`
- Current status: `[new project / partially built / bug exists / feature missing]`

## What Codex should inspect first

- `[file or folder]`
- `[file or folder]`
- `[file or folder]`

## In scope

- `[Feature or task 1]`
- `[Feature or task 2]`
- `[Feature or task 3]`

## Out of scope

- `[Thing Codex must not do]`
- `[Thing Codex must not touch]`
- `[Future feature, not now]`

## Constraints

- `[Language/framework/package constraint]`
- `[Architecture or style constraint]`
- `[Dependency or security constraint]`

## Definition of done

The task is done only when:

- `[Observable result 1]`
- `[Observable result 2]`
- `[All validation commands pass]`
- `[No known blocker remains]`

## Validation commands I expect to work

Fill in what you know. Codex can infer missing commands, but letting it guess everything is basically asking a raccoon to design CI.

```powershell
# examples
# npm install
# npm run lint
# npm test
# npm run build
# ./scripts/Validate-GoalLite.ps1
```

## Manual checks

- `[Manual check 1, if needed]`
- `[Manual check 2, if needed]`

## Known risks or sharp edges

- `[Risk 1]`
- `[Risk 2]`
- `[Risk 3]`

## Things Codex must ask before doing

- `[Destructive migration]`
- `[Deleting files]`
- `[Changing public API]`
- `[Adding paid dependencies]`
- `[Other project-specific danger zone]`
'@

$plan = @'
# PLAN.md

## Objective

`%%OBJECTIVE%%`

## Definition of done

This task is complete only when all of these are true:

- [ ] `[Acceptance condition 1]`
- [ ] `[Acceptance condition 2]`
- [ ] `[Acceptance condition 3]`
- [ ] `./scripts/Validate-GoalLite.ps1` passes, or `VALIDATION.md` documents why automated validation is impossible.
- [ ] `PROGRESS.md` is updated with final status.
- [ ] No unresolved blockers remain.

## In scope

- `[Item 1]`
- `[Item 2]`
- `[Item 3]`

## Out of scope

- `[Item 1]`
- `[Item 2]`
- `[Item 3]`

## Constraints

- Language/framework: `%%LANGUAGE%%`
- App type: `%%APP_TYPE%%`
- Package manager: `%%PACKAGE_MANAGER%%`
- `[Additional constraint]`

## Files and directories to inspect first

- `[path]` — `[why it matters]`
- `[path]` — `[why it matters]`
- `[path]` — `[why it matters]`

## Milestones

### Milestone 1: `[Name]`

Goal:

- `[What should be true after this milestone]`

Tasks:

- [ ] `[Task]`
- [ ] `[Task]`
- [ ] `[Task]`

Validation:

```powershell
./scripts/Validate-GoalLite.ps1
```

Acceptance criteria:

- [ ] `[Observable check]`
- [ ] `[Observable check]`

Checkpoint output:

- Update `PROGRESS.md`.
- Summarize changed files.
- Record validation results.

---

### Milestone 2: `[Name]`

Goal:

- `[What should be true after this milestone]`

Tasks:

- [ ] `[Task]`
- [ ] `[Task]`
- [ ] `[Task]`

Validation:

```powershell
./scripts/Validate-GoalLite.ps1
```

Acceptance criteria:

- [ ] `[Observable check]`
- [ ] `[Observable check]`

Checkpoint output:

- Update `PROGRESS.md`.
- Summarize changed files.
- Record validation results.

---

### Milestone 3: `[Name]`

Goal:

- `[What should be true after this milestone]`

Tasks:

- [ ] `[Task]`
- [ ] `[Task]`
- [ ] `[Task]`

Validation:

```powershell
./scripts/Validate-GoalLite.ps1
```

Acceptance criteria:

- [ ] `[Observable check]`
- [ ] `[Observable check]`

Checkpoint output:

- Update `PROGRESS.md`.
- Summarize changed files.
- Record validation results.

## Global validation command

Run this after each milestone when possible:

```powershell
./scripts/Validate-GoalLite.ps1
```

## Stop conditions

Codex must stop and ask for human input if any of these happen:

- A required secret/API key/credential is missing.
- Requirements conflict.
- A destructive migration or data deletion is required.
- The same validation failure repeats after `[NUMBER]` repair attempts.
- A dependency decision requires human judgment.
- The task exceeds the turn budget.
- The acceptance criteria are ambiguous.

## Turn budget

- Maximum checkpoint turns: `[NUMBER]`
- Maximum files changed per checkpoint: `[NUMBER]`
- Maximum validation repair attempts per checkpoint: `[NUMBER]`
- Max risk level per checkpoint: `[low/medium/high]`

## Risks

| Risk | Impact | Mitigation |
|---|---:|---|
| `[Risk]` | `[Low/Medium/High]` | `[Mitigation]` |
| `[Risk]` | `[Low/Medium/High]` | `[Mitigation]` |

## Open questions

- `[Question 1]`
- `[Question 2]`

## Final delivery checklist

- [ ] All milestones complete.
- [ ] All acceptance criteria pass.
- [ ] Global validation passes.
- [ ] `PROGRESS.md` updated.
- [ ] Final changed-file summary produced.
- [ ] Remaining risks documented.
'@

$agents = @'
# AGENTS.md

## Purpose

This repository uses a checkpointed goal-lite workflow. When working in this repo, behave like a careful implementation agent, not a caffeinated squirrel with commit privileges.

## Required reading before implementation

Before making changes, read:

1. `TASK_BRIEF.md` if present
2. `PLAN.md`
3. `PROGRESS.md`
4. `VALIDATION.md`
5. Relevant source files listed in `PLAN.md`

## Operating loop

For every implementation turn:

1. Read `PLAN.md` and `PROGRESS.md`.
2. Identify the next incomplete milestone.
3. Work only on that milestone unless the plan explicitly says otherwise.
4. Make the smallest useful set of changes.
5. Run the milestone validation commands.
6. Run `./scripts/Validate-GoalLite.ps1` when possible.
7. If validation fails, inspect the failure, fix it, and rerun.
8. Update `PROGRESS.md` with:
   - current milestone
   - files changed
   - validation commands run
   - pass/fail result
   - blockers
   - next action
9. Stop at a natural checkpoint.

## Completion rule

Do not claim the project is complete unless:

- Every acceptance criterion in `PLAN.md` is satisfied.
- `./scripts/Validate-GoalLite.ps1` passes, or `VALIDATION.md` documents why no automated validation is possible.
- `PROGRESS.md` has final status.
- Any remaining caveats are explicitly listed.

## Change discipline

- Prefer small, reviewable changes.
- Do not rewrite unrelated files.
- Do not introduce new dependencies unless the plan allows it or the user approves.
- Do not remove tests unless replacing them with better tests.
- Do not silently ignore failing tests.
- Do not fake validation results.
- Do not edit secrets or commit credentials.

## Ask before doing

Ask for human input before:

- destructive migrations
- deleting data
- changing public APIs
- adding paid dependencies
- changing auth/security behavior
- making architectural changes outside `PLAN.md`

## Default coding standards

- Language/framework: `%%LANGUAGE%%`
- App type: `%%APP_TYPE%%`
- Package manager: `%%PACKAGE_MANAGER%%`
- Test command: `[COMMAND]`
- Style/lint command: `[COMMAND]`
- Build command: `[COMMAND]`
- Runtime command: `[COMMAND]`

## Response format after each checkpoint

Use this format:

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
'@

$progress = @'
# PROGRESS.md

## Current status

- Overall status: `not started`
- Current milestone: `[Milestone name]`
- Current checkpoint: `[Short description]`
- Last updated: `[YYYY-MM-DD HH:MM]`

## Current hypothesis

`[What Codex currently believes needs to happen next.]`

## Completed milestones

- [ ] Milestone 1: `[Name]`
- [ ] Milestone 2: `[Name]`
- [ ] Milestone 3: `[Name]`

## Current milestone detail

### `[Milestone name]`

Tasks:

- [ ] `[Task]`
- [ ] `[Task]`
- [ ] `[Task]`

Files touched this checkpoint:

- `[path]` — `[change summary]`

## Validation history

| Time | Command | Result | Notes |
|---|---|---|---|
| `[YYYY-MM-DD HH:MM]` | `[command]` | `[pass/fail/not run]` | `[notes]` |

## Known blockers

- `None`

## Decisions made

| Decision | Reason | Date |
|---|---|---|
| `[Decision]` | `[Reason]` | `[YYYY-MM-DD]` |

## Next action

`[Exactly one next action.]`

## Completion checklist

- [ ] All planned milestones complete.
- [ ] All acceptance criteria in `PLAN.md` pass.
- [ ] `./scripts/Validate-GoalLite.ps1` passes.
- [ ] Manual checks completed if required.
- [ ] No unresolved blockers remain.
- [ ] Final summary written.
'@

$validation = @'
# VALIDATION.md

## Purpose

This file defines how to prove the project works. Codex must use this as the validation contract.

## Environment setup

```powershell
[setup command]
```

Examples:

```powershell
npm install
pnpm install
pip install -r requirements.txt
uv sync
cargo fetch
go mod download
```

## Validation commands

### 1. Format check

```powershell
[format check command]
```

Expected result:

- `[What passing means]`

If it fails:

- `[What Codex should do]`

### 2. Lint

```powershell
[lint command]
```

Expected result:

- `[What passing means]`

If it fails:

- `[What Codex should do]`

### 3. Typecheck

```powershell
[typecheck command]
```

Expected result:

- `[What passing means]`

If it fails:

- `[What Codex should do]`

### 4. Unit tests

```powershell
[test command]
```

Expected result:

- `[What passing means]`

If it fails:

- `[What Codex should do]`

### 5. Build

```powershell
[build command]
```

Expected result:

- `[What passing means]`

If it fails:

- `[What Codex should do]`

### 6. Smoke test

```powershell
[smoke test command]
```

Expected result:

- `[What passing means]`

If it fails:

- `[What Codex should do]`

## Global validation script

Codex should run:

```powershell
./scripts/Validate-GoalLite.ps1
```

## Manual verification

Use this only when automated validation cannot fully prove the behavior.

- [ ] `[Manual check 1]`
- [ ] `[Manual check 2]`
- [ ] `[Manual check 3]`

## Validation repair policy

When validation fails:

1. Read the error.
2. Identify the smallest likely fix.
3. Apply the fix.
4. Rerun the failed command.
5. Rerun `./scripts/Validate-GoalLite.ps1` if the failed command passes.
6. Update `PROGRESS.md`.

Stop if the same failure repeats after `[NUMBER]` repair attempts.
'@

$codexPrompts = @'
# Codex App Prompts

Copy/paste these into the Codex app.

## 1. Planning prompt

Use this first. Enable `/plan-mode` or the app's planning mode before sending it.

```text
Read TASK_BRIEF.md.

Create or update these files:

1. PLAN.md
2. AGENTS.md
3. PROGRESS.md
4. VALIDATION.md
5. scripts/Validate-GoalLite.ps1

Do not implement the project yet.

PLAN.md must include:
- objective
- definition of done
- in scope
- out of scope
- constraints
- files/directories to inspect first
- milestones
- acceptance criteria per milestone
- validation commands per milestone
- global validation command
- stop conditions
- turn budget
- risks
- open questions
- final delivery checklist

AGENTS.md must instruct Codex to:
- read PLAN.md and PROGRESS.md before every implementation turn
- work one checkpoint at a time
- run validation after each checkpoint
- fix validation failures before moving on
- update PROGRESS.md after every checkpoint
- stop if blocked by missing human input
- never claim completion until all acceptance criteria pass

PROGRESS.md must track:
- current status
- current milestone
- completed milestones
- validation history
- blockers
- decisions made
- next action
- completion checklist

VALIDATION.md must define:
- setup command
- format command
- lint command
- typecheck command
- test command
- build command
- smoke test command
- manual checks if needed
- validation repair policy

scripts/Validate-GoalLite.ps1 must run the project's actual validation commands. If a command is unknown, include a commented placeholder and explain what is missing.

After creating the files, stop and summarize the plan. Do not implement yet.
```

## 2. Execution prompt

Use this after reviewing `PLAN.md`.

```text
Start executing PLAN.md.

Follow AGENTS.md exactly.
Use PROGRESS.md as the state file.
Use VALIDATION.md and scripts/Validate-GoalLite.ps1 as the proof system.

Rules:
- Work only on the next incomplete milestone.
- Make the smallest useful set of changes.
- Run the validation commands for the milestone.
- Run ./scripts/Validate-GoalLite.ps1 when possible.
- If validation fails, fix the failure and rerun.
- Update PROGRESS.md with changed files, validation results, blockers, and the next action.
- Stop after one milestone or a natural checkpoint.
- Do not claim final completion unless every acceptance criterion in PLAN.md passes.
```

## 3. Continue prompt

Use this whenever Codex stops and you want it to continue.

```text
Continue from PROGRESS.md.

Read AGENTS.md, PLAN.md, PROGRESS.md, VALIDATION.md, and scripts/Validate-GoalLite.ps1.

Proceed with the next incomplete checkpoint only.
Run validation.
Fix failures before moving on.
Update PROGRESS.md.
Stop at the next natural checkpoint with a concise summary.
```

## 4. Repair prompt

Use this when validation fails or Codex gets messy.

```text
Validation failed or the implementation drifted.

Read the latest failure output, PLAN.md, PROGRESS.md, and VALIDATION.md.

Do not add new features.
Do not move to a new milestone.
Find the smallest fix for the failing validation.
Apply it.
Rerun the failed command.
If it passes, rerun ./scripts/Validate-GoalLite.ps1.
Update PROGRESS.md with the failure, fix, and validation result.
Stop after the repair checkpoint.
```

## 5. Final review prompt

Use this when Codex thinks everything is complete.

```text
Perform final goal-lite review.

Read PLAN.md, PROGRESS.md, VALIDATION.md, and AGENTS.md.

Verify:
- every milestone is complete
- every acceptance criterion is satisfied
- ./scripts/Validate-GoalLite.ps1 passes or VALIDATION.md explains why automated validation is impossible
- no blockers remain
- changed files are summarized
- remaining risks are listed

If anything is incomplete, do not claim completion. Update PROGRESS.md and identify the next action.
If everything is complete, write the final summary.
```

## 6. Automation prompt

Use this only if the Codex app supports Automations for your environment.

```text
Create a thread automation attached to this project/thread.

Cadence:
Every 15 minutes.

Automation task:
Read AGENTS.md, PLAN.md, PROGRESS.md, VALIDATION.md, and scripts/Validate-GoalLite.ps1. Continue the next incomplete checkpoint. Work on only one milestone or one coherent subtask per wake-up. Run the relevant validation commands. Fix failures if possible. Update PROGRESS.md. Stop if all acceptance criteria pass, or if blocked by missing human input.

Reporting:
Only report meaningful progress, validation failures, blockers, or completion.

Stop condition:
When PROGRESS.md says all acceptance criteria are complete and final validation has passed, report completion and stop making changes.
```
'@

$validatePs1 = @'
<#
.SYNOPSIS
Runs project validation for the Codex goal-lite workflow.

.DESCRIPTION
Codex should fill in the $ValidationCommands array with real project commands.
This script intentionally fails when no validation commands are configured, unless -AllowEmpty is supplied.
That prevents fake green checkmarks. Humanity has enough imaginary victories already.
#>

[CmdletBinding()]
param(
    [switch]$AllowEmpty
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ValidationCommands = @(
    # Uncomment and edit examples for your project.
    # @{ Name = "Install dependencies"; Command = "npm install" }
    # @{ Name = "Lint"; Command = "npm run lint" }
    # @{ Name = "Typecheck"; Command = "npm run typecheck" }
    # @{ Name = "Test"; Command = "npm test" }
    # @{ Name = "Build"; Command = "npm run build" }
    # @{ Name = "Smoke test"; Command = "node ./dist/index.js --help" }
)

if ($ValidationCommands.Count -eq 0) {
    $message = "No validation commands are configured in scripts/Validate-GoalLite.ps1. Add real commands before treating validation as passed."

    if ($AllowEmpty) {
        Write-Warning $message
        exit 0
    }

    Write-Error $message
    exit 1
}

function Invoke-ValidationStep {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Step
    )

    if (-not $Step.ContainsKey("Name") -or -not $Step.ContainsKey("Command")) {
        throw "Each validation step must include Name and Command keys."
    }

    Write-Host ""
    Write-Host "==> $($Step.Name)" -ForegroundColor Cyan
    Write-Host "    $($Step.Command)"

    Invoke-Expression $Step.Command

    Write-Host "    Passed: $($Step.Name)" -ForegroundColor Green
}

Write-Host "==> Running goal-lite validation" -ForegroundColor Cyan

foreach ($step in $ValidationCommands) {
    Invoke-ValidationStep -Step $step
}

Write-Host ""
Write-Host "==> All validation steps passed" -ForegroundColor Green
'@

$validateSh = @'
#!/usr/bin/env bash
set -euo pipefail

# Optional Bash validation wrapper for non-Windows environments.
# Replace the placeholder block with project-specific commands.

if [ "${ALLOW_EMPTY_VALIDATION:-0}" != "1" ]; then
  echo "No validation commands are configured in scripts/validate.sh. Add real commands before treating validation as passed." >&2
  exit 1
fi

echo "ALLOW_EMPTY_VALIDATION=1 set, skipping validation commands. Configure this file before real use."

# Examples:
# npm install
# npm run lint
# npm run typecheck
# npm test
# npm run build
'@

Write-GoalLiteFile -Root $targetRoot -RelativePath "TASK_BRIEF.md" -Content $taskBrief -Created $createdFiles -Skipped $skippedFiles
Write-GoalLiteFile -Root $targetRoot -RelativePath "PLAN.md" -Content $plan -Created $createdFiles -Skipped $skippedFiles
Write-GoalLiteFile -Root $targetRoot -RelativePath "AGENTS.md" -Content $agents -Created $createdFiles -Skipped $skippedFiles
Write-GoalLiteFile -Root $targetRoot -RelativePath "PROGRESS.md" -Content $progress -Created $createdFiles -Skipped $skippedFiles
Write-GoalLiteFile -Root $targetRoot -RelativePath "VALIDATION.md" -Content $validation -Created $createdFiles -Skipped $skippedFiles
Write-GoalLiteFile -Root $targetRoot -RelativePath "CODEX_APP_PROMPTS.md" -Content $codexPrompts -Created $createdFiles -Skipped $skippedFiles
Write-GoalLiteFile -Root $targetRoot -RelativePath "scripts/Validate-GoalLite.ps1" -Content $validatePs1 -Created $createdFiles -Skipped $skippedFiles

if (-not $NoBashValidation) {
    Write-GoalLiteFile -Root $targetRoot -RelativePath "scripts/validate.sh" -Content $validateSh -Created $createdFiles -Skipped $skippedFiles

    $bashPath = Join-Path -Path $targetRoot -ChildPath "scripts/validate.sh"
    if (Test-Path -Path $bashPath) {
        try {
            if ((Get-Variable -Name IsLinux -ErrorAction SilentlyContinue) -and $IsLinux) {
                chmod +x $bashPath
            }
            elseif ((Get-Variable -Name IsMacOS -ErrorAction SilentlyContinue) -and $IsMacOS) {
                chmod +x $bashPath
            }
        }
        catch {
            Write-Warning "Could not mark scripts/validate.sh executable. You can run: chmod +x scripts/validate.sh"
        }
    }
}

Write-Host ""
Write-Host "Codex goal-lite scaffold complete." -ForegroundColor Green
Write-Host "Target: $targetRoot"

if ($createdFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "Created/updated:" -ForegroundColor Cyan
    foreach ($file in $createdFiles) {
        Write-Host "  + $file"
    }
}

if ($skippedFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "Skipped existing files because -Force was not supplied:" -ForegroundColor Yellow
    foreach ($file in $skippedFiles) {
        Write-Host "  - $file"
    }
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Fill in TASK_BRIEF.md."
Write-Host "  2. Open the project in the Codex app."
Write-Host "  3. Enable plan mode and paste the planning prompt from CODEX_APP_PROMPTS.md."
Write-Host "  4. Review PLAN.md."
Write-Host "  5. Paste the execution prompt from CODEX_APP_PROMPTS.md."
Write-Host ""
Write-Host "Validation note: scripts/Validate-GoalLite.ps1 intentionally fails until real commands are configured." -ForegroundColor Yellow
