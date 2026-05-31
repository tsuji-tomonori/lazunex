# provisioning_operations

CognitoやAPI GatewayなどAWSリソース反映処理の親operationを表す。同期実行でも記録する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `operation_id` | `UUID` | NO | PK | AWS反映operation ID。 |
| `idempotency_key` | `VARCHAR(200)` | NO | UNIQUE | 冪等性キー。 |
| `operation_type` | `VARCHAR(50)` | NO |  | operation種別。PUBLISH_API、CREATE_PROJECT、UPDATE_PUBLIC_CLIENT、APPROVE_ACCESS、REJECT_ACCESS。 |
| `target_type` | `VARCHAR(50)` | NO |  | 対象種別。API、PROJECT、ACCESS_REQUEST。 |
| `target_id` | `UUID` | YES |  | 対象ID。作成前など未確定の場合はNULL。 |
| `request_payload` | `JSON` | NO |  | 入力内容の記録。secret値は含めない。 |
| `result_payload` | `JSON` | YES |  | 結果summary。secret値は含めない。 |
| `retry_count` | `INT` | NO |  | 同期再実行を含むリトライ回数。 |
| `created_at` | `TIMESTAMPTZ` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `TIMESTAMPTZ` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
