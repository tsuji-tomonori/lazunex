# 07. SQL と `queries.py` 生成

SQL は operation の `sql/` に置き、`src/tools/generate_queries.py` が operation 直下の `queries.py` を生成する。現行 SQL は MySQL 方言、`@name` placeholder、table alias を使う。

## 実装すべき内容

- SQL ファイル名は `001_select_apis.sql` 形式の 3 桁番号 prefix を持つ。
- SQL ファイルの最初の非空行は `-- ` で始まる処理要約にする。
- SQL bind placeholder は `@name` 形式にする。
- SELECT 句は取得列名を列挙する。
- 生成後の `queries.py` は Pydantic params/row model と query function を持つ。
- `src/app/db/query.py` は `@name` placeholder を SQLAlchemy `:name` に変換する `load_sql` を持つ。

## 実装してはいけない内容

- SQL で `SELECT *` を使わない。
- SQL ファイルへ `:name` placeholder を書かない。
- SQL 生成物を operation の `generated/` 配下へ置かない。

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| SQL-DO-001 | MUST | `operation_sql_dir_files` | - | SQL ファイル名は `001_select_apis.sql` 形式の 3 桁番号 prefix を持つ。 |
| SQL-DO-002 | MUST | `sql_first_comment_summary` | - | SQL ファイルの最初の非空行は `-- ` で始まる処理要約にする。 |
| SQL-DO-003 | MUST | `sql_placeholders_at_names` | - | SQL bind placeholder は `@name` 形式にする。 |
| SQL-DO-004 | MUST | `sql_no_select_star` | - | SELECT 句は取得列名を列挙する。 |
| SQL-DO-005 | MUST | `queries_generated_marker` | - | 生成後の `queries.py` は Pydantic params/row model と query function を持つ。 |
| SQL-DO-006 | MUST | `db_query_contract` | `src/app/db/query.py` | `@name` placeholder を SQLAlchemy `:name` に変換する `load_sql` を持つ。 |
| SQL-DONT-001 | MUST NOT | `sql_no_select_star` | - | SQL で `SELECT *` を使わない。 |
| SQL-DONT-002 | MUST NOT | `sql_placeholders_at_names` | - | SQL ファイルへ `:name` placeholder を書かない。 |
| SQL-DONT-003 | MUST NOT | `forbid_generated_subdir_queries` | - | SQL 生成物を operation の `generated/` 配下へ置かない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] SQL ファイル名は `001_select_apis.sql` 形式の 3 桁番号 prefix を持つ。 (`SQL-DO-001`, **MUST**, `[checker:operation_sql_dir_files]`)  `source:07_sql_and_query_generation.md:24`
- [ ] SQL ファイルの最初の非空行は `-- ` で始まる処理要約にする。 (`SQL-DO-002`, **MUST**, `[checker:sql_first_comment_summary]`)  `source:07_sql_and_query_generation.md:25`
- [ ] SQL bind placeholder は `@name` 形式にする。 (`SQL-DO-003`, **MUST**, `[checker:sql_placeholders_at_names]`)  `source:07_sql_and_query_generation.md:26`
- [ ] SELECT 句は取得列名を列挙する。 (`SQL-DO-004`, **MUST**, `[checker:sql_no_select_star]`)  `source:07_sql_and_query_generation.md:27`
- [ ] 生成後の `queries.py` は Pydantic params/row model と query function を持つ。 (`SQL-DO-005`, **MUST**, `[checker:queries_generated_marker]`)  `source:07_sql_and_query_generation.md:28`
- [ ] `src/app/db/query.py`: `@name` placeholder を SQLAlchemy `:name` に変換する `load_sql` を持つ。 (`SQL-DO-006`, **MUST**, `[checker:db_query_contract]`)  `source:07_sql_and_query_generation.md:29`
- [ ] SQL で `SELECT *` を使わない。 (`SQL-DONT-001`, **MUST NOT**, `[checker:sql_no_select_star]`)  `source:07_sql_and_query_generation.md:30`
- [ ] SQL ファイルへ `:name` placeholder を書かない。 (`SQL-DONT-002`, **MUST NOT**, `[checker:sql_placeholders_at_names]`)  `source:07_sql_and_query_generation.md:31`
- [ ] SQL 生成物を operation の `generated/` 配下へ置かない。 (`SQL-DONT-003`, **MUST NOT**, `[checker:forbid_generated_subdir_queries]`)  `source:07_sql_and_query_generation.md:32`

<!-- rulecheck:generated-checklist:end -->
