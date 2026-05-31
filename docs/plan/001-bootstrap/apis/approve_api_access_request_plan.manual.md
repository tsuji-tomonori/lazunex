# approve_api_access_request 実装計画

## 目的

API 審査者または Hub 管理者が利用申請を承認し、Usage Plan と Cognito App Client の scope へ同期反映できるようにする。

## 方針

- 承認対象 request が審査中であることを確認する。
- Usage Plan への API stage 追加と App Client への custom scope 追加を同期実行する。
- DB の subscription、request 状態、provisioning operation/step、audit event を整合させる。
- 途中失敗時は partial failure として記録し、同一 operation を再実行可能にする。

## 実装計画

1. 対象申請を取得する。
2. 申請が `PENDING` 相当であることを確認する。
3. 審査者が対象 API の reviewer であることを確認する。
4. project/API/stage が利用可能であることを確認する。
5. 既存 active subscription がないことを確認する。
6. `access_request.approving` イベントを追記する。
7. Provisioning operation を作成する。
8. FastAPI API Lambda が API Gateway `UpdateUsagePlan` で API stage を追加する。
9. FastAPI API Lambda が Cognito App Client を `DescribeUserPoolClient` で取得する。
10. 既存 `AllowedOAuthScopes` に対象 scope をマージする。
11. FastAPI API Lambda が Cognito `UpdateUserPoolClient` を実行する。
12. `api_access_reviews`、`project_api_subscriptions`、`project_usage_plan_api_stages`、`project_cognito_client_scopes` を保存する。
13. `access_request.approved`、`subscription.provisioned`、`audit_events` を追記する。

## 作業

- 承認 API の contract、request/response schema、router を実装する。
- 対象申請、Project、API、stage、subscription を取得・検証する SQL を実装する。
- API Gateway と Cognito の resource integration を実装する。
- provisioning operation/step と audit event の保存処理を実装する。
- 正常系、権限不足、状態不正、片側反映失敗、冪等再送の単体テストを作成する。

## 完了条件

- `POST /api-access-requests/{accessRequestId}/approve` で申請を承認できる。
- 承認済み subscription が作成される。
- Usage Plan と App Client scope の反映結果を追跡できる。
