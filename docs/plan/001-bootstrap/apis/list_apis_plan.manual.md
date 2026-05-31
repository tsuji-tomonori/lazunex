# list_apis 実装計画

## 目的

利用者、審査者、管理者が、公開済み API の一覧を取得し、利用申請や審査の起点にできるようにする。

## 方針

- 公開済み API を主対象にし、必要な検索・ページング条件を request schema に閉じる。
- 一覧では詳細な OpenAPI 本文ではなく、申請判断に必要な概要情報を返す。
- 認可条件は呼び出し元の role/group/scope をもとに service 層で判定する。
- unit test では SQLite in-memory で権限別の表示範囲とページングを検証する。

## 実装計画

1. 一覧取得条件を検証する。
2. 呼び出し元の role/group/scope を取得する。
3. 参照可能な公開 API を検索する。
4. API metadata、scope、reviewer、利用条件を取得する。
5. `limit` と `nextToken` を適用する。
6. 一覧 response に整形する。
7. API 一覧を返す。

## 作業

- API 一覧取得 API の contract、response schema、router を実装する。
- API metadata を取得する SQL を実装する。
- pagination と参照範囲の制御を実装する。
- 一覧 response の整形と nextToken 生成を実装する。
- 正常系、権限別表示、ページングの単体テストを作成する。

## 完了条件

- `GET /apis` で API 一覧を取得できる。
- 一覧レスポンスが申請作成に必要な API 識別子と概要を含む。
- ページング付きの取得方針が実装されている。
