# publish_api 実装計画

## 目的

API 提供者または Hub 管理者が、デプロイ済み API Gateway REST API を Lazunex の API カタログへ公開登録できるようにする。

## 方針

- 対象 API は既に API Gateway REST API にデプロイ済みである前提にする。
- 登録時に API metadata、stage、OpenAPI 情報、審査者、認可 scope を DB に保存する。
- Cognito Resource Server の custom scope は resource integration 経由で同期反映する。
- 変更系 API として `Idempotency-Key` を必須にし、反映結果を provisioning operation/step に残す。

## 実装計画

1. API 公開登録リクエストを検証する。
2. 呼び出し元が API 提供者または Hub 管理者であることを確認する。
3. `Idempotency-Key` から既存 operation の有無を確認する。
4. API Gateway REST API ID と stage の登録情報を検証する。
5. 登録対象 API が未登録であることを確認する。
6. API 公開用の provisioning operation を作成する。
7. FastAPI API Lambda が Cognito Resource Server に custom scope を追加する。
8. API metadata、stage、reviewer、OpenAPI metadata、scope を保存する。
9. `api.published` イベントを追記する。
10. `audit_events` を追記する。
11. 公開登録した API 情報を返す。

## 作業

- API 公開登録 API の contract、request/response schema、router を実装する。
- API metadata、stage、reviewer、OpenAPI metadata、scope の保存 SQL を実装する。
- Cognito Resource Server scope 反映の resource integration を実装する。
- provisioning operation/step と audit event の保存処理を実装する。
- 正常系、重複実行、Cognito 反映失敗の単体テストを作成する。

## 完了条件

- `POST /apis` で API カタログへ登録できる。
- `api:{apiId}:invoke` 相当の scope 反映方針が実装に表れている。
- 部分失敗時に再実行可能な operation 記録が残る。
