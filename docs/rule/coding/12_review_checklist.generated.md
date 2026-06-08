# 自動生成レビュー・チェックリスト

このファイルは `rulecheck generate` で生成する。手動編集しない。

<!-- rulecheck:generated-checklist:start -->

## 00_terms_and_scope.md

- [ ] `RULE-00_TERMS_AND_SCOPE-L017-01` **MUST** `[checker:rule_has_checker_tag]` `MUST`、`MUST NOT`、`SHOULD`、`SHOULD NOT`、`MAY` の規約行は checker tag を 1 個以上持つ。  `source:00_terms_and_scope.md:17`
- [ ] `RULE-00_TERMS_AND_SCOPE-L018-02` **MUST** `[checker:normative_no_ambiguous_words]` 規約行は設定ファイルの `ambiguous_words` に含まれる語を含めない。  `source:00_terms_and_scope.md:18`
- [ ] `RULE-00_TERMS_AND_SCOPE-L019-03` **MUST** `[checker:required_paths]` `src/app`、`src/db`、`src/tools` を配置する。  `source:00_terms_and_scope.md:19`
- [ ] `RULE-00_TERMS_AND_SCOPE-L020-04` **MUST** `[checker:repo_python_policy]` `pyproject.toml` は Python `>=3.14,<3.15`、Ruff `py314`、Pyright `3.14`、mypy `3.14` を宣言する。  `source:00_terms_and_scope.md:20`
- [ ] `RULE-00_TERMS_AND_SCOPE-L021-05` **MUST** `[checker:quality_commands_declared]` `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` の実行コマンドをリポジトリ内に記載する。  `source:00_terms_and_scope.md:21`
- [ ] `RULE-00_TERMS_AND_SCOPE-L025-06` **MUST NOT** `[checker:rule_has_checker_tag]` checker を持たない規約行を追加しない。  `source:00_terms_and_scope.md:25`
- [ ] `RULE-00_TERMS_AND_SCOPE-L026-07` **MUST NOT** `[checker:normative_no_ambiguous_words]` 規約行へ判定条件を数値化できない語を入れない。  `source:00_terms_and_scope.md:26`

## 01_src_layout.md

- [ ] `RULE-01_SRC_LAYOUT-L007-01` **MUST** `[checker:required_paths]` `src/app`、`src/db`、`src/tools` を配置する。  `source:01_src_layout.md:7`
- [ ] `RULE-01_SRC_LAYOUT-L008-02` **MUST** `[checker:required_paths]` `src/app/main.py`、`src/app/local.py`、`src/app/core`、`src/app/db`、`src/app/apis`、`src/app/integrations` を配置する。  `source:01_src_layout.md:8`
- [ ] `RULE-01_SRC_LAYOUT-L009-03` **MUST** `[checker:ddl_exists]` `src/db/ddl.sql` を配置し、空ファイルにしない。  `source:01_src_layout.md:9`
- [ ] `RULE-01_SRC_LAYOUT-L010-04` **MUST** `[checker:tools_existing_checks]` `src/tools` に現行の checker/generator スクリプトを配置する。  `source:01_src_layout.md:10`
- [ ] `RULE-01_SRC_LAYOUT-L011-05` **MUST** `[checker:file_logical_lines]` Python ファイルの論理行数は `config/rulecheck_config.example.json` の `file_logical_lines` 以下にする。  `source:01_src_layout.md:11`
- [ ] `RULE-01_SRC_LAYOUT-L015-06` **MUST NOT** `[checker:integration_provider_boundary]` `src/app/integrations/_aws_boto3.py` と `src/app/integrations/**/boto3_provider/*.py` 以外の `src/app/**/*.py` から provider import を行わない。  `source:01_src_layout.md:15`
- [ ] `RULE-01_SRC_LAYOUT-L016-07` **MUST NOT** `[checker:required_paths]` DDL を `src/app` 配下に配置しない。  `source:01_src_layout.md:16`

## 02_app_entrypoints.md

- [ ] `RULE-02_APP_ENTRYPOINTS-L007-01` **MUST** `[checker:entrypoint_fastapi]` `src/app/main.py` は `create_app()` を定義し、モジュール変数 `app` に `create_app()` の戻り値を代入する。  `source:02_app_entrypoints.md:7`
- [ ] `RULE-02_APP_ENTRYPOINTS-L008-02` **MUST** `[checker:health_route]` `src/app/main.py` は `/health` の GET route を登録する。  `source:02_app_entrypoints.md:8`
- [ ] `RULE-02_APP_ENTRYPOINTS-L009-03` **MUST** `[checker:main_router_includes]` `src/app/apis/{domain}/{operation}/router.py` を持つ operation は `src/app/main.py` で import し、`include_router(...)` で登録する。  `source:02_app_entrypoints.md:9`
- [ ] `RULE-02_APP_ENTRYPOINTS-L010-04` **MUST** `[checker:entrypoint_no_provider_imports]` `src/app/main.py` と `src/app/local.py` は `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。  `source:02_app_entrypoints.md:10`
- [ ] `RULE-02_APP_ENTRYPOINTS-L011-05` **MUST** `[checker:function_logical_lines]` entrypoint 内の関数は `config/rulecheck_config.example.json` の `function_logical_lines` 以下にする。  `source:02_app_entrypoints.md:11`
- [ ] `RULE-02_APP_ENTRYPOINTS-L015-06` **MUST NOT** `[checker:entrypoint_no_provider_imports]` entrypoint で AWS SDK client、HTTP client、provider client を生成しない。  `source:02_app_entrypoints.md:15`
- [ ] `RULE-02_APP_ENTRYPOINTS-L016-07` **MUST NOT** `[checker:main_router_includes]` operation router の登録を `src/app/main.py` 以外へ分散しない。  `source:02_app_entrypoints.md:16`

## 03_api_common_modules.md

- [ ] `RULE-03_API_COMMON_MODULES-L007-01` **MUST** `[checker:api_common_files]` `src/app/apis` 直下に `__init__.py`、`base.py`、`common.py`、`deps.py`、`responses.py`、`router_errors.py`、`sequence_types.py`、`types.py` を配置する。  `source:03_api_common_modules.md:7`
- [ ] `RULE-03_API_COMMON_MODULES-L008-02` **MUST** `[checker:api_domain_layout]` API operation は `src/app/apis/{domain}/{operation}/` の 2 階層で配置する。  `source:03_api_common_modules.md:8`
- [ ] `RULE-03_API_COMMON_MODULES-L009-03` **MUST** `[checker:managed_literals]` 認証方式、URL 種別、ドキュメント種別、公開状態の文字列リテラルは domain common module の定数または Enum から参照する。  `source:03_api_common_modules.md:9`
- [ ] `RULE-03_API_COMMON_MODULES-L010-04` **MUST** `[checker:function_argument_count]` 共通モジュールの Python 関数引数数は設定ファイルの `function_argument_count` 以下にする。  `source:03_api_common_modules.md:10`
- [ ] `RULE-03_API_COMMON_MODULES-L014-05` **MUST NOT** `[checker:managed_literals]` `PUBLIC_PKCE`、`CONFIDENTIAL_CLIENT_CREDENTIALS`、`CALLBACK`、`LOGOUT`、`OPENAPI`、`published` を operation 個別実装へ直書きしない。  `source:03_api_common_modules.md:14`
- [ ] `RULE-03_API_COMMON_MODULES-L015-06` **MUST NOT** `[checker:api_domain_layout]` `src/app/apis/{domain}/{operation}/{sub_operation}/` の 3 階層 operation を作らない。  `source:03_api_common_modules.md:15`

## 04_api_operation_directory.md

- [ ] `RULE-04_API_OPERATION_DIRECTORY-L007-01` **MUST** `[checker:api_operation_required_files]` `src/app/apis/{domain}/{operation}/` は `__init__.py`、`router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py`、`sql/` を持つ。  `source:04_api_operation_directory.md:7`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L008-02` **MUST** `[checker:operation_sql_dir_files]` `sql/` は 1 個以上の `000_name.sql` 形式 SQL ファイルを持つ。  `source:04_api_operation_directory.md:8`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L009-03` **MUST** `[checker:queries_generated_marker]` operation 直下の `queries.py` は sibling `sql/` 由来の生成物であることを示す marker と `SQL_DIR = Path(__file__).with_name("sql")` を持つ。  `source:04_api_operation_directory.md:9`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L010-04` **MUST** `[checker:forbid_generated_subdir_queries]` SQL 由来の query wrapper は `src/app/apis/{domain}/{operation}/queries.py` に配置する。  `source:04_api_operation_directory.md:10`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L011-05` **MUST** `[checker:required_paths]` `docs/spec/40.apis` を仕様生成物の出力先として配置する。  `source:04_api_operation_directory.md:11`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L015-06` **MUST NOT** `[checker:forbid_generated_subdir_queries]` `src/app/apis/{domain}/{operation}/generated/queries.py` を作らない。  `source:04_api_operation_directory.md:15`
- [ ] `RULE-04_API_OPERATION_DIRECTORY-L016-07` **MUST NOT** `[checker:api_operation_required_files]` operation ごとに `router.py`、`functions.py`、`schemas.py`、`samples.py`、`queries.py` の名前を変えない。  `source:04_api_operation_directory.md:16`

## 05_router_sequence_and_logging.md

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

## 06_functions_queries_and_resources.md

- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L007-01` **MUST** `[checker:functions_public_contract]` `functions.py` の public function は docstring、全引数型注釈、戻り値型注釈を持つ。  `source:06_functions_queries_and_resources.md:7`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L008-02` **MUST** `[checker:functions_vocab_names]` sequence vocabulary JSON が存在する場合、public function 名は `{action}_{target}` または `{is|has}_{condition}` の語彙に一致させる。  `source:06_functions_queries_and_resources.md:8`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L009-03` **MUST** `[checker:functions_resource_usage]` validation、predicate、response build、merge、pagination 以外の public function は `queries.*` または integration port を呼ぶか、`@resource-free` marker を持つ。  `source:06_functions_queries_and_resources.md:9`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L010-04` **MUST** `[checker:functions_exception_policy]` runtime dependency を既定値 `None` で受ける関数は、依存が無い経路で `return raise_missing_runtime_dependency("<function_name>")` を実行する。  `source:06_functions_queries_and_resources.md:10`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L011-05` **MUST** `[checker:functions_no_provider_imports]` `functions.py` は integration port と schemas へ依存し、provider client へ依存しない。  `source:06_functions_queries_and_resources.md:11`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L012-06` **MUST** `[checker:return_count]` public function の `return` 文数は設定ファイルの `return_count` 以下にする。  `source:06_functions_queries_and_resources.md:12`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L016-07` **MUST NOT** `[checker:functions_exception_policy]` `functions.py` で `HTTPException` を直接 raise しない。  `source:06_functions_queries_and_resources.md:16`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L017-08` **MUST NOT** `[checker:functions_no_provider_imports]` `functions.py` で `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。  `source:06_functions_queries_and_resources.md:17`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L018-09` **MUST NOT** `[checker:functions_resource_usage]` resource を使わない非 validation 関数を `@resource-free` marker なしで追加しない。  `source:06_functions_queries_and_resources.md:18`

## 07_sql_and_query_generation.md

- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L007-01` **MUST** `[checker:operation_sql_dir_files]` SQL ファイル名は `001_select_apis.sql` 形式の 3 桁番号 prefix を持つ。  `source:07_sql_and_query_generation.md:7`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L008-02` **MUST** `[checker:sql_first_comment_summary]` SQL ファイルの最初の非空行は `-- ` で始まる処理要約にする。  `source:07_sql_and_query_generation.md:8`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L009-03` **MUST** `[checker:sql_placeholders_at_names]` SQL bind placeholder は `@name` 形式にする。  `source:07_sql_and_query_generation.md:9`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L010-04` **MUST** `[checker:sql_no_select_star]` SELECT 句は取得列名を列挙する。  `source:07_sql_and_query_generation.md:10`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L011-05` **MUST** `[checker:queries_generated_marker]` 生成後の `queries.py` は Pydantic params/row model と query function を持つ。  `source:07_sql_and_query_generation.md:11`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L012-06` **MUST** `[checker:db_query_contract]` `src/app/db/query.py` は `@name` placeholder を SQLAlchemy `:name` に変換する `load_sql` を持つ。  `source:07_sql_and_query_generation.md:12`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L016-07` **MUST NOT** `[checker:sql_no_select_star]` SQL で `SELECT *` を使わない。  `source:07_sql_and_query_generation.md:16`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L017-08` **MUST NOT** `[checker:sql_placeholders_at_names]` SQL ファイルへ `:name` placeholder を書かない。  `source:07_sql_and_query_generation.md:17`
- [ ] `RULE-07_SQL_AND_QUERY_GENERATION-L018-09` **MUST NOT** `[checker:forbid_generated_subdir_queries]` SQL 生成物を operation の `generated/` 配下へ置かない。  `source:07_sql_and_query_generation.md:18`

## 08_integrations.md

- [ ] `RULE-08_INTEGRATIONS-L007-01` **MUST** `[checker:integration_port_provider_layout]` `src/app/integrations/{resource}/port.py` を持つ resource は `schemas.py`、`deps.py`、provider `client.py` を持つ。  `source:08_integrations.md:7`
- [ ] `RULE-08_INTEGRATIONS-L008-02` **MUST** `[checker:integration_provider_boundary]` provider SDK と HTTP client の import は provider boundary、`deps.py`、`common_errors.py` に閉じる。  `source:08_integrations.md:8`
- [ ] `RULE-08_INTEGRATIONS-L009-03` **MUST** `[checker:functions_no_provider_imports]` API operation の `functions.py` は `src/app/integrations/{resource}/port.py` の Protocol 型へ依存する。  `source:08_integrations.md:9`
- [ ] `RULE-08_INTEGRATIONS-L010-04` **MUST** `[checker:entrypoint_no_provider_imports]` `src/app/main.py` は integration provider 実装を import しない。  `source:08_integrations.md:10`
- [ ] `RULE-08_INTEGRATIONS-L011-05` **MUST** `[checker:function_argument_count]` integration public function と provider method の引数数は設定ファイルの `function_argument_count` 以下にする。  `source:08_integrations.md:11`
- [ ] `RULE-08_INTEGRATIONS-L015-06` **MUST NOT** `[checker:integration_provider_boundary]` provider SDK の例外型、payload 型、retry 設定を API operation へ露出しない。  `source:08_integrations.md:15`
- [ ] `RULE-08_INTEGRATIONS-L016-07` **MUST NOT** `[checker:functions_no_provider_imports]` API operation から `src/app/integrations/{resource}/boto3_provider/client.py` を import しない。  `source:08_integrations.md:16`

## 09_core_db_and_settings.md

- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L007-01` **MUST** `[checker:required_paths]` `src/app/core/config.py`、`src/app/core/exceptions.py`、`src/app/core/logging.py` を配置する。  `source:09_core_db_and_settings.md:7`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L008-02` **MUST** `[checker:db_query_contract]` `src/app/db/query.py` は `load_sql`、`model_parameters`、`fetch_all`、`fetch_one`、`execute_sql` を提供する。  `source:09_core_db_and_settings.md:8`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L009-03` **MUST** `[checker:required_paths]` `src/app/db/session.py` を配置する。  `source:09_core_db_and_settings.md:9`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L010-04` **MUST** `[checker:repo_python_policy]` 型検査は Pyright strict と mypy strict を使う。  `source:09_core_db_and_settings.md:10`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L011-05` **MUST** `[checker:quality_commands_declared]` formatter、linter、型検査、pytest のコマンドを README または設定に記録する。  `source:09_core_db_and_settings.md:11`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L015-06` **MUST NOT** `[checker:integration_provider_boundary]` `src/app/core` と `src/app/db` から provider client を import しない。  `source:09_core_db_and_settings.md:15`
- [ ] `RULE-09_CORE_DB_AND_SETTINGS-L016-07` **MUST NOT** `[checker:sql_placeholders_at_names]` SQL 実行 helper を迂回するために SQL ファイルへ SQLAlchemy `:name` placeholder を書かない。  `source:09_core_db_and_settings.md:16`

## 10_tools_docs_and_generated_outputs.md

- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L007-01` **MUST** `[checker:tools_existing_checks]` `src/tools/check_api_function_names.py`、`generate_api_sequences.py`、`check_api_mermaid_sequences.py`、`generate_queries.py`、`generate_db_crud.py`、`check_operational_logging.py` を配置する。  `source:10_tools_docs_and_generated_outputs.md:7`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L008-02` **MUST** `[checker:queries_generated_marker]` `generate_queries.py` の出力は operation 直下の `queries.py` にする。  `source:10_tools_docs_and_generated_outputs.md:8`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L009-03` **MUST** `[checker:quality_commands_declared]` CI 用コマンドに `ruff format`、`ruff check`、`pyright`、`mypy`、`pytest` を含める。  `source:10_tools_docs_and_generated_outputs.md:9`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L010-04` **MUST** `[checker:file_logical_lines]` `src/tools/**/*.py` のファイル論理行数は設定ファイルの `file_logical_lines` 以下にする。  `source:10_tools_docs_and_generated_outputs.md:10`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L011-05` **MUST** `[checker:function_logical_lines]` `src/tools/**/*.py` の関数論理行数は設定ファイルの `function_logical_lines` 以下にする。  `source:10_tools_docs_and_generated_outputs.md:11`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L015-06` **MUST NOT** `[checker:forbid_generated_subdir_queries]` `src/tools/generate_queries.py` の出力先を `generated/queries.py` に戻さない。  `source:10_tools_docs_and_generated_outputs.md:15`
- [ ] `RULE-10_TOOLS_DOCS_AND_GENERATED_OUTPUTS-L016-07` **MUST NOT** `[checker:tools_existing_checks]` 現行 checker/generator のファイル名を変更しない。  `source:10_tools_docs_and_generated_outputs.md:16`

## 11_quantitative_thresholds.md

- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L007-01` **MUST** `[checker:python_complexity]` `src/app/apis/**/router.py` の関数は循環的複雑度を `17` 以下にする。  `source:11_quantitative_thresholds.md:7`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L008-02` **MUST** `[checker:python_complexity]` `src/app/**/*.py` の関数は循環的複雑度を `17` 以下にする。  `source:11_quantitative_thresholds.md:8`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L009-03` **MUST** `[checker:python_complexity]` `src/tools/**/*.py` の関数は循環的複雑度を `21` 以下にする。  `source:11_quantitative_thresholds.md:9`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L010-04` **MUST** `[checker:control_nesting_depth]` `src/app/apis/**/router.py` の関数は制御構造ネスト深度を `5` 以下にする。  `source:11_quantitative_thresholds.md:10`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L011-05` **MUST** `[checker:control_nesting_depth]` `src/app/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。  `source:11_quantitative_thresholds.md:11`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L012-06` **MUST** `[checker:control_nesting_depth]` `src/tools/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。  `source:11_quantitative_thresholds.md:12`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L013-07` **MUST** `[checker:function_logical_lines]` `src/app/apis/**/router.py` の関数は論理行数を `450` 以下にする。  `source:11_quantitative_thresholds.md:13`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L014-08` **MUST** `[checker:function_logical_lines]` `src/app/**/*.py` の関数は論理行数を `450` 以下にする。  `source:11_quantitative_thresholds.md:14`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L015-09` **MUST** `[checker:function_logical_lines]` `src/tools/**/*.py` の関数は論理行数を `160` 以下にする。  `source:11_quantitative_thresholds.md:15`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L016-10` **MUST** `[checker:file_logical_lines]` `src/app/apis/**/router.py` のファイルは論理行数を `550` 以下にする。  `source:11_quantitative_thresholds.md:16`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L017-11` **MUST** `[checker:file_logical_lines]` `src/app/**/*.py` のファイルは論理行数を `800` 以下にする。  `source:11_quantitative_thresholds.md:17`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L018-12` **MUST** `[checker:file_logical_lines]` `src/tools/**/*.py` のファイルは論理行数を `1700` 以下にする。  `source:11_quantitative_thresholds.md:18`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L019-13` **MUST** `[checker:function_argument_count]` `src/app/apis/**/router.py` の関数引数数は `20` 以下にする。  `source:11_quantitative_thresholds.md:19`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L020-14` **MUST** `[checker:function_argument_count]` `src/app/**/*.py` の関数引数数は `20` 以下にする。  `source:11_quantitative_thresholds.md:20`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L021-15` **MUST** `[checker:function_argument_count]` `src/tools/**/*.py` の関数引数数は `12` 以下にする。  `source:11_quantitative_thresholds.md:21`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L022-16` **MUST** `[checker:return_count]` `src/app/**/*.py` の関数内 `return` 文数は `12` 以下にする。  `source:11_quantitative_thresholds.md:22`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L023-17` **MUST** `[checker:return_count]` `src/tools/**/*.py` の関数内 `return` 文数は `12` 以下にする。  `source:11_quantitative_thresholds.md:23`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L024-18` **MUST** `[checker:condition_complexity]` `if`、`while`、`assert`、三項式の条件式に含める `and` と `or` の演算子数は合計 `3` 以下にする。  `source:11_quantitative_thresholds.md:24`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L025-19` **MUST** `[checker:condition_complexity]` 条件式に含める比較演算子数は `4` 以下にする。  `source:11_quantitative_thresholds.md:25`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L026-20` **MUST** `[checker:condition_complexity]` 条件式 AST 深度は `9` 以下にする。  `source:11_quantitative_thresholds.md:26`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L030-21` **MUST NOT** `[checker:condition_complexity]` 三項式の中に三項式を入れない。  `source:11_quantitative_thresholds.md:30`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L031-22` **MUST NOT** `[checker:control_nesting_depth]` `src/app/**/*.py` で制御構造を 6 層にしない。  `source:11_quantitative_thresholds.md:31`

<!-- rulecheck:generated-checklist:end -->
