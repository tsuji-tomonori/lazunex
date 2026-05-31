# audit_events

誰が、いつ、何に対して、どの操作を行ったかを追跡する監査イベントを表す。append-onlyで扱う。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `audit_event_id` | `UUID` | NO | PK | 監査イベントID。 |
| `actor_principal_id` | `VARCHAR(256)` | NO |  | 操作した主体のprincipal。 |
| `action` | `VARCHAR(100)` | NO |  | 操作名。例: API_PUBLISHED、PROJECT_CREATED、ACCESS_APPROVED。 |
| `target_type` | `VARCHAR(50)` | NO |  | 操作対象種別。API、PROJECT、ACCESS_REQUEST。 |
| `target_id` | `UUID` | NO |  | 操作対象ID。 |
| `operation_id` | `UUID` | YES | FK -> provisioning_operations(operation_id) | 関連するAWS反映operation ID。 |
| `source_ip` | `VARCHAR(64)` | YES |  | 呼び出し元IPアドレス。 |
| `user_agent` | `TEXT` | YES |  | 呼び出し元User-Agent。 |
| `details` | `JSON` | YES |  | 監査用の詳細情報。secret値は含めない。 |
| `created_at` | `TIMESTAMPTZ` | NO |  | 監査イベント発生日時。 |
