# apis

APIカタログの親情報を表す。公開、停止、廃止などの状態はapi_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `api_id` | `CHAR(36)` | NO | PK | Lazunex内API ID。 |
| `api_code` | `VARCHAR(100)` | NO | UNIQUE | 人が読めるAPIコード。例: billing-api-v1。 |
| `name` | `VARCHAR(200)` | NO |  | API表示名。 |
| `description` | `TEXT` | NO |  | APIの説明。 |
| `provider_name` | `VARCHAR(200)` | NO |  | API提供チーム名。 |
| `provider_contact` | `VARCHAR(320)` | NO |  | API提供者の問い合わせ先。 |
| `owner_principal_id` | `VARCHAR(256)` | NO |  | APIオーナーのprincipal。 |
| `visibility` | `VARCHAR(20)` | NO |  | 公開範囲。INTERNALまたはRESTRICTED。 |
| `default_api_stage_id` | `CHAR(36)` | YES |  | 既定のAPI stage ID。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
