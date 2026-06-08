# api_access_requests

ProjectとAPI stageの組み合わせに対する利用申請を表す。状態はaccess_request_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `access_request_id` | `CHAR(36)` | NO | PK | 利用申請ID。 |
| `project_id` | `CHAR(36)` | NO | FK -> projects(project_id) | 申請元Project ID。 |
| `api_id` | `CHAR(36)` | NO | FK -> apis(api_id) | 申請対象API ID。 |
| `api_stage_id` | `CHAR(36)` | NO | FK -> api_gateway_stages(api_stage_id) | 申請対象API stage ID。 |
| `requested_auth_mode` | `VARCHAR(30)` | NO |  | 申請した認証方式。PUBLIC_PKCE、CLIENT_CREDENTIALS、BOTH。 |
| `requested_reason` | `TEXT` | NO |  | 利用申請理由。 |
| `requested_by` | `VARCHAR(256)` | NO |  | 申請者のprincipal。 |
| `requested_at` | `DATETIME(6)` | NO |  | 申請日時。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
