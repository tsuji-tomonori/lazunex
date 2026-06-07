# project_member_events

Projectメンバーの追加、役割変更、削除などを追記するイベントテーブル。

| カラム | 型 | NULL許可 | キー | 説明 |
| :--- | :--- | :--- | :--- | :--- |
| `event_id` | `CHAR(36)` | NO | PK | イベントID。 |
| `aggregate_id` | `CHAR(36)` | NO |  | イベント対象のProject member ID。 |
| `event_seq` | `BIGINT` | NO |  | Project memberごとのイベント連番。 |
| `event_name` | `VARCHAR(128)` | NO |  | イベント名。 |
| `actor_principal_id` | `VARCHAR(256)` | NO |  | イベントを発生させた主体のprincipal。 |
| `actor_type` | `VARCHAR(32)` | NO |  | イベント発生主体種別。USER、SYSTEM、CI。 |
| `occurred_at` | `DATETIME(6)` | NO |  | イベント発生日時。 |
| `reason` | `TEXT` | YES |  | イベントの理由またはコメント。 |
| `correlation_id` | `VARCHAR(128)` | NO |  | API requestを横断して追跡する相関ID。 |
| `idempotency_key` | `VARCHAR(256)` | YES |  | 関連する冪等性キー。 |
| `event_payload` | `JSON` | YES |  | イベント固有情報。secret値は含めない。 |

## テーブル制約

- `UNIQUE (aggregate_id, event_seq)`
