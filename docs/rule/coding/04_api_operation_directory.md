# 04. API operation ディレクトリ

各 operation は router、functions、schema、sample、SQL、生成 query wrapper を同じディレクトリに置く。

## 実装先の判断

| やりたいこと | 実装先 |
| :--- | :--- |
| HTTP path / method / response code を定義する | `router.py` |
| API の処理順を書く | `router.py` |
| 権限確認や状態判定を行う | `functions.py` |
| DB から取得・更新する | `sql/*.sql` + `queries.py` + `functions.py` |
| response model を組み立てる | `functions.py` の `build_*` |
| 外部 API を呼ぶ | `integrations/{resource}/port.py` 経由 |
| API request / response 型を定義する | `schemas.py` |
| sample response を定義する | `samples.py` |

## operation の責務

| ファイル | 役割 | 書いてよいもの |
| :--- | :--- | :--- |
| `router.py` | FastAPI endpoint と処理順 | decorator、dependency、`api_functions.*` 呼び出し |
| `functions.py` | 業務処理と境界呼び出し | 認可判定、query wrapper、integration port、response build |
| `schemas.py` | API 入出力型 | request / response model、field 制約、説明 |
| `samples.py` | 仕様生成用 sample | 正常系・異常系 response sample |
| `sql/*.sql` | DB access 定義 | `@name` placeholder 付き SQL |
| `queries.py` | SQL 由来の生成 wrapper | generator が出力した Pydantic model と query function |

## 実装すべき内容

- `src/app/apis/{domain}/{operation}/` は `__init__.py`、`router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py`、`sql/` を持つ。
- `sql/` は 1 個以上の `000_name.sql` 形式 SQL ファイルを持つ。
- operation 直下の `queries.py` は sibling `sql/` 由来の生成物であることを示す marker と `SQL_DIR = Path(__file__).with_name("sql")` を持つ。
- SQL 由来の query wrapper は `src/app/apis/{domain}/{operation}/queries.py` に配置する。
- `docs/spec/40.apis` を仕様生成物の出力先として配置する。

## 実装してはいけない内容

- `src/app/apis/{domain}/{operation}/generated/queries.py` を作らない。
- operation ごとに `router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py` の名前を変えない。

## OK例

```text
src/app/apis/projects/create_project/
  __init__.py
  router.py
  functions.py
  schemas.py
  samples.py
  queries.py
  sql/
    001_insert_project.sql
```

## NG例

```text
# NG: query wrapper を generated/ 配下へ戻している
src/app/apis/projects/create_project/generated/queries.py

# NG: operation の処理を service.py に分散している
src/app/apis/projects/create_project/service.py

# NG: operation 固有ファイル名を変えている
src/app/apis/projects/create_project/request_schema.py
```

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| OPERATION-DO-001 | MUST | `api_operation_required_files` | `src/app/apis/{domain}/{operation}/` | `__init__.py`、`router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py`、`sql/` を持つ。 |
| OPERATION-DO-002 | MUST | `operation_sql_dir_files` | `sql/` | 1 個以上の `000_name.sql` 形式 SQL ファイルを持つ。 |
| OPERATION-DO-003 | MUST | `queries_generated_marker` | - | operation 直下の `queries.py` は sibling `sql/` 由来の生成物であることを示す marker と `SQL_DIR = Path(__file__).with_name("sql")` を持つ。 |
| OPERATION-DO-004 | MUST | `forbid_generated_subdir_queries` | - | SQL 由来の query wrapper は `src/app/apis/{domain}/{operation}/queries.py` に配置する。 |
| OPERATION-DO-005 | MUST | `required_paths` | - | `docs/spec/40.apis` を仕様生成物の出力先として配置する。 |
| OPERATION-DONT-001 | MUST NOT | `forbid_generated_subdir_queries` | - | `src/app/apis/{domain}/{operation}/generated/queries.py` を作らない。 |
| OPERATION-DONT-002 | MUST NOT | `api_operation_required_files` | - | operation ごとに `router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py` の名前を変えない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `src/app/apis/{domain}/{operation}/`: `__init__.py`、`router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py`、`sql/` を持つ。 (`OPERATION-DO-001`, **MUST**, `[checker:api_operation_required_files]`)  `source:04_api_operation_directory.md:73`
- [ ] `sql/`: 1 個以上の `000_name.sql` 形式 SQL ファイルを持つ。 (`OPERATION-DO-002`, **MUST**, `[checker:operation_sql_dir_files]`)  `source:04_api_operation_directory.md:74`
- [ ] operation 直下の `queries.py` は sibling `sql/` 由来の生成物であることを示す marker と `SQL_DIR = Path(__file__).with_name("sql")` を持つ。 (`OPERATION-DO-003`, **MUST**, `[checker:queries_generated_marker]`)  `source:04_api_operation_directory.md:75`
- [ ] SQL 由来の query wrapper は `src/app/apis/{domain}/{operation}/queries.py` に配置する。 (`OPERATION-DO-004`, **MUST**, `[checker:forbid_generated_subdir_queries]`)  `source:04_api_operation_directory.md:76`
- [ ] `docs/spec/40.apis` を仕様生成物の出力先として配置する。 (`OPERATION-DO-005`, **MUST**, `[checker:required_paths]`)  `source:04_api_operation_directory.md:77`
- [ ] `src/app/apis/{domain}/{operation}/generated/queries.py` を作らない。 (`OPERATION-DONT-001`, **MUST NOT**, `[checker:forbid_generated_subdir_queries]`)  `source:04_api_operation_directory.md:78`
- [ ] operation ごとに `router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py` の名前を変えない。 (`OPERATION-DONT-002`, **MUST NOT**, `[checker:api_operation_required_files]`)  `source:04_api_operation_directory.md:79`

<!-- rulecheck:generated-checklist:end -->
