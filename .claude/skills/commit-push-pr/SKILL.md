---
name: commit-push-pr
description: Stage changes, commit with a conventional commit message, push to origin, and open a pull request on GitHub
disable-model-invocation: true
---

Complete phase 4 of the development workflow:

1. Run `git status` and `git diff` to review all changes
2. Run `git log --oneline -5` to follow the existing commit message style
3. Stage relevant files (do NOT use `git add -A`; add files by name)
4. Write a commit message following the format `<type>: <description>`
   - Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
   - Keep the subject line under 72 characters
5. Commit:
   ```
   git commit -m "<message>

   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
   ```
6. Push: `git push`
7. Open a PR: `gh pr create --title "<commit subject>" --body "$(cat <<'EOF'
   ## Summary
   - <bullet points of what changed>

   ## Test plan
   - [ ] Backend tests pass: `cd backend && pytest`
   - [ ] Frontend type check passes: `cd frontend && npm run typecheck`

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"`
8. Return the PR URL
