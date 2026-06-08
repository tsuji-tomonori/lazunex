# 00. 規約用語と適用範囲

この規約は、FastAPI/Python の `src/` 実装、生成系ツール、SQL、仕様生成ドキュメントを同じ粒度で検査するためのルールである。

## 規約語

| 用語 | 意味 |
| :--- | :--- |
| MUST | 実装で必ず満たす。未達の場合は CI を失敗にする。 |
| MUST NOT | 実装で禁止する。検出時は CI を失敗にする。 |
| SHOULD | 満たす対象にする。未達の場合は警告または段階導入の失敗にする。 |
| SHOULD NOT | 禁止対象にする。未達の場合は警告または段階導入の失敗にする。 |
| MAY | 採用を許可する。検査結果は SKIP または PASS にできる。 |

## 実装すべき内容

- `MUST`、`MUST NOT`、`SHOULD`、`SHOULD NOT`、`MAY` の規約行は checker tag を 1 個以上持つ。
- 規約行は設定ファイルの `ambiguous_words` に含まれる語を含めない。
- `src/app`、`src/db`、`src/tools` を配置する。
- `pyproject.toml` は Python `>=3.14,<3.15`、Ruff `py314`、Pyright `3.14`、mypy `3.14` を宣言する。
- `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` の実行コマンドをリポジトリ内に記載する。

## 実装してはいけない内容

- checker を持たない規約行を追加しない。
- 規約行へ判定条件を数値化できない語を入れない。

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| SCOPE-DO-001 | MUST | `rule_has_checker_tag` | - | `MUST`、`MUST NOT`、`SHOULD`、`SHOULD NOT`、`MAY` の規約行は checker tag を 1 個以上持つ。 |
| SCOPE-DO-002 | MUST | `normative_no_ambiguous_words` | - | 規約行は設定ファイルの `ambiguous_words` に含まれる語を含めない。 |
| SCOPE-DO-003 | MUST | `required_paths` | - | `src/app`、`src/db`、`src/tools` を配置する。 |
| SCOPE-DO-004 | MUST | `repo_python_policy` | `pyproject.toml` | Python `>=3.14,<3.15`、Ruff `py314`、Pyright `3.14`、mypy `3.14` を宣言する。 |
| SCOPE-DO-005 | MUST | `quality_commands_declared` | - | `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` の実行コマンドをリポジトリ内に記載する。 |
| SCOPE-DONT-001 | MUST NOT | `rule_has_checker_tag` | - | checker を持たない規約行を追加しない。 |
| SCOPE-DONT-002 | MUST NOT | `normative_no_ambiguous_words` | - | 規約行へ判定条件を数値化できない語を入れない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `MUST`、`MUST NOT`、`SHOULD`、`SHOULD NOT`、`MAY` の規約行は checker tag を 1 個以上持つ。 (`SCOPE-DO-001`, **MUST**, `[checker:rule_has_checker_tag]`)  `source:00_terms_and_scope.md:32`
- [ ] 規約行は設定ファイルの `ambiguous_words` に含まれる語を含めない。 (`SCOPE-DO-002`, **MUST**, `[checker:normative_no_ambiguous_words]`)  `source:00_terms_and_scope.md:33`
- [ ] `src/app`、`src/db`、`src/tools` を配置する。 (`SCOPE-DO-003`, **MUST**, `[checker:required_paths]`)  `source:00_terms_and_scope.md:34`
- [ ] `pyproject.toml`: Python `>=3.14,<3.15`、Ruff `py314`、Pyright `3.14`、mypy `3.14` を宣言する。 (`SCOPE-DO-004`, **MUST**, `[checker:repo_python_policy]`)  `source:00_terms_and_scope.md:35`
- [ ] `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` の実行コマンドをリポジトリ内に記載する。 (`SCOPE-DO-005`, **MUST**, `[checker:quality_commands_declared]`)  `source:00_terms_and_scope.md:36`
- [ ] checker を持たない規約行を追加しない。 (`SCOPE-DONT-001`, **MUST NOT**, `[checker:rule_has_checker_tag]`)  `source:00_terms_and_scope.md:37`
- [ ] 規約行へ判定条件を数値化できない語を入れない。 (`SCOPE-DONT-002`, **MUST NOT**, `[checker:normative_no_ambiguous_words]`)  `source:00_terms_and_scope.md:38`

<!-- rulecheck:generated-checklist:end -->
