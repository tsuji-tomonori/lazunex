# api_reviewers

APIごとの審査者割当を表す。追加や削除はapi_reviewer_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `api_reviewer_id` | `UUID` | NO | PK | API審査者割当ID。 |
| `api_id` | `UUID` | NO | FK -> apis(api_id) | 審査対象API ID。 |
| `reviewer_principal_id` | `VARCHAR(256)` | NO |  | 審査者のprincipal。 |
| `reviewer_role` | `VARCHAR(20)` | NO |  | 審査者の役割。PRIMARY、BACKUP、ADMIN。 |
| `created_at` | `TIMESTAMPTZ` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `TIMESTAMPTZ` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
