# 自動生成レビュー・チェックリスト

このファイルは `rulecheck generate` で生成する。手動編集しない。

<!-- rulecheck:generated-checklist:start -->

## 00_terms_and_scope.md

### 実装修正項目

- [ ] `MUST`、`MUST NOT`、`SHOULD`、`SHOULD NOT`、`MAY` の規約行は checker tag を 1 個以上持つ。 (`SCOPE-DO-001`, **MUST**, `[checker:rule_has_checker_tag]`)  `source:00_terms_and_scope.md:32`
- [ ] 規約行は設定ファイルの `ambiguous_words` に含まれる語を含めない。 (`SCOPE-DO-002`, **MUST**, `[checker:normative_no_ambiguous_words]`)  `source:00_terms_and_scope.md:33`
- [ ] `src/app`、`src/db`、`src/tools` を配置する。 (`SCOPE-DO-003`, **MUST**, `[checker:required_paths]`)  `source:00_terms_and_scope.md:34`
- [ ] `pyproject.toml`: Python `>=3.14,<3.15`、Ruff `py314`、Pyright `3.14`、mypy `3.14` を宣言する。 (`SCOPE-DO-004`, **MUST**, `[checker:repo_python_policy]`)  `source:00_terms_and_scope.md:35`
- [ ] `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` の実行コマンドをリポジトリ内に記載する。 (`SCOPE-DO-005`, **MUST**, `[checker:quality_commands_declared]`)  `source:00_terms_and_scope.md:36`
- [ ] checker を持たない規約行を追加しない。 (`SCOPE-DONT-001`, **MUST NOT**, `[checker:rule_has_checker_tag]`)  `source:00_terms_and_scope.md:37`
- [ ] 規約行へ判定条件を数値化できない語を入れない。 (`SCOPE-DONT-002`, **MUST NOT**, `[checker:normative_no_ambiguous_words]`)  `source:00_terms_and_scope.md:38`

## 01_src_layout.md

### 実装修正項目

- [ ] `src/app`、`src/db`、`src/tools` を配置する。 (`LAYOUT-DO-001`, **MUST**, `[checker:required_paths]`)  `source:01_src_layout.md:22`
- [ ] `src/app/main.py`、`src/app/local.py`、`src/app/core`、`src/app/db`、`src/app/apis`、`src/app/integrations` を配置する。 (`LAYOUT-DO-002`, **MUST**, `[checker:required_paths]`)  `source:01_src_layout.md:23`
- [ ] `src/db/ddl.sql` を配置し、空ファイルにしない。 (`LAYOUT-DO-003`, **MUST**, `[checker:ddl_exists]`)  `source:01_src_layout.md:24`
- [ ] `src/tools` に現行の checker/generator スクリプトを配置する。 (`LAYOUT-DO-004`, **MUST**, `[checker:tools_existing_checks]`)  `source:01_src_layout.md:25`
- [ ] Python ファイルの論理行数は `config/rulecheck_config.example.json` の `file_logical_lines` 以下にする。 (`LAYOUT-DO-005`, **MUST**, `[checker:file_logical_lines]`)  `source:01_src_layout.md:26`
- [ ] `src/app/integrations/_aws_boto3.py` と `src/app/integrations/**/boto3_provider/*.py` 以外の `src/app/**/*.py` から provider import を行わない。 (`LAYOUT-DONT-001`, **MUST NOT**, `[checker:integration_provider_boundary]`)  `source:01_src_layout.md:27`
- [ ] DDL を `src/app` 配下に配置しない。 (`LAYOUT-DONT-002`, **MUST NOT**, `[checker:required_paths]`)  `source:01_src_layout.md:28`

## 02_app_entrypoints.md

### 実装修正項目

- [ ] `src/app/main.py`: `create_app()` を定義し、モジュール変数 `app` に `create_app()` の戻り値を代入する。 (`ENTRYPOINT-DO-001`, **MUST**, `[checker:entrypoint_fastapi]`)  `source:02_app_entrypoints.md:22`
- [ ] `src/app/main.py`: `/health` の GET route を登録する。 (`ENTRYPOINT-DO-002`, **MUST**, `[checker:health_route]`)  `source:02_app_entrypoints.md:23`
- [ ] `src/app/apis/{domain}/{operation}/router.py` を持つ operation は `src/app/main.py` で import し、`include_router(...)` で登録する。 (`ENTRYPOINT-DO-003`, **MUST**, `[checker:main_router_includes]`)  `source:02_app_entrypoints.md:24`
- [ ] `src/app/main.py` と `src/app/local.py` は `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。 (`ENTRYPOINT-DO-004`, **MUST**, `[checker:entrypoint_no_provider_imports]`)  `source:02_app_entrypoints.md:25`
- [ ] entrypoint 内の関数は `config/rulecheck_config.example.json` の `function_logical_lines` 以下にする。 (`ENTRYPOINT-DO-005`, **MUST**, `[checker:function_logical_lines]`)  `source:02_app_entrypoints.md:26`
- [ ] entrypoint で AWS SDK client、HTTP client、provider client を生成しない。 (`ENTRYPOINT-DONT-001`, **MUST NOT**, `[checker:entrypoint_no_provider_imports]`)  `source:02_app_entrypoints.md:27`
- [ ] operation router の登録を `src/app/main.py` 以外へ分散しない。 (`ENTRYPOINT-DONT-002`, **MUST NOT**, `[checker:main_router_includes]`)  `source:02_app_entrypoints.md:28`

## 03_api_common_modules.md

### 実装修正項目

- [ ] `src/app/apis` 直下に `__init__.py`、`base.py`、`common.py`、`deps.py`、`responses.py`、`router_errors.py`、`sequence_types.py`、`types.py` を配置する。 (`API-COMMON-DO-001`, **MUST**, `[checker:api_common_files]`)  `source:03_api_common_modules.md:21`
- [ ] API operation は `src/app/apis/{domain}/{operation}/` の 2 階層で配置する。 (`API-COMMON-DO-002`, **MUST**, `[checker:api_domain_layout]`)  `source:03_api_common_modules.md:22`
- [ ] 認証方式、URL 種別、ドキュメント種別、公開状態の文字列リテラルは domain common module の定数または Enum から参照する。 (`API-COMMON-DO-003`, **MUST**, `[checker:managed_literals]`)  `source:03_api_common_modules.md:23`
- [ ] 共通モジュールの Python 関数引数数は設定ファイルの `function_argument_count` 以下にする。 (`API-COMMON-DO-004`, **MUST**, `[checker:function_argument_count]`)  `source:03_api_common_modules.md:24`
- [ ] `PUBLIC_PKCE`、`CONFIDENTIAL_CLIENT_CREDENTIALS`、`CALLBACK`、`LOGOUT`、`OPENAPI`、`published` を operation 個別実装へ直書きしない。 (`API-COMMON-DONT-001`, **MUST NOT**, `[checker:managed_literals]`)  `source:03_api_common_modules.md:25`
- [ ] `src/app/apis/{domain}/{operation}/{sub_operation}/` の 3 階層 operation を作らない。 (`API-COMMON-DONT-002`, **MUST NOT**, `[checker:api_domain_layout]`)  `source:03_api_common_modules.md:26`

## 04_api_operation_directory.md

### 実装修正項目

- [ ] `src/app/apis/{domain}/{operation}/`: `__init__.py`、`router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py`、`generated/`、`sql/` を持つ。 (`OPERATION-DO-001`, **MUST**, `[checker:api_operation_required_files]`)  `source:04_api_operation_directory.md:77`
- [ ] `sql/`: 1 個以上の `000_name.sql` 形式 SQL ファイルを持つ。 (`OPERATION-DO-002`, **MUST**, `[checker:operation_sql_dir_files]`)  `source:04_api_operation_directory.md:78`
- [ ] operation の `generated/queries.py` は sibling `sql/` 由来の生成物であることを示す marker と `SQL_DIR = Path(__file__).parents[1] / "sql"` を持つ。 (`OPERATION-DO-003`, **MUST**, `[checker:queries_generated_marker]`)  `source:04_api_operation_directory.md:79`
- [ ] SQL 由来の query wrapper は `src/app/apis/{domain}/{operation}/generated/queries.py` に配置する。 (`OPERATION-DO-004`, **MUST**, `[checker:generated_queries_layout]`)  `source:04_api_operation_directory.md:80`
- [ ] `docs/spec/40.apis` を仕様生成物の出力先として配置する。 (`OPERATION-DO-005`, **MUST**, `[checker:required_paths]`)  `source:04_api_operation_directory.md:81`
- [ ] operation 直下の `queries.py` は移行期間の互換 shim として `generated.queries` を re-export する。 (`OPERATION-DO-006`, **MUST**, `[checker:generated_queries_layout]`)  `source:04_api_operation_directory.md:82`
- [ ] operation ごとに `router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py` の名前を変えない。 (`OPERATION-DONT-002`, **MUST NOT**, `[checker:api_operation_required_files]`)  `source:04_api_operation_directory.md:83`

## 05_router_sequence_and_logging.md

### 実装修正項目

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

## 06_functions_queries_and_resources.md

### 実装修正項目

- [ ] `functions.py` の public function は docstring、全引数型注釈、戻り値型注釈を持つ。 (`FUNCTIONS-DO-001`, **MUST**, `[checker:functions_public_contract]`)  `source:06_functions_queries_and_resources.md:24`
- [ ] sequence vocabulary JSON が存在する場合、public function 名は `{action}_{target}` または `{is|has}_{condition}` の語彙に一致させる。 (`FUNCTIONS-DO-002`, **MUST**, `[checker:functions_vocab_names]`)  `source:06_functions_queries_and_resources.md:25`
- [ ] validation、predicate、response build、merge、pagination 以外の public function は `queries.*` または integration port を呼ぶか、`@resource-free` marker を持つ。 (`FUNCTIONS-DO-003`, **MUST**, `[checker:functions_resource_usage]`)  `source:06_functions_queries_and_resources.md:26`
- [ ] runtime dependency を既定値 `None` で受ける関数は、依存が無い経路で `return raise_missing_runtime_dependency("<function_name>")` を実行する。 (`FUNCTIONS-DO-004`, **MUST**, `[checker:functions_exception_policy]`)  `source:06_functions_queries_and_resources.md:27`
- [ ] `functions.py`: integration port と schemas へ依存し、provider client へ依存しない。 (`FUNCTIONS-DO-005`, **MUST**, `[checker:functions_no_provider_imports]`)  `source:06_functions_queries_and_resources.md:28`
- [ ] public function の `return` 文数は設定ファイルの `return_count` 以下にする。 (`FUNCTIONS-DO-006`, **MUST**, `[checker:return_count]`)  `source:06_functions_queries_and_resources.md:29`
- [ ] `functions.py` で `HTTPException` を直接 raise しない。 (`FUNCTIONS-DONT-001`, **MUST NOT**, `[checker:functions_exception_policy]`)  `source:06_functions_queries_and_resources.md:30`
- [ ] `functions.py` で `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。 (`FUNCTIONS-DONT-002`, **MUST NOT**, `[checker:functions_no_provider_imports]`)  `source:06_functions_queries_and_resources.md:31`
- [ ] resource を使わない非 validation 関数を `@resource-free` marker なしで追加しない。 (`FUNCTIONS-DONT-003`, **MUST NOT**, `[checker:functions_resource_usage]`)  `source:06_functions_queries_and_resources.md:32`

## 07_sql_and_query_generation.md

### 実装修正項目

- [ ] SQL ファイル名は `001_select_apis.sql` 形式の 3 桁番号 prefix を持つ。 (`SQL-DO-001`, **MUST**, `[checker:operation_sql_dir_files]`)  `source:07_sql_and_query_generation.md:24`
- [ ] SQL ファイルの最初の非空行は `-- ` で始まる処理要約にする。 (`SQL-DO-002`, **MUST**, `[checker:sql_first_comment_summary]`)  `source:07_sql_and_query_generation.md:25`
- [ ] SQL bind placeholder は `@name` 形式にする。 (`SQL-DO-003`, **MUST**, `[checker:sql_placeholders_at_names]`)  `source:07_sql_and_query_generation.md:26`
- [ ] SELECT 句は取得列名を列挙する。 (`SQL-DO-004`, **MUST**, `[checker:sql_no_select_star]`)  `source:07_sql_and_query_generation.md:27`
- [ ] 生成後の `generated/queries.py` は Pydantic params/row model と query function を持つ。 (`SQL-DO-005`, **MUST**, `[checker:queries_generated_marker]`)  `source:07_sql_and_query_generation.md:28`
- [ ] `src/app/db/query.py`: `@name` placeholder を SQLAlchemy `:name` に変換する `load_sql` を持つ。 (`SQL-DO-006`, **MUST**, `[checker:db_query_contract]`)  `source:07_sql_and_query_generation.md:29`
- [ ] SQL で `SELECT *` を使わない。 (`SQL-DONT-001`, **MUST NOT**, `[checker:sql_no_select_star]`)  `source:07_sql_and_query_generation.md:30`
- [ ] SQL ファイルへ `:name` placeholder を書かない。 (`SQL-DONT-002`, **MUST NOT**, `[checker:sql_placeholders_at_names]`)  `source:07_sql_and_query_generation.md:31`
- [ ] SQL 生成物を operation 直下の `queries.py` 本体へ戻さない。 (`SQL-DONT-003`, **MUST NOT**, `[checker:generated_queries_layout]`)  `source:07_sql_and_query_generation.md:32`

## 08_integrations.md

### 実装修正項目

- [ ] `src/app/integrations/{resource}/port.py` を持つ resource は `schemas.py`、`deps.py`、provider `client.py` を持つ。 (`INTEGRATION-DO-001`, **MUST**, `[checker:integration_port_provider_layout]`)  `source:08_integrations.md:22`
- [ ] provider SDK と HTTP client の import は provider boundary、`deps.py`、`common_errors.py` に閉じる。 (`INTEGRATION-DO-002`, **MUST**, `[checker:integration_provider_boundary]`)  `source:08_integrations.md:23`
- [ ] API operation の `functions.py` は `src/app/integrations/{resource}/port.py` の Protocol 型へ依存する。 (`INTEGRATION-DO-003`, **MUST**, `[checker:functions_no_provider_imports]`)  `source:08_integrations.md:24`
- [ ] `src/app/main.py`: integration provider 実装を import しない。 (`INTEGRATION-DO-004`, **MUST**, `[checker:entrypoint_no_provider_imports]`)  `source:08_integrations.md:25`
- [ ] integration public function と provider method の引数数は設定ファイルの `function_argument_count` 以下にする。 (`INTEGRATION-DO-005`, **MUST**, `[checker:function_argument_count]`)  `source:08_integrations.md:26`
- [ ] provider SDK の例外型、payload 型、retry 設定を API operation へ露出しない。 (`INTEGRATION-DONT-001`, **MUST NOT**, `[checker:integration_provider_boundary]`)  `source:08_integrations.md:27`
- [ ] API operation から `src/app/integrations/{resource}/boto3_provider/client.py` を import しない。 (`INTEGRATION-DONT-002`, **MUST NOT**, `[checker:functions_no_provider_imports]`)  `source:08_integrations.md:28`

## 09_core_db_and_settings.md

### 実装修正項目

- [ ] `src/app/core/config.py`、`src/app/core/exceptions.py`、`src/app/core/logging.py` を配置する。 (`CORE-DO-001`, **MUST**, `[checker:required_paths]`)  `source:09_core_db_and_settings.md:22`
- [ ] `src/app/db/query.py`: `load_sql`、`model_parameters`、`fetch_all`、`fetch_one`、`execute_sql` を提供する。 (`CORE-DO-002`, **MUST**, `[checker:db_query_contract]`)  `source:09_core_db_and_settings.md:23`
- [ ] `src/app/db/session.py` を配置する。 (`CORE-DO-003`, **MUST**, `[checker:required_paths]`)  `source:09_core_db_and_settings.md:24`
- [ ] 型検査は Pyright strict と mypy strict を使う。 (`CORE-DO-004`, **MUST**, `[checker:repo_python_policy]`)  `source:09_core_db_and_settings.md:25`
- [ ] formatter、linter、型検査、pytest のコマンドを README または設定に記録する。 (`CORE-DO-005`, **MUST**, `[checker:quality_commands_declared]`)  `source:09_core_db_and_settings.md:26`
- [ ] `src/app/core` と `src/app/db` から provider client を import しない。 (`CORE-DONT-001`, **MUST NOT**, `[checker:integration_provider_boundary]`)  `source:09_core_db_and_settings.md:27`
- [ ] SQL 実行 helper を迂回するために SQL ファイルへ SQLAlchemy `:name` placeholder を書かない。 (`CORE-DONT-002`, **MUST NOT**, `[checker:sql_placeholders_at_names]`)  `source:09_core_db_and_settings.md:28`

## 10_tools_docs_and_generated_outputs.md

### 実装修正項目

- [ ] `src/tools/check_api_function_names.py`、`generate_api_sequences.py`、`check_api_mermaid_sequences.py`、`generate_queries.py`、`generate_db_crud.py`、`check_operational_logging.py` を配置する。 (`TOOLS-DO-001`, **MUST**, `[checker:tools_existing_checks]`)  `source:10_tools_docs_and_generated_outputs.md:22`
- [ ] `generate_queries.py` の出力は operation の `generated/queries.py` にする。 (`TOOLS-DO-002`, **MUST**, `[checker:generated_queries_layout]`)  `source:10_tools_docs_and_generated_outputs.md:23`
- [ ] CI 用コマンドに `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` を含める。 (`TOOLS-DO-003`, **MUST**, `[checker:quality_commands_declared]`)  `source:10_tools_docs_and_generated_outputs.md:24`
- [ ] `src/tools/**/*.py` のファイル論理行数は設定ファイルの `file_logical_lines` 以下にする。 (`TOOLS-DO-004`, **MUST**, `[checker:file_logical_lines]`)  `source:10_tools_docs_and_generated_outputs.md:25`
- [ ] `src/tools/**/*.py` の関数論理行数は設定ファイルの `function_logical_lines` 以下にする。 (`TOOLS-DO-005`, **MUST**, `[checker:function_logical_lines]`)  `source:10_tools_docs_and_generated_outputs.md:26`
- [ ] `src/tools/generate_queries.py` の出力先を operation 直下の `queries.py` 本体へ戻さない。 (`TOOLS-DONT-001`, **MUST NOT**, `[checker:generated_queries_layout]`)  `source:10_tools_docs_and_generated_outputs.md:27`
- [ ] 現行 checker/generator のファイル名を変更しない。 (`TOOLS-DONT-002`, **MUST NOT**, `[checker:tools_existing_checks]`)  `source:10_tools_docs_and_generated_outputs.md:28`

## 11_quantitative_thresholds.md

### 実装修正項目

- [ ] `src/app/apis/**/router.py` の endpoint 関数は循環的複雑度を `10` 以下にする。 (`METRICS-DO-001`, **MUST**, `[checker:python_complexity]`)  `source:11_quantitative_thresholds.md:92`
- [ ] `src/app/**/*.py` の関数は循環的複雑度を `10` 以下にする。 (`METRICS-DO-002`, **MUST**, `[checker:python_complexity]`)  `source:11_quantitative_thresholds.md:93`
- [ ] `src/tools/**/*.py` の関数は循環的複雑度を `12` 以下にする。 (`METRICS-DO-003`, **MUST**, `[checker:python_complexity]`)  `source:11_quantitative_thresholds.md:94`
- [ ] `src/app/apis/**/router.py` の endpoint 関数は制御構造ネスト深度を `3` 以下にする。 (`METRICS-DO-004`, **MUST**, `[checker:control_nesting_depth]`)  `source:11_quantitative_thresholds.md:95`
- [ ] `src/app/**/*.py` の関数は制御構造ネスト深度を `3` 以下にする。 (`METRICS-DO-005`, **MUST**, `[checker:control_nesting_depth]`)  `source:11_quantitative_thresholds.md:96`
- [ ] `src/tools/**/*.py` の関数は制御構造ネスト深度を `4` 以下にする。 (`METRICS-DO-006`, **MUST**, `[checker:control_nesting_depth]`)  `source:11_quantitative_thresholds.md:97`
- [ ] `src/app/apis/**/router.py` の endpoint 関数は論理行数を `120` 以下にする。 (`METRICS-DO-007`, **MUST**, `[checker:function_logical_lines]`)  `source:11_quantitative_thresholds.md:98`
- [ ] `src/app/**/*.py` の関数は論理行数を `100` 以下にする。 (`METRICS-DO-008`, **MUST**, `[checker:function_logical_lines]`)  `source:11_quantitative_thresholds.md:99`
- [ ] `src/tools/**/*.py` の関数は論理行数を `120` 以下にする。 (`METRICS-DO-009`, **MUST**, `[checker:function_logical_lines]`)  `source:11_quantitative_thresholds.md:100`
- [ ] `src/app/apis/**/router.py` のファイルは論理行数を `260` 以下にする。 (`METRICS-DO-010`, **MUST**, `[checker:file_logical_lines]`)  `source:11_quantitative_thresholds.md:101`
- [ ] `src/app/**/*.py` の manual ファイルは論理行数を `600` 以下にする。 (`METRICS-DO-011`, **MUST**, `[checker:file_logical_lines]`)  `source:11_quantitative_thresholds.md:102`
- [ ] `src/tools/**/*.py` のファイルは論理行数を `1000` 以下にする。 (`METRICS-DO-012`, **MUST**, `[checker:file_logical_lines]`)  `source:11_quantitative_thresholds.md:103`
- [ ] `src/app/apis/**/router.py` の endpoint 関数は総引数数を `8` 以下にする。 (`METRICS-DO-013`, **MUST**, `[checker:function_argument_count]`)  `source:11_quantitative_thresholds.md:104`
- [ ] `src/app/apis/**/router.py` の endpoint 関数は業務引数数を `3` 以下にする。 (`METRICS-DO-014`, **MUST**, `[checker:endpoint_business_argument_count]`)  `source:11_quantitative_thresholds.md:105`
- [ ] `src/app/**/*.py` の public 関数は引数数を `5` 以下にする。 (`METRICS-DO-015`, **MUST**, `[checker:function_argument_count]`)  `source:11_quantitative_thresholds.md:106`
- [ ] `src/app/**/*.py` の private helper 関数は引数数を `5` 以下にする。 (`METRICS-DO-016`, **MUST**, `[checker:function_argument_count]`)  `source:11_quantitative_thresholds.md:107`
- [ ] `src/tools/**/*.py` の通常関数は引数数を `6` 以下にする。 (`METRICS-DO-017`, **MUST**, `[checker:function_argument_count]`)  `source:11_quantitative_thresholds.md:108`
- [ ] `src/tools/**/*.py` の CLI adapter 関数は引数数を `8` 以下にする。 (`METRICS-DO-018`, **MUST**, `[checker:function_argument_count]`)  `source:11_quantitative_thresholds.md:109`
- [ ] `src/app/apis/**/router.py` の endpoint 関数内 `return` 文数は `6` 以下にする。 (`METRICS-DO-019`, **MUST**, `[checker:return_count]`)  `source:11_quantitative_thresholds.md:110`
- [ ] `src/app/**/*.py` の関数内 `return` 文数は `6` 以下にする。 (`METRICS-DO-020`, **MUST**, `[checker:return_count]`)  `source:11_quantitative_thresholds.md:111`
- [ ] `src/tools/**/*.py` の関数内 `return` 文数は `8` 以下にする。 (`METRICS-DO-021`, **MUST**, `[checker:return_count]`)  `source:11_quantitative_thresholds.md:112`
- [ ] `src/app/apis/**/router.py` の `try` body statement 数は `5` 以下にする。 (`METRICS-DO-022`, **MUST**, `[checker:try_body_statement_count]`)  `source:11_quantitative_thresholds.md:113`
- [ ] `src/app/**/*.py` の local variable 数は `10` 以下にする。 (`METRICS-DO-023`, **MUST**, `[checker:local_variable_count]`)  `source:11_quantitative_thresholds.md:114`
- [ ] `src/tools/**/*.py` の local variable 数は `15` 以下にする。 (`METRICS-DO-024`, **MUST**, `[checker:local_variable_count]`)  `source:11_quantitative_thresholds.md:115`
- [ ] `src/app/apis/**/router.py` の branch 数は `4` 以下にする。 (`METRICS-DO-025`, **MUST**, `[checker:branch_count]`)  `source:11_quantitative_thresholds.md:116`
- [ ] `src/app/**/*.py` の branch 数は `8` 以下にする。 (`METRICS-DO-026`, **MUST**, `[checker:branch_count]`)  `source:11_quantitative_thresholds.md:117`
- [ ] `src/tools/**/*.py` の branch 数は `10` 以下にする。 (`METRICS-DO-027`, **MUST**, `[checker:branch_count]`)  `source:11_quantitative_thresholds.md:118`
- [ ] `src/app/apis/**/router.py` の条件式に含める `and` と `or` の演算子数は合計 `1` 以下にする。 (`METRICS-DO-028`, **MUST**, `[checker:condition_complexity]`)  `source:11_quantitative_thresholds.md:119`
- [ ] `src/app/**/*.py` と `src/tools/**/*.py` の条件式に含める `and` と `or` の演算子数は合計 `3` 以下にする。 (`METRICS-DO-029`, **MUST**, `[checker:condition_complexity]`)  `source:11_quantitative_thresholds.md:120`
- [ ] 条件式に含める比較演算子数は `3` 以下にする。 (`METRICS-DO-030`, **MUST**, `[checker:condition_complexity]`)  `source:11_quantitative_thresholds.md:121`
- [ ] 条件式 AST 深度は `7` 以下にする。 (`METRICS-DO-031`, **MUST**, `[checker:condition_complexity]`)  `source:11_quantitative_thresholds.md:122`
- [ ] 三項式の中に三項式を入れる。 (`METRICS-DONT-001`, **MUST NOT**, `[checker:condition_complexity]`)  `source:11_quantitative_thresholds.md:123`
- [ ] `src/app/**/*.py` で制御構造を `4` 層以上にする。 (`METRICS-DONT-002`, **MUST NOT**, `[checker:control_nesting_depth]`)  `source:11_quantitative_thresholds.md:124`
- [ ] `src/tools/**/*.py` で制御構造を `5` 層以上にする。 (`METRICS-DONT-003`, **MUST NOT**, `[checker:control_nesting_depth]`)  `source:11_quantitative_thresholds.md:125`

<!-- rulecheck:generated-checklist:end -->
