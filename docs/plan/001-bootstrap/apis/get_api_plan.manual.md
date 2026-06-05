# get_api 実装計画

## 目的

利用者、審査者、管理者が、公開済み API の詳細、認可 scope、審査者、呼び出し条件を確認できるようにする。

## 方針

- API Gateway REST API ID、stage、scope、OpenAPI metadata、審査者情報を返す。
- secret や AWS 操作に不要な内部情報は response に含めない。
- API が存在しない場合と参照権限がない場合のエラーを明確に分ける。
- unit test では SQLite in-memory で参照権限と not found を検証する。

## 実装計画

1. 対象 API を取得する。
2. API が公開済みまたは呼び出し元が参照可能な状態であることを確認する。
3. API Gateway REST API ID、stage、scope、reviewer を取得する。
4. OpenAPI metadata と利用条件を取得する。
5. 参照可能な項目だけを response に整形する。
6. API 詳細を返す。

## 作業

- API 詳細取得 API の contract、response schema、router を実装する。
- API、stage、reviewer、OpenAPI metadata を取得する SQL を実装する。
- 参照権限と not found のエラーハンドリングを実装する。
- 詳細 response の整形と不要な内部情報の除外を実装する。
- 正常系、not found、権限不足の単体テストを作成する。

## 完了条件

- `GET /apis/{apiId}` で API 詳細を取得できる。
- 利用申請に必要な scope と審査者情報を確認できる。
- エラー仕様が API spec と一致している。
