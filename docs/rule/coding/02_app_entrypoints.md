# 02. `src/app/main.py` と entrypoint

`main.py` は FastAPI アプリを生成し、operation router を登録する入口である。

## 実装すべき内容

- `src/app/main.py` は `create_app()` を定義し、モジュール変数 `app` に `create_app()` の戻り値を代入する。
- `src/app/main.py` は `/health` の GET route を登録する。
- `src/app/apis/{domain}/{operation}/router.py` を持つ operation は `src/app/main.py` で import し、`include_router(...)` で登録する。
- `src/app/main.py` と `src/app/local.py` は `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。
- entrypoint 内の関数は `config/rulecheck_config.example.json` の `function_logical_lines` 以下にする。

## 実装してはいけない内容

- entrypoint で AWS SDK client、HTTP client、provider client を生成しない。
- operation router の登録を `src/app/main.py` 以外へ分散しない。

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| ENTRYPOINT-DO-001 | MUST | `entrypoint_fastapi` | `src/app/main.py` | `create_app()` を定義し、モジュール変数 `app` に `create_app()` の戻り値を代入する。 |
| ENTRYPOINT-DO-002 | MUST | `health_route` | `src/app/main.py` | `/health` の GET route を登録する。 |
| ENTRYPOINT-DO-003 | MUST | `main_router_includes` | - | `src/app/apis/{domain}/{operation}/router.py` を持つ operation は `src/app/main.py` で import し、`include_router(...)` で登録する。 |
| ENTRYPOINT-DO-004 | MUST | `entrypoint_no_provider_imports` | - | `src/app/main.py` と `src/app/local.py` は `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。 |
| ENTRYPOINT-DO-005 | MUST | `function_logical_lines` | - | entrypoint 内の関数は `config/rulecheck_config.example.json` の `function_logical_lines` 以下にする。 |
| ENTRYPOINT-DONT-001 | MUST NOT | `entrypoint_no_provider_imports` | - | entrypoint で AWS SDK client、HTTP client、provider client を生成しない。 |
| ENTRYPOINT-DONT-002 | MUST NOT | `main_router_includes` | - | operation router の登録を `src/app/main.py` 以外へ分散しない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `src/app/main.py`: `create_app()` を定義し、モジュール変数 `app` に `create_app()` の戻り値を代入する。 (`ENTRYPOINT-DO-001`, **MUST**, `[checker:entrypoint_fastapi]`)  `source:02_app_entrypoints.md:22`
- [ ] `src/app/main.py`: `/health` の GET route を登録する。 (`ENTRYPOINT-DO-002`, **MUST**, `[checker:health_route]`)  `source:02_app_entrypoints.md:23`
- [ ] `src/app/apis/{domain}/{operation}/router.py` を持つ operation は `src/app/main.py` で import し、`include_router(...)` で登録する。 (`ENTRYPOINT-DO-003`, **MUST**, `[checker:main_router_includes]`)  `source:02_app_entrypoints.md:24`
- [ ] `src/app/main.py` と `src/app/local.py` は `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。 (`ENTRYPOINT-DO-004`, **MUST**, `[checker:entrypoint_no_provider_imports]`)  `source:02_app_entrypoints.md:25`
- [ ] entrypoint 内の関数は `config/rulecheck_config.example.json` の `function_logical_lines` 以下にする。 (`ENTRYPOINT-DO-005`, **MUST**, `[checker:function_logical_lines]`)  `source:02_app_entrypoints.md:26`
- [ ] entrypoint で AWS SDK client、HTTP client、provider client を生成しない。 (`ENTRYPOINT-DONT-001`, **MUST NOT**, `[checker:entrypoint_no_provider_imports]`)  `source:02_app_entrypoints.md:27`
- [ ] operation router の登録を `src/app/main.py` 以外へ分散しない。 (`ENTRYPOINT-DONT-002`, **MUST NOT**, `[checker:main_router_includes]`)  `source:02_app_entrypoints.md:28`

<!-- rulecheck:generated-checklist:end -->
