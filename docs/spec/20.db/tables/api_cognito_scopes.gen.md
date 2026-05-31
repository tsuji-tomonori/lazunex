# api_cognito_scopes

APIごとのCognito custom scopeを表す。削除や無効化の状態はapi_scope_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `api_scope_id` | `UUID` | NO | PK | API scope ID。 |
| `api_id` | `UUID` | NO | UNIQUE, FK -> apis(api_id) | 紐づくAPI ID。 |
| `cognito_user_pool_id` | `VARCHAR(55)` | NO |  | Cognito User Pool ID。 |
| `resource_server_identifier` | `VARCHAR(256)` | NO |  | Cognito Resource Server識別子。例: api-hub。 |
| `scope_name` | `VARCHAR(256)` | NO |  | Resource Server内のscope名。例: api:{apiId}:invoke。 |
| `scope_full_name` | `VARCHAR(600)` | NO | UNIQUE | Resource Server識別子を含むscope名。例: api-hub/api:{apiId}:invoke。 |
| `scope_description` | `VARCHAR(256)` | NO |  | scopeの説明。 |
| `created_at` | `TIMESTAMPTZ` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `TIMESTAMPTZ` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
