# 05. `router.py` の sequence とログ

`router.py` は FastAPI endpoint、dependency injection、処理順、HTTP response 変換を持つ。DB query と provider client の実処理は持たない。

## このファイルに実装するもの

| 実装するもの | 内容 |
| :--- | :--- |
| FastAPI endpoint | HTTP method、path、request/response model、status code を定義する。 |
| 処理順 | `api_functions.*` の呼び出し順を上から順に書く。 |
| 認可分岐 | `has_*` / `is_*` の bool 関数だけを `if` 条件に使う。 |
| operational log | `ops_logger` wrapper 経由で WARNING / ERROR を記録する。 |
| response 変換 | `api_error_response` または `build_*` の戻り値を返す。 |

## このファイルに実装しないもの

| 実装しないもの | 理由 |
| :--- | :--- |
| SQL 実行 | DB access は `functions.py` と `queries.py` に閉じる。 |
| provider SDK 呼び出し | 外部 API は integration port 経由にする。 |
| 複雑な業務判断 | sequence 生成と静的解析を安定させるため。 |
| response dict の手組み | response model の組み立ては `build_*` 関数へ寄せる。 |

## 実装すべき内容

- `router.py` は同一 operation の `functions.py` を `api_functions` alias で import する。
- `functions.py` で戻り値 `bool` を宣言した public function は、`router.py` で `if` 条件に直接使うか、代入した変数を条件として使う。
- `router.py` の WARNING 以上のログは `get_operation_logger(__name__)` で得た wrapper から出す。
- `router.py` の `except` は `ROUTER_HANDLED_EXCEPTIONS`、`NonBlockingOperationalError`、`IntegrityError`、`SQLAlchemyError` だけを捕捉する。
- `router.py` の `if` 条件には inline 比較演算を入れない。
- `router.py` から `queries.*`、`fetch_all`、`fetch_one`、`execute_sql`、provider client を呼ばない。

## 実装してはいけない内容

- `router.py` で SQL 実行、query wrapper 呼び出し、provider client 呼び出しを実装しない。transaction の `session.commit()` と `session.rollback()` は許可する。
  - 理由: router は sequence 生成の入力であり、DB access や外部境界を混ぜると処理順の静的解析が不安定になる。
- `router.py` で `except Exception` または `except BaseException` を使わない。
  - 理由: error response と operational log の分類を固定するため。
- `router.py` で標準 `logging` を import しない。
  - 理由: 運用ログの catalog、context、runbook を wrapper で揃えるため。
- `router.py` の `if` 条件に `==`、`!=`、`<`、`>`、`in`、`is` の比較を直接書かない。
  - 理由: 業務判断を `functions.py` の named predicate に閉じ、sequence の条件文を安定させるため。

## OK例

```python
from app.apis.projects.create_project import functions as api_functions

has_permission = await api_functions.has_project_create_permission(caller, session)
if not has_permission:
    return api_error_response(status.HTTP_403_FORBIDDEN, "forbidden")

project = await api_functions.create_project(request, caller, session)
return await api_functions.build_create_project_response(project)
```

## NG例

```python
# NG: router.py で SQL を直接実行している
result = await session.execute(text("SELECT * FROM projects"))

# NG: router.py で provider client を直接呼んでいる
client = boto3.client("cognito-idp")

# NG: router.py で複雑な業務判断を展開している
if caller.role == "admin" or (
    caller.department == request.department_code
    and request.project_code.startswith("internal-")
):
    ...
```

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| ROUTER-DO-001 | MUST | `router_import_api_functions_alias` | - | `router.py` は同一 operation の `functions.py` を `api_functions` alias で import する。 |
| ROUTER-DO-002 | MUST | `router_bool_conditions` | - | `functions.py` で戻り値 `bool` を宣言した public function は、`router.py` で `if` 条件に直接使うか、代入した変数を条件として使う。 |
| ROUTER-DO-003 | MUST | `router_logging_wrapper` | - | `router.py` の WARNING 以上のログは `get_operation_logger(__name__)` で得た wrapper から出す。 |
| ROUTER-DO-004 | MUST | `router_error_handling` | - | `router.py` の `except` は `ROUTER_HANDLED_EXCEPTIONS`、`NonBlockingOperationalError`、`IntegrityError`、`SQLAlchemyError` だけを捕捉する。 |
| ROUTER-DO-005 | MUST | `router_no_inline_business_comparison` | - | `router.py` の `if` 条件には inline 比較演算を入れない。 |
| ROUTER-DO-006 | MUST | `router_no_direct_resource_calls` | - | `router.py` から `queries.*`、`fetch_all`、`fetch_one`、`execute_sql`、provider client を呼ばない。 |
| ROUTER-DONT-001 | MUST NOT | `router_no_direct_resource_calls` | - | `router.py` で SQL 実行、query wrapper 呼び出し、provider client 呼び出しを実装しない。transaction の `session.commit()` と `session.rollback()` は許可する。 |
| ROUTER-DONT-002 | MUST NOT | `router_error_handling` | - | `router.py` で `except Exception` または `except BaseException` を使わない。 |
| ROUTER-DONT-003 | MUST NOT | `router_logging_wrapper` | - | `router.py` で標準 `logging` を import しない。 |
| ROUTER-DONT-004 | MUST NOT | `router_no_inline_business_comparison` | - | `router.py` の `if` 条件に `==`、`!=`、`<`、`>`、`in`、`is` の比較を直接書かない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `router.py` は同一 operation の `functions.py` を `api_functions` alias で import する。 (`ROUTER-DO-001`, **MUST**, `[checker:router_import_api_functions_alias]`)  `source:05_router_sequence_and_logging.md:78`
- [ ] `functions.py` で戻り値 `bool` を宣言した public function は、`router.py` で `if` 条件に直接使うか、代入した変数を条件として使う。 (`ROUTER-DO-002`, **MUST**, `[checker:router_bool_conditions]`)  `source:05_router_sequence_and_logging.md:79`
- [ ] `router.py` の WARNING 以上のログは `get_operation_logger(__name__)` で得た wrapper から出す。 (`ROUTER-DO-003`, **MUST**, `[checker:router_logging_wrapper]`)  `source:05_router_sequence_and_logging.md:80`
- [ ] `router.py` の `except` は `ROUTER_HANDLED_EXCEPTIONS`、`NonBlockingOperationalError`、`IntegrityError`、`SQLAlchemyError` だけを捕捉する。 (`ROUTER-DO-004`, **MUST**, `[checker:router_error_handling]`)  `source:05_router_sequence_and_logging.md:81`
- [ ] `router.py` の `if` 条件には inline 比較演算を入れない。 (`ROUTER-DO-005`, **MUST**, `[checker:router_no_inline_business_comparison]`)  `source:05_router_sequence_and_logging.md:82`
- [ ] `router.py` から `queries.*`、`fetch_all`、`fetch_one`、`execute_sql`、provider client を呼ばない。 (`ROUTER-DO-006`, **MUST**, `[checker:router_no_direct_resource_calls]`)  `source:05_router_sequence_and_logging.md:83`
- [ ] `router.py` で SQL 実行、query wrapper 呼び出し、provider client 呼び出しを実装しない。transaction の `session.commit()` と `session.rollback()` は許可する。 (`ROUTER-DONT-001`, **MUST NOT**, `[checker:router_no_direct_resource_calls]`)  `source:05_router_sequence_and_logging.md:84`
- [ ] `router.py` で `except Exception` または `except BaseException` を使わない。 (`ROUTER-DONT-002`, **MUST NOT**, `[checker:router_error_handling]`)  `source:05_router_sequence_and_logging.md:85`
- [ ] `router.py` で標準 `logging` を import しない。 (`ROUTER-DONT-003`, **MUST NOT**, `[checker:router_logging_wrapper]`)  `source:05_router_sequence_and_logging.md:86`
- [ ] `router.py` の `if` 条件に `==`、`!=`、`<`、`>`、`in`、`is` の比較を直接書かない。 (`ROUTER-DONT-004`, **MUST NOT**, `[checker:router_no_inline_business_comparison]`)  `source:05_router_sequence_and_logging.md:87`

<!-- rulecheck:generated-checklist:end -->
