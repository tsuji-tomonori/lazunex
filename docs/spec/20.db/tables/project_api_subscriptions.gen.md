# project_api_subscriptions

承認済みのProjectとAPI stageの利用権を表す。状態はsubscription_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `subscription_id` | `CHAR(36)` | NO | PK | 利用権ID。 |
| `project_id` | `CHAR(36)` | NO | FK -> projects(project_id) | 利用権を持つProject ID。 |
| `api_id` | `CHAR(36)` | NO | FK -> apis(api_id) | 利用可能なAPI ID。 |
| `api_stage_id` | `CHAR(36)` | NO | FK -> api_gateway_stages(api_stage_id) | 利用可能なAPI stage ID。 |
| `access_request_id` | `CHAR(36)` | NO | FK -> api_access_requests(access_request_id) | 利用権の元になった利用申請ID。 |
| `approved_auth_mode` | `VARCHAR(30)` | NO |  | 承認された認証方式。PUBLIC_PKCE、CLIENT_CREDENTIALS、BOTH。 |
| `approved_by` | `VARCHAR(256)` | NO |  | 承認者のprincipal。 |
| `approved_at` | `DATETIME(6)` | NO |  | 承認日時。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |

## テーブル制約

- `UNIQUE (project_id, api_stage_id)`
