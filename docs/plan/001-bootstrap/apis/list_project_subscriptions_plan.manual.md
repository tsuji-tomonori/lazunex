# list_project_subscriptions 実装計画

## 目的

Project owner、API 実行クライアント、Hub 管理者が、Project で現在利用可能な API 一覧を取得できるようにする。

## 方針

- 承認済み subscription を正とし、呼び出し先、scope、API key metadata、利用条件を返す。
- API 実行クライアントからの参照は Cognito token の `sub`、`client_id`、scope をもとに Project を解決する。
- secret 値は返さない。
- Runtime API 呼び出しに必要な `Authorization` と `X-API-Key` の利用前提を仕様に反映する。

## 実装計画

1. Project ID と一覧取得条件を検証する。
2. 対象 Project を取得する。
3. 呼び出し元が Project owner、API 実行クライアント、Hub 管理者のいずれかであることを確認する。
4. active subscription を検索する。
5. 対象 API metadata、stage、scope、呼び出し条件を取得する。
6. API key metadata と client metadata を取得する。
7. secret 値を含めずに response を整形する。
8. 利用可能 API 一覧を返す。

## 作業

- Project subscription 一覧 API の contract、response schema、router を実装する。
- subscription、API metadata、Project metadata を取得する SQL を実装する。
- Project owner/admin/client credentials の参照制御を実装する。
- 利用可能 API 一覧 response の整形と secret 非表示を実装する。
- 承認済みのみ返すこと、secret 非表示、権限別表示の単体テストを作成する。

## 完了条件

- `GET /projects/{projectId}/subscriptions` で利用可能 API を取得できる。
- 承認済み API の呼び出しに必要な情報を返す。
- API key 値や client secret 値を返さない。
