# create_project 実装計画

## 目的

API 利用者が API 利用単位となる Project を作成し、API key、Usage Plan、Cognito App Client を払い出せるようにする。

## 方針

- Project 作成時に API Gateway API key、Usage Plan、public/confidential App Client を同期作成する。
- API key と client secret は初回レスポンスでのみ返し、DB にはハッシュと末尾だけを保存する。
- AWS 反映は resource integration に閉じ、失敗時は provisioning operation/step に記録する。
- unit test では AWS を呼ばず fake integration で払い出し結果を検証する。

## 実装計画

1. Project 作成リクエストを検証する。
2. 呼び出し元が Project を作成できる利用者であることを確認する。
3. `Idempotency-Key` から既存 operation の有無を確認する。
4. Project 作成用の provisioning operation を作成する。
5. FastAPI API Lambda が API Gateway API key を作成する。
6. FastAPI API Lambda が API Gateway Usage Plan を作成する。
7. FastAPI API Lambda が Cognito public App Client を作成する。
8. FastAPI API Lambda が Cognito confidential App Client を作成する。
9. API key 値と client secret 値の hash、hash key version、last4 を計算する。
10. `projects`、Project owner、API key metadata、Usage Plan metadata、App Client metadata を保存する。
11. `project.created`、`project.provisioned`、`audit_events` を追記する。
12. 初回レスポンスとして API key 値と client secret 値を返す。

## 作業

- Project 作成 API の contract、request/response schema、router を実装する。
- Project、owner、API key、Usage Plan、App Client metadata の保存 SQL を実装する。
- API Gateway と Cognito の resource integration を実装する。
- secret hash 生成と平文非保存の処理を実装する。
- 正常系、冪等再送、部分失敗、secret 非保存の単体テストを作成する。

## 完了条件

- `POST /projects` で Project を作成できる。
- 初回レスポンス以外で API key 値や client secret 値を返さない。
- DB には secret 平文が保存されない。
