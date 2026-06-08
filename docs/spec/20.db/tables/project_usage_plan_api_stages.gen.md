# project_usage_plan_api_stages

承認時にProject Usage Planへ追加したAPI stageの紐づけを表す。状態はusage_plan_stage_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `usage_plan_api_stage_id` | `CHAR(36)` | NO | PK | Usage Plan stage紐づけID。 |
| `project_id` | `CHAR(36)` | NO | FK -> projects(project_id) | 紐づくProject ID。 |
| `project_usage_plan_id` | `CHAR(36)` | NO | FK -> project_usage_plans(project_usage_plan_id) | 紐づくProject Usage Plan ID。 |
| `subscription_id` | `CHAR(36)` | NO | FK -> project_api_subscriptions(subscription_id) | 紐づく利用権ID。 |
| `api_stage_id` | `CHAR(36)` | NO | FK -> api_gateway_stages(api_stage_id) | 紐づくAPI stage ID。 |
| `apigw_rest_api_id` | `VARCHAR(128)` | NO |  | API Gateway REST API ID。 |
| `apigw_stage_name` | `VARCHAR(128)` | NO |  | API Gateway stage名。 |
| `provisioned_at` | `DATETIME(6)` | YES |  | API Gatewayへ反映した日時。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
