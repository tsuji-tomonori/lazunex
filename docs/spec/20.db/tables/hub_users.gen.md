# hub_users

Hub内の利用者、API提供者、審査者、プロジェクトメンバーを表す。状態はhub_user_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | `CHAR(36)` | NO | PK | Hub内ユーザーID。 |
| `external_subject` | `VARCHAR(256)` | NO | UNIQUE | Cognito subまたは社内IdPのsubject。 |
| `email` | `VARCHAR(320)` | NO |  | メールアドレス。 |
| `display_name` | `VARCHAR(200)` | NO |  | 表示名。 |
| `department_code` | `VARCHAR(64)` | NO |  | 所属部門コード。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
