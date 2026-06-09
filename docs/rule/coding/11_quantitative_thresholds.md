# 11. 数値閾値

解釈が分かれる表現を避けるため、ネスト、循環的複雑度、関数長、ファイル長、引数数、条件式を数値で制限する。

この規約は、現行コードに適用する移行値と、設計上の最終推奨値を分ける。機械チェックは移行値を使い、生成 Python は論理行数や関数長ではなく再生成差分、型、契約整合で検査する。

## 適用対象

- `src/app/**/generated/**/*.py` は数値メトリクスの対象外にする。
- `tests/generated/**/*.py` は数値メトリクスの対象外にする。

## 実装すべき内容

- `src/app/apis/**/router.py` の endpoint 関数は循環的複雑度を `10` 以下にする。
- `src/app/**/*.py` の関数は循環的複雑度を `10` 以下にする。
- `src/tools/**/*.py` の関数は循環的複雑度を `12` 以下にする。
- `src/app/apis/**/router.py` の endpoint 関数は制御構造ネスト深度を `3` 以下にする。
- `src/app/**/*.py` の関数は制御構造ネスト深度を `3` 以下にする。
- `src/tools/**/*.py` の関数は制御構造ネスト深度を `4` 以下にする。
- `src/app/apis/**/router.py` の endpoint 関数は論理行数を `120` 以下にする。
- `src/app/**/*.py` の関数は論理行数を `100` 以下にする。
- `src/tools/**/*.py` の関数は論理行数を `120` 以下にする。
- `src/app/apis/**/router.py` のファイルは論理行数を `260` 以下にする。
- `src/app/**/*.py` の manual ファイルは論理行数を `600` 以下にする。
- `src/tools/**/*.py` のファイルは論理行数を `1000` 以下にする。
- `src/app/apis/**/router.py` の endpoint 関数は総引数数を `8` 以下にする。
- `src/app/apis/**/router.py` の endpoint 関数は業務引数数を `3` 以下にする。
- `src/app/**/*.py` の public 関数は引数数を `5` 以下にする。
- `src/app/**/*.py` の private helper 関数は引数数を `5` 以下にする。
- `src/tools/**/*.py` の通常関数は引数数を `6` 以下にする。
- `src/tools/**/*.py` の CLI adapter 関数は引数数を `8` 以下にする。
- `src/app/apis/**/router.py` の endpoint 関数内 `return` 文数は `6` 以下にする。
- `src/app/**/*.py` の関数内 `return` 文数は `6` 以下にする。
- `src/tools/**/*.py` の関数内 `return` 文数は `8` 以下にする。
- `src/app/apis/**/router.py` の `try` body statement 数は `5` 以下にする。
- `src/app/**/*.py` の local variable 数は `10` 以下にする。
- `src/tools/**/*.py` の local variable 数は `15` 以下にする。
- `src/app/apis/**/router.py` の branch 数は `4` 以下にする。
- `src/app/**/*.py` の branch 数は `8` 以下にする。
- `src/tools/**/*.py` の branch 数は `10` 以下にする。
- `src/app/apis/**/router.py` の条件式に含める `and` と `or` の演算子数は合計 `1` 以下にする。
- `src/app/**/*.py` と `src/tools/**/*.py` の条件式に含める `and` と `or` の演算子数は合計 `3` 以下にする。
- 条件式に含める比較演算子数は `3` 以下にする。
- 条件式 AST 深度は `7` 以下にする。

## 実装してはいけない内容

- 三項式の中に三項式を入れる。
- `src/app/**/*.py` で制御構造を `4` 層以上にする。
- `src/tools/**/*.py` で制御構造を `5` 層以上にする。

## 最終推奨値

| 項目 | 最終推奨値 |
| :--- | ---: |
| `src/app/apis/**/router.py` endpoint 循環的複雑度 | `5` |
| `src/app/**/*.py` 関数循環的複雑度 | `8` |
| `src/tools/**/*.py` 関数循環的複雑度 | `10` |
| `src/app/apis/**/router.py` endpoint ネスト深度 | `2` |
| `src/app/**/*.py` 関数ネスト深度 | `2` |
| `src/tools/**/*.py` 関数ネスト深度 | `3` |
| `src/app/apis/**/router.py` endpoint 論理行数 | `60` |
| `src/app/**/*.py` 関数論理行数 | `50` |
| `src/tools/**/*.py` 関数論理行数 | `80` |
| `src/app/apis/**/router.py` ファイル論理行数 | `220` |
| `src/app/**/*.py` manual ファイル論理行数 | `400` |
| `src/tools/**/*.py` ファイル論理行数 | `800` |
| `src/app/apis/**/router.py` endpoint 総引数数 | `3` |
| `src/app/apis/**/router.py` endpoint 業務引数数 | `3` |
| `src/app/**/*.py` public 関数引数数 | `3` |
| `src/app/**/*.py` private helper 関数引数数 | `4` |
| `src/tools/**/*.py` 通常関数引数数 | `4` |
| `src/tools/**/*.py` CLI adapter 関数引数数 | `6` |
| `src/app/apis/**/router.py` endpoint `return` 文数 | `6` |
| `src/app/**/*.py` 関数 `return` 文数 | `4` |
| `src/tools/**/*.py` 関数 `return` 文数 | `6` |
| `src/app/apis/**/router.py` `try` body statement 数 | `5` |
| `src/app/**/*.py` local variable 数 | `10` |
| `src/tools/**/*.py` local variable 数 | `15` |
| `src/app/apis/**/router.py` branch 数 | `4` |
| `src/app/**/*.py` branch 数 | `8` |
| `src/tools/**/*.py` branch 数 | `10` |
| `src/app/apis/**/router.py` 条件式 `and` / `or` 演算子数 | `1` |
| `src/app/**/*.py` と `src/tools/**/*.py` 条件式 `and` / `or` 演算子数 | `2` |
| 条件式比較演算子数 | `2` |
| 条件式 AST 深度 | `6` |

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| METRICS-DO-001 | MUST | `python_complexity` | - | `src/app/apis/**/router.py` の endpoint 関数は循環的複雑度を `10` 以下にする。 |
| METRICS-DO-002 | MUST | `python_complexity` | - | `src/app/**/*.py` の関数は循環的複雑度を `10` 以下にする。 |
| METRICS-DO-003 | MUST | `python_complexity` | - | `src/tools/**/*.py` の関数は循環的複雑度を `12` 以下にする。 |
| METRICS-DO-004 | MUST | `control_nesting_depth` | - | `src/app/apis/**/router.py` の endpoint 関数は制御構造ネスト深度を `3` 以下にする。 |
| METRICS-DO-005 | MUST | `control_nesting_depth` | - | `src/app/**/*.py` の関数は制御構造ネスト深度を `3` 以下にする。 |
| METRICS-DO-006 | MUST | `control_nesting_depth` | - | `src/tools/**/*.py` の関数は制御構造ネスト深度を `4` 以下にする。 |
| METRICS-DO-007 | MUST | `function_logical_lines` | - | `src/app/apis/**/router.py` の endpoint 関数は論理行数を `120` 以下にする。 |
| METRICS-DO-008 | MUST | `function_logical_lines` | - | `src/app/**/*.py` の関数は論理行数を `100` 以下にする。 |
| METRICS-DO-009 | MUST | `function_logical_lines` | - | `src/tools/**/*.py` の関数は論理行数を `120` 以下にする。 |
| METRICS-DO-010 | MUST | `file_logical_lines` | - | `src/app/apis/**/router.py` のファイルは論理行数を `260` 以下にする。 |
| METRICS-DO-011 | MUST | `file_logical_lines` | - | `src/app/**/*.py` の manual ファイルは論理行数を `600` 以下にする。 |
| METRICS-DO-012 | MUST | `file_logical_lines` | - | `src/tools/**/*.py` のファイルは論理行数を `1000` 以下にする。 |
| METRICS-DO-013 | MUST | `function_argument_count` | - | `src/app/apis/**/router.py` の endpoint 関数は総引数数を `8` 以下にする。 |
| METRICS-DO-014 | MUST | `endpoint_business_argument_count` | - | `src/app/apis/**/router.py` の endpoint 関数は業務引数数を `3` 以下にする。 |
| METRICS-DO-015 | MUST | `function_argument_count` | - | `src/app/**/*.py` の public 関数は引数数を `5` 以下にする。 |
| METRICS-DO-016 | MUST | `function_argument_count` | - | `src/app/**/*.py` の private helper 関数は引数数を `5` 以下にする。 |
| METRICS-DO-017 | MUST | `function_argument_count` | - | `src/tools/**/*.py` の通常関数は引数数を `6` 以下にする。 |
| METRICS-DO-018 | MUST | `function_argument_count` | - | `src/tools/**/*.py` の CLI adapter 関数は引数数を `8` 以下にする。 |
| METRICS-DO-019 | MUST | `return_count` | - | `src/app/apis/**/router.py` の endpoint 関数内 `return` 文数は `6` 以下にする。 |
| METRICS-DO-020 | MUST | `return_count` | - | `src/app/**/*.py` の関数内 `return` 文数は `6` 以下にする。 |
| METRICS-DO-021 | MUST | `return_count` | - | `src/tools/**/*.py` の関数内 `return` 文数は `8` 以下にする。 |
| METRICS-DO-022 | MUST | `try_body_statement_count` | - | `src/app/apis/**/router.py` の `try` body statement 数は `5` 以下にする。 |
| METRICS-DO-023 | MUST | `local_variable_count` | - | `src/app/**/*.py` の local variable 数は `10` 以下にする。 |
| METRICS-DO-024 | MUST | `local_variable_count` | - | `src/tools/**/*.py` の local variable 数は `15` 以下にする。 |
| METRICS-DO-025 | MUST | `branch_count` | - | `src/app/apis/**/router.py` の branch 数は `4` 以下にする。 |
| METRICS-DO-026 | MUST | `branch_count` | - | `src/app/**/*.py` の branch 数は `8` 以下にする。 |
| METRICS-DO-027 | MUST | `branch_count` | - | `src/tools/**/*.py` の branch 数は `10` 以下にする。 |
| METRICS-DO-028 | MUST | `condition_complexity` | - | `src/app/apis/**/router.py` の条件式に含める `and` と `or` の演算子数は合計 `1` 以下にする。 |
| METRICS-DO-029 | MUST | `condition_complexity` | - | `src/app/**/*.py` と `src/tools/**/*.py` の条件式に含める `and` と `or` の演算子数は合計 `3` 以下にする。 |
| METRICS-DO-030 | MUST | `condition_complexity` | - | 条件式に含める比較演算子数は `3` 以下にする。 |
| METRICS-DO-031 | MUST | `condition_complexity` | - | 条件式 AST 深度は `7` 以下にする。 |
| METRICS-DONT-001 | MUST NOT | `condition_complexity` | - | 三項式の中に三項式を入れる。 |
| METRICS-DONT-002 | MUST NOT | `control_nesting_depth` | - | `src/app/**/*.py` で制御構造を `4` 層以上にする。 |
| METRICS-DONT-003 | MUST NOT | `control_nesting_depth` | - | `src/tools/**/*.py` で制御構造を `5` 層以上にする。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

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
