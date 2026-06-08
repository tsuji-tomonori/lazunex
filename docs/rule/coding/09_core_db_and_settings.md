# 09. `core`、`app/db`、設定

`core` は設定、例外、構造化ログを持つ。`app/db` は session と SQL 実行 helper を持つ。

## 実装すべき内容

- **MUST** `[checker:required_paths]`: `src/app/core/config.py`、`src/app/core/exceptions.py`、`src/app/core/logging.py` を配置する。
- **MUST** `[checker:db_query_contract]`: `src/app/db/query.py` は `load_sql`、`model_parameters`、`fetch_all`、`fetch_one`、`execute_sql` を提供する。
- **MUST** `[checker:required_paths]`: `src/app/db/session.py` を配置する。
- **MUST** `[checker:repo_python_policy]`: 型検査は Pyright strict と mypy strict を使う。
- **MUST** `[checker:quality_commands_declared]`: formatter、linter、型検査、pytest のコマンドを README または設定に記録する。

## 実装してはいけない内容

- **MUST NOT** `[checker:integration_provider_boundary]`: `src/app/core` と `src/app/db` から provider client を import しない。
- **MUST NOT** `[checker:sql_placeholders_at_names]`: SQL 実行 helper を迂回するために SQL ファイルへ SQLAlchemy `:name` placeholder を書かない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L007-01` **MUST** `[checker:required_paths]` `src/app/core/config.py`、`src/app/core/exceptions.py`、`src/app/core/logging.py` を配置する。  `source:09_core_db_and_settings.md:7`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L008-02` **MUST** `[checker:db_query_contract]` `src/app/db/query.py` は `load_sql`、`model_parameters`、`fetch_all`、`fetch_one`、`execute_sql` を提供する。  `source:09_core_db_and_settings.md:8`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L009-03` **MUST** `[checker:required_paths]` `src/app/db/session.py` を配置する。  `source:09_core_db_and_settings.md:9`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L010-04` **MUST** `[checker:repo_python_policy]` 型検査は Pyright strict と mypy strict を使う。  `source:09_core_db_and_settings.md:10`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L011-05` **MUST** `[checker:quality_commands_declared]` formatter、linter、型検査、pytest のコマンドを README または設定に記録する。  `source:09_core_db_and_settings.md:11`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L015-06` **MUST NOT** `[checker:integration_provider_boundary]` `src/app/core` と `src/app/db` から provider client を import しない。  `source:09_core_db_and_settings.md:15`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L016-07` **MUST NOT** `[checker:sql_placeholders_at_names]` SQL 実行 helper を迂回するために SQL ファイルへ SQLAlchemy `:name` placeholder を書かない。  `source:09_core_db_and_settings.md:16`

<!-- rulecheck:generated-checklist:end -->
