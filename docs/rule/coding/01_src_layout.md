# 01. `src/` 全体構成

現行構成は `src/app`、`src/db`、`src/tools` をトップレベルに置く。アプリ本体、DDL、開発用 checker/generator を分離する。

## 実装すべき内容

- `src/app`、`src/db`、`src/tools` を配置する。
- `src/app/main.py`、`src/app/local.py`、`src/app/core`、`src/app/db`、`src/app/apis`、`src/app/integrations` を配置する。
- `src/db/ddl.sql` を配置し、空ファイルにしない。
- `src/tools` に現行の checker/generator スクリプトを配置する。
- Python ファイルの論理行数は `config/rulecheck_config.example.json` の `file_logical_lines` 以下にする。

## 実装してはいけない内容

- `src/app/integrations/_aws_boto3.py` と `src/app/integrations/**/boto3_provider/*.py` 以外の `src/app/**/*.py` から provider import を行わない。
- DDL を `src/app` 配下に配置しない。

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| LAYOUT-DO-001 | MUST | `required_paths` | - | `src/app`、`src/db`、`src/tools` を配置する。 |
| LAYOUT-DO-002 | MUST | `required_paths` | - | `src/app/main.py`、`src/app/local.py`、`src/app/core`、`src/app/db`、`src/app/apis`、`src/app/integrations` を配置する。 |
| LAYOUT-DO-003 | MUST | `ddl_exists` | - | `src/db/ddl.sql` を配置し、空ファイルにしない。 |
| LAYOUT-DO-004 | MUST | `tools_existing_checks` | - | `src/tools` に現行の checker/generator スクリプトを配置する。 |
| LAYOUT-DO-005 | MUST | `file_logical_lines` | - | Python ファイルの論理行数は `config/rulecheck_config.example.json` の `file_logical_lines` 以下にする。 |
| LAYOUT-DONT-001 | MUST NOT | `integration_provider_boundary` | - | `src/app/integrations/_aws_boto3.py` と `src/app/integrations/**/boto3_provider/*.py` 以外の `src/app/**/*.py` から provider import を行わない。 |
| LAYOUT-DONT-002 | MUST NOT | `required_paths` | - | DDL を `src/app` 配下に配置しない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `src/app`、`src/db`、`src/tools` を配置する。 (`LAYOUT-DO-001`, **MUST**, `[checker:required_paths]`)  `source:01_src_layout.md:22`
- [ ] `src/app/main.py`、`src/app/local.py`、`src/app/core`、`src/app/db`、`src/app/apis`、`src/app/integrations` を配置する。 (`LAYOUT-DO-002`, **MUST**, `[checker:required_paths]`)  `source:01_src_layout.md:23`
- [ ] `src/db/ddl.sql` を配置し、空ファイルにしない。 (`LAYOUT-DO-003`, **MUST**, `[checker:ddl_exists]`)  `source:01_src_layout.md:24`
- [ ] `src/tools` に現行の checker/generator スクリプトを配置する。 (`LAYOUT-DO-004`, **MUST**, `[checker:tools_existing_checks]`)  `source:01_src_layout.md:25`
- [ ] Python ファイルの論理行数は `config/rulecheck_config.example.json` の `file_logical_lines` 以下にする。 (`LAYOUT-DO-005`, **MUST**, `[checker:file_logical_lines]`)  `source:01_src_layout.md:26`
- [ ] `src/app/integrations/_aws_boto3.py` と `src/app/integrations/**/boto3_provider/*.py` 以外の `src/app/**/*.py` から provider import を行わない。 (`LAYOUT-DONT-001`, **MUST NOT**, `[checker:integration_provider_boundary]`)  `source:01_src_layout.md:27`
- [ ] DDL を `src/app` 配下に配置しない。 (`LAYOUT-DONT-002`, **MUST NOT**, `[checker:required_paths]`)  `source:01_src_layout.md:28`

<!-- rulecheck:generated-checklist:end -->
