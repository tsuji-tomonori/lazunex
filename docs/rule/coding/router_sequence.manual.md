# Router Sequence Coding Rule

## 目的

`src/app/apis/{domain}/{api}/router.py` は、FastAPI endpoint と sequence 仕様生成の入力を兼ねる。
router 層には API の入口定義と処理順だけを書き、業務判断、SQL、外部 API 呼び出し、
ログ出力、複雑なデータ加工は `functions.py` へ閉じる。

## 必須ルール

- `router.py` は同一 API ディレクトリの `functions.py` を `api_functions` alias で import する。
- endpoint body は `await api_functions.{action}_{target}(...)` または
  `return await api_functions.build_{target}(...)` を上から順に並べる。
- 関数名は `docs/rule/docs/sequence_function_*.json` で定義された語彙だけを使う。
- `functions.py` の public function には、sequence message に使う日本語 docstring を必ず書く。
- `functions.py` の public function は、引数と戻り値の型注釈を明記する。
- path parameter の resource ID は `app.apis.types.ResourceId` を使う。
- response は最後の `build_*` 関数で生成し、router 内で dict/list を直接組み立てない。
- permission や状態判定は `has_*` / `is_*` 関数として呼び、router 内で比較条件を展開しない。
- 生成される sequence では、endpoint を API 要素、`src/app/integrations/{resource}` に
  定義された外部境界だけを Resource 要素、`sql/*.sql` から抽出したテーブルアクセスを
  DB 要素として扱う。

## 許可構文

```text
assignment = await api_functions.function_name(...)
await api_functions.function_name(...)
return await api_functions.function_name(...)
```

必要な場合に限り、`.workspace/spec_03.md` の基本設計に従って以下も許可する。

```text
if predicate_function(...)
for item in items
try-except NonBlockingOperationalError
continue
```

## 禁止事項

- SQL 直接実行
- `httpx`、`requests`、AWS SDK、provider SDK の直接 import
- logger の直接呼び出し
- `except Exception` などの汎用例外 catch
- inline 比較による業務判断
- dict/list の複雑な加工
- `functions.py` 以外の service/helper に処理順を分散すること

## Sequence 生成との対応

- router endpoint 名を sequence の API participant とする。
- `api_functions.{function_name}` の message label は、`functions.py` の docstring から生成する。
- message label には関数名を出さず、引数と戻り値がある場合は型注釈付きで併記する。
- message label の処理順は Mermaid の `autonumber` で表示し、手動採番しない。
- `api_functions.{function_name}` 1 呼び出しにつき sequence の線は 1 本だけ出す。
- `{action}_{target}` の `target` が `src/app/integrations/{resource}` または
  `{resource}_*` に一致する場合だけ、該当 integration を Resource participant とする。
- integration に一致しない `{action}_{target}` は API 内部処理として `API->>API` で出す。
- `{is|has}_{condition}` は resource participant にせず、docstring 由来の日本語条件を
  Mermaid の `alt` 条件として出す。
- `src/app/apis/{domain}/{api}/sql/*.sql` に出現する table 名は個別 participant にせず、
  `DB` participant への SQL ファイル単位の message として、SQL ファイル名と table 名を併記する。

## 検証

- `uv run python -m tools.check_api_function_names`
- `uv run python -m tools.generate_api_sequences --check`
- `uv run python -m tools.check_api_mermaid_sequences`
- `uv run pytest tests/tools/test_generate_api_sequences.py`
