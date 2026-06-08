# 実装者向けチートシート

このページは詳細規約を読む前に、`src/` 実装の置き場所と禁止事項を確認するための入口である。
checker ID や `MUST` の詳細は各規約ファイルの「機械チェック項目」を参照する。

## 実装先の判断

| やりたいこと | 実装先 |
| :--- | :--- |
| HTTP path / method / response code を定義する | `router.py` |
| API の処理順を書く | `router.py` |
| 権限確認や状態判定を行う | `functions.py` |
| DB から取得・更新する | `sql/*.sql` + `queries.py` + `functions.py` |
| response model を組み立てる | `functions.py` の `build_*` |
| 外部 API を呼ぶ | `integrations/{resource}/port.py` 経由 |
| provider SDK payload を組み立てる | `integrations/{resource}/boto3_provider/mapper.py` |
| API request / response 型を定義する | `schemas.py` |
| sample response を定義する | `samples.py` |

## `router.py`

書く:

- FastAPI decorator
- dependency injection
- `api_functions.*` の呼び出し順
- `has_*` / `is_*` による分岐
- operational logging wrapper
- HTTP response 変換

書かない:

- SQL 実行
- provider SDK / HTTP client 呼び出し
- response dict の手組み
- 複雑な業務条件式
- `except Exception`

## `functions.py`

書く:

- 認可判定
- DB query wrapper 呼び出し
- integration port 呼び出し
- response model 組み立て
- sequence message に使う docstring

書かない:

- FastAPI route decorator
- provider SDK direct import
- 生 SQL 文字列
- `HTTPException` の直接 raise

## `sql/*.sql` と `queries.py`

書く:

- `001_select_apis.sql` 形式の SQL ファイル
- `@name` placeholder
- 最初の非空行に `-- ` で始まる処理要約
- generator が出力した operation 直下の `queries.py`

書かない:

- `SELECT *`
- SQLAlchemy `:name` placeholder
- `generated/queries.py`
- 手編集した query wrapper

## integration

書く:

- `port.py` にアプリ側の境界 Protocol
- `schemas.py` に provider 非依存の入出力型
- `deps.py` に dependency provider
- provider 実装を `boto3_provider/client.py` または legacy flat `client.py`

書かない:

- API operation から provider client を直接 import
- provider SDK の例外型や payload 型を API operation へ露出
- `src/app/main.py` から provider 実装を import
