# 11. 数値閾値

解釈が分かれる表現を避けるため、ネスト、循環的複雑度、関数長、ファイル長、引数数、条件式を数値で制限する。

## 実装すべき内容

- `src/app/apis/**/router.py` の関数は循環的複雑度を `17` 以下にする。
- `src/app/**/*.py` の関数は循環的複雑度を `17` 以下にする。
- `src/tools/**/*.py` の関数は循環的複雑度を `21` 以下にする。
- `src/app/apis/**/router.py` の関数は制御構造ネスト深度を `5` 以下にする。
- `src/app/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。
- `src/tools/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。
- `src/app/apis/**/router.py` の関数は論理行数を `450` 以下にする。
- `src/app/**/*.py` の関数は論理行数を `450` 以下にする。
- `src/tools/**/*.py` の関数は論理行数を `160` 以下にする。
- `src/app/apis/**/router.py` のファイルは論理行数を `550` 以下にする。
- `src/app/**/*.py` のファイルは論理行数を `800` 以下にする。
- `src/tools/**/*.py` のファイルは論理行数を `1700` 以下にする。
- `src/app/apis/**/router.py` の関数引数数は `20` 以下にする。
- `src/app/**/*.py` の関数引数数は `20` 以下にする。
- `src/tools/**/*.py` の関数引数数は `12` 以下にする。
- `src/app/**/*.py` の関数内 `return` 文数は `12` 以下にする。
- `src/tools/**/*.py` の関数内 `return` 文数は `12` 以下にする。
- `if`、`while`、`assert`、三項式の条件式に含める `and` と `or` の演算子数は合計 `3` 以下にする。
- 条件式に含める比較演算子数は `4` 以下にする。
- 条件式 AST 深度は `9` 以下にする。

## 実装してはいけない内容

- 三項式の中に三項式を入れない。
- `src/app/**/*.py` で制御構造を 6 層にしない。

## 機械チェック項目

| Rule ID | Level | Checker | 対象 | 判定条件 |
| :--- | :--- | :--- | :--- | :--- |
| METRICS-DO-001 | MUST | `python_complexity` | - | `src/app/apis/**/router.py` の関数は循環的複雑度を `17` 以下にする。 |
| METRICS-DO-002 | MUST | `python_complexity` | - | `src/app/**/*.py` の関数は循環的複雑度を `17` 以下にする。 |
| METRICS-DO-003 | MUST | `python_complexity` | - | `src/tools/**/*.py` の関数は循環的複雑度を `21` 以下にする。 |
| METRICS-DO-004 | MUST | `control_nesting_depth` | - | `src/app/apis/**/router.py` の関数は制御構造ネスト深度を `5` 以下にする。 |
| METRICS-DO-005 | MUST | `control_nesting_depth` | - | `src/app/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。 |
| METRICS-DO-006 | MUST | `control_nesting_depth` | - | `src/tools/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。 |
| METRICS-DO-007 | MUST | `function_logical_lines` | - | `src/app/apis/**/router.py` の関数は論理行数を `450` 以下にする。 |
| METRICS-DO-008 | MUST | `function_logical_lines` | - | `src/app/**/*.py` の関数は論理行数を `450` 以下にする。 |
| METRICS-DO-009 | MUST | `function_logical_lines` | - | `src/tools/**/*.py` の関数は論理行数を `160` 以下にする。 |
| METRICS-DO-010 | MUST | `file_logical_lines` | - | `src/app/apis/**/router.py` のファイルは論理行数を `550` 以下にする。 |
| METRICS-DO-011 | MUST | `file_logical_lines` | - | `src/app/**/*.py` のファイルは論理行数を `800` 以下にする。 |
| METRICS-DO-012 | MUST | `file_logical_lines` | - | `src/tools/**/*.py` のファイルは論理行数を `1700` 以下にする。 |
| METRICS-DO-013 | MUST | `function_argument_count` | - | `src/app/apis/**/router.py` の関数引数数は `20` 以下にする。 |
| METRICS-DO-014 | MUST | `function_argument_count` | - | `src/app/**/*.py` の関数引数数は `20` 以下にする。 |
| METRICS-DO-015 | MUST | `function_argument_count` | - | `src/tools/**/*.py` の関数引数数は `12` 以下にする。 |
| METRICS-DO-016 | MUST | `return_count` | - | `src/app/**/*.py` の関数内 `return` 文数は `12` 以下にする。 |
| METRICS-DO-017 | MUST | `return_count` | - | `src/tools/**/*.py` の関数内 `return` 文数は `12` 以下にする。 |
| METRICS-DO-018 | MUST | `condition_complexity` | - | `if`、`while`、`assert`、三項式の条件式に含める `and` と `or` の演算子数は合計 `3` 以下にする。 |
| METRICS-DO-019 | MUST | `condition_complexity` | - | 条件式に含める比較演算子数は `4` 以下にする。 |
| METRICS-DO-020 | MUST | `condition_complexity` | - | 条件式 AST 深度は `9` 以下にする。 |
| METRICS-DONT-001 | MUST NOT | `condition_complexity` | - | 三項式の中に三項式を入れない。 |
| METRICS-DONT-002 | MUST NOT | `control_nesting_depth` | - | `src/app/**/*.py` で制御構造を 6 層にしない。 |

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `src/app/apis/**/router.py` の関数は循環的複雑度を `17` 以下にする。 (`METRICS-DO-001`, **MUST**, `[checker:python_complexity]`)  `source:11_quantitative_thresholds.md:37`
- [ ] `src/app/**/*.py` の関数は循環的複雑度を `17` 以下にする。 (`METRICS-DO-002`, **MUST**, `[checker:python_complexity]`)  `source:11_quantitative_thresholds.md:38`
- [ ] `src/tools/**/*.py` の関数は循環的複雑度を `21` 以下にする。 (`METRICS-DO-003`, **MUST**, `[checker:python_complexity]`)  `source:11_quantitative_thresholds.md:39`
- [ ] `src/app/apis/**/router.py` の関数は制御構造ネスト深度を `5` 以下にする。 (`METRICS-DO-004`, **MUST**, `[checker:control_nesting_depth]`)  `source:11_quantitative_thresholds.md:40`
- [ ] `src/app/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。 (`METRICS-DO-005`, **MUST**, `[checker:control_nesting_depth]`)  `source:11_quantitative_thresholds.md:41`
- [ ] `src/tools/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。 (`METRICS-DO-006`, **MUST**, `[checker:control_nesting_depth]`)  `source:11_quantitative_thresholds.md:42`
- [ ] `src/app/apis/**/router.py` の関数は論理行数を `450` 以下にする。 (`METRICS-DO-007`, **MUST**, `[checker:function_logical_lines]`)  `source:11_quantitative_thresholds.md:43`
- [ ] `src/app/**/*.py` の関数は論理行数を `450` 以下にする。 (`METRICS-DO-008`, **MUST**, `[checker:function_logical_lines]`)  `source:11_quantitative_thresholds.md:44`
- [ ] `src/tools/**/*.py` の関数は論理行数を `160` 以下にする。 (`METRICS-DO-009`, **MUST**, `[checker:function_logical_lines]`)  `source:11_quantitative_thresholds.md:45`
- [ ] `src/app/apis/**/router.py` のファイルは論理行数を `550` 以下にする。 (`METRICS-DO-010`, **MUST**, `[checker:file_logical_lines]`)  `source:11_quantitative_thresholds.md:46`
- [ ] `src/app/**/*.py` のファイルは論理行数を `800` 以下にする。 (`METRICS-DO-011`, **MUST**, `[checker:file_logical_lines]`)  `source:11_quantitative_thresholds.md:47`
- [ ] `src/tools/**/*.py` のファイルは論理行数を `1700` 以下にする。 (`METRICS-DO-012`, **MUST**, `[checker:file_logical_lines]`)  `source:11_quantitative_thresholds.md:48`
- [ ] `src/app/apis/**/router.py` の関数引数数は `20` 以下にする。 (`METRICS-DO-013`, **MUST**, `[checker:function_argument_count]`)  `source:11_quantitative_thresholds.md:49`
- [ ] `src/app/**/*.py` の関数引数数は `20` 以下にする。 (`METRICS-DO-014`, **MUST**, `[checker:function_argument_count]`)  `source:11_quantitative_thresholds.md:50`
- [ ] `src/tools/**/*.py` の関数引数数は `12` 以下にする。 (`METRICS-DO-015`, **MUST**, `[checker:function_argument_count]`)  `source:11_quantitative_thresholds.md:51`
- [ ] `src/app/**/*.py` の関数内 `return` 文数は `12` 以下にする。 (`METRICS-DO-016`, **MUST**, `[checker:return_count]`)  `source:11_quantitative_thresholds.md:52`
- [ ] `src/tools/**/*.py` の関数内 `return` 文数は `12` 以下にする。 (`METRICS-DO-017`, **MUST**, `[checker:return_count]`)  `source:11_quantitative_thresholds.md:53`
- [ ] `if`、`while`、`assert`、三項式の条件式に含める `and` と `or` の演算子数は合計 `3` 以下にする。 (`METRICS-DO-018`, **MUST**, `[checker:condition_complexity]`)  `source:11_quantitative_thresholds.md:54`
- [ ] 条件式に含める比較演算子数は `4` 以下にする。 (`METRICS-DO-019`, **MUST**, `[checker:condition_complexity]`)  `source:11_quantitative_thresholds.md:55`
- [ ] 条件式 AST 深度は `9` 以下にする。 (`METRICS-DO-020`, **MUST**, `[checker:condition_complexity]`)  `source:11_quantitative_thresholds.md:56`
- [ ] 三項式の中に三項式を入れない。 (`METRICS-DONT-001`, **MUST NOT**, `[checker:condition_complexity]`)  `source:11_quantitative_thresholds.md:57`
- [ ] `src/app/**/*.py` で制御構造を 6 層にしない。 (`METRICS-DONT-002`, **MUST NOT**, `[checker:control_nesting_depth]`)  `source:11_quantitative_thresholds.md:58`

<!-- rulecheck:generated-checklist:end -->
