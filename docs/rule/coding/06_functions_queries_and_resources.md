# 06. `functions.py` と query/resource 使用

`functions.py` は業務関数を公開し、query wrapper と integration port を呼ぶ。HTTP response 形式の最終組み立ては `build_*` 関数で行う。

## 実装すべき内容

- **MUST** `[checker:functions_public_contract]`: `functions.py` の public function は docstring、全引数型注釈、戻り値型注釈を持つ。
- **MUST** `[checker:functions_vocab_names]`: sequence vocabulary JSON が存在する場合、public function 名は `{action}_{target}` または `{is|has}_{condition}` の語彙に一致させる。
- **MUST** `[checker:functions_resource_usage]`: validation、predicate、response build、merge、pagination 以外の public function は `queries.*` または integration port を呼ぶか、`@resource-free` marker を持つ。
- **MUST** `[checker:functions_exception_policy]`: runtime dependency を既定値 `None` で受ける関数は、依存が無い経路で `return raise_missing_runtime_dependency("<function_name>")` を実行する。
- **MUST** `[checker:functions_no_provider_imports]`: `functions.py` は integration port と schemas へ依存し、provider client へ依存しない。
- **MUST** `[checker:return_count]`: public function の `return` 文数は設定ファイルの `return_count` 以下にする。

## 実装してはいけない内容

- **MUST NOT** `[checker:functions_exception_policy]`: `functions.py` で `HTTPException` を直接 raise しない。
- **MUST NOT** `[checker:functions_no_provider_imports]`: `functions.py` で `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。
- **MUST NOT** `[checker:functions_resource_usage]`: resource を使わない非 validation 関数を `@resource-free` marker なしで追加しない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L007-01` **MUST** `[checker:functions_public_contract]` `functions.py` の public function は docstring、全引数型注釈、戻り値型注釈を持つ。  `source:06_functions_queries_and_resources.md:7`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L008-02` **MUST** `[checker:functions_vocab_names]` sequence vocabulary JSON が存在する場合、public function 名は `{action}_{target}` または `{is|has}_{condition}` の語彙に一致させる。  `source:06_functions_queries_and_resources.md:8`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L009-03` **MUST** `[checker:functions_resource_usage]` validation、predicate、response build、merge、pagination 以外の public function は `queries.*` または integration port を呼ぶか、`@resource-free` marker を持つ。  `source:06_functions_queries_and_resources.md:9`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L010-04` **MUST** `[checker:functions_exception_policy]` runtime dependency を既定値 `None` で受ける関数は、依存が無い経路で `return raise_missing_runtime_dependency("<function_name>")` を実行する。  `source:06_functions_queries_and_resources.md:10`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L011-05` **MUST** `[checker:functions_no_provider_imports]` `functions.py` は integration port と schemas へ依存し、provider client へ依存しない。  `source:06_functions_queries_and_resources.md:11`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L012-06` **MUST** `[checker:return_count]` public function の `return` 文数は設定ファイルの `return_count` 以下にする。  `source:06_functions_queries_and_resources.md:12`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L016-07` **MUST NOT** `[checker:functions_exception_policy]` `functions.py` で `HTTPException` を直接 raise しない。  `source:06_functions_queries_and_resources.md:16`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L017-08` **MUST NOT** `[checker:functions_no_provider_imports]` `functions.py` で `boto3`、`botocore`、`httpx`、`requests`、provider client を import しない。  `source:06_functions_queries_and_resources.md:17`
- [ ] `RULE-06_FUNCTIONS_QUERIES_AND_RESOURCES-L018-09` **MUST NOT** `[checker:functions_resource_usage]` resource を使わない非 validation 関数を `@resource-free` marker なしで追加しない。  `source:06_functions_queries_and_resources.md:18`

<!-- rulecheck:generated-checklist:end -->
