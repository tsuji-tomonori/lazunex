# 02. `src/app/main.py` と entrypoint

`main.py` は FastAPI アプリを生成し、operation router を登録する入口である。

## 実装すべき内容

- **MUST** `[checker:entrypoint_fastapi]`: `src/app/main.py` は `create_app()` を定義し、モジュール変数 `app` に `create_app()` の戻り値を代入する。
- **MUST** `[checker:health_route]`: `src/app/main.py` は `/health` の GET route を登録する。
- **MUST** `[checker:main_router_includes]`: `src/app/apis/{domain}/{operation}/router.py` を持つ operation は `src/app/main.py` で import し、`include_router(...)` で登録する。
- **MUST** `[checker:entrypoint_no_provider_imports]`: `src/app/main.py` と `src/app/local.py` は `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。
- **MUST** `[checker:function_logical_lines]`: entrypoint 内の関数は `config/rulecheck_config.example.json` の `function_logical_lines` 以下にする。

## 実装してはいけない内容

- **MUST NOT** `[checker:entrypoint_no_provider_imports]`: entrypoint で AWS SDK client、HTTP client、provider client を生成しない。
- **MUST NOT** `[checker:main_router_includes]`: operation router の登録を `src/app/main.py` 以外へ分散しない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-02_APP_ENTRYPOINTS-L007-01` **MUST** `[checker:entrypoint_fastapi]` `src/app/main.py` は `create_app()` を定義し、モジュール変数 `app` に `create_app()` の戻り値を代入する。  `source:02_app_entrypoints.md:7`
- [ ] `RULE-02_APP_ENTRYPOINTS-L008-02` **MUST** `[checker:health_route]` `src/app/main.py` は `/health` の GET route を登録する。  `source:02_app_entrypoints.md:8`
- [ ] `RULE-02_APP_ENTRYPOINTS-L009-03` **MUST** `[checker:main_router_includes]` `src/app/apis/{domain}/{operation}/router.py` を持つ operation は `src/app/main.py` で import し、`include_router(...)` で登録する。  `source:02_app_entrypoints.md:9`
- [ ] `RULE-02_APP_ENTRYPOINTS-L010-04` **MUST** `[checker:entrypoint_no_provider_imports]` `src/app/main.py` と `src/app/local.py` は `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。  `source:02_app_entrypoints.md:10`
- [ ] `RULE-02_APP_ENTRYPOINTS-L011-05` **MUST** `[checker:function_logical_lines]` entrypoint 内の関数は `config/rulecheck_config.example.json` の `function_logical_lines` 以下にする。  `source:02_app_entrypoints.md:11`
- [ ] `RULE-02_APP_ENTRYPOINTS-L015-06` **MUST NOT** `[checker:entrypoint_no_provider_imports]` entrypoint で AWS SDK client、HTTP client、provider client を生成しない。  `source:02_app_entrypoints.md:15`
- [ ] `RULE-02_APP_ENTRYPOINTS-L016-07` **MUST NOT** `[checker:main_router_includes]` operation router の登録を `src/app/main.py` 以外へ分散しない。  `source:02_app_entrypoints.md:16`

<!-- rulecheck:generated-checklist:end -->
