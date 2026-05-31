# update_project_public_client 実装計画

## 目的

Project owner が PKCE 用 public App Client の callback URL、logout URL、token 設定を変更できるようにする。

## 方針

- public App Client のみを対象にし、confidential App Client の secret 再発行は扱わない。
- Cognito App Client 更新は resource integration 経由で同期実行する。
- 変更内容と反映結果を audit/provisioning に記録する。
- `Idempotency-Key` を `idempotency_records` に記録し、同じ変更の二重反映を防ぐ。
- Cognito 更新の AWS API 呼び出しは provisioning step と provisioning event に残す。

## 実装計画

1. public client 更新リクエストを検証する。
2. 対象 Project を取得する。
3. 呼び出し元が Project owner であることを確認する。
4. Project の public App Client metadata を取得する。
5. `Idempotency-Key` から既存 operation の有無を確認する。
6. public client 更新用の provisioning operation を作成する。
7. `idempotency_records` を作成または確認する。
8. FastAPI API Lambda が Cognito App Client を `DescribeUserPoolClient` で取得し、provisioning step を記録する。
9. callback URL、logout URL、token 設定をマージする。
10. FastAPI API Lambda が Cognito `UpdateUserPoolClient` を実行し、provisioning step を記録する。
11. public App Client metadata を更新する。
12. `project_public_client.updated`、provisioning operation/step event、`audit_events` を追記する。
13. 更新後の public client 設定概要を返す。

## 作業

- public client 更新 API の contract、request/response schema、router を実装する。
- Project owner 認可と public client metadata 取得 SQL を実装する。
- Cognito App Client 更新の resource integration を実装する。
- DB metadata 更新、provisioning operation/step、provisioning event、audit event 記録を実装する。
- `idempotency_records` の保存 SQL を実装する。
- 正常系、権限不足、Cognito 失敗、冪等再送の単体テストを作成する。

## 完了条件

- `PATCH /projects/{projectId}/public-client` で public App Client 設定を更新できる。
- 更新内容が DB metadata と Cognito 反映結果に整合している。
- 失敗時に再実行可能な operation 記録が残る。
