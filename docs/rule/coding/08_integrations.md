# 08. `src/app/integrations` 境界

integration はアプリ内 port、共通 schema、dependency、provider 実装を分ける。provider 実装は `_provider` ディレクトリまたは legacy flat `client.py` に閉じる。

## 実装すべき内容

- `src/app/integrations/{resource}/port.py` を持つ resource は `schemas.py`、`deps.py`、provider `client.py` を持つ。
- provider SDK と HTTP client の import は provider boundary、`deps.py`、`common_errors.py` に閉じる。
- API operation の `functions.py` は `src/app/integrations/{resource}/port.py` の Protocol 型へ依存する。
- `src/app/main.py` は integration provider 実装を import しない。
- integration public function と provider method の引数数は設定ファイルの `function_argument_count` 以下にする。

## 実装してはいけない内容

- provider SDK の例外型、payload 型、retry 設定を API operation へ露出しない。
- API operation から `src/app/integrations/{resource}/boto3_provider/client.py` を import しない。

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| INTEGRATION-DO-001 | MUST | `integration_port_provider_layout` | - | `src/app/integrations/{resource}/port.py` を持つ resource は `schemas.py`、`deps.py`、provider `client.py` を持つ。 |
| INTEGRATION-DO-002 | MUST | `integration_provider_boundary` | - | provider SDK と HTTP client の import は provider boundary、`deps.py`、`common_errors.py` に閉じる。 |
| INTEGRATION-DO-003 | MUST | `functions_no_provider_imports` | - | API operation の `functions.py` は `src/app/integrations/{resource}/port.py` の Protocol 型へ依存する。 |
| INTEGRATION-DO-004 | MUST | `entrypoint_no_provider_imports` | `src/app/main.py` | integration provider 実装を import しない。 |
| INTEGRATION-DO-005 | MUST | `function_argument_count` | - | integration public function と provider method の引数数は設定ファイルの `function_argument_count` 以下にする。 |
| INTEGRATION-DONT-001 | MUST NOT | `integration_provider_boundary` | - | provider SDK の例外型、payload 型、retry 設定を API operation へ露出しない。 |
| INTEGRATION-DONT-002 | MUST NOT | `functions_no_provider_imports` | - | API operation から `src/app/integrations/{resource}/boto3_provider/client.py` を import しない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `src/app/integrations/{resource}/port.py` を持つ resource は `schemas.py`、`deps.py`、provider `client.py` を持つ。 (`INTEGRATION-DO-001`, **MUST**, `[checker:integration_port_provider_layout]`)  `source:08_integrations.md:22`
- [ ] provider SDK と HTTP client の import は provider boundary、`deps.py`、`common_errors.py` に閉じる。 (`INTEGRATION-DO-002`, **MUST**, `[checker:integration_provider_boundary]`)  `source:08_integrations.md:23`
- [ ] API operation の `functions.py` は `src/app/integrations/{resource}/port.py` の Protocol 型へ依存する。 (`INTEGRATION-DO-003`, **MUST**, `[checker:functions_no_provider_imports]`)  `source:08_integrations.md:24`
- [ ] `src/app/main.py`: integration provider 実装を import しない。 (`INTEGRATION-DO-004`, **MUST**, `[checker:entrypoint_no_provider_imports]`)  `source:08_integrations.md:25`
- [ ] integration public function と provider method の引数数は設定ファイルの `function_argument_count` 以下にする。 (`INTEGRATION-DO-005`, **MUST**, `[checker:function_argument_count]`)  `source:08_integrations.md:26`
- [ ] provider SDK の例外型、payload 型、retry 設定を API operation へ露出しない。 (`INTEGRATION-DONT-001`, **MUST NOT**, `[checker:integration_provider_boundary]`)  `source:08_integrations.md:27`
- [ ] API operation から `src/app/integrations/{resource}/boto3_provider/client.py` を import しない。 (`INTEGRATION-DONT-002`, **MUST NOT**, `[checker:functions_no_provider_imports]`)  `source:08_integrations.md:28`

<!-- rulecheck:generated-checklist:end -->
