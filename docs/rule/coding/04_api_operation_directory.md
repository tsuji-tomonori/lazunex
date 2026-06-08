# 04. API operation ディレクトリ

各 operation は router、functions、schema、sample、SQL、生成 query wrapper を同じディレクトリに置く。

## 実装すべき内容

- **MUST** `[checker:api_operation_required_files]`: `src/app/apis/{domain}/{operation}/` は `__init__.py`、`router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py`、`sql/` を持つ。
- **MUST** `[checker:operation_sql_dir_files]`: `sql/` は 1 個以上の `000_name.sql` 形式 SQL ファイルを持つ。
- **MUST** `[checker:queries_generated_marker]`: operation 直下の `queries.py` は sibling `sql/` 由来の生成物であることを示す marker と `SQL_DIR = Path(__file__).with_name("sql")` を持つ。
- **MUST** `[checker:forbid_generated_subdir_queries]`: SQL 由来の query wrapper は `src/app/apis/{domain}/{operation}/queries.py` に配置する。
- **MUST** `[checker:required_paths]`: `docs/spec/40.apis` を仕様生成物の出力先として配置する。

## 実装してはいけない内容

- **MUST NOT** `[checker:forbid_generated_subdir_queries]`: `src/app/apis/{domain}/{operation}/generated/queries.py` を作らない。
- **MUST NOT** `[checker:api_operation_required_files]`: operation ごとに `router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py` の名前を変えない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-04_API_OPERATION_DIRECTORY-L007-01` **MUST** `[checker:api_operation_required_files]` `src/app/apis/{domain}/{operation}/` は `__init__.py`、`router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py`、`sql/` を持つ。  `source:04_api_operation_directory.md:7`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L008-02` **MUST** `[checker:operation_sql_dir_files]` `sql/` は 1 個以上の `000_name.sql` 形式 SQL ファイルを持つ。  `source:04_api_operation_directory.md:8`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L009-03` **MUST** `[checker:queries_generated_marker]` operation 直下の `queries.py` は sibling `sql/` 由来の生成物であることを示す marker と `SQL_DIR = Path(__file__).with_name("sql")` を持つ。  `source:04_api_operation_directory.md:9`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L010-04` **MUST** `[checker:forbid_generated_subdir_queries]` SQL 由来の query wrapper は `src/app/apis/{domain}/{operation}/queries.py` に配置する。  `source:04_api_operation_directory.md:10`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L011-05` **MUST** `[checker:required_paths]` `docs/spec/40.apis` を仕様生成物の出力先として配置する。  `source:04_api_operation_directory.md:11`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L015-06` **MUST NOT** `[checker:forbid_generated_subdir_queries]` `src/app/apis/{domain}/{operation}/generated/queries.py` を作らない。  `source:04_api_operation_directory.md:15`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L016-07` **MUST NOT** `[checker:api_operation_required_files]` operation ごとに `router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py` の名前を変えない。  `source:04_api_operation_directory.md:16`

<!-- rulecheck:generated-checklist:end -->
