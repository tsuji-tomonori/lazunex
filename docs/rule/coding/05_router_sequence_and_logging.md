# 05. `router.py` の sequence とログ

`router.py` は FastAPI endpoint、dependency injection、処理順、HTTP response 変換を持つ。DB query と provider client の実処理は持たない。

## 実装すべき内容

- **MUST** `[checker:router_import_api_functions_alias]`: `router.py` は同一 operation の `functions.py` を `api_functions` alias で import する。
- **MUST** `[checker:router_bool_conditions]`: `functions.py` で戻り値 `bool` を宣言した public function は、`router.py` で `if` 条件に直接使うか、代入した変数を条件として使う。
- **MUST** `[checker:router_logging_wrapper]`: `router.py` の WARNING 以上のログは `get_operation_logger(__name__)` で得た wrapper から出す。
- **MUST** `[checker:router_error_handling]`: `router.py` の `except` は `ROUTER_HANDLED_EXCEPTIONS`、`NonBlockingOperationalError`、`IntegrityError`、`SQLAlchemyError` だけを捕捉する。
- **MUST** `[checker:router_no_inline_business_comparison]`: `router.py` の `if` 条件には inline 比較演算を入れない。
- **MUST** `[checker:router_no_direct_resource_calls]`: `router.py` から `queries.*`、`fetch_all`、`fetch_one`、`execute_sql`、provider client を呼ばない。

## 実装してはいけない内容

- **MUST NOT** `[checker:router_no_direct_resource_calls]`: `router.py` で SQL 実行、query wrapper 呼び出し、provider client 呼び出しを実装しない。transaction の `session.commit()` と `session.rollback()` は許可する。
- **MUST NOT** `[checker:router_error_handling]`: `router.py` で `except Exception` または `except BaseException` を使わない。
- **MUST NOT** `[checker:router_logging_wrapper]`: `router.py` で標準 `logging` を import しない。
- **MUST NOT** `[checker:router_no_inline_business_comparison]`: `router.py` の `if` 条件に `==`、`!=`、`<`、`>`、`in`、`is` の比較を直接書かない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-05_ROUTER_SEQUENCE_AND_LOGGING-L007-01` **MUST** `[checker:router_import_api_functions_alias]` `router.py` は同一 operation の `functions.py` を `api_functions` alias で import する。  `source:05_router_sequence_and_logging.md:7`
- [ ] `RULE-05_ROUTER_SEQUENCE_AND_LOGGING-L008-02` **MUST** `[checker:router_bool_conditions]` `functions.py` で戻り値 `bool` を宣言した public function は、`router.py` で `if` 条件に直接使うか、代入した変数を条件として使う。  `source:05_router_sequence_and_logging.md:8`
- [ ] `RULE-05_ROUTER_SEQUENCE_AND_LOGGING-L009-03` **MUST** `[checker:router_logging_wrapper]` `router.py` の WARNING 以上のログは `get_operation_logger(__name__)` で得た wrapper から出す。  `source:05_router_sequence_and_logging.md:9`
- [ ] `RULE-05_ROUTER_SEQUENCE_AND_LOGGING-L010-04` **MUST** `[checker:router_error_handling]` `router.py` の `except` は `ROUTER_HANDLED_EXCEPTIONS`、`NonBlockingOperationalError`、`IntegrityError`、`SQLAlchemyError` だけを捕捉する。  `source:05_router_sequence_and_logging.md:10`
- [ ] `RULE-05_ROUTER_SEQUENCE_AND_LOGGING-L011-05` **MUST** `[checker:router_no_inline_business_comparison]` `router.py` の `if` 条件には inline 比較演算を入れない。  `source:05_router_sequence_and_logging.md:11`
- [ ] `RULE-05_ROUTER_SEQUENCE_AND_LOGGING-L012-06` **MUST** `[checker:router_no_direct_resource_calls]` `router.py` から `queries.*`、`fetch_all`、`fetch_one`、`execute_sql`、provider client を呼ばない。  `source:05_router_sequence_and_logging.md:12`
- [ ] `RULE-05_ROUTER_SEQUENCE_AND_LOGGING-L016-07` **MUST NOT** `[checker:router_no_direct_resource_calls]` `router.py` で SQL 実行、query wrapper 呼び出し、provider client 呼び出しを実装しない。transaction の `session.commit()` と `session.rollback()` は許可する。  `source:05_router_sequence_and_logging.md:16`
- [ ] `RULE-05_ROUTER_SEQUENCE_AND_LOGGING-L017-08` **MUST NOT** `[checker:router_error_handling]` `router.py` で `except Exception` または `except BaseException` を使わない。  `source:05_router_sequence_and_logging.md:17`
- [ ] `RULE-05_ROUTER_SEQUENCE_AND_LOGGING-L018-09` **MUST NOT** `[checker:router_logging_wrapper]` `router.py` で標準 `logging` を import しない。  `source:05_router_sequence_and_logging.md:18`
- [ ] `RULE-05_ROUTER_SEQUENCE_AND_LOGGING-L019-10` **MUST NOT** `[checker:router_no_inline_business_comparison]` `router.py` の `if` 条件に `==`、`!=`、`<`、`>`、`in`、`is` の比較を直接書かない。  `source:05_router_sequence_and_logging.md:19`

<!-- rulecheck:generated-checklist:end -->
