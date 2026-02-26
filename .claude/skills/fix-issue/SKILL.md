---
name: fix-issue
description: Fix a GitHub issue end-to-end — fetch details, implement fix, test, commit, and open a PR
disable-model-invocation: true
---

Fix the GitHub issue: $ARGUMENTS

1. Run `gh issue view $ARGUMENTS` to read the issue details
2. Identify the affected layer (frontend / backend route / service / data fetcher)
3. Search the codebase for relevant files
4. Implement the minimal fix
5. Run the relevant tests:
   - Backend: `cd backend && pytest`
   - Frontend: `cd frontend && npm run test:run && npm run typecheck`
6. Commit with message: `fix: <short description> (closes #$ARGUMENTS)`
7. Push and open a PR: `gh pr create`
