# 03. `src/app/apis` 共通モジュール

`src/app/apis` 直下は API 横断の型、依存、レスポンス、例外、sequence 用型を持つ。

## 実装すべき内容

- `src/app/apis` 直下に `__init__.py`、`base.py`、`common.py`、`deps.py`、`responses.py`、`router_errors.py`、`sequence_types.py`、`types.py` を配置する。
- API operation は `src/app/apis/{domain}/{operation}/` の 2 階層で配置する。
- 認証方式、URL 種別、ドキュメント種別、公開状態の文字列リテラルは domain common module の定数または Enum から参照する。
- 共通モジュールの Python 関数引数数は設定ファイルの `function_argument_count` 以下にする。

## 実装してはいけない内容

- `PUBLIC_PKCE`、`CONFIDENTIAL_CLIENT_CREDENTIALS`、`CALLBACK`、`LOGOUT`、`OPENAPI`、`published` を operation 個別実装へ直書きしない。
- `src/app/apis/{domain}/{operation}/{sub_operation}/` の 3 階層 operation を作らない。

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| API-COMMON-DO-001 | MUST | `api_common_files` | - | `src/app/apis` 直下に `__init__.py`、`base.py`、`common.py`、`deps.py`、`responses.py`、`router_errors.py`、`sequence_types.py`、`types.py` を配置する。 |
| API-COMMON-DO-002 | MUST | `api_domain_layout` | - | API operation は `src/app/apis/{domain}/{operation}/` の 2 階層で配置する。 |
| API-COMMON-DO-003 | MUST | `managed_literals` | - | 認証方式、URL 種別、ドキュメント種別、公開状態の文字列リテラルは domain common module の定数または Enum から参照する。 |
| API-COMMON-DO-004 | MUST | `function_argument_count` | - | 共通モジュールの Python 関数引数数は設定ファイルの `function_argument_count` 以下にする。 |
| API-COMMON-DONT-001 | MUST NOT | `managed_literals` | - | `PUBLIC_PKCE`、`CONFIDENTIAL_CLIENT_CREDENTIALS`、`CALLBACK`、`LOGOUT`、`OPENAPI`、`published` を operation 個別実装へ直書きしない。 |
| API-COMMON-DONT-002 | MUST NOT | `api_domain_layout` | - | `src/app/apis/{domain}/{operation}/{sub_operation}/` の 3 階層 operation を作らない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `src/app/apis` 直下に `__init__.py`、`base.py`、`common.py`、`deps.py`、`responses.py`、`router_errors.py`、`sequence_types.py`、`types.py` を配置する。 (`API-COMMON-DO-001`, **MUST**, `[checker:api_common_files]`)  `source:03_api_common_modules.md:21`
- [ ] API operation は `src/app/apis/{domain}/{operation}/` の 2 階層で配置する。 (`API-COMMON-DO-002`, **MUST**, `[checker:api_domain_layout]`)  `source:03_api_common_modules.md:22`
- [ ] 認証方式、URL 種別、ドキュメント種別、公開状態の文字列リテラルは domain common module の定数または Enum から参照する。 (`API-COMMON-DO-003`, **MUST**, `[checker:managed_literals]`)  `source:03_api_common_modules.md:23`
- [ ] 共通モジュールの Python 関数引数数は設定ファイルの `function_argument_count` 以下にする。 (`API-COMMON-DO-004`, **MUST**, `[checker:function_argument_count]`)  `source:03_api_common_modules.md:24`
- [ ] `PUBLIC_PKCE`、`CONFIDENTIAL_CLIENT_CREDENTIALS`、`CALLBACK`、`LOGOUT`、`OPENAPI`、`published` を operation 個別実装へ直書きしない。 (`API-COMMON-DONT-001`, **MUST NOT**, `[checker:managed_literals]`)  `source:03_api_common_modules.md:25`
- [ ] `src/app/apis/{domain}/{operation}/{sub_operation}/` の 3 階層 operation を作らない。 (`API-COMMON-DONT-002`, **MUST NOT**, `[checker:api_domain_layout]`)  `source:03_api_common_modules.md:26`

<!-- rulecheck:generated-checklist:end -->
