# project_cognito_client_urls

Cognito App Clientに設定するcallback URLとlogout URLを表す。URL差分は行更新とproject_cognito_client_eventsで追跡する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `client_url_id` | `UUID` | NO | PK | App Client URL ID。 |
| `project_cognito_client_id` | `UUID` | NO | FK -> project_cognito_clients(project_cognito_client_id) | 紐づくProject App Client ID。 |
| `url_type` | `VARCHAR(20)` | NO |  | URL種別。CALLBACKまたはLOGOUT。 |
| `url` | `TEXT` | NO |  | callback URLまたはlogout URL。 |
| `created_at` | `TIMESTAMPTZ` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `TIMESTAMPTZ` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |

## テーブル制約

- `UNIQUE (project_cognito_client_id, url_type, url)`
