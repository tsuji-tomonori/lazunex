# idempotency_records

変更系APIの二重実行を防止するための冪等性記録を表す。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `idempotency_record_id` | `CHAR(36)` | NO | PK | 冪等性記録ID。 |
| `idempotency_key` | `VARCHAR(200)` | NO | UNIQUE | クライアントが指定した冪等性キー。 |
| `request_hash` | `VARCHAR(128)` | NO |  | request bodyのハッシュ。 |
| `operation_id` | `CHAR(36)` | YES | FK -> provisioning_operations(operation_id) | 関連するAWS反映operation ID。 |
| `response_payload` | `JSON` | YES |  | 成功時レスポンスの記録。secret値は初回以降返さない方針に注意する。 |
| `expires_at` | `DATETIME(6)` | NO |  | 冪等性記録の有効期限。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
