# 01. `src/` 全体構成

現行構成は `src/app`、`src/db`、`src/tools` をトップレベルに置く。アプリ本体、DDL、開発用 checker/generator を分離する。

## 実装すべき内容

- **MUST** `[checker:required_paths]`: `src/app`、`src/db`、`src/tools` を配置する。
- **MUST** `[checker:required_paths]`: `src/app/main.py`、`src/app/local.py`、`src/app/core`、`src/app/db`、`src/app/apis`、`src/app/integrations` を配置する。
- **MUST** `[checker:ddl_exists]`: `src/db/ddl.sql` を配置し、空ファイルにしない。
- **MUST** `[checker:tools_existing_checks]`: `src/tools` に現行の checker/generator スクリプトを配置する。
- **MUST** `[checker:file_logical_lines]`: Python ファイルの論理行数は `config/rulecheck_config.example.json` の `file_logical_lines` 以下にする。

## 実装してはいけない内容

- **MUST NOT** `[checker:integration_provider_boundary]`: `src/app/integrations/_aws_boto3.py` と `src/app/integrations/**/boto3_provider/*.py` 以外の `src/app/**/*.py` から provider import を行わない。
- **MUST NOT** `[checker:required_paths]`: DDL を `src/app` 配下に配置しない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-01_SRC_LAYOUT-L007-01` **MUST** `[checker:required_paths]` `src/app`、`src/db`、`src/tools` を配置する。  `source:01_src_layout.md:7`
- [ ] `RULE-01_SRC_LAYOUT-L008-02` **MUST** `[checker:required_paths]` `src/app/main.py`、`src/app/local.py`、`src/app/core`、`src/app/db`、`src/app/apis`、`src/app/integrations` を配置する。  `source:01_src_layout.md:8`
- [ ] `RULE-01_SRC_LAYOUT-L009-03` **MUST** `[checker:ddl_exists]` `src/db/ddl.sql` を配置し、空ファイルにしない。  `source:01_src_layout.md:9`
- [ ] `RULE-01_SRC_LAYOUT-L010-04` **MUST** `[checker:tools_existing_checks]` `src/tools` に現行の checker/generator スクリプトを配置する。  `source:01_src_layout.md:10`
- [ ] `RULE-01_SRC_LAYOUT-L011-05` **MUST** `[checker:file_logical_lines]` Python ファイルの論理行数は `config/rulecheck_config.example.json` の `file_logical_lines` 以下にする。  `source:01_src_layout.md:11`
- [ ] `RULE-01_SRC_LAYOUT-L015-06` **MUST NOT** `[checker:integration_provider_boundary]` `src/app/integrations/_aws_boto3.py` と `src/app/integrations/**/boto3_provider/*.py` 以外の `src/app/**/*.py` から provider import を行わない。  `source:01_src_layout.md:15`
- [ ] `RULE-01_SRC_LAYOUT-L016-07` **MUST NOT** `[checker:required_paths]` DDL を `src/app` 配下に配置しない。  `source:01_src_layout.md:16`

<!-- rulecheck:generated-checklist:end -->
