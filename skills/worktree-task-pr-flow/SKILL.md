---
name: worktree-task-pr-flow
description: Use when the user asks to work through a dedicated git worktree, task file, validation, commit, push, and pull request workflow.
---

# Worktree Task PR Flow

Use this skill when the user explicitly asks to use a worktree, create a task file before implementation, commit changes, push a branch, or create a pull request.

Do not force this full workflow for ordinary repository edits, pure question answering, plan-only requests, or cases where the user explicitly asks not to create a worktree, commit, push, or PR. In those cases, apply only the relevant preparation, validation, and reporting steps.

## Workflow

1. Understand the request before editing.
   - Identify deliverables, validations, and risks.
   - Classify the task as `機能追加`, `修正`, `調査`, or `ドキュメント更新` when task tracking is needed.
   - State a checklist and Done conditions before implementation.
   - Write acceptance criteria before touching the main deliverables.
2. Create a dedicated worktree when requested or useful.
   - Use the repository's default base branch unless the user specifies another base.
   - Keep unrelated changes in the original worktree out of scope.
3. Create or update a task file when task tracking is requested.
   - Include background, purpose, scope, task type, plan, documentation maintenance plan, acceptance criteria, validation plan, review points, risks, and state.
   - For fix tasks, include the root-cause summary before the implementation plan when evidence is available.
4. Implement the requested change.
   - Follow repository-local skills and `AGENTS.md`.
   - Update durable docs when behavior or workflow changes require it.
5. Validate before commit.
   - Use `skills/implementation-test-selector/SKILL.md`.
   - Use `skills/repository-test-runner/SKILL.md` to run, retry, escalate, and report selected checks.
   - Run relevant checks such as `git diff --check` and targeted test/lint/docs commands.
   - Do not claim unrun checks as completed.
6. Write a post-task report when required by repository policy or user request.
   - Use `skills/post-task-fit-report/SKILL.md`.
   - Do not create a post-task report solely for commit execution or commit message creation.
7. Commit and push when requested.
   - Inspect `git diff --cached --name-only` before committing.
   - Use `skills/japanese-git-commit-gitmoji/SKILL.md`.
8. Create or update the PR when requested.
   - Use `skills/github-apps-pr-operator/SKILL.md` when GitHub operations are involved.
   - Use `skills/japanese-pr-title-comment/SKILL.md` for Japanese title, body, and comments.
   - Use the requested base branch, or the repository default when unspecified.
9. Comment on acceptance criteria after PR creation when requested or required.
   - Add a Japanese PR comment summarizing each acceptance criterion as pass, fail, or not verified.
   - If any required criterion fails, do not mark the task complete.
10. Complete the task file only after deliverables and validations are done.
    - Update state and path consistently if state directories are used.

## Task File Rules

- Keep one task per file.
- Every task file should state `タスク種別` as one of `機能追加`, `修正`, `調査`, or `ドキュメント更新`.
- Fix task files should include root-cause notes or explicitly state why the task is still investigative.
- Do not move a task to `done` when known validation failures or blocked PR actions remain.

## PR Comment Format

Use this structure after the PR exists:

```markdown
## 受け入れ条件確認

- [x] <criterion>: 満たした。根拠: <file, command, or PR detail>
- [ ] <criterion>: 未達。理由: <reason>
- [ ] <criterion>: 未検証。理由: <reason>

補足:
- 実行した検証: `<command>` pass
- 未実施の検証: `<command>` は <reason> のため未実施
```

Only check items that were actually satisfied.
