# 07. SQL と `queries.py` 生成

SQL は operation の `sql/` に置き、`src/tools/generate_queries.py` が operation 直下の `queries.py` を生成する。現行 SQL は MySQL 方言、`@name` placeholder、table alias を使う。

## 実装すべき内容

- **MUST** `[checker:operation_sql_dir_files]`: SQL ファイル名は `001_select_apis.sql` 形式の 3 桁番号 prefix を持つ。
- **MUST** `[checker:sql_first_comment_summary]`: SQL ファイルの最初の非空行は `-- ` で始まる処理要約にする。
- **MUST** `[checker:sql_placeholders_at_names]`: SQL bind placeholder は `@name` 形式にする。
- **MUST** `[checker:sql_no_select_star]`: SELECT 句は取得列名を列挙する。
- **MUST** `[checker:queries_generated_marker]`: 生成後の `queries.py` は Pydantic params/row model と query function を持つ。
- **MUST** `[checker:db_query_contract]`: `src/app/db/query.py` は `@name` placeholder を SQLAlchemy `:name` に変換する `load_sql` を持つ。

## 実装してはいけない内容

- **MUST NOT** `[checker:sql_no_select_star]`: SQL で `SELECT *` を使わない。
- **MUST NOT** `[checker:sql_placeholders_at_names]`: SQL ファイルへ `:name` placeholder を書かない。
- **MUST NOT** `[checker:forbid_generated_subdir_queries]`: SQL 生成物を operation の `generated/` 配下へ置かない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L007-01` **MUST** `[checker:operation_sql_dir_files]` SQL ファイル名は `001_select_apis.sql` 形式の 3 桁番号 prefix を持つ。  `source:07_sql_and_query_generation.md:7`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L008-02` **MUST** `[checker:sql_first_comment_summary]` SQL ファイルの最初の非空行は `-- ` で始まる処理要約にする。  `source:07_sql_and_query_generation.md:8`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L009-03` **MUST** `[checker:sql_placeholders_at_names]` SQL bind placeholder は `@name` 形式にする。  `source:07_sql_and_query_generation.md:9`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L010-04` **MUST** `[checker:sql_no_select_star]` SELECT 句は取得列名を列挙する。  `source:07_sql_and_query_generation.md:10`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L011-05` **MUST** `[checker:queries_generated_marker]` 生成後の `queries.py` は Pydantic params/row model と query function を持つ。  `source:07_sql_and_query_generation.md:11`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L012-06` **MUST** `[checker:db_query_contract]` `src/app/db/query.py` は `@name` placeholder を SQLAlchemy `:name` に変換する `load_sql` を持つ。  `source:07_sql_and_query_generation.md:12`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L016-07` **MUST NOT** `[checker:sql_no_select_star]` SQL で `SELECT *` を使わない。  `source:07_sql_and_query_generation.md:16`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L017-08` **MUST NOT** `[checker:sql_placeholders_at_names]` SQL ファイルへ `:name` placeholder を書かない。  `source:07_sql_and_query_generation.md:17`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L018-09` **MUST NOT** `[checker:forbid_generated_subdir_queries]` SQL 生成物を operation の `generated/` 配下へ置かない。  `source:07_sql_and_query_generation.md:18`

<!-- rulecheck:generated-checklist:end -->
