# project_cognito_clients

Projectごとのpublicまたはconfidential Cognito App Clientを表す。client secret平文は保存しない。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `project_cognito_client_id` | `UUID` | NO | PK | Project App Client ID。 |
| `project_id` | `UUID` | NO | FK -> projects(project_id) | 紐づくProject ID。 |
| `client_type` | `VARCHAR(40)` | NO |  | App Client種別。PUBLIC_PKCEまたはCONFIDENTIAL_CLIENT_CREDENTIALS。 |
| `cognito_user_pool_id` | `VARCHAR(55)` | NO |  | Cognito User Pool ID。 |
| `app_client_id` | `VARCHAR(128)` | NO | UNIQUE | Cognito App Client ID。 |
| `app_client_name` | `VARCHAR(128)` | NO |  | Cognito App Client名。 |
| `generate_secret` | `BOOLEAN` | NO |  | Cognito App Client作成時にclient secretを生成するかどうか。publicではfalse、confidentialではtrue。 |
| `client_secret_value_hash` | `VARCHAR(128)` | YES |  | client secret値のHMAC-SHA256などによるハッシュ。publicではNULL。 |
| `client_secret_hash_key_version` | `INT` | YES |  | client secret値のハッシュ化に使ったpepperのバージョン。publicではNULL。 |
| `client_secret_last4` | `VARCHAR(8)` | YES |  | client secret値の末尾表示用文字列。publicではNULL。 |
| `allowed_oauth_flows` | `JSON` | NO |  | 許可するOAuthフロー。例: code、client_credentials。 |
| `base_allowed_scopes` | `JSON` | NO |  | 初期状態で許可するscope。例: openid、email、profile。 |
| `access_token_validity` | `INT` | NO |  | access tokenの有効期間の値。 |
| `access_token_unit` | `VARCHAR(10)` | NO |  | access tokenの有効期間単位。minutes、hours、days。 |
| `id_token_validity` | `INT` | YES |  | id tokenの有効期間の値。public client向け。 |
| `id_token_unit` | `VARCHAR(10)` | YES |  | id tokenの有効期間単位。public client向け。 |
| `refresh_token_validity` | `INT` | YES |  | refresh tokenの有効期間の値。public client向け。 |
| `refresh_token_unit` | `VARCHAR(10)` | YES |  | refresh tokenの有効期間単位。public client向け。 |
| `refresh_token_rotation_enabled` | `BOOLEAN` | NO |  | refresh token rotationを有効にするかどうか。 |
| `retry_grace_period_seconds` | `INT` | YES |  | refresh token rotationの再試行猶予秒数。 |
| `enable_token_revocation` | `BOOLEAN` | NO |  | token revocationを有効にするかどうか。 |
| `last_synced_at` | `TIMESTAMPTZ` | YES |  | Cognitoとの最終同期日時。 |
| `created_at` | `TIMESTAMPTZ` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `TIMESTAMPTZ` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |

## テーブル制約

- `UNIQUE (project_id, client_type)`
