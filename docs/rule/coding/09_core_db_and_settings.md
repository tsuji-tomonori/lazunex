# 09. `core`、`app/db`、設定

`core` は設定、例外、構造化ログを持つ。`app/db` は session と SQL 実行 helper を持つ。

## 実装すべき内容

- `src/app/core/config.py`、`src/app/core/exceptions.py`、`src/app/core/logging.py` を配置する。
- `src/app/db/query.py` は `load_sql`、`model_parameters`、`fetch_all`、`fetch_one`、`execute_sql` を提供する。
- `src/app/db/session.py` を配置する。
- 型検査は Pyright strict と mypy strict を使う。
- formatter、linter、型検査、pytest のコマンドを README または設定に記録する。

## 実装してはいけない内容

- `src/app/core` と `src/app/db` から provider client を import しない。
- SQL 実行 helper を迂回するために SQL ファイルへ SQLAlchemy `:name` placeholder を書かない。

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| CORE-DO-001 | MUST | `required_paths` | - | `src/app/core/config.py`、`src/app/core/exceptions.py`、`src/app/core/logging.py` を配置する。 |
| CORE-DO-002 | MUST | `db_query_contract` | `src/app/db/query.py` | `load_sql`、`model_parameters`、`fetch_all`、`fetch_one`、`execute_sql` を提供する。 |
| CORE-DO-003 | MUST | `required_paths` | - | `src/app/db/session.py` を配置する。 |
| CORE-DO-004 | MUST | `repo_python_policy` | - | 型検査は Pyright strict と mypy strict を使う。 |
| CORE-DO-005 | MUST | `quality_commands_declared` | - | formatter、linter、型検査、pytest のコマンドを README または設定に記録する。 |
| CORE-DONT-001 | MUST NOT | `integration_provider_boundary` | - | `src/app/core` と `src/app/db` から provider client を import しない。 |
| CORE-DONT-002 | MUST NOT | `sql_placeholders_at_names` | - | SQL 実行 helper を迂回するために SQL ファイルへ SQLAlchemy `:name` placeholder を書かない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `src/app/core/config.py`、`src/app/core/exceptions.py`、`src/app/core/logging.py` を配置する。 (`CORE-DO-001`, **MUST**, `[checker:required_paths]`)  `source:09_core_db_and_settings.md:22`
- [ ] `src/app/db/query.py`: `load_sql`、`model_parameters`、`fetch_all`、`fetch_one`、`execute_sql` を提供する。 (`CORE-DO-002`, **MUST**, `[checker:db_query_contract]`)  `source:09_core_db_and_settings.md:23`
- [ ] `src/app/db/session.py` を配置する。 (`CORE-DO-003`, **MUST**, `[checker:required_paths]`)  `source:09_core_db_and_settings.md:24`
- [ ] 型検査は Pyright strict と mypy strict を使う。 (`CORE-DO-004`, **MUST**, `[checker:repo_python_policy]`)  `source:09_core_db_and_settings.md:25`
- [ ] formatter、linter、型検査、pytest のコマンドを README または設定に記録する。 (`CORE-DO-005`, **MUST**, `[checker:quality_commands_declared]`)  `source:09_core_db_and_settings.md:26`
- [ ] `src/app/core` と `src/app/db` から provider client を import しない。 (`CORE-DONT-001`, **MUST NOT**, `[checker:integration_provider_boundary]`)  `source:09_core_db_and_settings.md:27`
- [ ] SQL 実行 helper を迂回するために SQL ファイルへ SQLAlchemy `:name` placeholder を書かない。 (`CORE-DONT-002`, **MUST NOT**, `[checker:sql_placeholders_at_names]`)  `source:09_core_db_and_settings.md:28`

<!-- rulecheck:generated-checklist:end -->
