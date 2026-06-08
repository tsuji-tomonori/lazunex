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

- **MUST** `[checker:rule_has_checker_tag]`: `MUST`、`MUST NOT`、`SHOULD`、`SHOULD NOT`、`MAY` の規約行は checker tag を 1 個以上持つ。
- **MUST** `[checker:normative_no_ambiguous_words]`: 規約行は設定ファイルの `ambiguous_words` に含まれる語を含めない。
- **MUST** `[checker:required_paths]`: `src/app`、`src/db`、`src/tools` を配置する。
- **MUST** `[checker:repo_python_policy]`: `pyproject.toml` は Python `>=3.14,<3.15`、Ruff `py314`、Pyright `3.14`、mypy `3.14` を宣言する。
- **MUST** `[checker:quality_commands_declared]`: `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` の実行コマンドをリポジトリ内に記載する。

## 実装してはいけない内容

- **MUST NOT** `[checker:rule_has_checker_tag]`: checker を持たない規約行を追加しない。
- **MUST NOT** `[checker:normative_no_ambiguous_words]`: 規約行へ判定条件を数値化できない語を入れない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-00_TERMS_AND_SCOPE-L017-01` **MUST** `[checker:rule_has_checker_tag]` `MUST`、`MUST NOT`、`SHOULD`、`SHOULD NOT`、`MAY` の規約行は checker tag を 1 個以上持つ。  `source:00_terms_and_scope.md:17`
- [ ] `RULE-00_TERMS_AND_SCOPE-L018-02` **MUST** `[checker:normative_no_ambiguous_words]` 規約行は設定ファイルの `ambiguous_words` に含まれる語を含めない。  `source:00_terms_and_scope.md:18`
- [ ] `RULE-00_TERMS_AND_SCOPE-L019-03` **MUST** `[checker:required_paths]` `src/app`、`src/db`、`src/tools` を配置する。  `source:00_terms_and_scope.md:19`
- [ ] `RULE-00_TERMS_AND_SCOPE-L020-04` **MUST** `[checker:repo_python_policy]` `pyproject.toml` は Python `>=3.14,<3.15`、Ruff `py314`、Pyright `3.14`、mypy `3.14` を宣言する。  `source:00_terms_and_scope.md:20`
- [ ] `RULE-00_TERMS_AND_SCOPE-L021-05` **MUST** `[checker:quality_commands_declared]` `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` の実行コマンドをリポジトリ内に記載する。  `source:00_terms_and_scope.md:21`
- [ ] `RULE-00_TERMS_AND_SCOPE-L025-06` **MUST NOT** `[checker:rule_has_checker_tag]` checker を持たない規約行を追加しない。  `source:00_terms_and_scope.md:25`
- [ ] `RULE-00_TERMS_AND_SCOPE-L026-07` **MUST NOT** `[checker:normative_no_ambiguous_words]` 規約行へ判定条件を数値化できない語を入れない。  `source:00_terms_and_scope.md:26`

<!-- rulecheck:generated-checklist:end -->
