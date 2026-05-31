# project_usage_plans

ProjectごとのAPI Gateway Usage Plan情報を表す。ライフサイクルはproject_usage_plan_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `project_usage_plan_id` | `UUID` | NO | PK | Project Usage Plan ID。 |
| `project_id` | `UUID` | NO | UNIQUE, FK -> projects(project_id) | 紐づくProject ID。1 Projectにつき1 Usage Plan。 |
| `aws_account_id` | `VARCHAR(12)` | NO |  | Usage Planが存在するAWSアカウントID。 |
| `aws_region` | `VARCHAR(32)` | NO |  | Usage Planが存在するAWSリージョン。 |
| `apigw_usage_plan_id` | `VARCHAR(128)` | NO | UNIQUE | API Gateway Usage Plan ID。 |
| `usage_plan_name` | `VARCHAR(255)` | NO |  | API Gateway Usage Plan名。 |
| `default_rate_limit` | `INT` | YES |  | 通常時の1秒あたりリクエスト数上限。 |
| `default_burst_limit` | `INT` | YES |  | 短時間の急増を許容するリクエスト数上限。 |
| `default_quota_limit` | `INT` | YES |  | 指定期間内に利用できる総リクエスト数上限。 |
| `default_quota_period` | `VARCHAR(10)` | YES |  | 総リクエスト数上限を集計する期間。DAY、WEEK、MONTH。 |
| `last_synced_at` | `TIMESTAMPTZ` | YES |  | API Gatewayとの最終同期日時。 |
| `created_at` | `TIMESTAMPTZ` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `TIMESTAMPTZ` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
