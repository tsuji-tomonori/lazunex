# 08. `src/app/integrations` 境界

integration はアプリ内 port、共通 schema、dependency、provider 実装を分ける。provider 実装は `_provider` ディレクトリまたは legacy flat `client.py` に閉じる。

## 実装すべき内容

- **MUST** `[checker:integration_port_provider_layout]`: `src/app/integrations/{resource}/port.py` を持つ resource は `schemas.py`、`deps.py`、provider `client.py` を持つ。
- **MUST** `[checker:integration_provider_boundary]`: provider SDK と HTTP client の import は provider boundary、`deps.py`、`common_errors.py` に閉じる。
- **MUST** `[checker:functions_no_provider_imports]`: API operation の `functions.py` は `src/app/integrations/{resource}/port.py` の Protocol 型へ依存する。
- **MUST** `[checker:entrypoint_no_provider_imports]`: `src/app/main.py` は integration provider 実装を import しない。
- **MUST** `[checker:function_argument_count]`: integration public function と provider method の引数数は設定ファイルの `function_argument_count` 以下にする。

## 実装してはいけない内容

- **MUST NOT** `[checker:integration_provider_boundary]`: provider SDK の例外型、payload 型、retry 設定を API operation へ露出しない。
- **MUST NOT** `[checker:functions_no_provider_imports]`: API operation から `src/app/integrations/{resource}/boto3_provider/client.py` を import しない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-08_INTEGRATIONS-L007-01` **MUST** `[checker:integration_port_provider_layout]` `src/app/integrations/{resource}/port.py` を持つ resource は `schemas.py`、`deps.py`、provider `client.py` を持つ。  `source:08_integrations.md:7`
- [ ] `RULE-08_INTEGRATIONS-L008-02` **MUST** `[checker:integration_provider_boundary]` provider SDK と HTTP client の import は provider boundary、`deps.py`、`common_errors.py` に閉じる。  `source:08_integrations.md:8`
- [ ] `RULE-08_INTEGRATIONS-L009-03` **MUST** `[checker:functions_no_provider_imports]` API operation の `functions.py` は `src/app/integrations/{resource}/port.py` の Protocol 型へ依存する。  `source:08_integrations.md:9`
- [ ] `RULE-08_INTEGRATIONS-L010-04` **MUST** `[checker:entrypoint_no_provider_imports]` `src/app/main.py` は integration provider 実装を import しない。  `source:08_integrations.md:10`
- [ ] `RULE-08_INTEGRATIONS-L011-05` **MUST** `[checker:function_argument_count]` integration public function と provider method の引数数は設定ファイルの `function_argument_count` 以下にする。  `source:08_integrations.md:11`
- [ ] `RULE-08_INTEGRATIONS-L015-06` **MUST NOT** `[checker:integration_provider_boundary]` provider SDK の例外型、payload 型、retry 設定を API operation へ露出しない。  `source:08_integrations.md:15`
- [ ] `RULE-08_INTEGRATIONS-L016-07` **MUST NOT** `[checker:functions_no_provider_imports]` API operation から `src/app/integrations/{resource}/boto3_provider/client.py` を import しない。  `source:08_integrations.md:16`

<!-- rulecheck:generated-checklist:end -->
