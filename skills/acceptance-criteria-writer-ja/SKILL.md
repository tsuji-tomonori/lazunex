---
name: acceptance-criteria-writer-ja
description: task から正常系、異常系、境界値、権限、非機能、セキュリティを含む日本語の受け入れ条件を作成する。
---

# Acceptance Criteria Writer JA

## What this skill does

タスク、仕様、調査結果、作業計画から、日本語の受け入れ条件を作成する。通常の UI / API 機能だけでなく、異常系、権限、境界値、非機能、セキュリティも含める。

## Inputs

- ユーザー依頼、タスクファイル、仕様、画面、API、テスト、作業レポート
- 関連する既存コード、ドキュメント、Issue、PR

## Acceptance Criteria Principles

- 受け入れ条件は検証可能に書く。
- 1 つの条件には 1 つの期待結果を書く。
- Given/When/Then 形式を優先する。
- UI 表示だけでなく、データ状態、権限、ログ、永続化、エラー処理も考慮する。
- 非機能要件は曖昧にせず、確認方法または測定方法を添える。
- 推定は `Confidence: inferred` とし、事実確認済みの条件と分ける。

## Coverage Dimensions

For each task, consider these dimensions:

```text
normal_path
error_path
permission
boundary
empty_state
loading_state
retry_or_recovery
data_persistence
audit_log
security
privacy
performance
accessibility
compatibility
non_functional
```

## Output Format

Create or update the requested task or specification document. If no destination is specified, return Markdown that can be copied into a task file.

```markdown
## AC-001: PDF 文書をアップロードできる

- Task: TASK-001
- Type: normal_path
- Confidence: confirmed
- Source: FACT-001

### Given
- ユーザーがログイン済みである
- ユーザーに文書登録権限がある

### When
- ユーザーがドキュメント管理画面から PDF ファイルをアップロードする

### Then
- ファイルが文書一覧に表示される
- ステータスが処理中または完了として確認できる
- 失敗時はユーザーに再試行可能なエラーが表示される
```

## Quality Checks

Before finishing:

- Every task has at least one acceptance criterion.
- Every critical user-facing task has normal and error path criteria.
- Every privileged operation has permission criteria.
- Boundary, empty, retry, and compatibility cases are included when relevant.
- Any missing threshold becomes an open question, not a fabricated number.
