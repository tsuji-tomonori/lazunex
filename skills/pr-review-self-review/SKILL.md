---
name: pr-review-self-review
description: Use when creating, updating, reviewing, or commenting on pull requests; run a general self-review checklist and write the result as a Japanese PR comment.
---

# PR Review Self Review

Use this skill for pull requests when:

- creating a PR
- updating a PR branch, PR body, or PR title
- writing a PR comment or review comment from a diff, status, report, or PR content
- doing a self-review before asking for review

Always combine this skill with `skills/japanese-pr-title-comment/SKILL.md` for Japanese PR text.

## Required Workflow

1. Inspect the PR scope.
   - Read `git status`, `git diff --name-only`, staged files, and relevant work reports.
   - If a PR already exists, inspect the PR body, changed files, and prior comments.
2. Classify the change.
   - `patch`: backward-compatible fix or documentation/process correction.
   - `minor`: backward-compatible feature or workflow addition.
   - `major`: breaking API, data, operation, or user-visible contract change.
3. Select checklist sections.
   - Always review: PR whole, docs sync, tests/validation, security/privacy, residual risks.
   - Add API, UI, data, infrastructure, operations, performance, accessibility, or migration sections only when touched or affected.
4. Run or confirm validation.
   - Do not mark unrun checks as complete.
   - Record skipped checks with the concrete reason.
5. Write a Japanese top-level PR comment after PR creation or material PR updates.
   - Summarize pass / concern / not verified.
   - Include commands actually run.
   - Include blocking / should fix / suggestion / question only when actionable.
6. If a blocking issue is found, fix it before marking the task done. If it cannot be fixed, report the PR as blocked or partially complete.

## PR Comment Template

```markdown
## セルフレビュー結果

対象: <PR作成時 | PR更新時 | commit SHA | branch>

### 判定

- 結論: <問題なし | should fix あり | blocking あり | 未検証あり>
- semver: <patch | minor | major> と判断。理由: <reason>

### 確認した観点

- [x] PR全体: <title/body/scope/report/risk の確認結果>
- [x] docs と実装の同期: <確認結果>
- [x] 変更範囲に見合うテスト: <確認結果>
- [x] セキュリティ・プライバシー: <確認結果または非該当理由>

### 実行した検証

- `<command>`: pass

### 未実施・制約

- `<command>`: 未実施。理由: <reason>

### 指摘

- blocking: なし
- should fix: なし
- suggestion: なし
- question: なし
```

Use checkboxes only for items actually satisfied. Use unchecked items for unresolved or unverified required items.

## Review Severity Labels

- `blocking`: merging would create safety, compatibility, security, operational, or specification problems.
- `should fix`: should be fixed before merge for quality, maintainability, or reviewability.
- `suggestion`: optional improvement.
- `question`: intent or scope clarification.

## Core Review Checklist

### PR Whole

- PR title clearly shows purpose and impact scope.
- PR body includes background/purpose, changes, impact, verification, and unverified items.
- Semver classification is reasonable: patch / minor / major.
- The PR scope is neither too broad nor incomplete for the stated goal.
- Independent goals are not mixed into one PR.
- Work reports or supplemental materials are linked or summarized when present.
- Unrun checks are listed with reason and risk.

### Requirements, Architecture, and Docs

- Feature or behavior changes update related requirements, design, operations, API, or user documentation when needed.
- Requirements describe what must be true; architecture/design docs describe how it is achieved.
- README, API examples, local verification, operations, deploy docs, and CI docs are updated or explicitly judged unaffected.
- Traceability to issues, requirements, ADRs, or design notes is preserved when those artifacts exist.

### API and Backend Changes

- Request/response schemas remain centralized and consistent with generated or published API docs.
- Route handlers mainly do validation, authorization, service calls, and HTTP status mapping.
- Business logic is kept in the appropriate service or domain layer.
- Backward compatibility is preserved unless the PR explicitly declares a breaking change.
- Errors distinguish validation, domain, permission, not found, dependency, and infrastructure failures.
- Internal exception details are not returned to clients.

### UI Changes

- API contract changes are reflected in UI types, rendering, and error handling.
- Loading, failure, empty, permission denied, and success states render coherently.
- Important interactions have accessible names, labels, focus behavior, keyboard support, and state announcements where relevant.
- UI hiding is not the only authorization control for protected data or actions.

### Data, Compatibility, and Migration

- Optional fields remain readable for old data.
- Required field additions, schema changes, migrations, cutover, and rollback are called out.
- Existing serialized artifacts, fixtures, and external integrations remain compatible or have a migration plan.
- Time/date/timezone behavior is deterministic.

### Infrastructure and Operations

- Permissions are least privilege.
- Environment variables, secrets, CI, deployment, rollback, logging, monitoring, and cost implications are documented when affected.
- Health checks and operational logs remain useful for incidents.
- Retry and fail-fast behavior is intentional.

### Tests and Validation

- Tests cover the smallest meaningful unit for the change.
- Normal, error, boundary, permission, missing data, compatibility, and regression cases are covered when relevant.
- Snapshot updates have meaningful assertions and are not broad unrelated churn.
- Test names describe expected behavior.
- E2E/smoke checks are run or intentionally skipped with reason.

### Code Quality and Maintainability

- Names match domain language.
- Responsibilities are separated across UI, route/controller, service, repository/store, and infrastructure layers.
- Duplicate logic is not increased without need.
- Test fixtures and mocks do not drift from production logic.
- Types express states instead of `string` or `any` where practical.
- Type assertions are minimal and justified.
- Async errors propagate correctly.

## Recommended Commands

Choose the smallest sufficient subset available in the repository:

```bash
npm run lint --if-present
npm run typecheck --if-present
npm test --if-present
npm run build --if-present
```

Repository Markdown / skills / agent instructions:

```bash
git diff --check
pre-commit run --files <changed-files>
```

## Merge Readiness Gate

Before saying a PR is ready:

- CI is green, or unavailable/pending checks are explicitly recorded.
- Tests are sufficient for the changed scope.
- Docs and implementation do not contradict each other.
- Implementation sits in the right layer.
- API, data, auth, and infra breaking changes are explicit.
- Security, privacy, cost, and operations concerns are resolved or documented.
- PR body has enough unverified and impact details for review judgment.
