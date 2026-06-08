# 03. `src/app/apis` 共通モジュール

`src/app/apis` 直下は API 横断の型、依存、レスポンス、例外、sequence 用型を持つ。

## 実装すべき内容

- **MUST** `[checker:api_common_files]`: `src/app/apis` 直下に `__init__.py`、`base.py`、`common.py`、`deps.py`、`responses.py`、`router_errors.py`、`sequence_types.py`、`types.py` を配置する。
- **MUST** `[checker:api_domain_layout]`: API operation は `src/app/apis/{domain}/{operation}/` の 2 階層で配置する。
- **MUST** `[checker:managed_literals]`: 認証方式、URL 種別、ドキュメント種別、公開状態の文字列リテラルは domain common module の定数または Enum から参照する。
- **MUST** `[checker:function_argument_count]`: 共通モジュールの Python 関数引数数は設定ファイルの `function_argument_count` 以下にする。

## 実装してはいけない内容

- **MUST NOT** `[checker:managed_literals]`: `PUBLIC_PKCE`、`CONFIDENTIAL_CLIENT_CREDENTIALS`、`CALLBACK`、`LOGOUT`、`OPENAPI`、`published` を operation 個別実装へ直書きしない。
- **MUST NOT** `[checker:api_domain_layout]`: `src/app/apis/{domain}/{operation}/{sub_operation}/` の 3 階層 operation を作らない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-03_API_COMMON_MODULES-L007-01` **MUST** `[checker:api_common_files]` `src/app/apis` 直下に `__init__.py`、`base.py`、`common.py`、`deps.py`、`responses.py`、`router_errors.py`、`sequence_types.py`、`types.py` を配置する。  `source:03_api_common_modules.md:7`
- [ ] `RULE-03_API_COMMON_MODULES-L008-02` **MUST** `[checker:api_domain_layout]` API operation は `src/app/apis/{domain}/{operation}/` の 2 階層で配置する。  `source:03_api_common_modules.md:8`
- [ ] `RULE-03_API_COMMON_MODULES-L009-03` **MUST** `[checker:managed_literals]` 認証方式、URL 種別、ドキュメント種別、公開状態の文字列リテラルは domain common module の定数または Enum から参照する。  `source:03_api_common_modules.md:9`
- [ ] `RULE-03_API_COMMON_MODULES-L010-04` **MUST** `[checker:function_argument_count]` 共通モジュールの Python 関数引数数は設定ファイルの `function_argument_count` 以下にする。  `source:03_api_common_modules.md:10`
- [ ] `RULE-03_API_COMMON_MODULES-L014-05` **MUST NOT** `[checker:managed_literals]` `PUBLIC_PKCE`、`CONFIDENTIAL_CLIENT_CREDENTIALS`、`CALLBACK`、`LOGOUT`、`OPENAPI`、`published` を operation 個別実装へ直書きしない。  `source:03_api_common_modules.md:14`
- [ ] `RULE-03_API_COMMON_MODULES-L015-06` **MUST NOT** `[checker:api_domain_layout]` `src/app/apis/{domain}/{operation}/{sub_operation}/` の 3 階層 operation を作らない。  `source:03_api_common_modules.md:15`

<!-- rulecheck:generated-checklist:end -->
