# update_project_public_client 実装計画

## 目的

Project owner が PKCE 用 public App Client の callback URL、logout URL、token 設定を変更できるようにする。

## 方針

- public App Client のみを対象にし、confidential App Client の secret 再発行は扱わない。
- Cognito App Client 更新は resource integration 経由で同期実行する。
- 変更内容と反映結果を audit/provisioning に記録する。
- `Idempotency-Key` により同じ変更の二重反映を防ぐ。

## 実装計画

1. public client 更新リクエストを検証する。
2. 対象 Project を取得する。
3. 呼び出し元が Project owner であることを確認する。
4. Project の public App Client metadata を取得する。
5. `Idempotency-Key` から既存 operation の有無を確認する。
6. public client 更新用の provisioning operation を作成する。
7. FastAPI API Lambda が Cognito App Client を `DescribeUserPoolClient` で取得する。
8. callback URL、logout URL、token 設定をマージする。
9. FastAPI API Lambda が Cognito `UpdateUserPoolClient` を実行する。
10. public App Client metadata を更新する。
11. `project_public_client.updated` と `audit_events` を追記する。
12. 更新後の public client 設定概要を返す。

## 作業

- public client 更新 API の contract、request/response schema、router を実装する。
- Project owner 認可と public client metadata 取得 SQL を実装する。
- Cognito App Client 更新の resource integration を実装する。
- DB metadata 更新、provisioning operation/step、audit event 記録を実装する。
- 正常系、権限不足、Cognito 失敗、冪等再送の単体テストを作成する。

## 完了条件

- `PATCH /projects/{projectId}/public-client` で public App Client 設定を更新できる。
- 更新内容が DB metadata と Cognito 反映結果に整合している。
- 失敗時に再実行可能な operation 記録が残る。
