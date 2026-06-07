# api_gateway_stages

API Gateway REST APIのstage、呼び出しURL、認可設定の観測結果を表す。利用可能状態はapi_stage_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `api_stage_id` | `CHAR(36)` | NO | PK | API stage ID。 |
| `api_id` | `CHAR(36)` | NO | FK -> apis(api_id) | 紐づくAPI ID。 |
| `aws_account_id` | `VARCHAR(12)` | NO |  | API Gatewayが存在するAWSアカウントID。 |
| `aws_region` | `VARCHAR(32)` | NO |  | API Gatewayが存在するAWSリージョン。例: ap-northeast-1。 |
| `apigw_rest_api_id` | `VARCHAR(128)` | NO |  | API Gateway REST API ID。 |
| `apigw_stage_name` | `VARCHAR(128)` | NO |  | API Gateway stage名。例: prod。 |
| `invoke_url` | `TEXT` | NO |  | execute-apiの呼び出しURL。 |
| `custom_domain_url` | `TEXT` | YES |  | カスタムドメインの呼び出しURL。 |
| `deployment_id` | `VARCHAR(128)` | YES |  | API Gateway deployment ID。 |
| `authorizer_id` | `VARCHAR(128)` | YES |  | Cognito authorizer ID。 |
| `api_key_required_observed` | `BOOLEAN` | NO |  | API Gateway methodでAPI key必須が設定されているかの検証結果。 |
| `scope_config_observed` | `VARCHAR(30)` | NO |  | Cognito scope設定の検証結果。VERIFIED、NOT_CONFIGURED、UNKNOWN。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |

## テーブル制約

- `UNIQUE (aws_account_id, aws_region, apigw_rest_api_id, apigw_stage_name)`
