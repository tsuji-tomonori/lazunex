# Repository Agent Instructions

このリポジトリで作業する AI agent は、以下を守る。

## 共通

- 指定 skill が利用可能一覧に出ない場合も、リポジトリローカルの明示ルールとして該当 `SKILL.md` を読む。
- `git diff`、`git status`、変更ファイル一覧、ステージ済み差分、PR 内容、作業レポートから文面を作る場合も該当 skill を適用する。
- 実施していないテスト、確認、検証を実施済みとして書かない。
- 既存の未コミット変更やユーザー作業を勝手に戻さない。

## Completion Discipline

- 完了条件を満たすまで「完了」と報告しない。
- 実作業前にチェックリストと Done 条件（deliverables + validations）を明示する。
- 計画のみ依頼でない限り、計画作成で止まらず実装・検証まで進める。
- 検証失敗時は修正して再実行し、未解決失敗を残したまま完了扱いしない。
- ブロック時は「完了」ではなく「blocked / partially complete」として報告する。
- 不可逆操作（破壊的削除、履歴改変、外部サービスの本番変更など）は最終実行前に確認を要求する。
- 長時間・複雑タスクでは以下 skills の併用を推奨する。
  - `skills/task-completion-guardian/SKILL.md`
  - `skills/verification-repair-loop/SKILL.md`
  - `skills/milestone-exec-runner/SKILL.md`
  - `skills/blocker-recovery/SKILL.md`
  - `skills/completion-status-reporter/SKILL.md`

## Task and Work Tracking

- 複数ステップの作業では、着手前に目的、受け入れ条件、検証方法を明確にする。
- タスクファイルを作る場合は、状態、背景、範囲、非対象、受け入れ条件、検証方法、リスクを記載する。
- 作業完了後にレポートが必要な場合は `skills/post-task-fit-report/SKILL.md` を使い、指示、判断、実施内容、成果物、未対応・リスクを分けて記録する。
- `git commit`、commit message 作成、ステージ済み差分確認、commit 用の文面作成だけを依頼された場合は、新規の作業レポートを作成しない。

## Git Commit Message

- 対象: Git commit message、コミットメッセージ、コミットコメント、git comment、`git commit`。
- 必読: `skills/japanese-git-commit-gitmoji/SKILL.md`
- commit 前に `git diff --cached --name-only` でステージ済みファイルを確認する。
- 変更目的が複数に分かれる場合は、1 commit にまとめず目的別分割を検討する。
- 1 行目は原則 `<emoji> <type>(<scope>): <日本語の要約>`。scope 不要または不明なら省略可。
- commit 作業のためだけに `reports/working/` へ新規レポートを追加しない。既にステージ済みの作業レポートがある場合のみ、内容を確認して commit message に反映する。

## Pull Request Title and Comment

- 対象: Pull Request、PR、PR タイトル、PR 本文、PR コメント、レビューコメント、`gh pr create`。
- 必読: `skills/japanese-pr-title-comment/SKILL.md`
- PR タイトル、PR 本文、PR コメント、レビューコメントは日本語で書く。
- ブランチ名、ファイルパス、コマンド、API 名、型名、関数名、issue 番号は原文維持可。
- PR 本文は、リポジトリにテンプレートがある場合はその見出しを優先する。

## PR Self Review

- 対象: PR 作成、PR 更新、PR 本文更新、PR コメント、レビューコメント、PR のセルフレビュー、`git diff` や作業レポートからレビュー観点を作る作業。
- 必読: `skills/pr-review-self-review/SKILL.md`
- PR を作成または更新する場合は、変更差分・PR本文・検証結果を確認し、日本語のセルフレビュー結果を PR の top-level comment として記載する。
- セルフレビューでは特に、目的と差分の整合、docs と実装の同期、変更範囲に見合うテスト、未確認事項の明示を確認する。
- 未実施の検証、未確認の CI、push の制約は実施済み扱いしない。
- blocking 指摘がある場合は、修正または blocked / partially complete として明示するまで「完了」扱いにしない。

## Implementation Docs Maintenance

- 対象: 実装、修正、リファクタ、設定変更、API 変更、運用手順変更など、コードまたは挙動に影響する作業。
- 必読（必要に応じて）: `skills/implementation-docs-maintainer/SKILL.md`
- 作業前後に、README、`docs/`、API 例、運用手順、`AGENTS.md` への影響を確認する。
- ドキュメント更新が必要なら同じ作業範囲で更新する。不要なら最終回答または作業レポートで理由を簡潔に示す。

## Implementation Test Selection

- 対象: 実装、修正、リファクタ、設定変更、ドキュメント変更の完了前。
- 必読: `skills/implementation-test-selector/SKILL.md`
- 検証コマンドの実行・再実行・権限委譲・未実施理由の報告には `skills/repository-test-runner/SKILL.md` も適用する。
- Taskfile 経由の検証コマンドには `skills/taskfile-command-runner/SKILL.md` も適用する。
- 変更範囲を確認し、最小十分な lint、typecheck、test、build、smoke、docs check を選ぶ。
- 実行できる検証は実行する。省略した場合は、コマンド名と理由を最終回答または作業レポートに記載する。

## Permission Delegation

- 対象: gh commands、Taskfile コマンド、テスト・lint・typecheck・build・docs check・smoke・benchmark の実行。
- 必読（必要に応じて）: `skills/github-apps-pr-operator/SKILL.md`、`skills/taskfile-command-runner/SKILL.md`、`skills/repository-test-runner/SKILL.md`
- repository 内で定義された Taskfile / npm scripts / 検証コマンドを実行する前に、実際に解決されるコマンド本文を確認する。
- `require_escalated` を使う再実行は自動化しない。必要性・影響範囲・実行コマンド（prefix を含む）を明示して、都度ユーザー確認を取る。
- 破壊的削除、履歴改変、PR merge/close、deploy/release/bootstrap、production/external state を変更する操作は、確認必須とする。
