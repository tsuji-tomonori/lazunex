# project_members

プロジェクトメンバーとProject内の役割を表す。状態はproject_member_eventsから導出する。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `project_member_id` | `CHAR(36)` | NO | PK | Project member ID。 |
| `project_id` | `CHAR(36)` | NO | FK -> projects(project_id) | 所属Project ID。 |
| `member_principal_id` | `VARCHAR(256)` | NO |  | メンバーのprincipal。 |
| `member_role` | `VARCHAR(20)` | NO |  | Project内の役割。OWNER、ADMIN、VIEWER。 |
| `created_at` | `DATETIME(6)` | NO |  | 作成日時。 |
| `created_by` | `VARCHAR(256)` | NO |  | 作成者のprincipal。 |
| `updated_at` | `DATETIME(6)` | NO |  | 更新日時。 |
| `updated_by` | `VARCHAR(256)` | NO |  | 更新者のprincipal。 |
| `row_version` | `INT` | NO |  | 楽観ロック用の行バージョン。 |

## テーブル制約

- `UNIQUE (project_id, member_principal_id)`
