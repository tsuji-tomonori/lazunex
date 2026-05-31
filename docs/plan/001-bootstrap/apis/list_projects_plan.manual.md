# list_projects 実装計画

## 目的

API 利用者、Project owner、Hub 管理者が、自分の参照可能な Project 一覧を取得できるようにする。

## 方針

- 呼び出し元の Cognito token 情報をもとに参照可能な Project を絞り込む。
- secret 値は一覧に含めず、metadata と状態だけを返す。
- 一覧は pagination を前提にし、将来の検索条件追加に備える。
- unit test では SQLite in-memory で権限別の表示範囲と secret 非表示を検証する。

## 実装計画

1. 一覧取得条件を検証する。
2. 呼び出し元の `sub`、group、scope を取得する。
3. 呼び出し元が参照可能な Project を検索する。
4. Project owner/member 情報を取得する。
5. API key/App Client の概要 metadata を取得する。
6. `limit` と `nextToken` を適用する。
7. secret 値を含めずに Project 一覧を返す。

## 作業

- Project 一覧取得 API の contract、response schema、router を実装する。
- Project owner/member/admin の参照範囲を表す SQL を実装する。
- API key/App Client metadata の response 整形を実装する。
- pagination と nextToken 生成を実装する。
- 権限別、ページング、secret 非表示の単体テストを作成する。

## 完了条件

- `GET /projects` で参照可能な Project 一覧を取得できる。
- secret 値を返さない。
- role に応じた表示範囲が検証されている。
