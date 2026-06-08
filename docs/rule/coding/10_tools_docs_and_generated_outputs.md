# 10. `src/tools` と生成物

`src/tools` は仕様生成、SQL query 生成、CRUD 生成、sequence 生成、operational logging 検査を担う。生成物は `docs/spec/40.apis` に出す。

## 実装すべき内容

- **MUST** `[checker:tools_existing_checks]`: `src/tools/check_api_function_names.py`、`generate_api_sequences.py`、`check_api_mermaid_sequences.py`、`generate_queries.py`、`generate_db_crud.py`、`check_operational_logging.py` を配置する。
- **MUST** `[checker:queries_generated_marker]`: `generate_queries.py` の出力は operation 直下の `queries.py` にする。
- **MUST** `[checker:quality_commands_declared]`: CI 用コマンドに `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` を含める。
- **MUST** `[checker:file_logical_lines]`: `src/tools/**/*.py` のファイル論理行数は設定ファイルの `file_logical_lines` 以下にする。
- **MUST** `[checker:function_logical_lines]`: `src/tools/**/*.py` の関数論理行数は設定ファイルの `function_logical_lines` 以下にする。

## 実装してはいけない内容

- **MUST NOT** `[checker:forbid_generated_subdir_queries]`: `src/tools/generate_queries.py` の出力先を `generated/queries.py` に戻さない。
- **MUST NOT** `[checker:tools_existing_checks]`: 現行 checker/generator のファイル名を変更しない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L007-01` **MUST** `[checker:tools_existing_checks]` `src/tools/check_api_function_names.py`、`generate_api_sequences.py`、`check_api_mermaid_sequences.py`、`generate_queries.py`、`generate_db_crud.py`、`check_operational_logging.py` を配置する。  `source:10_tools_docs_and_generated_outputs.md:7`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L008-02` **MUST** `[checker:queries_generated_marker]` `generate_queries.py` の出力は operation 直下の `queries.py` にする。  `source:10_tools_docs_and_generated_outputs.md:8`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L009-03` **MUST** `[checker:quality_commands_declared]` CI 用コマンドに `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` を含める。  `source:10_tools_docs_and_generated_outputs.md:9`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L010-04` **MUST** `[checker:file_logical_lines]` `src/tools/**/*.py` のファイル論理行数は設定ファイルの `file_logical_lines` 以下にする。  `source:10_tools_docs_and_generated_outputs.md:10`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L011-05` **MUST** `[checker:function_logical_lines]` `src/tools/**/*.py` の関数論理行数は設定ファイルの `function_logical_lines` 以下にする。  `source:10_tools_docs_and_generated_outputs.md:11`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L015-06` **MUST NOT** `[checker:forbid_generated_subdir_queries]` `src/tools/generate_queries.py` の出力先を `generated/queries.py` に戻さない。  `source:10_tools_docs_and_generated_outputs.md:15`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L016-07` **MUST NOT** `[checker:tools_existing_checks]` 現行 checker/generator のファイル名を変更しない。  `source:10_tools_docs_and_generated_outputs.md:16`

<!-- rulecheck:generated-checklist:end -->
