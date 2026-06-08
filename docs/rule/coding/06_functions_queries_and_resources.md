# 06. `functions.py` と query/resource 使用

`functions.py` は業務関数を公開し、query wrapper と integration port を呼ぶ。HTTP response 形式の最終組み立ては `build_*` 関数で行う。

## 実装すべき内容

- `functions.py` の public function は docstring、全引数型注釈、戻り値型注釈を持つ。
- sequence vocabulary JSON が存在する場合、public function 名は `{action}_{target}` または `{is|has}_{condition}` の語彙に一致させる。
- validation、predicate、response build、merge、pagination 以外の public function は `queries.*` または integration port を呼ぶか、`@resource-free` marker を持つ。
- runtime dependency を既定値 `None` で受ける関数は、依存が無い経路で `return raise_missing_runtime_dependency("<function_name>")` を実行する。
- `functions.py` は integration port と schemas へ依存し、provider client へ依存しない。
- public function の `return` 文数は設定ファイルの `return_count` 以下にする。

## 実装してはいけない内容

- `functions.py` で `HTTPException` を直接 raise しない。
- `functions.py` で `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。
- resource を使わない非 validation 関数を `@resource-free` marker なしで追加しない。

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| FUNCTIONS-DO-001 | MUST | `functions_public_contract` | - | `functions.py` の public function は docstring、全引数型注釈、戻り値型注釈を持つ。 |
| FUNCTIONS-DO-002 | MUST | `functions_vocab_names` | - | sequence vocabulary JSON が存在する場合、public function 名は `{action}_{target}` または `{is\|has}_{condition}` の語彙に一致させる。 |
| FUNCTIONS-DO-003 | MUST | `functions_resource_usage` | - | validation、predicate、response build、merge、pagination 以外の public function は `queries.*` または integration port を呼ぶか、`@resource-free` marker を持つ。 |
| FUNCTIONS-DO-004 | MUST | `functions_exception_policy` | - | runtime dependency を既定値 `None` で受ける関数は、依存が無い経路で `return raise_missing_runtime_dependency("<function_name>")` を実行する。 |
| FUNCTIONS-DO-005 | MUST | `functions_no_provider_imports` | `functions.py` | integration port と schemas へ依存し、provider client へ依存しない。 |
| FUNCTIONS-DO-006 | MUST | `return_count` | - | public function の `return` 文数は設定ファイルの `return_count` 以下にする。 |
| FUNCTIONS-DONT-001 | MUST NOT | `functions_exception_policy` | - | `functions.py` で `HTTPException` を直接 raise しない。 |
| FUNCTIONS-DONT-002 | MUST NOT | `functions_no_provider_imports` | - | `functions.py` で `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。 |
| FUNCTIONS-DONT-003 | MUST NOT | `functions_resource_usage` | - | resource を使わない非 validation 関数を `@resource-free` marker なしで追加しない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `functions.py` の public function は docstring、全引数型注釈、戻り値型注釈を持つ。 (`FUNCTIONS-DO-001`, **MUST**, `[checker:functions_public_contract]`)  `source:06_functions_queries_and_resources.md:24`
- [ ] sequence vocabulary JSON が存在する場合、public function 名は `{action}_{target}` または `{is|has}_{condition}` の語彙に一致させる。 (`FUNCTIONS-DO-002`, **MUST**, `[checker:functions_vocab_names]`)  `source:06_functions_queries_and_resources.md:25`
- [ ] validation、predicate、response build、merge、pagination 以外の public function は `queries.*` または integration port を呼ぶか、`@resource-free` marker を持つ。 (`FUNCTIONS-DO-003`, **MUST**, `[checker:functions_resource_usage]`)  `source:06_functions_queries_and_resources.md:26`
- [ ] runtime dependency を既定値 `None` で受ける関数は、依存が無い経路で `return raise_missing_runtime_dependency("<function_name>")` を実行する。 (`FUNCTIONS-DO-004`, **MUST**, `[checker:functions_exception_policy]`)  `source:06_functions_queries_and_resources.md:27`
- [ ] `functions.py`: integration port と schemas へ依存し、provider client へ依存しない。 (`FUNCTIONS-DO-005`, **MUST**, `[checker:functions_no_provider_imports]`)  `source:06_functions_queries_and_resources.md:28`
- [ ] public function の `return` 文数は設定ファイルの `return_count` 以下にする。 (`FUNCTIONS-DO-006`, **MUST**, `[checker:return_count]`)  `source:06_functions_queries_and_resources.md:29`
- [ ] `functions.py` で `HTTPException` を直接 raise しない。 (`FUNCTIONS-DONT-001`, **MUST NOT**, `[checker:functions_exception_policy]`)  `source:06_functions_queries_and_resources.md:30`
- [ ] `functions.py` で `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。 (`FUNCTIONS-DONT-002`, **MUST NOT**, `[checker:functions_no_provider_imports]`)  `source:06_functions_queries_and_resources.md:31`
- [ ] resource を使わない非 validation 関数を `@resource-free` marker なしで追加しない。 (`FUNCTIONS-DONT-003`, **MUST NOT**, `[checker:functions_resource_usage]`)  `source:06_functions_queries_and_resources.md:32`

<!-- rulecheck:generated-checklist:end -->
