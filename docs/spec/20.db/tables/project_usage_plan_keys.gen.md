# project_usage_plan_keys

API Gateway API KeyとUsage Planの紐づけを表す。解除はproject_usage_plan_key_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `project_usage_plan_key_id` | `CHAR(36)` | NO | PK | Usage Plan Key紐づけID。 |
| `project_id` | `CHAR(36)` | NO | FK -> projects(project_id) | 紐づくProject ID。 |
| `project_usage_plan_id` | `CHAR(36)` | NO | FK -> project_usage_plans(project_usage_plan_id) | 紐づくProject Usage Plan ID。 |
| `project_api_key_id` | `CHAR(36)` | NO | FK -> project_api_keys(project_api_key_id) | 紐づくProject API Key ID。 |
| `apigw_usage_plan_key_id` | `VARCHAR(128)` | NO | UNIQUE | API Gateway Usage Plan Key ID。 |
| `apigw_usage_plan_id` | `VARCHAR(128)` | NO |  | API Gateway Usage Plan ID。 |
| `apigw_api_key_id` | `VARCHAR(128)` | NO |  | API Gateway API Key ID。 |
| `provisioned_at` | `DATETIME(6)` | YES |  | AWSへ紐づけを反映した日時。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |

## テーブル制約

- `UNIQUE (project_usage_plan_id, project_api_key_id)`
