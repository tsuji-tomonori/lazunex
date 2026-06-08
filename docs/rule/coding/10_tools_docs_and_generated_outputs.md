# 10. `src/tools` と生成物

`src/tools` は仕様生成、SQL query 生成、CRUD 生成、sequence 生成、operational logging 検査を担う。生成物は `docs/spec/40.apis` に出す。

## 実装すべき内容

- `src/tools/check_api_function_names.py`、`generate_api_sequences.py`、`check_api_mermaid_sequences.py`、`generate_queries.py`、`generate_db_crud.py`、`check_operational_logging.py` を配置する。
- `generate_queries.py` の出力は operation 直下の `queries.py` にする。
- CI 用コマンドに `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` を含める。
- `src/tools/**/*.py` のファイル論理行数は設定ファイルの `file_logical_lines` 以下にする。
- `src/tools/**/*.py` の関数論理行数は設定ファイルの `function_logical_lines` 以下にする。

## 実装してはいけない内容

- `src/tools/generate_queries.py` の出力先を `generated/queries.py` に戻さない。
- 現行 checker/generator のファイル名を変更しない。

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| TOOLS-DO-001 | MUST | `tools_existing_checks` | - | `src/tools/check_api_function_names.py`、`generate_api_sequences.py`、`check_api_mermaid_sequences.py`、`generate_queries.py`、`generate_db_crud.py`、`check_operational_logging.py` を配置する。 |
| TOOLS-DO-002 | MUST | `queries_generated_marker` | - | `generate_queries.py` の出力は operation 直下の `queries.py` にする。 |
| TOOLS-DO-003 | MUST | `quality_commands_declared` | - | CI 用コマンドに `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` を含める。 |
| TOOLS-DO-004 | MUST | `file_logical_lines` | - | `src/tools/**/*.py` のファイル論理行数は設定ファイルの `file_logical_lines` 以下にする。 |
| TOOLS-DO-005 | MUST | `function_logical_lines` | - | `src/tools/**/*.py` の関数論理行数は設定ファイルの `function_logical_lines` 以下にする。 |
| TOOLS-DONT-001 | MUST NOT | `forbid_generated_subdir_queries` | - | `src/tools/generate_queries.py` の出力先を `generated/queries.py` に戻さない。 |
| TOOLS-DONT-002 | MUST NOT | `tools_existing_checks` | - | 現行 checker/generator のファイル名を変更しない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `src/tools/check_api_function_names.py`、`generate_api_sequences.py`、`check_api_mermaid_sequences.py`、`generate_queries.py`、`generate_db_crud.py`、`check_operational_logging.py` を配置する。 (`TOOLS-DO-001`, **MUST**, `[checker:tools_existing_checks]`)  `source:10_tools_docs_and_generated_outputs.md:22`
- [ ] `generate_queries.py` の出力は operation 直下の `queries.py` にする。 (`TOOLS-DO-002`, **MUST**, `[checker:queries_generated_marker]`)  `source:10_tools_docs_and_generated_outputs.md:23`
- [ ] CI 用コマンドに `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` を含める。 (`TOOLS-DO-003`, **MUST**, `[checker:quality_commands_declared]`)  `source:10_tools_docs_and_generated_outputs.md:24`
- [ ] `src/tools/**/*.py` のファイル論理行数は設定ファイルの `file_logical_lines` 以下にする。 (`TOOLS-DO-004`, **MUST**, `[checker:file_logical_lines]`)  `source:10_tools_docs_and_generated_outputs.md:25`
- [ ] `src/tools/**/*.py` の関数論理行数は設定ファイルの `function_logical_lines` 以下にする。 (`TOOLS-DO-005`, **MUST**, `[checker:function_logical_lines]`)  `source:10_tools_docs_and_generated_outputs.md:26`
- [ ] `src/tools/generate_queries.py` の出力先を `generated/queries.py` に戻さない。 (`TOOLS-DONT-001`, **MUST NOT**, `[checker:forbid_generated_subdir_queries]`)  `source:10_tools_docs_and_generated_outputs.md:27`
- [ ] 現行 checker/generator のファイル名を変更しない。 (`TOOLS-DONT-002`, **MUST NOT**, `[checker:tools_existing_checks]`)  `source:10_tools_docs_and_generated_outputs.md:28`

<!-- rulecheck:generated-checklist:end -->
