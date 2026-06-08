# 04. API operation ディレクトリ

各 operation は router、functions、schema、sample、SQL、生成 query wrapper を同じディレクトリ単位で管理する。

## 実装先の判断

| やりたいこと | 実装先 |
| :--- | :--- |
| HTTP path / method / response code を定義する | `router.py` |
| API の処理順を書く | `router.py` |
| 権限確認や状態判定を行う | `functions.py` |
| DB から取得・更新する | `sql/*.sql` + `generated/queries.py` + `functions.py` |
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
| `generated/queries.py` | SQL 由来の生成 wrapper | generator が出力した Pydantic model と query function |
| `queries.py` | 移行期間の互換 shim | `generated.queries` の re-export |

## 実装すべき内容

- `src/app/apis/{domain}/{operation}/` は `__init__.py`、`router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py`、`generated/`、`sql/` を持つ。
- `sql/` は 1 個以上の `000_name.sql` 形式 SQL ファイルを持つ。
- operation の `generated/queries.py` は sibling `sql/` 由来の生成物であることを示す marker と `SQL_DIR = Path(__file__).parents[1] / "sql"` を持つ。
- SQL 由来の query wrapper は `src/app/apis/{domain}/{operation}/generated/queries.py` に配置する。
- operation 直下の `queries.py` は移行期間の互換 shim として `generated.queries` を re-export する。
- `docs/spec/40.apis` を仕様生成物の出力先として配置する。

## 実装してはいけない内容

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
  generated/
    __init__.py
    queries.py
  sql/
    001_insert_project.sql
```

## NG例

```text
# NG: generated query wrapper を operation 直下だけに置いている
src/app/apis/projects/create_project/queries.py

# NG: operation の処理を service.py に分散している
src/app/apis/projects/create_project/service.py

# NG: operation 固有ファイル名を変えている
src/app/apis/projects/create_project/request_schema.py
```

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| OPERATION-DO-001 | MUST | `api_operation_required_files` | `src/app/apis/{domain}/{operation}/` | `__init__.py`、`router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py`、`generated/`、`sql/` を持つ。 |
| OPERATION-DO-002 | MUST | `operation_sql_dir_files` | `sql/` | 1 個以上の `000_name.sql` 形式 SQL ファイルを持つ。 |
| OPERATION-DO-003 | MUST | `queries_generated_marker` | - | operation の `generated/queries.py` は sibling `sql/` 由来の生成物であることを示す marker と `SQL_DIR = Path(__file__).parents[1] / "sql"` を持つ。 |
| OPERATION-DO-004 | MUST | `generated_queries_layout` | - | SQL 由来の query wrapper は `src/app/apis/{domain}/{operation}/generated/queries.py` に配置する。 |
| OPERATION-DO-005 | MUST | `required_paths` | - | `docs/spec/40.apis` を仕様生成物の出力先として配置する。 |
| OPERATION-DO-006 | MUST | `generated_queries_layout` | - | operation 直下の `queries.py` は移行期間の互換 shim として `generated.queries` を re-export する。 |
| OPERATION-DONT-002 | MUST NOT | `api_operation_required_files` | - | operation ごとに `router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py` の名前を変えない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `src/app/apis/{domain}/{operation}/`: `__init__.py`、`router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py`、`generated/`、`sql/` を持つ。 (`OPERATION-DO-001`, **MUST**, `[checker:api_operation_required_files]`)  `source:04_api_operation_directory.md:77`
- [ ] `sql/`: 1 個以上の `000_name.sql` 形式 SQL ファイルを持つ。 (`OPERATION-DO-002`, **MUST**, `[checker:operation_sql_dir_files]`)  `source:04_api_operation_directory.md:78`
- [ ] operation の `generated/queries.py` は sibling `sql/` 由来の生成物であることを示す marker と `SQL_DIR = Path(__file__).parents[1] / "sql"` を持つ。 (`OPERATION-DO-003`, **MUST**, `[checker:queries_generated_marker]`)  `source:04_api_operation_directory.md:79`
- [ ] SQL 由来の query wrapper は `src/app/apis/{domain}/{operation}/generated/queries.py` に配置する。 (`OPERATION-DO-004`, **MUST**, `[checker:generated_queries_layout]`)  `source:04_api_operation_directory.md:80`
- [ ] `docs/spec/40.apis` を仕様生成物の出力先として配置する。 (`OPERATION-DO-005`, **MUST**, `[checker:required_paths]`)  `source:04_api_operation_directory.md:81`
- [ ] operation 直下の `queries.py` は移行期間の互換 shim として `generated.queries` を re-export する。 (`OPERATION-DO-006`, **MUST**, `[checker:generated_queries_layout]`)  `source:04_api_operation_directory.md:82`
- [ ] operation ごとに `router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py` の名前を変えない。 (`OPERATION-DONT-002`, **MUST NOT**, `[checker:api_operation_required_files]`)  `source:04_api_operation_directory.md:83`

<!-- rulecheck:generated-checklist:end -->
