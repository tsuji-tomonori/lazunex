# 11. 数値閾値

解釈が分かれる表現を避けるため、ネスト、循環的複雑度、関数長、ファイル長、引数数、条件式を数値で制限する。

## 実装すべき内容

- **MUST** `[checker:python_complexity]`: `src/app/apis/**/router.py` の関数は循環的複雑度を `17` 以下にする。
- **MUST** `[checker:python_complexity]`: `src/app/**/*.py` の関数は循環的複雑度を `17` 以下にする。
- **MUST** `[checker:python_complexity]`: `src/tools/**/*.py` の関数は循環的複雑度を `21` 以下にする。
- **MUST** `[checker:control_nesting_depth]`: `src/app/apis/**/router.py` の関数は制御構造ネスト深度を `5` 以下にする。
- **MUST** `[checker:control_nesting_depth]`: `src/app/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。
- **MUST** `[checker:control_nesting_depth]`: `src/tools/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。
- **MUST** `[checker:function_logical_lines]`: `src/app/apis/**/router.py` の関数は論理行数を `450` 以下にする。
- **MUST** `[checker:function_logical_lines]`: `src/app/**/*.py` の関数は論理行数を `450` 以下にする。
- **MUST** `[checker:function_logical_lines]`: `src/tools/**/*.py` の関数は論理行数を `160` 以下にする。
- **MUST** `[checker:file_logical_lines]`: `src/app/apis/**/router.py` のファイルは論理行数を `550` 以下にする。
- **MUST** `[checker:file_logical_lines]`: `src/app/**/*.py` のファイルは論理行数を `800` 以下にする。
- **MUST** `[checker:file_logical_lines]`: `src/tools/**/*.py` のファイルは論理行数を `1700` 以下にする。
- **MUST** `[checker:function_argument_count]`: `src/app/apis/**/router.py` の関数引数数は `20` 以下にする。
- **MUST** `[checker:function_argument_count]`: `src/app/**/*.py` の関数引数数は `20` 以下にする。
- **MUST** `[checker:function_argument_count]`: `src/tools/**/*.py` の関数引数数は `12` 以下にする。
- **MUST** `[checker:return_count]`: `src/app/**/*.py` の関数内 `return` 文数は `12` 以下にする。
- **MUST** `[checker:return_count]`: `src/tools/**/*.py` の関数内 `return` 文数は `12` 以下にする。
- **MUST** `[checker:condition_complexity]`: `if`、`while`、`assert`、三項式の条件式に含める `and` と `or` の演算子数は合計 `3` 以下にする。
- **MUST** `[checker:condition_complexity]`: 条件式に含める比較演算子数は `4` 以下にする。
- **MUST** `[checker:condition_complexity]`: 条件式 AST 深度は `9` 以下にする。

## 実装してはいけない内容

- **MUST NOT** `[checker:condition_complexity]`: 三項式の中に三項式を入れない。
- **MUST NOT** `[checker:control_nesting_depth]`: `src/app/**/*.py` で制御構造を 6 層にしない。

<!-- rulecheck:generated-checklist:start -->

## 自動生成チェックリスト

- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L007-01` **MUST** `[checker:python_complexity]` `src/app/apis/**/router.py` の関数は循環的複雑度を `17` 以下にする。  `source:11_quantitative_thresholds.md:7`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L008-02` **MUST** `[checker:python_complexity]` `src/app/**/*.py` の関数は循環的複雑度を `17` 以下にする。  `source:11_quantitative_thresholds.md:8`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L009-03` **MUST** `[checker:python_complexity]` `src/tools/**/*.py` の関数は循環的複雑度を `21` 以下にする。  `source:11_quantitative_thresholds.md:9`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L010-04` **MUST** `[checker:control_nesting_depth]` `src/app/apis/**/router.py` の関数は制御構造ネスト深度を `5` 以下にする。  `source:11_quantitative_thresholds.md:10`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L011-05` **MUST** `[checker:control_nesting_depth]` `src/app/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。  `source:11_quantitative_thresholds.md:11`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L012-06` **MUST** `[checker:control_nesting_depth]` `src/tools/**/*.py` の関数は制御構造ネスト深度を `5` 以下にする。  `source:11_quantitative_thresholds.md:12`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L013-07` **MUST** `[checker:function_logical_lines]` `src/app/apis/**/router.py` の関数は論理行数を `450` 以下にする。  `source:11_quantitative_thresholds.md:13`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L014-08` **MUST** `[checker:function_logical_lines]` `src/app/**/*.py` の関数は論理行数を `450` 以下にする。  `source:11_quantitative_thresholds.md:14`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L015-09` **MUST** `[checker:function_logical_lines]` `src/tools/**/*.py` の関数は論理行数を `160` 以下にする。  `source:11_quantitative_thresholds.md:15`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L016-10` **MUST** `[checker:file_logical_lines]` `src/app/apis/**/router.py` のファイルは論理行数を `550` 以下にする。  `source:11_quantitative_thresholds.md:16`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L017-11` **MUST** `[checker:file_logical_lines]` `src/app/**/*.py` のファイルは論理行数を `800` 以下にする。  `source:11_quantitative_thresholds.md:17`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L018-12` **MUST** `[checker:file_logical_lines]` `src/tools/**/*.py` のファイルは論理行数を `1700` 以下にする。  `source:11_quantitative_thresholds.md:18`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L019-13` **MUST** `[checker:function_argument_count]` `src/app/apis/**/router.py` の関数引数数は `20` 以下にする。  `source:11_quantitative_thresholds.md:19`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L020-14` **MUST** `[checker:function_argument_count]` `src/app/**/*.py` の関数引数数は `20` 以下にする。  `source:11_quantitative_thresholds.md:20`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L021-15` **MUST** `[checker:function_argument_count]` `src/tools/**/*.py` の関数引数数は `12` 以下にする。  `source:11_quantitative_thresholds.md:21`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L022-16` **MUST** `[checker:return_count]` `src/app/**/*.py` の関数内 `return` 文数は `12` 以下にする。  `source:11_quantitative_thresholds.md:22`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L023-17` **MUST** `[checker:return_count]` `src/tools/**/*.py` の関数内 `return` 文数は `12` 以下にする。  `source:11_quantitative_thresholds.md:23`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L024-18` **MUST** `[checker:condition_complexity]` `if`、`while`、`assert`、三項式の条件式に含める `and` と `or` の演算子数は合計 `3` 以下にする。  `source:11_quantitative_thresholds.md:24`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L025-19` **MUST** `[checker:condition_complexity]` 条件式に含める比較演算子数は `4` 以下にする。  `source:11_quantitative_thresholds.md:25`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L026-20` **MUST** `[checker:condition_complexity]` 条件式 AST 深度は `9` 以下にする。  `source:11_quantitative_thresholds.md:26`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L030-21` **MUST NOT** `[checker:condition_complexity]` 三項式の中に三項式を入れない。  `source:11_quantitative_thresholds.md:30`
- [ ] `RULE-11_QUANTITATIVE_THRESHOLDS-L031-22` **MUST NOT** `[checker:control_nesting_depth]` `src/app/**/*.py` で制御構造を 6 層にしない。  `source:11_quantitative_thresholds.md:31`

<!-- rulecheck:generated-checklist:end -->
