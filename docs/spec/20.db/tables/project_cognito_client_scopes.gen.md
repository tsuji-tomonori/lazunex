# project_cognito_client_scopes

承認時にCognito App Clientへ付与したAPI scopeの紐づけを表す。状態はclient_scope_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `project_cognito_client_scope_id` | `CHAR(36)` | NO | PK | App Client scope紐づけID。 |
| `project_id` | `CHAR(36)` | NO | FK -> projects(project_id) | 紐づくProject ID。 |
| `project_cognito_client_id` | `CHAR(36)` | NO | FK -> project_cognito_clients(project_cognito_client_id) | scopeを付与したProject App Client ID。 |
| `api_scope_id` | `CHAR(36)` | NO | FK -> api_cognito_scopes(api_scope_id) | 付与したAPI Scope ID。 |
| `subscription_id` | `CHAR(36)` | NO | FK -> project_api_subscriptions(subscription_id) | scope付与の元になった利用権ID。 |
| `scope_full_name` | `VARCHAR(600)` | NO |  | Resource Server識別子を含むscope名。 |
| `granted_at` | `DATETIME(6)` | YES |  | Cognito App Clientへscopeを付与した日時。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |

## テーブル制約

- `UNIQUE (project_cognito_client_id, api_scope_id)`
