# reject_api_access_request 実装計画

## 目的

API 審査者または Hub 管理者が利用申請を却下し、理由と審査結果を記録できるようにする。

## 方針

- 却下では AWS resource への反映を行わない。
- 申請状態、却下理由、審査者、監査イベントを DB に保存する。
- 審査中以外の request は状態不正として扱う。
- `Idempotency-Key` を `idempotency_records` に記録し、二重却下を防ぐ。

## 実装計画

1. 対象申請を取得する。
2. 申請が `PENDING` 相当であることを確認する。
3. 審査者が対象 API の reviewer または Hub 管理者であることを確認する。
4. 却下理由を検証する。
5. `access_request.rejecting` イベントを追記する。
6. `api_access_reviews` に却下結果を保存する。
7. `idempotency_records` を作成または確認する。
8. 申請状態を `REJECTED` 相当に更新する。
9. `access_request.rejected` イベントを追記する。
10. `audit_events` を追記する。
11. 却下結果を返す。

## 作業

- 却下 API の contract、request/response schema、router を実装する。
- reviewer/admin 認可と request 状態確認 SQL を実装する。
- request 状態更新、review 保存、audit event 記録を実装する。
- `Idempotency-Key` による二重却下防止と `idempotency_records` 保存 SQL を実装する。
- 正常系、権限不足、状態不正、冪等再送の単体テストを作成する。

## 実装状況

- router は `CallerIdentity`、`AsyncSession`、request context を依存注入し、application sequence に渡す。
- 対象 access request 取得と reviewer 権限確認は生成済み query で実行する。
- `access_request.rejecting` / `access_request.rejected` event、`api_access_reviews`、`idempotency_records`、`audit_events` への保存を実装済み。
- 却下では AWS integration を呼び出さず、DB 変更と監査記録に閉じる。
- 現状の idempotency は成功レスポンス snapshot の保存までで、既存 record の read/replay と状態更新 SQL は未接続。

## 完了条件

- `POST /api-access-requests/{accessRequestId}/reject` で申請を却下できる。
- 却下理由と審査者を追跡できる。
- AWS resource に不要な変更を行わない。
