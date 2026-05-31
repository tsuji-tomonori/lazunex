---
name: task-file-writer
description: リポジトリ内で実装・修正・調査・ドキュメント更新タスクを Markdown ファイルとして分解、作成、更新し、タスク種別、背景、受け入れ条件、実行計画、検証、リスクを書く。
---

# Task File Writer

## Overview

Use this skill to convert a plan, investigation report, review finding, roadmap, or user request into repository-local task files. Keep each file scoped to exactly one executable task.

## Output Location

- Default directory for new planned work: `tasks/todo/`.
- State directories:
  - `tasks/todo/`: accepted or planned but not started.
  - `tasks/do/`: in progress.
  - `tasks/done/`: complete only after implementation, validation, and completion notes are recorded.
- Create task directories only when the repository uses task files or the user asks for them.
- Use Markdown files only.
- Use a predictable filename convention such as `YYYYMMDD-HHMM-<task-summary>.md`.
- Do not combine multiple implementation goals in one task file.
- Keep `保存先` aligned with the task file's current path whenever moving between state directories.

## Required Sections

Each task file should include these sections:

1. `# <task title>`
2. `保存先`
3. `状態`
4. `タスク種別`
5. `背景`
6. `目的`
7. `対象範囲`
8. `方針`
9. `必要情報`
10. `実行計画`
11. `ドキュメントメンテナンス計画`
12. `受け入れ条件`
13. `検証計画`
14. `レビュー観点`
15. `未決事項・リスク`

Use Japanese prose unless the user requests another language. Keep file paths, commands, API names, type names, and function names in their original spelling.

## Task Decomposition

When converting a report or plan:

- Treat each independent implementation outcome as a separate task.
- Include all tasks unless the user explicitly asks to filter.
- Split broad platform work from domain-specific cleanup.
- If one task depends on another, record it under `必要情報` or `未決事項・リスク`; do not merge them.
- Preserve source references such as report paths, code paths, issue IDs, PR numbers, or benchmark names.

## Writing Guidance

For each task:

- `状態`: Use `todo`, `do`, or `done` consistently with the parent directory when state directories exist.
- `タスク種別`: Choose one primary type from `機能追加`, `修正`, `調査`, or `ドキュメント更新`.
  - `機能追加`: A new user, API, workflow, infrastructure, or developer capability is added.
  - `修正`: Existing behavior, output, tests, CI, docs, operations, security boundary, or data handling is wrong and must be corrected.
  - `調査`: The main deliverable is analysis, diagnosis, review, evidence collection, or a recommendation without directly changing product behavior.
  - `ドキュメント更新`: The main deliverable is durable documentation, agent instructions, skill instructions, specs, reports, or task metadata.
  - If multiple labels seem possible, pick the dominant deliverable and record secondary aspects in `背景` or `対象範囲`.
- `背景`: Explain why the task exists and what concrete problem it addresses.
- `目的`: State the desired outcome in one or two sentences.
- `対象範囲`: List files, modules, docs, tests, or behavior likely to be touched.
- `方針`: Describe the implementation approach and design constraints.
- `必要情報`: Include prior reports, relevant code paths, assumptions, dependencies, and decisions needed before implementation.
- `実行計画`: Write concrete steps in execution order.
- `ドキュメントメンテナンス計画`: State which README, docs, API examples, local verification, operations, deploy docs, or PR notes must be updated or explicitly judged unaffected.
- `受け入れ条件`: Write observable completion checks. Avoid vague conditions such as "works well".
- `検証計画`: Name likely commands or checks. Mark environment-dependent checks as candidates, not completed.
- `レビュー観点`: Translate quality expectations into checks reviewers can apply.
- `未決事項・リスク`: Prefer explicit decisions over unresolved questions. Decide recommended defaults when reasonable, and leave only truly implementation-dependent items as proposals or risks.

## Documentation Maintenance Policy

Every task that can affect code, behavior, API contracts, data schemas, security, operations, or developer workflows must include a concrete `ドキュメントメンテナンス計画`.

The plan should cover the relevant subset below:

- Requirements:
  - identify related requirements or acceptance criteria
  - update or add durable requirements docs when behavior changes
  - keep "what must be true" in requirements and move "how to implement" to architecture / design docs
- Architecture / design:
  - update architecture, authorization, data structure, API, or deployment design docs when affected
  - preserve traceability to issues, ADRs, design docs, or decision records when they exist
- User / developer docs:
  - update root `README.md`, API examples, local verification, operations, and deploy docs when behavior, API, verification, environment variables, permissions, rollback, cost, or deployment changes
- PR body:
  - if a doc is intentionally not updated, require the future PR body to explain why it is unaffected
  - list unrun checks and residual documentation risks

## Decision Policy

When updating or creating task files:

- Do not leave "要判断" or "未決" as a placeholder if the repository context supports a conservative default.
- Use `決定事項` for recommended choices that should guide implementation.
- Use `実装時確認` only when the answer depends on runtime measurements, missing stakeholder input, environment state, or data that is not available in the repository.
- Use `リスク` for known hazards such as compatibility, security, cost, latency, migration, or release instability.
- Prefer backward-compatible decisions:
  - keep existing API request / response behavior unless the task explicitly requires a contract change
  - add optional fields before required fields
  - preserve existing manifests / artifacts through runtime fallback
  - record version or migration notes when behavior becomes configurable

## State Transitions

- New tasks from plans, reports, reviews, or roadmaps start in `tasks/todo/` unless they are being executed immediately.
- Before implementation starts, move the task file to `tasks/do/`, update `保存先`, and set `状態` to `do`.
- After all deliverables and validations are complete, move the task file to `tasks/done/`, update `保存先`, set `状態` to `done`, and add completion notes when useful.
- Do not move a task to `tasks/done/` when validation is failing or known blockers remain.
- When moving task files, update direct task-to-task references in affected task files so they point to the new state directory.

## Review Checklist Base

Every implementation task should include task-specific review points covering the relevant subset below:

- Whole change:
  - title, body, changed scope, reports, unverified checks, and risks are clear
  - unrelated goals are not mixed
- Requirements and docs:
  - feature or behavior changes update related requirements or docs when needed
  - requirements stay separate from architecture / design details
  - README, API examples, local verification, operations, deploy docs, and API docs are updated or explicitly judged unaffected
- Architecture and layering:
  - UI, route/controller, service, repository/store, and infrastructure responsibilities stay separated
  - new abstractions remove real complexity or follow existing patterns
- Testing:
  - tests match the changed layer: API, UI, data, infra, docs, or smoke
  - normal, error, boundary, permission, missing data, and compatibility cases are covered when relevant
  - unrun checks are not claimed as complete
- Security and access control:
  - authentication, authorization, response filtering, logs, debug output, tokens, and confidential data exposure are reviewed
- Data, compatibility, and migration:
  - optional fields remain backward-compatible
  - required field additions, schema changes, migrations, cutover, and rollback are called out
- Operations, dependencies, and configuration:
  - environment variables, permissions, CI, cost, logging, deployment, and rollback implications are documented when affected

Use review comment severity labels when capturing expected review outcomes:

- `blocking`: merge would create a safety, compatibility, security, or operational problem
- `should fix`: should be fixed before merge for quality or maintainability
- `suggestion`: optional quality improvement
- `question`: intent or scope clarification

## Validation

Before finishing:

- Inspect changed task files for missing required sections.
- Ensure `保存先` and `状態` match the file's current state directory when state directories are used.
- Ensure each task has a `タスク種別` value and that it is one of `機能追加`, `修正`, `調査`, or `ドキュメント更新`.
- Ensure each task has a `ドキュメントメンテナンス計画` section.
- Ensure each task has a `レビュー観点` section.
- Ensure `未決事項・リスク` uses explicit `決定事項` where a recommended choice is possible.
- Run a trailing-whitespace check on created Markdown and skill files.
- Run `git diff --check` when practical.
- If a validation command is skipped, record the reason in the final response or post-task report.
