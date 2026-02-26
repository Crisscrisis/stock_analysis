# Development Workflow

All non-trivial tasks follow four phases:

| Phase | Mode | Goal |
|-------|------|------|
| 1 Explore | Plan Mode (read-only) | Understand codebase, locate relevant files |
| 2 Plan | Plan Mode (read-only) | Draft implementation plan, confirm scope |
| 3 Code | Normal Mode | Implement per plan, run tests |
| 4 Commit | Normal Mode | Commit, push, open PR |

## Phase 1 — Explore (Plan Mode)
- Enter Plan Mode with `Shift+Tab`
- Read relevant files; do NOT make any changes
- Identify all files that will need to change

## Phase 2 — Plan (Plan Mode)
- Write a step-by-step implementation plan
- Press `Ctrl+G` to open the plan in editor for direct editing
- Get user confirmation before proceeding

## Phase 3 — Code (Normal Mode)
- Switch back to Normal Mode with `Shift+Tab`
- Implement strictly following the approved plan
- Run tests after each logical change:
  - Backend: `cd backend && pytest`
  - Frontend: `cd frontend && npm run test:run && npm run typecheck`
- Do not change scope without re-entering Plan Mode

## Phase 4 — Commit (Normal Mode)
- Run `/commit-push-pr` to commit, push, and open a PR in one step
- Commit message format: `<type>: <short description>`
  - Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

## When to skip planning
Skip phases 1–2 only for changes describable in one sentence (typo fix, rename, single log line).
