# create_api_access_request 実装計画

## 目的

Project owner が Project 単位で利用したい API を選び、利用理由と認証方式を指定して申請できるようにする。

## 方針

- Project と API の組み合わせを申請単位にする。
- 既存の承認済み subscription や審査中 request との重複を制御する。
- 作成時点では AWS resource へ反映せず、申請状態と監査イベントを保存する。
- 変更系 API として `Idempotency-Key` を前提にする。

## 実装計画

1. 利用申請作成リクエストを検証する。
2. 対象 Project を取得する。
3. 呼び出し元が Project owner であることを確認する。
4. 対象 API が公開済みであることを確認する。
5. 対象 API の reviewer を取得する。
6. 既存 active subscription がないことを確認する。
7. 同一 Project/API の審査中申請がないことを確認する。
8. `api_access_requests` に `PENDING` 相当の申請を保存する。
9. `access_request.created` イベントを追記する。
10. `audit_events` を追記する。
11. 作成した申請情報を返す。

## 作業

- 利用申請作成 API の contract、request/response schema、router を実装する。
- Project owner 認可、API 公開状態確認、重複確認の SQL を実装する。
- access request と audit event の保存処理を実装する。
- `Idempotency-Key` による二重作成防止を実装する。
- 正常系、重複、権限不足、存在しない API/Project の単体テストを作成する。

## 完了条件

- `POST /projects/{projectId}/api-access-requests` で利用申請を作成できる。
- 審査対象 API と reviewer を追跡できる。
- 重複申請を適切に防止できる。
