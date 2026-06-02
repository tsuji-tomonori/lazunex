# approve_api_access_request 実装計画

## 目的

API 審査者または Hub 管理者が利用申請を承認し、Usage Plan と Cognito App Client の scope へ同期反映できるようにする。

## 方針

- 承認対象 request が審査中であることを確認する。
- Usage Plan への API stage 追加と App Client への custom scope 追加を同期実行する。
- DB の subscription、request 状態、provisioning operation/step、audit event を整合させる。
- `Idempotency-Key` を `idempotency_records` に記録し、二重承認を防ぐ。
- Usage Plan stage 追加と App Client scope 付与は `usage_plan_stage_events`、`client_scope_events` に残す。
- 途中失敗時は partial failure として記録し、同一 operation を再実行可能にする。

## 実装計画

1. 対象申請を取得する。
2. 申請が `PENDING` 相当であることを確認する。
3. 審査者が対象 API の reviewer であることを確認する。
4. project/API/stage が利用可能であることを確認する。
5. 既存 active subscription がないことを確認する。
6. `access_request.approving` イベントを追記する。
7. Provisioning operation を作成する。
8. `idempotency_records` を作成または確認する。
9. FastAPI API Lambda が API Gateway `UpdateUsagePlan` で API stage を追加し、provisioning step を記録する。
10. FastAPI API Lambda が Cognito App Client を `DescribeUserPoolClient` で取得する。
11. 既存 `AllowedOAuthScopes` に対象 scope をマージする。
12. FastAPI API Lambda が Cognito `UpdateUserPoolClient` を実行し、provisioning step を記録する。
13. `api_access_reviews`、`project_api_subscriptions`、`project_usage_plan_api_stages`、`project_cognito_client_scopes` を保存する。
14. `usage_plan_stage_events`、`client_scope_events` を追記する。
15. `access_request.approved`、`subscription.provisioned`、provisioning operation/step event、`audit_events` を追記する。

## 作業

- 承認 API の contract、request/response schema、router を実装する。
- 対象申請、Project、API、stage、subscription を取得・検証する SQL を実装する。
- API Gateway と Cognito の resource integration を実装する。
- provisioning operation/step、provisioning event、audit event の保存処理を実装する。
- `idempotency_records`、Usage Plan stage event、client scope event の保存 SQL を実装する。
- 正常系、権限不足、状態不正、片側反映失敗、冪等再送の単体テストを作成する。

## 実装状況

- router は `AsyncSession` と request context を依存注入し、承認 sequence に渡す。
- 対象 access request 取得時に DB から `apigw_rest_api_id`、`apigw_stage_name`、API scope、Cognito scope を解決する。
- 承認時の API Gateway `UpdateUsagePlan` は `project_usage_plans.apigw_usage_plan_id` と API stage の AWS ID を使う。
- Cognito client 更新は `project_cognito_clients.app_client_id` と user pool ID を使い、既存 client 設定に scope を merge して更新する。
- `provisioning_operations`、`idempotency_records`、`api_access_reviews`、`project_api_subscriptions`、`project_usage_plan_api_stages`、`project_cognito_client_scopes` への保存を実装済み。
- `usage_plan_stage_events`、`client_scope_events`、承認後の lifecycle/provisioning/audit event 永続化、既存 idempotency record の read/replay は未接続。

## 完了条件

- `POST /api-access-requests/{accessRequestId}/approve` で申請を承認できる。
- 承認済み subscription が作成される。
- Usage Plan と App Client scope の反映結果を追跡できる。
