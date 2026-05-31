# projects

API利用単位となるプロジェクトを表す。状態はproject_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `project_id` | `UUID` | NO | PK | Project ID。 |
| `project_code` | `VARCHAR(100)` | NO | UNIQUE | 人が読めるProjectコード。例: payment-frontend。 |
| `name` | `VARCHAR(200)` | NO |  | プロジェクト名。 |
| `description` | `TEXT` | NO |  | プロジェクトの説明。 |
| `owner_principal_id` | `VARCHAR(256)` | NO |  | プロジェクトオーナーのprincipal。 |
| `department_code` | `VARCHAR(64)` | NO |  | 部門コード。 |
| `created_at` | `TIMESTAMPTZ` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `TIMESTAMPTZ` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
