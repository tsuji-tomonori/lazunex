# provisioning_steps

AWS反映operation内のAWS API呼び出し単位のstepを表す。状態はprovisioning_step_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `operation_step_id` | `UUID` | NO | PK | AWS反映step ID。 |
| `operation_id` | `UUID` | NO | FK -> provisioning_operations(operation_id) | 親operation ID。 |
| `step_order` | `INT` | NO |  | operation内の実行順。 |
| `step_name` | `VARCHAR(100)` | NO |  | step名。例: CREATE_API_KEY。 |
| `aws_service` | `VARCHAR(50)` | NO |  | 呼び出し先AWSサービス。APIGATEWAY、COGNITO_IDP、SECRETS_MANAGER。 |
| `aws_action` | `VARCHAR(100)` | NO |  | 呼び出したAWS API名。 |
| `request_payload` | `JSON` | YES |  | AWS API入力内容。secret値はマスクする。 |
| `response_payload` | `JSON` | YES |  | AWS API出力内容。secret値はマスクする。 |
| `error_code` | `VARCHAR(100)` | YES |  | 失敗時のエラーコード。 |
| `error_message` | `TEXT` | YES |  | 失敗時のエラーメッセージ。 |
| `started_at` | `TIMESTAMPTZ` | YES |  | step開始日時。 |
| `finished_at` | `TIMESTAMPTZ` | YES |  | step終了日時。 |
| `created_at` | `TIMESTAMPTZ` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `TIMESTAMPTZ` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
