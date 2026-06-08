# project_api_keys

ProjectごとのAPI Gateway API Keyの識別子、ハッシュ、末尾表示情報を表す。平文のAPI key値は保存しない。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `project_api_key_id` | `CHAR(36)` | NO | PK | Project API Key ID。 |
| `project_id` | `CHAR(36)` | NO | UNIQUE, FK -> projects(project_id) | 紐づくProject ID。1 Projectにつき1 API key。 |
| `aws_account_id` | `VARCHAR(12)` | NO |  | API keyが存在するAWSアカウントID。 |
| `aws_region` | `VARCHAR(32)` | NO |  | API keyが存在するAWSリージョン。 |
| `apigw_api_key_id` | `VARCHAR(128)` | NO | UNIQUE | API Gateway API Key ID。 |
| `apigw_api_key_name` | `VARCHAR(255)` | NO |  | API Gateway API Key名。 |
| `api_key_value_hash` | `VARCHAR(128)` | NO |  | API key値のHMAC-SHA256などによるハッシュ。 |
| `api_key_hash_key_version` | `INT` | NO |  | API key値のハッシュ化に使ったpepperのバージョン。 |
| `api_key_last4` | `VARCHAR(8)` | NO |  | API key値の末尾表示用文字列。 |
| `observed_enabled` | `BOOLEAN` | NO |  | API Gateway上でAPI keyが有効化されているかの観測結果。 |
| `last_synced_at` | `DATETIME(6)` | YES |  | API Gatewayとの最終同期日時。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
