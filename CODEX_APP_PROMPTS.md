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
