# api_access_reviews

利用申請に対する承認または却下の審査結果を表す事実テーブル。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `access_review_id` | `UUID` | NO | PK | 審査ID。 |
| `access_request_id` | `UUID` | NO | FK -> api_access_requests(access_request_id) | 審査対象の利用申請ID。 |
| `decision` | `VARCHAR(20)` | NO |  | 審査結果。APPROVEDまたはREJECTED。 |
| `approved_auth_mode` | `VARCHAR(30)` | YES |  | 承認された認証方式。却下時はNULL。 |
| `reviewer_principal_id` | `VARCHAR(256)` | NO |  | 審査者のprincipal。 |
| `review_comment` | `TEXT` | YES |  | 審査コメント。 |
| `reviewed_at` | `TIMESTAMPTZ` | NO |  | 審査日時。 |
| `created_at` | `TIMESTAMPTZ` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `TIMESTAMPTZ` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |
